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
#       依赖倒置通道；见【T3 冻结注记】第 1 条）。T4 起定义于
#       manifest_validation.py，本模块再导出（import 面与语义零变化）；
#       bind-once：槽已非 None 再绑定=RuntimeError（T4 D2/GR-08）
#   class InvalidUnitConfig(Exception)
#       清单/工况配置非法（GR-11 Invalid* 族；condition.py 同层引用）。
#       T4 起定义于 manifest_validation.py，本模块再导出
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
# 【T4 拆分注记】（总控简报 D1 裁决，2026-08-24）
#   - 校验器机器部分（InvalidUnitConfig、_DimensionSpec 协议、装配槽
#     bind_dimension_lookup、键集常量、全部纯守卫器）拆至
#     manifest_validation.py（GR-36 类①；纯移动零行为变化）；本文件
#     留公开 schema 面与 load_manifest 正门，并再导出
#     InvalidUnitConfig 与 bind_dimension_lookup——condition.py /
#     unit_api.py / registry/dimensions.py 的 import 面零改动。
#   - 例外留守：_param_spec/_param_specs/_condition_mappings 三个装配
#     函数构造公开类 ParamSpec/ConditionMapping（D1"ParamSpec 留
#     manifest.py，公开 schema 面不动"），移入子模块将成环；单向
#     import：manifest→manifest_validation（包内合法，先例
#     unit_api→manifest）。
#
# 【测试要求】四类静态校验各自的拒绝路径、合法最小清单往返序列化无损。
#
# 【参照】重写计划 §3-5/§13.6/§14.1；ADR-007；数据包 data/coefficients/
#   README.md；简报 T3 D8 / T4 D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, final

from waterprint.contracts.manifest_validation import (
    _BUSINESS_LINES,
    _MAPPING_KEYS,
    _PARAM_KEYS,
    InvalidUnitConfig,
    _check_rule,
    _dict_entries,
    _dim_key,
    _finite,
    _float_tuple,
    _identifier,
    _ports,
    _range_tuple,
    _registered_dim,
    _removal_refs,
    _require_str,
    _require_top_keys,
    _str_tuple,
    _unknown_keys,
    bind_dimension_lookup,
)
from waterprint.contracts.ports import Port
from waterprint.contracts.quantity import DimKey

# 再导出面（D1）：InvalidUnitConfig 与 bind_dimension_lookup 定义已拆至
# manifest_validation.py，此处经 __all__ 显式再导出（mypy no-implicit-
# reexport 与 ruff F401/PLC0414 三方认可的形态，先例 contracts/__init__.py）
# ——condition.py / unit_api.py / registry/dimensions.py 的 import 面不变。
__all__ = [
    "ConditionMapping",
    "InvalidUnitConfig",
    "ParamSpec",
    "UnitManifest",
    "bind_dimension_lookup",
    "load_manifest",
]


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
