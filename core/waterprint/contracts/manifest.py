"""模组清单 schema：参数/端口/去除率/规范引用/工况映射的声明式唯一真源。

输入:  清单数据（单元包内 manifest.py 声明，或序列化 JSON）
输出:  UnitManifest（加载即静态校验，非法清单 = 启动失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 冻结；镜像测试 tests/contracts/test_manifest.py）
#
# 【公开接口】
#   class ParamSpec(不可变)：field_id: str、dim: DimKey、default: float、
#       grid: tuple[float, ...] | None（离散网格，solution/grid.py 消费）、
#       range: tuple[float, float] | None（闭区间 (min, max)，GR-06，
#       结构 {min,max}，约束层消费）
#   class ConditionMapping(不可变)：target: str（目标参数键）+ rule: str
#       （受限表达式 DSL，形如 "n if pool.all_pools else n - 1"）
#   class UnitManifest(不可变)：
#       unit_id / i18n_key / version / business_line
#       params: tuple[ParamSpec, ...]
#       ports:  tuple[Port, ...]
#       removal_refs: Mapping[指标 → coefficients 键]（去除率引用数据包）
#       norm_refs: tuple[条文引用, ...]    （GB 50014-2021 §x.x.x 等）
#       condition_mappings: tuple[ConditionMapping, ...]
#       constraint_refs: tuple[str, ...]   （constraint_kb 键）
#   load_manifest(data: Mapping) -> UnitManifest   加载+静态校验正门
#   bind_dimension_lookup(lookup) —— L1 注册表安装字段查询钩子（R1a
#       依赖倒置通道；见【T3 冻结注记】第 1 条）
#   class InvalidUnitConfig(Exception)
#       清单/工况配置非法（GR-11 Invalid* 族；condition.py 同层引用）
#
# 【工况映射 DSL】（T0.5 冻结；求值内核 = contracts/expr.py 共享受限求值器）
#   统一写法：目标参数 → 表达式字符串，形如
#      {"n_active": "n if pool.all_pools else n - 1"}（本示例为正典，
#      ADR-007 决策 3 同此写法，消除两处示例漂移的双源）。
#   语法子集 = 公式 DSL（见 registry/formulas.py【表达式 DSL】）+ 条件
#      扩展：IfExp（x if cond else y）、Compare（== != < > <= >=）、
#      BoolOp（and/or）、布尔字面量。
#   静态校验（load_manifest R1c 执行细则，D8 修正口径）：
#      a) rule 经 expr.parse_checked 强制受限 DSL 白名单（节点/运算符/
#         函数/常量——任意 Python 一律拒）；
#      b) 点式上下文引用 ⊆ {pool.all_pools}（其余点式名加载期拒）；
#      c) 裸名（含未在 params 声明者，如最小正典例的 n）不在加载期
#         拒——绑定完备性由求值期 expr.eval_checked 的"未绑定名字"
#         兜底（executor T7 闭环）。原 R1c"引用名 ⊆ params ∪ {pool.*}"
#         与锁定测试 VALID_MINIMAL（rule 引用未声明名 n）矛盾，以
#         测试为唯一真源修正为上述口径（规格冲突已报总控）。
#   求值时机：executor 在调 compute 前按 ADR-007 变换参数（graph/
#   executor R2）；compute 内禁止工况 if 分支（与 ADR-007 一致）。
#
# 【行为规格】
#   R1 静态校验（加载时，失败=启动失败不是运行时警告，§3 保证 2 思想）：
#      a) 参数 field_id 必须在 dimensions 注册表登记且单位匹配 DimKey；
#      b) 端口经 ports 构造 + 枚举合法（fluid/direction 字符串 → 枚举）；
#      c) 工况映射必须是受限 DSL 白名单表达式（禁止任意 Python——
#         声明式，ADR-007；细则见【工况映射 DSL】节）；
#      d) norm_refs 非空（无条文出处的设计参数不允许——溯源最低门槛）。
#      e) 顶层未知键拒（防拼写静默，与 project_schema extra=forbid
#         同精神——D8）；unit_id/target GR-26 字符集；数值字段有限性
#         （GR-02）；params 字段不重复；range 下界 ≤ 上界。
#   R2 去除率/系数只存引用键，数值在 data/coefficients 数据包（版本化，
#      随规范版本演进），清单不含魔法数。
#   R3 清单可序列化（项目文件内嵌单元版本），确定性序列化规则同 project/io。
#   R4 业务线字段 ∈ {municipal, mine_water, sludge, conveyance}（§14.3 边界）。
#
# 【T3 冻结注记】（总控简报 D8 裁决 + 实现期裁决，2026-08-23）
#   - R1a 依赖倒置：L0 禁止 import L1（AGENTS §1 / import-linter 分层
#     契约 / 图谱 §1b 仅声明 registry→contracts 边），故本文件暴露
#     bind_dimension_lookup 安装槽——registry/dimensions.py 在其模块
#     导入时安装 dimension_of（返回 None=未登记）。装配层（app.py，
#     声明边 app→registry）先装载注册表再加载单元清单；未绑定时
#     load_manifest 抛 RuntimeError（装配缺陷按 GR-08 不包装领域异常）。
#   - range 存储形态 (min, max) 二元组（闭区间 GR-06）；输入 dict
#     {"min","max"} 精确双键。
#   - 数值纪律：本文件不在魔法数字白名单——数值字面量仅 0（isfinite/
#     空容器判定归零处），无任何换算系数。
#
# 【测试要求】四类静态校验各自的拒绝路径、合法最小清单往返序列化无损。
#
# 【参照】重写计划 §3-5/§13.6/§14.1；ADR-007；数据包 data/coefficients/
#   README.md；简报 T3 D8
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Any, Protocol, final

from waterprint.contracts.expr import ExprSyntaxError, parse_checked
from waterprint.contracts.ports import Direction, FluidKind, Port
from waterprint.contracts.quantity import DimKey


# N818 豁免理由：InvalidUnitConfig 之名由宪法 AGENTS.md §3（领域异常族例举）
# 与锁定测试/简报 D8 裁决冻结，改名 = 违宪；GR-11 三族语义不受后缀拼写影响。
class InvalidUnitConfig(Exception):  # noqa: N818
    """清单/工况配置非法（加载期快速失败，非运行时警告——§3 保证 2 思想）。"""


class _DimensionSpec(Protocol):
    """已登记字段的最小结构面（registry FieldSpec 的 L0 投影——零依赖倒置）。

    dim 声明为只读属性：frozen 值对象（FieldSpec 等）可结构满足——
    查询面只读，不承诺可写。
    """

    @property
    def dim(self) -> DimKey: ...


# 安装槽以单元素列表承载（免 global 语句；绑定动作是装配期一次性事件）。
_dimension_lookup_cell: list[Callable[[str], _DimensionSpec | None] | None] = [
    None,
]


def bind_dimension_lookup(
    lookup: Callable[[str], _DimensionSpec | None],
) -> None:
    """L1 注册表安装字段查询钩子（R1a 依赖倒置：L0 不 import L1，AGENTS §1）。"""
    _dimension_lookup_cell[0] = lookup


_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "unit_id", "i18n_key", "version", "business_line", "params", "ports",
        "removal_refs", "norm_refs", "condition_mappings", "constraint_refs",
    }
)
_BUSINESS_LINES: frozenset[str] = frozenset(
    {"municipal", "mine_water", "sludge", "conveyance"}
)
_PARAM_KEYS: frozenset[str] = frozenset(
    {"field_id", "dim", "default", "grid", "range"}
)
_PORT_KEYS: frozenset[str] = frozenset(
    {"port_id", "fluid", "direction", "recycle"}
)
_MAPPING_KEYS: frozenset[str] = frozenset({"target", "rule"})
_POOL_CONTEXT: frozenset[str] = frozenset({"pool.all_pools"})
_IDENTIFIER_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z0-9_]+\Z")


@dataclass(frozen=True)
@final
class ParamSpec:
    """单参数声明：字段 ID + 量纲 + 默认值 + 可选离散网格/闭区间范围。"""

    field_id: str
    dim: DimKey
    default: float
    grid: tuple[float, ...] | None = None
    range: tuple[float, float] | None = None


@dataclass(frozen=True)
@final
class ConditionMapping:
    """单条声明式工况映射：目标参数键 → 受限 DSL 表达式（ADR-007）。"""

    target: str
    rule: str


@dataclass(frozen=True)
@final
class UnitManifest:
    """单元清单（不可变）：参数/端口/去除率引用/条文/工况映射/约束引用。"""

    unit_id: str
    i18n_key: str
    version: str
    business_line: str
    params: tuple[ParamSpec, ...]
    ports: tuple[Port, ...]
    removal_refs: Mapping[str, str]
    norm_refs: tuple[str, ...]
    condition_mappings: tuple[ConditionMapping, ...]
    constraint_refs: tuple[str, ...]


def _identifier(value: Any, what: str) -> str:
    """GR-26 标识符守卫：仅 ASCII 字母数字下划线且非空（消息含原值）。"""
    if not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InvalidUnitConfig(
            f"{what} 非法：{value!r}（GR-26：仅 ASCII 字母数字下划线且非空串）"
        )
    return value


def _finite(value: Any, what: str) -> float:
    """数值守卫：int/float（非 bool）且有限（GR-02 输入即拒绝）。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidUnitConfig(f"{what} 必须为数值：得到 {value!r}")
    number = float(value)
    if not isfinite(number):
        raise InvalidUnitConfig(
            f"{what} 必须为有限实数：得到 {value!r}（GR-02 输入即拒绝）"
        )
    return number


