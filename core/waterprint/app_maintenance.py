"""检修观测与校核三面全厂投影：offline 工况 × 目标单元 → summary maint.* 平键（UF-61）。

输入:  PlantResult.conditions（design/online 双帧目标单元 dims）+
       ConditionSet（sensitivity offline 工况+baseline[0] 对比基线）+
       UnitRegistry（units[node].manifest.unit_id——kb 适用 kind 口径）+
       Sequence[KbConstraint]（kb 执法面数据源——run_full_calc 注入）
输出:  maintenance_summary_of（app.run_full_calc 经 _with_maintenance 合并
       注入 summary——开放映射槽位，result_schema 零改）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（UF-61 余轴批 uf61-axes-20261002；镜像测试
#   tests/app/test_app_maintenance.py；app_carbon.py 家族先例同构
#   第九例——根模块聚合投影件，不进 import-linter layers 契约
#   （app_trust 同款 unconstrained）。
#
# 【公开接口】
#   maintenance_summary_of(plant, conditions, units, constraints)
#       -> dict[工况→dict[maint.*平键→float]]：三面纯投影——对每个
#       sensitivity 工况（offline_unit 非 None）×目标单元；目标单元快照
#       双方在场才发键（sparse——缺席=空面不造键）。
#   _with_maintenance(base, extra) -> dict[...]
#       summary 合并注入（_with_carbon 同语义——同工况字典 update、
#       base 键族优先，两族键集无交集由 maint.* 命名域保证）。
#
# 【三面口径】
#   观测面（轴③）maint.<node>.ratio.<field> = offline/design——分化键集：
#       两帧同键交集内 design 值有限且≠0、offline 值有限、exact != 才
#       发键（全等字段不发——对比面=差异面；主控探针实证 aao 30 dims
#       键中恰 4 键漂移、几何四键全等）。不发键四态（全等/design 零或
#       非有限/offline 非有限/单帧缺席）消费者不区分——观测面=差异面
#       语义（缺键即「该工况下此字段无检修效应/不可算」，无四态分型）。
#   kb 执法面（轴②）maint.<node>.kb.<constraint_key> = 1.0 通过/0.0 越门：
#       适用判据=kb unit_kinds∋units[node].manifest.unit_id 且表达式全
#       字段∈offline dims（expression_fields 单源列举）且 kind≠
#       boundary_check（装载器 _BOUNDARY_CHECK_KIND 同款豁免镜像——
#       符号契约面非比较 DSL 域，消费面零求值）→ solution.
#       apply_constraints 单行 DataFrame（列=offline dims）求值，
#       pass=pass_matrix 全真（标注不阻断——全厂计算无行可滤；与枚举面
#       「勾选=硬滤」执法分级差异属两面语义）。禁绕开 apply_constraints
#       手写求值（DSL 单源）。
#   固定几何校核（轴①）maint.<node>.fixgeom.min = min(1−offline/design)：
#       min over kb 覆盖字段集 F（去重）∩ ratio 可算域——固定设计几何在
#       检修负荷下的归一裕度（<0=超载深度；aao 检修风机台数 ×2 → −1.0）；
#       F∩可算域空=不发键；逐字段明细不发（数值可由 ratio 面对出，
#       禁同值双源）。
#
# 【行为口径】
#   R1 对比基线=ConditionSet.key(conditions.baseline[0])（design_condition
#      同锚——禁字符串字面量 "design"）；baseline 两帧零发键（face 只遍
#      历 sensitivity 工况）。**空 baseline=返回 {}**（无对比基线即无
#      观测面——不炸不造键；run_full_calc 既有面对空 baseline 可通透
#      〔terminal_summary/energy 面均不炸〕，face 同口径通透不独自响亮拒
#      ——回炉轮 1 R1 裁量）。
#   R2 确定性：字段迭代=dims 插入序；kb 迭代=传入序；min=选择无序敏感；
#      serialize sort_keys 统一收口（本面产出裸 float 不预 round）。
#   R3 纯投影：不重算不造数——比例/DSL 求值/取 min 的投影组合。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量无（_PASS/_FAIL
#   =kb 通过/越门、_FULL=fixgeom 归一满额裕度基准，三者语义常量）。
#
# 【测试要求】stub 三面各态（分化键集/全等不发/非有限与零基跳过/kb 适用
#   三态/pass 双档/fixgeom 负值语义/F∩域空）+golden aao 实跑锚（分化恰
#   四键+kb 8 条 1.0+fixgeom −1.0）+双跑 serialize 字节同+空 sensitivity
#   零键+run_full_calc 接线（缺省 () 零 kb 键/baseline 帧零 maint 键）。
#
# 【参照】UF-61（undefined-features-register）；app_carbon.py（先例）；
#   solution.constraints（DSL 单源+kb 装载器）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.result_schema import PlantResult
from waterprint.graph.executor_assembly import UnitRegistry
from waterprint.solution.constraints import (
    KbConstraint,
    apply_constraints,
    expression_fields,
)

_KEY_PREFIX: str = "maint."
_RATIO_INFIX: str = ".ratio."
_KB_INFIX: str = ".kb."
_FIXGEOM_SUFFIX: str = ".fixgeom.min"
_PASS: float = 1.0  # kb 门内（语义常量）
_FAIL: float = 0.0  # kb 越门（标注不阻断——语义常量）
_FULL: Final[float] = 1.0  # fixgeom 归一满额裕度基准（语义常量——回炉 R5）
# 装载器 _BOUNDARY_CHECK_KIND 同款豁免镜像（constraints.py 私有名跨包禁
# 取——宪 §1 正门约束，本地常量+注释指针双源对齐）
_BOUNDARY_KIND: Final[str] = "boundary_check"


def _maint_face(
    design_dims: Mapping[str, float],
    offline_dims: Mapping[str, float],
    node: str,
    unit_kind: str,
    constraints: Sequence[KbConstraint],
) -> dict[str, float]:
    """单工况×单目标单元三面（ratio/kb/fixgeom——dims 插入序确定性）。"""
    face: dict[str, float] = {}
    slack: dict[str, float] = {}  # field → _FULL−ratio（ratio 可算域全量——fixgeom 候选）
    for field, base in design_dims.items():
        off = offline_dims.get(field)
        if off is None or not isfinite(base) or not isfinite(off) or base == 0.0:
            continue  # 两帧同键+design 有限非零+offline 有限才可算
        ratio = off / base
        if off != base:  # exact !=——分化键集（全等不发）
            face[f"{_KEY_PREFIX}{node}{_RATIO_INFIX}{field}"] = ratio
        slack[field] = _FULL - ratio
    applicable = tuple(
        kb for kb in constraints
        if kb.kind != _BOUNDARY_KIND  # 装载器 _BOUNDARY_CHECK_KIND 同款豁免镜像（回炉 R2）
        and unit_kind in kb.unit_kinds
        and set(expression_fields(kb.constraint.expression)) <= offline_dims.keys()
    )
    if applicable:  # 单行 DataFrame=offline dims（apply_constraints 单源求值）
        frame = pandas.DataFrame([dict(offline_dims)])
        for kb in applicable:
            outcome = apply_constraints(frame, [kb.constraint])
            face[f"{_KEY_PREFIX}{node}{_KB_INFIX}{kb.constraint.key}"] = (
                _PASS if bool(outcome.pass_matrix.to_numpy().all()) else _FAIL
            )
        margins = [
            slack[field]
            for kb in applicable
            for field in expression_fields(kb.constraint.expression)
            if field in slack
        ]
        if margins:
            face[f"{_KEY_PREFIX}{node}{_FIXGEOM_SUFFIX}"] = min(margins)
    return face


def maintenance_summary_of(
    plant: PlantResult,
    conditions: ConditionSet,
    units: UnitRegistry,
    constraints: Sequence[KbConstraint],
) -> dict[str, dict[str, float]]:
    """UF-61 三面纯投影：逐 sensitivity 工况 × 目标单元（sparse 双帧快照在场）。

    空 baseline=返回 {}（无对比基线即无观测面——不炸不造键；run_full_calc
    既有面对空 baseline 可通透，face 同口径通透——回炉轮 1 R1 裁量记档）。"""
    if not conditions.baseline:
        return {}
    base_key = ConditionSet.key(conditions.baseline[0])
    out: dict[str, dict[str, float]] = {}
    for condition in conditions.sensitivity:
        if condition.offline_unit is None:
            continue  # 基线两帧零发键（face 只走 offline 工况）
        node = condition.offline_unit
        key = ConditionSet.key(condition)
        base_snapshot = plant.conditions.get(base_key, {}).get(node)
        off_snapshot = plant.conditions.get(key, {}).get(node)
        if base_snapshot is None or off_snapshot is None:
            out[key] = {}  # 目标单元快照缺席（sparse）=空面不造键
            continue
        out[key] = _maint_face(
            base_snapshot.dims, off_snapshot.dims,
            node, units[node].manifest.unit_id, constraints,
        )
    return out


def _with_maintenance(
    base: dict[str, dict[str, float]], extra: dict[str, dict[str, float]]
) -> dict[str, dict[str, float]]:
    """summary 合并注入：既有平键族 + maint.* 检修观测键（UF-61——同工况
    字典 update；base 键族优先，两族键集无交集由命名域保证）。"""
    for condition_key, fields in extra.items():
        if condition_key in base:
            base[condition_key].update(fields)
    return base
