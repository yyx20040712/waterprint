"""定额单价加载与版本管理：YAML 数据包 → 不可变单价库（版本 = 三元组成员）。

输入:  data/unit_prices/*.yaml（每条带出处与版本）
输出:  PriceBook 查询对象 + price_data_version
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_prices.py）
#
# 【公开接口】
#   class PriceBook(不可变)：data_version、get(price_key) -> PriceItem、
#       keys(prefix) 列举（按章节/定额编号分组）
#   load_prices(path) -> PriceBook        加载正门（严格校验）
#   class PriceItem：price、unit、source（定额编号+出处，如 2019 黑龙江
#      建筑工程计价定额子目号）、note
#
# 【行为规格】
#   R1 数据驱动迁移：旧 src/models/cost/unit_prices.py 的单价迁移为
#      YAML，每条带出处；迁移时人工抽验 10%（§5 迁移清单——抽验流程
#      归 M0 数据整理，代码侧保证：无 source 条目加载即失败）。
#   R2 price_data_version 进入可复算三元组（data_version 聚合系数包与
#      单价包版本，三元组任一变化 = 概算结果过期，§16 A8）。
#   R3 takeoff 的 price_key 必须可解析：失联键 = 启动失败（静态校验，
#      与 coefficients 同门槛）。
#   R4 单价只读：不提供写入 API（数据维护走版本化发布流程）。
#
# 【COST2 实装注记】（概算段二，2026-08-28）
#   - D1 字段名归一：manifest 顶层版本字段读 price_data_version
#     （规格头 R2 原词；真库 manifest.yaml 已同步重命名，1.0.0 结构
#     修正不升版——与 coefficients 的 data_version 惯例分立）。
#   - 条目键集：必填 {key,name,unit,price,source} + 可选 {note,quantity}
#     （quantity=设备参考台数，仅设备族条目携带）；多键少键均拒，
#     source 缺失或空白 = 拒绝（R1 出处门槛），键全包唯一（跨文件）。
#   - field_mapping.yaml 是数据包伴生清单文件（takeoff 映射+费率 DSL，
#     COST2 新建），非单价条目——装载按文件名排除清单跳过。
#   - idiom 对齐 registry/coefficients：yaml.safe_load 唯一入口、
#     解析异常 from exc 包装、消息含键名与包版本（GR-11 Invalid* 族）。
#
# 【测试要求】加载往返、失联键拒绝、无 source 拒绝、版本传播进三元组。
#
# 【参照】重写计划 §5/§16 A8；数据规格 data/unit_prices/README.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import final

import yaml


class InvalidPriceError(Exception):
    """单价包装载/查询非法（结构/出处/重复键/失联键）——领域异常。"""


_MANIFEST_NAME = "manifest.yaml"
# manifest 顶层键集（真实包其余内容全为注释行，解析后恰此一键）。
_MANIFEST_KEYS = frozenset({"price_data_version"})
# 数据包伴生清单文件（非单价条目）：版本清单 + COST2 字段映射/费率 DSL。
_NON_ENTRY_NAMES = frozenset({"manifest.yaml", "field_mapping.yaml"})
_ENTRY_REQUIRED = frozenset({"key", "name", "unit", "price", "source"})
_ENTRY_OPTIONAL = frozenset({"note", "quantity"})


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
        raise InvalidPriceError(f"{what} {path.name} {reason}") from exc


def _nonempty_str(value: object, what: str) -> str:
    """字符串守卫：非空 str（空串/空白/异类型均拒，消息含字段名）。"""
    if not isinstance(value, str) or not value.strip():
        raise InvalidPriceError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


def _finite_number(value: object, what: str) -> float:
    """数值守卫：int/float（bool 除外）且有限（NaN/±Inf 拒，GR-02 同精神）。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidPriceError(
            f"{what} 必须为有限数值：得到 {value!r}（类型 "
            f"{type(value).__name__}）"
        )
    number = float(value)
    if not math.isfinite(number):
        raise InvalidPriceError(f"{what} 非有限（NaN/±Inf）：{value!r}")
    return number


@dataclass(frozen=True)
@final
class PriceItem:
    """单条定额单价：键/名称/计量单位/单价/出处（+可选注记与参考台数）。

    quantity 仅设备族条目携带（2019/2024 参考台数，概算侧不参与计算——
    takeoff 以结果字段实测台数为准，此处为数据包随行参考列）。
    """

    key: str
    name: str
    unit: str
    price: float
    source: str
    note: str = ""
    quantity: float | None = None


@dataclass(frozen=True)
@final
class PriceBook:
    """不可变单价库：get 失联键=领域异常，keys 前缀列举（R3/R4 只读）。"""

    _entries: Mapping[str, PriceItem]
    _data_version: str

    def __post_init__(self) -> None:
        """entries 构造即快照（外部改原容器不泄漏——coefficients 同防线）。"""
        object.__setattr__(self, "_entries", dict(self._entries))

    @property
    def data_version(self) -> str:
        """price_data_version（可复算三元组成员，§16 A8）。"""
        return self._data_version

    def get(self, price_key: str) -> PriceItem:
        """查询正门：失联键 = 领域异常（禁 None 假装成功，R3）。"""
        try:
            return self._entries[price_key]
        except KeyError as exc:
            raise InvalidPriceError(
                f"失联单价键：{price_key!r}（数据包 price_data_version="
                f"{self._data_version}；可用键经 keys() 前缀列举）"
            ) from exc

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """前缀列举（按章节/定额编号分组），排序返回（GR-18 确定性）。"""
        return tuple(sorted(key for key in self._entries if key.startswith(prefix)))


