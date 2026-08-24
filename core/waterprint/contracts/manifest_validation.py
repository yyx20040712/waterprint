"""manifest 冻结 schema 的静态校验器集 + 装配槽（manifest.py 机器部分，T4 拆分）。

输入:  清单数据节点（load_manifest 逐层下发的原始 Mapping/list）
输出:  守卫器（非法即 InvalidUnitConfig）、键集常量、bind_dimension_lookup 装配槽
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T4 拆分自 manifest.py；镜像测试 tests/contracts/test_manifest.py
#   经 load_manifest 正门全覆盖——本文件为机器部分，无独立公开面变更）
#
# 【拆分注记】（简报 T4 D1，2026-08-24）
#   - 本文件承接 manifest.py 原校验器机器部分（纯移动零行为变化）：
#     InvalidUnitConfig、_DimensionSpec 协议、_dimension_lookup_cell
#     装配槽 + bind_dimension_lookup、键集常量（_REQUIRED_KEYS…
#     _IDENTIFIER_PATTERN）、全部纯守卫器；manifest.py 留公开 schema 面
#     （ParamSpec/ConditionMapping/UnitManifest/load_manifest）并再导出
#     InvalidUnitConfig 与 bind_dimension_lookup（调用方 import 面零改动：
#     condition.py / unit_api.py / registry/dimensions.py 不动）。
#   - 例外：构造公开 schema 类的三个装配函数 _param_spec/_param_specs/
#     _condition_mappings 留 manifest.py——它们构造 ParamSpec/
#     ConditionMapping（D1 明文"ParamSpec 留 manifest.py，公开 schema 面
#     不动"），移入本文件将构成 manifest↔本文件环；单向 import：
#     manifest→manifest_validation（contracts 包内合法，先例
#     unit_api→manifest），本文件永不 import manifest。
#   - GR-36 类①（conventions §11）：冻结 schema 的静态校验器集，
#     file-contracts 行已注明类别。
#
# 【公开接口】（均经 manifest.py 再导出，调用方 import 面不变）
#   class InvalidUnitConfig(Exception)
#       清单/工况配置非法（GR-11 Invalid* 族；condition.py 同层引用）
#   bind_dimension_lookup(lookup) —— L1 注册表安装字段查询钩子（R1a
#       依赖倒置通道；装配语义见 manifest.py 规格头【T3 冻结注记】第 1 条；
#       bind-once：槽已非 None 再绑定=RuntimeError，T4 D2）
#   其余 _ 前缀守卫器与键集常量：manifest.py 的 load_manifest 与三个
#       装配函数内部消费，不作公开承诺
#
# 【行为规格】全部守卫行为与拆分前一致（纯移动）；行为规格正文见
#   manifest.py 规格头（R1a~R1e/R4 与【工况映射 DSL】节）——本文件
#   不重复载文，漂移即 bug。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 0（装配槽单元素
#   列表索引；沿袭 manifest.py 注记），无任何换算系数。
#
# 【测试要求】无独立镜像测试（test_manifest 经正门 5 用例覆盖，不回退
#   即拆分零行为漂移的实证）。
#
# 【参照】简报 T4 D1；GR-36（conventions §11）；AGENTS §2 文件预算
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Mapping
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Any, Protocol

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
    查询面只读，不承诺可写。类型随 T4 D6 放宽为 DimKey | str
    （FieldSpec.__post_init__ 归一为 DimKey 后实际恒为枚举；本投影
    按声明面放宽以保持结构可满足，StrEnum 值==名，== 比较语义不变）。
    """

    @property
    def dim(self) -> DimKey | str: ...


# 安装槽以单元素列表承载（免 global 语句；绑定动作是装配期一次性事件）。
# bind-once 守卫（T4 D2）：槽已非 None 时再绑定 = RuntimeError（GR-08 装配
# 缺陷不包装领域异常）——一次性注入语义，见 GR-36 记档豁免。
_dimension_lookup_cell: list[Callable[[str], _DimensionSpec | None] | None] = [
    None,
]


def bind_dimension_lookup(
    lookup: Callable[[str], _DimensionSpec | None],
) -> None:
    """L1 注册表安装字段查询钩子（R1a 依赖倒置：L0 不 import L1，AGENTS §1）。

    装配槽一次性注入（bind-once，T4 D2）：槽已非 None 时再绑定即
    RuntimeError——重复绑定属装配缺陷（GR-08），按 GR-36 记档豁免执行。
    """
    if _dimension_lookup_cell[0] is not None:
        raise RuntimeError(
            "装配槽重复绑定：bind_dimension_lookup 是装配期一次性注入"
            "（bind-once，T4 D2），重复绑定=装配缺陷（GR-08 不包装）；"
            "如需更换查询源，须重启进程重新装配，禁止运行期换绑"
        )
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
        registered = spec.dim
        raise InvalidUnitConfig(
            f"参数 {field_id!r} 量纲不匹配：清单声明 {dim.value}，"
            f"注册表登记 "
            f"{registered.value if isinstance(registered, DimKey) else registered}"
            "（R1a）"
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
