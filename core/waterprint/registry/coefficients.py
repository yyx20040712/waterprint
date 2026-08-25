"""去除率/经验系数库加载：数据驱动，随规范版本演进（清单只存引用键）。

输入:  data/coefficients/ YAML 数据包（带版本与出处）
输出:  Coefficients 查询对象 + data_version（可复算三元组成员）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T5 实现；镜像测试 tests/registry/test_coefficients.py）
#
# 【公开接口】
#   class CoefficientValue(不可变)：value: float / unit: str / source: str /
#       note: str——四字段，key 在映射层不重复入条目（unit 为非空 str
#       原样透出：真实包含 "1e3m3"/"m3/(m2.h)" 等展示单位，不做
#       CANONICAL_UNITS 校验——条目不带 DimKey，量纲一致性由消费侧
#       公式量纲签名层负责，本层校验=发明映射）
#   class Coefficients(不可变)：
#       data_version: str          数据包版本（三元组成员，§16 A8）
#       get(key: str) -> CoefficientValue
#           未知键 = InvalidCoefficientError（禁 None），消息含
#           key+data_version
#       keys(prefix: str = "") -> tuple[str, ...]
#           前缀列举（单元/指标分组），排序返回（GR-18 确定性）
#       require_keys(keys: Iterable[str]) -> None
#           R3 失联键闭环的执行面：缺任一键 = InvalidCoefficientError
#           （消息含缺失键清单+data_version）；T7 装配层对
#           manifest.removal_refs 值集调用
#   load_coefficients(path: str | Path) -> Coefficients
#       加载正门：目录数据包（manifest.yaml + 其余全部 *.yaml 条目文件）
#       → 严格校验 → 不可变对象
#   class InvalidCoefficientError(Exception)
#       装载/查询/require_keys 一切拒绝的统一载体（GR-11 族）
#
# 【行为规格】
#   R1 数据驱动：去除率、经验系数（如各单元 BOD5/COD/SS/NH3-N/TN/TP
#      去除率、曝气修正系数、污泥产率等）全部来自数据包；代码内出现
#      具体系数数值 = 评审拒绝（数值只允许出现在测试期望与数据包）。
#   R2 每条系数必须带 source；数据包整体带 data_version——数据更新
#      = 版本号变化 = 全部旧结果过期（可复算三元组）。
#   R3 manifest.removal_refs 引用的键必须可在包内解析，加载时静态校验，
#      失联键 = 启动失败。【T5 注记】执行面 = require_keys（本文件），
#      装配层 T7 接线（当前 units_lib 全骨架无真实对象，机制经探针实证）。
#   R4 数据包只读：内核不写 data/（写入是数据维护流程，走版本化发布）。
#
# 【装载口径】（T5 D1 裁决 2026-08-24——锁定测试 entries.yaml 单文件与
#   真实包 manifest+factors+removal_rates 双文件张力的消解）
#   - path 须为目录（否则拒）；目录内 manifest.yaml 必在（缺=拒）。
#   - manifest：yaml.safe_load 须为 dict；data_version 键必在且非空 str；
#     未知键拒（R1e 同精神——真实包注释行由 YAML 解析器剥除不受扰）。
#   - 其余全部 *.yaml 为条目文件，按文件名排序逐个装载（GR-18 确定性；
#     README.md 等非 yaml 忽略）；无任何条目文件 = 拒（GR-14 空集显式：
#     数据包无条目=装配缺陷）。
#   - 条目文件顶层须为 list（否则拒）；空 list = 拒；每条目恰五键
#     key/value/unit/source/note（多键少键均拒，防拼写静默）。
#   - key 非空 str 且全包唯一（跨文件+文件内重复均拒）；value 为
#     int|float 且非 bool、有限（GR-02），归一 float，巨 int 的
#     OverflowError 收编为本异常（ARCH1 D1 同款）；unit/source/note
#     非空 str（source 空白串=拒，锁定用例在册）。
#   - YAML 解析与解码异常一律 from exc 包装为本异常（消息区分
#     "解码失败（非 UTF-8）"与"YAML 解析失败"，二审 M-2）。
#   - Coefficients 内部 entries 映射构造即快照 MappingProxyType
#     （T3A-01 防线首日到位：外部改原容器不泄漏）。
#
# 【测试要求】加载往返、失联引用键拒绝、data_version 传播、
#   无 source 条目拒绝。
#
# 【参照】重写计划 §5/§16 A8；数据规格 data/coefficients/README.md；
#   简报 T5 D1/D2/D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Final, final

import yaml


class InvalidCoefficientError(Exception):
    """系数装载/查询非法（数据包形态/未知键/失联键）——领域异常。"""


_MANIFEST_NAME: Final[str] = "manifest.yaml"
_MANIFEST_KEYS: Final[frozenset[str]] = frozenset({"data_version"})
_ENTRY_KEYS: Final[frozenset[str]] = frozenset(
    {"key", "value", "unit", "source", "note"}
)


def _nonempty_str(value: object, what: str) -> str:
    """非空 str 守卫：类型不符/空串均拒，消息含字段名+原值。"""
    if not isinstance(value, str) or not value:
        raise InvalidCoefficientError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


def _normalize_value(key: str, value: object) -> float:
    """value 守卫（GR-02）：bool 拒/非数值拒/非有限拒，归一 float。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidCoefficientError(
            f"系数 {key!r} 的 value 必须为数值（int|float，bool 拒）："
            f"得到 {value!r}"
        )
    try:
        number = float(value)
    except OverflowError as exc:
        raise InvalidCoefficientError(
            f"系数 {key!r} 的 value 超出浮点域：原值类型 {type(value).__name__}"
            "（GR-02 输入即拒；ARCH1 D1 同款——原生异常收编）"
        ) from exc
    if not isfinite(number):
        raise InvalidCoefficientError(
            f"系数 {key!r} 的 value 非有限：{number!r}（GR-02 输入即拒）"
        )
    return number


