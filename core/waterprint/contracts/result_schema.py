"""全厂结果与计算迹节点 schema（全架构总线：概算/图纸/三维/前端都消费它）。

输入:  图引擎执行产出（graph/executor.py）、公式应用记录（trace/collector.py）
输出:  PlantResult / TraceNode（序列化模型，字段 ID 制）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 冻结；镜像测试 tests/contracts/test_result_schema.py）
#
# 【公开接口】
#   class InvalidResultError(Exception)
#       结果数据非法（非有限值/结构非法/JSON 非法）——GR-11 Invalid* 族
#       新类（D6：结果数据非法语义，非同义复用既有异常）。
#   class TraceNode(不可变)：一次公式应用的完整记录——
#       formula_id: str、inputs: Mapping[str → float]（字段 ID→规范单位值
#       输入快照）、output: float、norm_ref: str（条文号）、unit_id: str、
#       condition_key: str（五要素审计链）
#   class UnitResultSnapshot(不可变)：UnitResult 的序列化形态——
#       unit_id: str、outflows/outqualities/dims: Mapping[str → float]
#       （端口/指标/字段 ID 键）、warnings: tuple[Warning, ...]（复用
#       unit_api.Warning，D3）、formula_ids: tuple[str, ...]
#   class ReproTriple(不可变)：design_hash / engine_version / data_version
#       三元组（全 str——结果永不脱离三元组存在，R4）
#   class PlantResult(不可变)：
#       conditions: Mapping[condition_key → Mapping[unit_id → UnitResultSnapshot]]
#       summary:    Mapping[condition_key → Mapping[字段 ID → float]]
#                   （出水裕度、总泥量等汇总，非中文名）
#       trace:      tuple[TraceNode, ...]     全程可审计（§3 保证 5）
#       repro:      ReproTriple
#   serialize(result: PlantResult) -> bytes     确定性序列化正门
#   deserialize(data: bytes) -> PlantResult     严格反序列化正门
#
# 【行为规格】
#   R1 本 schema 是全架构总线（§16 A4）：elevation/cost/drafting/geometry/
#      前端全部只消费它，互不感知；变更必须走 ADR + 契约测试 + 前端重新生成。
#   R2 稳定字段 ID：概算/Excel/图纸按字段 ID 取数；中文名只存在于 i18n
#      显示层（§3 保证 4，病灶"概算 4 级中文模糊匹配/361 条影子标签"）。
#   R3 序列化确定性：键递归排序、round(x,10) 浮点定点、无随机 ID——
#      同结果两次序列化字节级相同（与 project/io 同规则，供"双跑 diff=0"
#      测试）；UTF-8、紧凑分隔符、ensure_ascii=False（D6）。
#   R4 结果绑定三元组：repro 三元组与项目 metadata 不一致 = 结果过期，
#      消费方（导出/前端）必须显式提示，禁止静默使用（§16 A8）。
#   R5 计算迹完整性：任一输出数值都能沿 trace 回溯到公式 ID + 条文号 +
#      输入快照——审计链路（M4 验收）以此为准。
#   R6 非有限值拒绝（D6/GR-02）：serialize 输入含 NaN/±Inf →
#      InvalidResultError（消息含值与位置）；deserialize 对 NaN/Infinity
#      JSON 字面量与非有限浮点同样拒绝——带病结果禁止落盘/入流；
#      巨 int（10**400 级，float() 溢出）两侧同收编（消息含 path，
#      ARCH1 D1c；转换收拢 _finite_rounded 两路共用）。
#
# 【T3 冻结注记】（总控简报 D5/D6 裁决，2026-08-23）
#   - D5：TraceNode 字段名照锁定测试——inputs/output（单数）。
#   - D6：serialize 返回 bytes（UTF-8 编码后）——"字节级相同"以 bytes
#     直接可比；deserialize 收 bytes，往返serialize(deserialize(x))==x。
#   - Warning 构造面无数值字段（字符串/枚举/字符串元组）——NaN 面只在
#     serialize/deserialize 的数值通路上（探针集中处，简报 §5）。
#   - R1 修复轮收紧（二审 T3A-03+T3G-01，2026-08-23）：deserialize
#     四顶层键必在（缺一拒，消息含缺失键名）+ 根级未知键拒（消息含
#     未知键名）+ 未知键拒下推 trace/snapshot/warning/repro 节点级 +
#     Warning.param_key/condition_key 校验 None|str（消 7→7.0 往返漂移）。
#   - T4 收口（简报 D4，2026-08-24）：deserialize 内层三键必在（缺省
#     [] 收口，T3-R1 残余）——Warning.affected_unit_ids、
#     UnitResultSnapshot.warnings、UnitResultSnapshot.formula_ids，缺失
#     = InvalidResultError（消息含 {path}.{键名} 缺失）；serialize 经
#     dataclasses.fields 恒发全键（空容器也发射），往返恒等保持。
#   - 数值纪律：本文件不在魔法数字白名单——数值字面量仅 round(x,10) 的 10。
#
# 【测试要求】往返无损、确定性序列化、按 condition_key 索引完整性、
#   三元组不一致检测（后两项消费侧用例随 T7/T9 解锁窗补）。
#
# 【参照】重写计划 §3-4/§3-6/§12.3/§16 A4；ADR-004；简报 T3 D5/D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Any, final

from waterprint.contracts.unit_api import Severity, Warning

_ROUND_DIGITS: int = 10
_JSON_KWARGS: dict[str, Any] = {
    "sort_keys": True,
    "ensure_ascii": False,
    "separators": (",", ":"),
}
# 各节点合法键集（deserialize 未知键拒的判据——与上文 dataclass 字段一一对应）
_ROOT_KEYS: frozenset[str] = frozenset({"conditions", "summary", "trace", "repro"})
_TRACE_NODE_KEYS: frozenset[str] = frozenset(
    {"formula_id", "inputs", "output", "norm_ref", "unit_id", "condition_key"}
)
_SNAPSHOT_KEYS: frozenset[str] = frozenset(
    {"unit_id", "outflows", "outqualities", "dims", "warnings", "formula_ids"}
)
_WARNING_KEYS: frozenset[str] = frozenset(
    {
        "severity",
        "source",
        "message",
        "param_key",
        "condition_key",
        "affected_unit_ids",
    }
)
_REPRO_KEYS: frozenset[str] = frozenset(
    {"design_hash", "engine_version", "data_version"}
)


class InvalidResultError(Exception):
    """结果数据非法（非有限值/结构非法/JSON 非法）——领域异常（D6）。"""


@dataclass(frozen=True)
@final
class TraceNode:
    """单次公式应用的完整记录（计算迹最小审计单元，五要素）。"""

    formula_id: str
    inputs: Mapping[str, float]
    output: float
    norm_ref: str
    unit_id: str
    condition_key: str

    def __post_init__(self) -> None:
        """输入快照只读冻结。"""
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))


@dataclass(frozen=True)
@final
class UnitResultSnapshot:
    """UnitResult 的序列化形态：端口/指标/字段 ID 键 + 警告 + 公式审计通道。"""

    unit_id: str
    outflows: Mapping[str, float]
    outqualities: Mapping[str, float]
    dims: Mapping[str, float]
    warnings: tuple[Warning, ...]
    formula_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Mapping 只读快照 + tuple 归一。"""
        object.__setattr__(self, "outflows", MappingProxyType(dict(self.outflows)))
        object.__setattr__(
            self, "outqualities", MappingProxyType(dict(self.outqualities))
        )
        object.__setattr__(self, "dims", MappingProxyType(dict(self.dims)))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "formula_ids", tuple(self.formula_ids))