def _require_str(value: Any, what: str) -> str:
    """非空字符串守卫（i18n_key/version 等元数据键）。"""
    if not isinstance(value, str) or not value:
        raise InvalidUnitConfig(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


def _require_top_keys(data: Mapping[str, Any]) -> None:
    """顶层键完备性：未知键拒（防拼写静默）+ 缺键拒（十键必填）。"""
    unknown = sorted(set(data) - _REQUIRED_KEYS)
    if unknown:
        raise InvalidUnitConfig(
            f"清单未知顶层键：{unknown}（合法键 {sorted(_REQUIRED_KEYS)}"
            "——防拼写静默，与 project_schema extra=forbid 同精神）"
        )
    missing = sorted(_REQUIRED_KEYS - set(data))
    if missing:
        raise InvalidUnitConfig(f"清单缺键：{missing}（十键必填，R1e）")


def _dict_entries(raw: Any, what: str) -> list[Mapping[str, Any]]:
    """列表-of-对象守卫（params/ports/condition_mappings 的输入形态）。"""
    if not isinstance(raw, list):
        raise InvalidUnitConfig(f"{what} 必须为列表：得到 {type(raw).__name__}")
    for entry in raw:
        if not isinstance(entry, dict):
            raise InvalidUnitConfig(
                f"{what} 条目必须为对象：得到 {type(entry).__name__}"
            )
    return raw


def _unknown_keys(entry: Mapping[str, Any], allowed: frozenset[str], what: str) -> None:
    """条目级未知键守卫（与顶层同精神，D8）。"""
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise InvalidUnitConfig(
            f"{what} 条目未知键：{unknown}（合法键 {sorted(allowed)}）"
        )


def _enum_member[E: Enum](enum_type: type[E], value: Any, what: str) -> E:
    """枚举守卫：字符串成员名 → 枚举成员（R1b 枚举合法）。"""
    if not isinstance(value, str):
        raise InvalidUnitConfig(f"{what} 必须为字符串：得到 {value!r}")
    try:
        return enum_type[value]
    except KeyError as exc:
        members = sorted(member.name for member in enum_type)
        raise InvalidUnitConfig(
            f"{what} 非法：{value!r}（合法成员 {members}）"
        ) from exc


def _dim_key(value: Any) -> DimKey:
    """量纲守卫：字符串 → DimKey 成员。"""
    if not isinstance(value, str):
        raise InvalidUnitConfig(f"dim 必须为字符串（DimKey 成员名）：得到 {value!r}")
    try:
        return DimKey(value)
    except ValueError as exc:
        members = sorted(member.value for member in DimKey)
        raise InvalidUnitConfig(
            f"未知量纲：{value!r}（合法 {members}）"
        ) from exc


def _registered_dim(field_id: str, dim: DimKey) -> DimKey:
    """R1a：field_id 已登记且量纲匹配（查询钩子未绑定 = 装配缺陷，GR-08）。"""
    lookup = _dimension_lookup_cell[0]
    if lookup is None:
        raise RuntimeError(
            "dimensions 注册表未绑定：load_manifest 的 R1a 校验需先 import "
            "waterprint.registry.dimensions（bind_dimension_lookup 装配；"
            "L0 不 import L1，AGENTS §1 依赖倒置）"
        )
    spec = lookup(field_id)
    if spec is None:
        raise InvalidUnitConfig(
            f"参数 field_id 未登记 dimensions 注册表：{field_id!r}"
            "（R1a——先 register_dimension 登记，D2 扩围口径）"
        )
    if spec.dim != dim:
        raise InvalidUnitConfig(
            f"参数 {field_id!r} 量纲不匹配：清单声明 {dim.value}，"
            f"注册表登记 {spec.dim.value}（R1a）"
        )
    return dim


def _float_tuple(raw: Any, field_id: str, what: str) -> tuple[float, ...] | None:
    """离散网格守卫：可选列表 → 有限浮点元组。"""
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise InvalidUnitConfig(
            f"params[{field_id!r}].{what} 必须为列表：得到 {type(raw).__name__}"
        )
    return tuple(
        _finite(item, f"params[{field_id!r}].{what} 条目") for item in raw
    )


def _range_tuple(raw: Any, field_id: str) -> tuple[float, float] | None:
    """范围守卫：可选 {"min","max"} → 闭区间二元组（GR-06）。"""
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != {"min", "max"}:
        raise InvalidUnitConfig(
            f"params[{field_id!r}].range 结构须为 {{min,max}}：得到 {raw!r}"
            "（闭区间语义 GR-06）"
        )
    lower = _finite(raw["min"], f"params[{field_id!r}].range.min")
    upper = _finite(raw["max"], f"params[{field_id!r}].range.max")
    if lower > upper:
        raise InvalidUnitConfig(
            f"params[{field_id!r}].range 下界大于上界：[{lower!r}, {upper!r}]"
        )
    return (lower, upper)


def _param_spec(entry: Mapping[str, Any], field_id: str) -> ParamSpec:
    """单参数构造：R1a 登记/量纲校验 + 默认值/网格/范围守卫。"""
    dim = _dim_key(entry["dim"])
    default = _finite(entry["default"], f"params[{field_id!r}].default")
    return ParamSpec(
        field_id=field_id,
        dim=_registered_dim(field_id, dim),
        default=default,
        grid=_float_tuple(entry.get("grid"), field_id, "grid"),
        range=_range_tuple(entry.get("range"), field_id),
    )


def _param_specs(raw: Any) -> tuple[ParamSpec, ...]:
    """params 列表构造：条目键/重复字段守卫 + 逐条 ParamSpec。"""
    specs: list[ParamSpec] = []
    seen: set[str] = set()
    for entry in _dict_entries(raw, "params"):
        _unknown_keys(entry, _PARAM_KEYS, "params")
        field_id = _identifier(entry["field_id"], "params.field_id")
        if field_id in seen:
            raise InvalidUnitConfig(f"params 字段重复：{field_id!r}（R1e）")
        seen.add(field_id)
        specs.append(_param_spec(entry, field_id))
    return tuple(specs)


def _ports(raw: Any) -> tuple[Port, ...]:
    """ports 列表构造：R1b 枚举合法 + recycle 可选布尔。"""
    result: list[Port] = []
    for entry in _dict_entries(raw, "ports"):
        _unknown_keys(entry, _PORT_KEYS, "ports")
        recycle = entry.get("recycle", False)
        if not isinstance(recycle, bool):
            raise InvalidUnitConfig(
                f"ports.recycle 必须为布尔：得到 {recycle!r}"
            )
        result.append(
            Port(
                port_id=_identifier(entry["port_id"], "ports.port_id"),
                fluid=_enum_member(FluidKind, entry["fluid"], "ports.fluid"),
                direction=_enum_member(
                    Direction, entry["direction"], "ports.direction"
                ),
                recycle=recycle,
            )
        )
    return tuple(result)


def _dotted_path(node: ast.AST) -> str | None:
    """Name/Attribute 链 → 点式扁平名（根非 Name 返回 None）。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_path(node.value)
        if base is not None:
            return f"{base}.{node.attr}"
    return None


def _referenced_names(rule: str) -> tuple[frozenset[str], frozenset[str]]:
    """收集 rule 的（裸名, 点式名）两集（加载期 DSL 校验的输入面）。"""
    try:
        tree = ast.parse(rule, mode="eval")
    except SyntaxError as exc:
        raise InvalidUnitConfig(
            f"工况映射 rule 语法非法：{rule!r}（{exc.msg}）"
        ) from exc
    bare: set[str] = set()
    dotted: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            bare.add(node.id)
        elif isinstance(node, ast.Attribute):
            path = _dotted_path(node)
            if path is not None:
                dotted.add(path)
    return frozenset(bare), frozenset(dotted)


def _check_rule(rule: str, param_ids: frozenset[str]) -> None:
    """R1c：受限 DSL 白名单 + 点式上下文 ⊆ {pool.all_pools}（D8 修正口径）。"""
    bare, dotted = _referenced_names(rule)
    unexpected = sorted(dotted - _POOL_CONTEXT)
    if unexpected:
        raise InvalidUnitConfig(
            f"工况映射引用未预留上下文字段：{unexpected}"
            f"（预留仅 {sorted(_POOL_CONTEXT)}——DSL 冻结面）"
        )
    try:
        parse_checked(rule, bare | dotted | param_ids | _POOL_CONTEXT)
    except ExprSyntaxError as exc:
        raise InvalidUnitConfig(
            f"工况映射 rule 非受限 DSL：{rule!r}"
            "（仅白名单节点/运算符/函数，ADR-007——禁止任意 Python）"
        ) from exc


def _condition_mappings(
    raw: Any, param_ids: frozenset[str]
) -> tuple[ConditionMapping, ...]:
    """condition_mappings 列表构造：target/rule 精确双键 + R1c 校验。"""
    result: list[ConditionMapping] = []
    for entry in _dict_entries(raw, "condition_mappings"):
        _unknown_keys(entry, _MAPPING_KEYS, "condition_mappings")
        target = _identifier(entry["target"], "condition_mappings.target")
        rule = entry["rule"]
        if not isinstance(rule, str) or not rule:
            raise InvalidUnitConfig(
                f"condition_mappings.rule 必须为非空字符串：得到 {rule!r}"
            )
        _check_rule(rule, param_ids)
        result.append(ConditionMapping(target=target, rule=rule))
    return tuple(result)


def _str_tuple(raw: Any, key: str) -> tuple[str, ...]:
    """字符串列表守卫（norm_refs/constraint_refs）。"""
    if not isinstance(raw, list):
        raise InvalidUnitConfig(f"{key} 必须为列表：得到 {type(raw).__name__}")
    for item in raw:
        if not isinstance(item, str) or not item:
            raise InvalidUnitConfig(f"{key} 条目必须为非空字符串：{item!r}")
    return tuple(raw)


def _removal_refs(raw: Any) -> Mapping[str, str]:
    """去除率引用守卫：指标 → coefficients 键（只存引用，数值在数据包 R2）。"""
    if not isinstance(raw, dict):
        raise InvalidUnitConfig(
            f"removal_refs 必须为对象：得到 {type(raw).__name__}"
        )
    for key, value in raw.items():
        if not isinstance(key, str) or not key or not isinstance(value, str) or not value:
            raise InvalidUnitConfig(
                f"removal_refs 条目须为 指标→coefficients 键（均非空字符串）："
                f"{key!r}→{value!r}"
            )
    return MappingProxyType(dict(raw))


def load_manifest(data: Mapping[str, Any]) -> UnitManifest:
    """加载+静态校验正门：R1a~R1e/R4 全量守卫，非法清单 = 启动失败。"""
    _require_top_keys(data)
    business_line = data["business_line"]
    if business_line not in _BUSINESS_LINES:
        raise InvalidUnitConfig(
            f"business_line 非法：{business_line!r}"
            f"（四线 {sorted(_BUSINESS_LINES)}，§14.3 边界——R4）"
        )
    params = _param_specs(data["params"])
    norm_refs = _str_tuple(data["norm_refs"], "norm_refs")
    if not norm_refs:
        raise InvalidUnitConfig(
            "norm_refs 为空：无条文出处的设计参数不允许（R1d 溯源最低门槛）"
        )
    return UnitManifest(
        unit_id=_identifier(data["unit_id"], "unit_id"),
        i18n_key=_require_str(data["i18n_key"], "i18n_key"),
        version=_require_str(data["version"], "version"),
        business_line=business_line,
        params=params,
        ports=_ports(data["ports"]),
        removal_refs=_removal_refs(data["removal_refs"]),
        norm_refs=norm_refs,
        condition_mappings=_condition_mappings(
            data["condition_mappings"],
            frozenset(spec.field_id for spec in params),
        ),
        constraint_refs=_str_tuple(data["constraint_refs"], "constraint_refs"),
    )