def _parse_entry(where: str, raw: object) -> tuple[str, PriceItem]:
    """单条目守卫：键集恰必填+可选、逐字段校验，返回 (key, PriceItem)。"""
    if not isinstance(raw, dict):
        raise InvalidPriceError(
            f"条目形态非法（{where}）：须为映射，得到 {type(raw).__name__}"
        )
    given = set(raw)
    missing = _ENTRY_REQUIRED - given
    unknown = given - _ENTRY_REQUIRED - _ENTRY_OPTIONAL
    if missing or unknown:
        raise InvalidPriceError(
            f"条目键集非法（{where}）：缺 {sorted(missing)}，多 "
            f"{sorted(unknown)}（必填 {sorted(_ENTRY_REQUIRED)}，可选 "
            f"{sorted(_ENTRY_OPTIONAL)}——多键少键均拒，防拼写静默）"
        )
    key = _nonempty_str(raw["key"], f"条目 key（{where}）")
    source = _nonempty_str(raw["source"], f"单价 {key!r} 的 source")
    if not source.strip():
        raise InvalidPriceError(
            f"单价 {key!r} 的 source 不能为空白串（R1：无出处不准入库）"
        )
    quantity_raw = raw.get("quantity")
    note_raw = raw.get("note", "")
    return (
        key,
        PriceItem(
            key=key,
            name=_nonempty_str(raw["name"], f"单价 {key!r} 的 name"),
            unit=_nonempty_str(raw["unit"], f"单价 {key!r} 的 unit"),
            price=_finite_number(raw["price"], f"单价 {key!r} 的 price"),
            source=source,
            note=(
                ""
                if note_raw == ""
                else _nonempty_str(note_raw, f"单价 {key!r} 的 note")
            ),
            quantity=(
                None
                if quantity_raw is None
                else _finite_number(quantity_raw, f"单价 {key!r} 的 quantity")
            ),
        ),
    )


def _load_manifest(directory: Path) -> str:
    """manifest 三守卫：必在 / 顶层 dict / 键集恰 {price_data_version} 且非空。"""
    manifest_file = directory / _MANIFEST_NAME
    if not manifest_file.is_file():
        raise InvalidPriceError(
            f"单价包缺 {_MANIFEST_NAME}：{directory}"
            "（price_data_version 与变更记录的唯一载体，R2 三元组成员）"
        )
    data = _load_yaml(manifest_file, "清单文件")
    if not isinstance(data, dict):
        raise InvalidPriceError(
            f"{_MANIFEST_NAME} 顶层须为映射：得到 {type(data).__name__}"
        )
    unknown = sorted(set(data) - _MANIFEST_KEYS)
    if unknown:
        raise InvalidPriceError(
            f"{_MANIFEST_NAME} 含未知键：{unknown}"
            f"（只允许 {sorted(_MANIFEST_KEYS)}——真实包注释行不受扰）"
        )
    if "price_data_version" not in data:
        raise InvalidPriceError(
            f"{_MANIFEST_NAME} 缺 price_data_version 键（D1 字段名归一："
            "规格头 R2 口径，三元组成员 §16 A8）"
        )
    return _nonempty_str(data["price_data_version"], "price_data_version")


def load_prices(path: str | Path) -> PriceBook:
    """加载正门：目录内 manifest+条目 YAML 严格校验 → PriceBook（R4 只读）。"""
    directory = Path(path)
    if not directory.is_dir():
        raise InvalidPriceError(f"单价包目录不存在：{directory}")
    data_version = _load_manifest(directory)
    entry_files = sorted(
        path_
        for path_ in directory.glob("*.yaml")
        if path_.name not in _NON_ENTRY_NAMES
    )
    if not entry_files:
        raise InvalidPriceError(
            f"单价包无条目文件：{directory}"
            "（GR-14 空集显式：数据包无条目=装配缺陷，禁静默空库）"
        )
    entries: dict[str, PriceItem] = {}
    for path_ in entry_files:
        data = _load_yaml(path_, "条目文件")
        if not isinstance(data, list):
            raise InvalidPriceError(
                f"条目文件 {path_.name} 顶层须为列表：得到 {type(data).__name__}"
            )
        if not data:
            raise InvalidPriceError(f"条目文件 {path_.name} 为空列表")
        for index, raw in enumerate(data):
            key, item = _parse_entry(f"{path_.name}[{index}]", raw)
            if key in entries:
                raise InvalidPriceError(
                    f"单价键重复：{key!r}（{path_.name} 与既有条目冲突——"
                    "键全包唯一，R3 失联/重复双向门槛）"
                )
            entries[key] = item
    return PriceBook(entries, data_version)