@dataclass(frozen=True)
@final
class ReproTriple:
    """可复算三元组：结果 = f(design_hash, engine_version, data_version)。"""

    design_hash: str
    engine_version: str
    data_version: str


@dataclass(frozen=True)
@final
class PlantResult:
    """全厂结果总线：工况索引结果 + 汇总 + 全程迹 + 三元组（R1/R4）。"""

    conditions: Mapping[str, Mapping[str, UnitResultSnapshot]]
    summary: Mapping[str, Mapping[str, float]]
    trace: tuple[TraceNode, ...]
    repro: ReproTriple

    def __post_init__(self) -> None:
        """两层 Mapping 只读快照冻结（外层 + 各工况内层）。"""
        frozen_conditions = {
            key: MappingProxyType(dict(units))
            for key, units in self.conditions.items()
        }
        object.__setattr__(
            self, "conditions", MappingProxyType(frozen_conditions)
        )
        object.__setattr__(
            self, "summary", MappingProxyType(
                {key: MappingProxyType(dict(fields)) for key, fields in self.summary.items()}
            )
        )
        object.__setattr__(self, "trace", tuple(self.trace))


def _finite_rounded(value: int | float, path: str) -> float:
    """数值守卫：巨 int（float() 溢出）与非有限均拒（消息含位置，
    ARCH1 D1c 收编；转换收拢本函数，serialize/deserialize 两路共用）
    + round(x,10) 定点（R3/R6）。"""
    try:
        number = float(value)
    except OverflowError as exc:
        raise InvalidResultError(
            f"结果含超浮点域整数：{path} 处原值类型 {type(value).__name__}"
            "（R6/GR-02——带病结果禁止序列化）"
        ) from exc
    if not isfinite(number):
        raise InvalidResultError(
            f"结果含非有限值（NaN/±Inf）：{path} 处 {number!r}"
            "（R6/GR-02——带病结果禁止序列化）"
        )
    return round(number, _ROUND_DIGITS)