@dataclass(frozen=True)
@final
class CoefficientValue:
    """单条系数：值 + 展示单位 + 出处 + 说明（四字段，key 在映射层）。"""

    value: float
    unit: str
    source: str
    note: str


@dataclass(frozen=True)
@final
class Coefficients:
    """系数库查询对象：data_version + 键→CoefficientValue 只读快照。"""

    data_version: str
    _entries: Mapping[str, CoefficientValue]

    def __post_init__(self) -> None:
        """entries 构造即快照（T3A-01 防线：外部改原容器不泄漏）。"""
        object.__setattr__(self, "_entries", MappingProxyType(dict(self._entries)))

    def get(self, key: str) -> CoefficientValue:
        """查询正门：未知键 = 领域异常（禁 None 假装成功）。"""
        try:
            return self._entries[key]
        except KeyError as exc:
            raise InvalidCoefficientError(
                f"未知系数键：{key!r}（数据包 data_version={self.data_version}；"
                "可用键经 keys() 前缀列举）"
            ) from exc

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """前缀列举（单元/指标分组），排序返回（GR-18 确定性）。"""
        return tuple(
            sorted(key for key in self._entries if key.startswith(prefix))
        )

    def require_keys(self, keys: Iterable[str]) -> None:
        """R3 失联键闭环执行面：缺任一键 = 领域异常（清单+版本在消息）。"""
        missing = sorted(key for key in keys if key not in self._entries)
        if missing:
            raise InvalidCoefficientError(
                f"失联系数键：{missing}（数据包 data_version={self.data_version} "
                "无法解析——manifest.removal_refs 引用必须可在包内解析，R3；"
                "装配层 T7 接线）"
            )


def _load_yaml(path: Path, what: str) -> object:
    """yaml.safe_load 唯一入口：解析/解码异常一律 from exc 包装（含文件名）。"""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        reason = (
            f"解码失败（非 UTF-8）：{exc}"
            if isinstance(exc, UnicodeDecodeError)
            else f"YAML 解析失败：{exc}"
        )
        raise InvalidCoefficientError(f"{what} {path.name} {reason}") from exc


