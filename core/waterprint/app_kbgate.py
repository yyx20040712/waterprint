"""design 帧阻断门：kb enforcement=block 条目越门 → KbBlockError 全败丢弃（P1 选项 3）。

输入:  PlantResult.conditions（baseline[0] design 帧目标单元 dims）+
       ConditionSet（baseline[0] 同锚）+ UnitRegistry（units[node].manifest.
       unit_id——kb 适用 kind 口径）+ Sequence[KbConstraint]（kb 执法面数据源
       ——run_full_calc 注入）
输出:  assert_kb_gate(...) -> None（None=通过；违规=raise KbBlockError——
       异常全败丢弃，半成品不进 summary/diagnostics/result）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（kbblock-20261006 批；镜像测试 tests/app/test_app_kbgate.py；
#   app_maintenance.py 家族先例同构第十例——根模块聚合执法件，不进
#   import-linter layers 契约（app_trust/app_maintenance 同款
#   unconstrained）。
#
# 【公开接口】
#   assert_kb_gate(plant, conditions, units, constraints) -> None
#       design 帧阻断门：None=通过；违规=raise KbBlockError（violations
#       三联结构化+传入序确定性）。接线点=app.run_full_calc 内
#       execute_graph 之后、summary 组装之前（D1——「返回+标记」「降级
#       stale」两案否决记档 ADR-026）。
#
# 【求值口径（D2）】
#   求值面=conditions.baseline[0] 帧独占（ConditionSet.key(conditions.
#       baseline[0]) 同锚——禁字符串字面量 "design"）；offline/sensitivity
#       帧零阻断求值（D3 豁免=架构性缺席非运行时开关——offline 帧看 n−1
#       恶劣态，阻断=检修分析在最需亮灯时刻熄灯；R3 呈裁默认全部豁免）。
#   逐 node 判据=app_maintenance._maint_face 三 conjunction 镜像 ∧
#       enforcement=="block"：kind≠BOUNDARY_CHECK_KIND（符号契约面非比较
#       DSL 域——零求值）∧ unit_kinds∋units[node].manifest.unit_id ∧
#       set(expression_fields(expression)) ⊆ design_snapshot.dims.keys()。
#   求值经 solution.apply_constraints 单行 DataFrame（列=design 帧 dims）
#       ——禁手写 DSL 求值（DSL 单源，maint face 同款纪律）。
#
# 【行为口径】
#   R1 空 baseline=通透不炸（maintenance_summary_of 同口径镜像——无对比
#      基线即无观测面，face 零键 gate 零执法，不独自响亮拒）。
#   R2 确定性：节点迭代=帧 dims 载体插入序；kb 迭代=传入序（violations
#      顺序=R2 纪律的传入序锚）；求值单源无选择序。
#   R3 sparse 镜像：node 快照缺席=通透跳过（帧内无该节点=零 applicable）。
#   R4 铁律二：constraints=() 零行为变更（无条件目=None——golden 零漂锚）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量无（_ENFORCEMENT_BLOCK
#   等档位语义经 solution.constraints 单源常量承载，禁本地字面双源）。
#
# 【测试要求】stub 阻断/通过双档+violations 三联与传入序+flag 永不阻断+
#   豁免面（sensitivity 帧零求值）+空 baseline+sparse+三 conjunction 守卫+
#   run_full_calc 接线（真实 kb 零 raise/构造违规 raise/缺省 () serialize
#   双跑字节同）——全量见 tests/app/test_app_kbgate.py。
#
# 【参照】ADR-026（kb-block-gate 决策记档）；app_maintenance.py（判据镜像
#   源）；solution.constraints（DSL 单源+kb 装载器+KbBlockError）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.result_schema import PlantResult
from waterprint.graph.executor_assembly import UnitRegistry
from waterprint.solution.constraints import (
    _ENFORCEMENT_BLOCK,  # 跨件私有引用（cli_calc→flows._CONSTRAINT_KB 先例——禁字面双源）
    BOUNDARY_CHECK_KIND,
    KbBlockError,
    KbConstraint,
    apply_constraints,
    expression_fields,
)


def assert_kb_gate(
    plant: PlantResult,
    conditions: ConditionSet,
    units: UnitRegistry,
    constraints: Sequence[KbConstraint],
) -> None:
    """design 帧阻断门（D1~D3）：block 条目越门=KbBlockError 全败丢弃。

    空 baseline=通透（R1 镜像——不炸不执法）；node 迭代=帧插入序、kb 迭代=
    传入序（R2 确定性）；求值=apply_constraints 单行 DataFrame 单源。"""
    if not conditions.baseline:
        return  # R1：无对比基线即无阻断面（maintenance face 同口径通透）
    base_key = ConditionSet.key(conditions.baseline[0])
    frame = plant.conditions.get(base_key, {})
    violations: list[tuple[str, str, str]] = []
    for node, snapshot in frame.items():
        unit_kind = units[node].manifest.unit_id
        dims: Mapping[str, float] = snapshot.dims
        applicable = tuple(
            kb for kb in constraints
            if kb.enforcement == _ENFORCEMENT_BLOCK  # 断路器档独占（flag=仪表灯）
            and kb.kind != BOUNDARY_CHECK_KIND  # 装载器豁免镜像（符号式零求值）
            and unit_kind in kb.unit_kinds
            and set(expression_fields(kb.constraint.expression)) <= dims.keys()
        )
        if not applicable:
            continue
        table = pandas.DataFrame([dict(dims)])  # 单行 DataFrame=design 帧 dims
        for kb in applicable:
            outcome = apply_constraints(table, [kb.constraint])
            if not bool(outcome.pass_matrix.to_numpy().all()):
                violations.append((node, kb.constraint.key, kb.kind))
    if violations:
        raise KbBlockError(tuple(violations))