def _to_json(value: Any, path: str) -> Any:
    """值 → 确定性 JSON 树：数值一律 float 定点（int 归一——往返字节级
    稳定的前提）、键限字符串、容器递归。"""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int | float):
        return _finite_rounded(value, path)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_json(getattr(value, field.name), f"{path}.{field.name}")
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        return {
            _string_key(key, path): _to_json(item, f"{path}.{key}")
            for key, item in value.items()
        }
    if isinstance(value, Sequence):
        return [
            _to_json(item, f"{path}[{index}]") for index, item in enumerate(value)
        ]
    raise InvalidResultError(
        f"结果含不可序列化类型 {type(value).__name__}：{path}"
        "（R3 确定性序列化面：数值/字符串/布尔/None/容器/dataclass）"
    )


def _string_key(key: Any, path: str) -> str:
    """JSON 对象键守卫：仅字符串键（字段 ID 制，禁复合键漂移）。"""
    if not isinstance(key, str):
        raise InvalidResultError(
            f"结果 Mapping 键必须为字符串：{path} 处 {key!r}"
            "（字段 ID 制——R2 稳定取数键）"
        )
    return key


def serialize(result: PlantResult) -> bytes:
    """确定性序列化正门：键递归排序、round(x,10)、紧凑分隔符、UTF-8。"""
    tree: dict[str, Any] = {
        "conditions": _to_json(result.conditions, "conditions"),
        "summary": _to_json(result.summary, "summary"),
        "trace": _to_json(result.trace, "trace"),
        "repro": _to_json(result.repro, "repro"),
    }
    return json.dumps(tree, **_JSON_KWARGS).encode("utf-8")


def _reject_constant(token: str) -> float:
    """JSON 的 NaN/Infinity/-Infinity 字面量 → 拒（R6 反序列化侧）。"""
    raise ValueError(f"非有限 JSON 字面量：{token}")


def _parse_float(token: str) -> float:
    """浮点字面量守卫：1e999 等溢出为 inf 同样拒（R6）。"""
    value = float(token)
    if not isfinite(value):
        raise ValueError(f"非有限浮点字面量：{token}")
    return value


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    """结构守卫：对象节点。"""
    if not isinstance(value, dict):
        raise InvalidResultError(
            f"结果数据结构非法：{path} 应为对象，得到 {type(value).__name__}"
        )
    return value