def _load_manifest(directory: Path) -> str:
    """manifest 三守卫：必在 / 顶层为 dict / 键集恰 {data_version} 且值非空。"""
    manifest_file = directory / _MANIFEST_NAME
    if not manifest_file.is_file():
        raise InvalidCoefficientError(
            f"系数包缺 {_MANIFEST_NAME}：{directory}"
            "（版本与变更记录的唯一载体，R2 可复算三元组成员）"
        )
    data = _load_yaml(manifest_file, "清单文件")
    if not isinstance(data, dict):
        raise InvalidCoefficientError(
            f"{_MANIFEST_NAME} 顶层须为映射：得到 {type(data).__name__}"
        )
    unknown = sorted(set(data) - _MANIFEST_KEYS)
    if unknown:
        raise InvalidCoefficientError(
            f"{_MANIFEST_NAME} 含未知键：{unknown}"
            f"（只允许 {sorted(_MANIFEST_KEYS)}——R1e 同精神，真实包注释行不受扰）"
        )
    if "data_version" not in data:
        raise InvalidCoefficientError(
            f"{_MANIFEST_NAME} 缺 data_version 键（三元组成员，§16 A8）"
        )
    return _nonempty_str(data["data_version"], "data_version")


def _parse_entry(where: str, raw: object) -> tuple[str, CoefficientValue]:
    """单条目守卫：恰五键 + 逐字段校验，返回 (key, CoefficientValue)。"""
    if not isinstance(raw, dict):
        raise InvalidCoefficientError(
            f"条目形态非法（{where}）：须为五键映射，得到 {type(raw).__name__}"
        )
    given = set(raw)
    if given != _ENTRY_KEYS:
        raise InvalidCoefficientError(
            f"条目键集非法（{where}）：缺 {sorted(_ENTRY_KEYS - given)}，"
            f"多 {sorted(given - _ENTRY_KEYS)}（应恰为 {sorted(_ENTRY_KEYS)}"
            "——多键少键均拒，防拼写静默）"
        )
    key = _nonempty_str(raw["key"], f"条目 key（{where}）")
    source = _nonempty_str(raw["source"], f"系数 {key!r} 的 source")
    if not source.strip():
        raise InvalidCoefficientError(
            f"系数 {key!r} 的 source 不能为空白串（R2：无出处不准入库）"
        )
    return (
        key,
        CoefficientValue(
            value=_normalize_value(key, raw["value"]),
            unit=_nonempty_str(raw["unit"], f"系数 {key!r} 的 unit"),
            source=source,
            note=_nonempty_str(raw["note"], f"系数 {key!r} 的 note"),
        ),
    )


def _load_entry_files(directory: Path) -> dict[str, CoefficientValue]:
    """其余全部 *.yaml 按文件名排序逐个装载；键全包唯一（跨+文件内）。"""
    entry_files = sorted(
        path for path in directory.glob("*.yaml") if path.name != _MANIFEST_NAME
    )
    if not entry_files:
        raise InvalidCoefficientError(
            f"系数包无条目文件：{directory}"
            "（GR-14 空集显式：数据包无条目=装配缺陷，禁静默空库）"
        )
    entries: dict[str, CoefficientValue] = {}
    for path in entry_files:
        data = _load_yaml(path, "条目文件")
        if not isinstance(data, list):
            raise InvalidCoefficientError(
                f"条目文件 {path.name} 顶层须为列表：得到 {type(data).__name__}"
            )
        if not data:
            raise InvalidCoefficientError(
                f"条目文件 {path.name} 为空列表"
                "（GR-14：空文件=装配缺陷，删文件而非留空）"
            )
        for index, raw in enumerate(data):
            key, value = _parse_entry(f"{path.name}[{index}]", raw)
            if key in entries:
                raise InvalidCoefficientError(
                    f"系数键重复：{key!r}（{path.name}[{index}] 与既有条目冲突"
                    "——键全包唯一，跨文件与文件内重复均拒）"
                )
            entries[key] = value
    return entries


def load_coefficients(path: str | Path) -> Coefficients:
    """加载正门：目录数据包 → manifest 校验 → 逐条目文件校验 → 不可变对象。"""
    directory = Path(path)
    if not directory.is_dir():
        raise InvalidCoefficientError(
            f"系数包路径必须为目录：{path!r}（得到非目录——装载面只认数据包目录）"
        )
    return Coefficients(
        data_version=_load_manifest(directory),
        _entries=_load_entry_files(directory),
    )