def _require_str(value: Any, path: str) -> str:
    """结构守卫：字符串叶子。"""
    if not isinstance(value, str):
        raise InvalidResultError(
            f"结果数据结构非法：{path} 应为字符串，得到 {type(value).__name__}"
        )
    return value


def _require_opt_str(value: Any, path: str) -> str | None:
    """结构守卫：可选字符串叶子（None|str——消 7→7.0 往返字节漂移面）。"""
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidResultError(
            f"结果数据结构非法：{path} 应为字符串或 null，得到 {value!r}"
            "（T3A-03：可选字段只收 str|None，禁止数值静默漂移）"
        )
    return value


def _reject_missing_keys(
    raw: Mapping[str, Any], required: frozenset[str], path: str
) -> None:
    """结构守卫：必需键缺一即拒（消息含缺失键名——T3A-03 段级宽松封死）。"""
    missing = sorted(key for key in required if key not in raw)
    if missing:
        raise InvalidResultError(
            f"结果数据结构非法：{path} 缺失必需键 {missing}"
            "（T3A-03——四顶层键必在，禁止段级缺省静默通过）"
        )


def _reject_unknown_keys(
    raw: Mapping[str, Any], allowed: frozenset[str], path: str
) -> None:
    """结构守卫：未知键即拒（消息含未知键名——T3G-01 节点级下推）。"""
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise InvalidResultError(
            f"结果数据结构非法：{path} 含未知键 {unknown}（合法键 {sorted(allowed)}）"
            "（T3G-01——与 project_schema extra=forbid 同精神）"
        )


def _required_entry(raw: Mapping[str, Any], key: str, path: str) -> Any:
    """内层键必在守卫（D4，T3A-03 同风格）：缺省 [] 收口，消息含 path.键名。

    serialize 经 dataclasses.fields 恒发全键（空容器也发射），故反序列化
    侧缺失即数据源缺陷，禁止静默补缺省值通过。
    """
    if key not in raw:
        raise InvalidResultError(
            f"结果数据结构非法：{path}.{key} 缺失"
            "（D4——内层键必在，serialize 恒发全键，缺失即数据源缺陷）"
        )
    return raw[key]


def _require_number(value: Any, path: str) -> float:
    """结构守卫：数值叶子（再过有限性守卫）。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidResultError(
            f"结果数据结构非法：{path} 应为数值，得到 {value!r}"
        )
    return _finite_rounded(value, path)


def _require_float_mapping(value: Any, path: str) -> Mapping[str, float]:
    """结构守卫：字段 ID → float 映射节点。"""
    raw = _require_mapping(value, path)
    return {key: _require_number(item, f"{path}.{key}") for key, item in raw.items()}


def _require_str_tuple(value: Any, path: str) -> tuple[str, ...]:
    """结构守卫：字符串数组节点。"""
    if not isinstance(value, list):
        raise InvalidResultError(
            f"结果数据结构非法：{path} 应为数组，得到 {type(value).__name__}"
        )
    return tuple(_require_str(item, f"{path}[{index}]") for index, item in enumerate(value))


def _warning_of(value: Any, path: str) -> Warning:
    """Warning 节点重建：severity 枚举 + 三必带字段 + 未知键拒。"""
    raw = _require_mapping(value, path)
    _reject_unknown_keys(raw, _WARNING_KEYS, path)
    severity_raw = _require_str(raw.get("severity"), f"{path}.severity")
    try:
        severity = Severity(severity_raw)
    except ValueError as exc:
        raise InvalidResultError(
            f"警告级别非法：{severity_raw!r}（合法 {sorted(s.value for s in Severity)}）"
        ) from exc
    return Warning(
        severity=severity,
        source=_require_str(raw.get("source"), f"{path}.source"),
        message=_require_str(raw.get("message"), f"{path}.message"),
        param_key=_require_opt_str(raw.get("param_key"), f"{path}.param_key"),
        condition_key=_require_opt_str(
            raw.get("condition_key"), f"{path}.condition_key"
        ),
        affected_unit_ids=_require_str_tuple(
            _required_entry(raw, "affected_unit_ids", path),
            f"{path}.affected_unit_ids",
        ),
    )


def _snapshot_of(value: Any, path: str) -> UnitResultSnapshot:
    """UnitResultSnapshot 节点重建。"""
    raw = _require_mapping(value, path)
    _reject_unknown_keys(raw, _SNAPSHOT_KEYS, path)
    return UnitResultSnapshot(
        unit_id=_require_str(raw.get("unit_id"), f"{path}.unit_id"),
        outflows=_require_float_mapping(raw.get("outflows"), f"{path}.outflows"),
        outqualities=_require_float_mapping(
            raw.get("outqualities"), f"{path}.outqualities"
        ),
        dims=_require_float_mapping(raw.get("dims"), f"{path}.dims"),
        warnings=tuple(
            _warning_of(item, f"{path}.warnings[{index}]")
            for index, item in enumerate(
                _require_list(
                    _required_entry(raw, "warnings", path), f"{path}.warnings"
                )
            )
        ),
        formula_ids=_require_str_tuple(
            _required_entry(raw, "formula_ids", path), f"{path}.formula_ids"
        ),
    )


def _require_list(value: Any, path: str) -> list[Any]:
    """结构守卫：数组节点（宽松元素——由上层逐元素重建）。"""
    if not isinstance(value, list):
        raise InvalidResultError(
            f"结果数据结构非法：{path} 应为数组，得到 {type(value).__name__}"
        )
    return value


def _trace_node_of(value: Any, path: str) -> TraceNode:
    """TraceNode 节点重建（五要素完备 + 未知键拒）。"""
    raw = _require_mapping(value, path)
    _reject_unknown_keys(raw, _TRACE_NODE_KEYS, path)
    return TraceNode(
        formula_id=_require_str(raw.get("formula_id"), f"{path}.formula_id"),
        inputs=_require_float_mapping(raw.get("inputs"), f"{path}.inputs"),
        output=_require_number(raw.get("output"), f"{path}.output"),
        norm_ref=_require_str(raw.get("norm_ref"), f"{path}.norm_ref"),
        unit_id=_require_str(raw.get("unit_id"), f"{path}.unit_id"),
        condition_key=_require_str(raw.get("condition_key"), f"{path}.condition_key"),
    )


def deserialize(data: bytes) -> PlantResult:
    """严格反序列化正门：UTF-8 + JSON + 结构/有限性全量守卫（R6）。"""
    try:
        tree = json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise InvalidResultError(f"结果数据非法 JSON（UTF-8/NaN 面）：{exc}") from exc
    root = _require_mapping(tree, "$")
    _reject_missing_keys(root, _ROOT_KEYS, "$")
    _reject_unknown_keys(root, _ROOT_KEYS, "$")
    conditions_raw = _require_mapping(root["conditions"], "$.conditions")
    summary_raw = _require_mapping(root["summary"], "$.summary")
    return PlantResult(
        conditions={
            key: {
                unit_id: _snapshot_of(snap, f"$.conditions.{key}.{unit_id}")
                for unit_id, snap in _require_mapping(units, f"$.conditions.{key}").items()
            }
            for key, units in conditions_raw.items()
        },
        summary={
            key: _require_float_mapping(fields, f"$.summary.{key}")
            for key, fields in summary_raw.items()
        },
        trace=tuple(
            _trace_node_of(node, f"$.trace[{index}]")
            for index, node in enumerate(_require_list(root["trace"], "$.trace"))
        ),
        repro=_repro_of(root["repro"], "$.repro"),
    )


def _repro_of(value: Any, path: str) -> ReproTriple:
    """三元组节点重建（三键必在，R4；未知键拒）。"""
    raw = _require_mapping(value, path)
    _reject_unknown_keys(raw, _REPRO_KEYS, path)
    return ReproTriple(
        design_hash=_require_str(raw.get("design_hash"), f"{path}.design_hash"),
        engine_version=_require_str(
            raw.get("engine_version"), f"{path}.engine_version"
        ),
        data_version=_require_str(raw.get("data_version"), f"{path}.data_version"),
    )
