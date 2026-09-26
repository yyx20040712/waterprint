"""方案空间枚举用例正门族：单单元枚举+联合枚举（app.py 贴墙拆件伴生件）。

输入:  ProjectFile+ConditionSet+RunEnv+选项（app 正门装配注入面消费）
输出:  EnumerationOutcome / JointOutcome（app 再导出=server/cli/测试单入口）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批5 2026-09-26 拆件：app.py 500 行恰满零余量——批2a 登记欠账
#   「app.py=500 恰满零余量（批5 堆）」兑现；app_assembly/app_enumeration
#   伴生件先例第三例；run_design_map 留守 app.py=锁定测试 monkeypatch
#   耦合 app 模块命名空间〔test_design_map.py test_run_design_map_fixed_
#   params_authoritative setattr(app_mod, "enumerate_solutions", …)〕，
#   迁移须随锁面工序呈批——非本批范围）
#
# 【公开接口】
#   run_enumeration(project, unit_id, conditions, env, options)
#       -> EnumerationOutcome（语义自 app.py 迁入，除批5 双源可行口径
#       统一行为变更：见下 AUD-W5；镜像测试 tests/app/test_enumeration_
#       usecase.py 锁面期望随批呈批件翻转）
#   run_joint_enumerate(project, unit_ids, conditions, env, options)
#       -> JointOutcome（B4-3/ADR-25 装配注入+转发——语义零变）
#
# 【批5 AUD-W5 口径统一（行为变更）】单单元枚举可行集=行非 NaN ∧ 约束
#   通过（enumerate.feasible_indices 单源——联合枚举阶段/可行域图 PD2
#   同源上收）：域拒行（nan_flag=True，R5 行级域拒）不再进可行集/排序/
#   分页；无解诊断增 domain_rejected 拒因维度（diagnose.DiagnosisReport
#   扩域拒计数字段），全域拒+空约束=域拒报告（fail_counts 仅
#   domain_nan_rows——不再进 diagnose 空矩阵路径）。
#
# 【层序注记】L4.app 伴生件（app_assembly 同款未列 pyproject layers——
#   B3 R1 先例）；零 waterprint.app 依赖防环（env 补齐经 app_assembly.
#   completed_env 批5 迁入单源），消费=app.py 再导出单入口。
#
# 【测试要求】随 app 镜像测试（tests/app/）既有用例——期望翻转面走
#   .workflow 呈批件 [HUMAN-LOCK] 工序。
#
# 【参照】AGENTS §2 预算墙拆件纪律；audit-norms-20260925 AUD-W5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from types import MappingProxyType
from typing import cast

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（enumerate 同款记档）

from waterprint.app_assembly import InvalidAssemblyError, assemble, completed_env
from waterprint.app_enumeration import (
    EnumerationOptions,
    EnumerationOutcome,
    UpstreamSource,
    enumerate_across_conditions,
)
from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.run_env import RunEnv
from waterprint.graph.executor import execute_graph
from waterprint.solution.constraints import (
    MARGIN_COLUMN,
    Constraint,
    FilterResult,
    apply_constraints,
    band_margin_column,
)
from waterprint.solution.diagnose import DiagnosisReport, diagnose_infeasibility
from waterprint.solution.enumerate import feasible_indices
from waterprint.solution.grid import Grid, build_grid
from waterprint.solution.joint_enumeration import (
    AssembleFn,
    JointEnumerationOptions,
    JointOutcome,
)
from waterprint.solution.joint_enumeration import run_joint_enumerate as _joint_run
from waterprint.solution.ranking import RankingKey, rank


def _enumeration_diagnosis(
    frame: pandas.DataFrame,
    constraints: Sequence[Constraint],
    matrix: pandas.DataFrame,
    grid: Grid,
) -> DiagnosisReport:
    """无解诊断（批5 AUD-W5 拒因维度）：全域拒=域拒报告；含约束=既有 diagnose+域拒计数。"""
    rejected = int(frame["nan_flag"].sum())
    if not constraints:
        return DiagnosisReport(
            minimal_conflicts=(),
            fail_counts=MappingProxyType({"domain_nan_rows": rejected}),
            suggestions=(),
            domain_rejected=rejected,
        )
    report = diagnose_infeasibility(
        matrix, {c.expression: c for c in constraints}, grid=grid
    )
    return replace(report, domain_rejected=rejected)


def run_enumeration(project: ProjectFile, unit_id: str, conditions: ConditionSet,
                    env: RunEnv, options: EnumerationOptions | None = None
                    ) -> EnumerationOutcome:
    """单单元枚举正门（ADR-005/UF-33）：装配→网格→上游快照→枚举→过滤→排序→诊断。

    批5 AUD-W5：可行集双源口径统一（行非 NaN ∧ 约束通过——联合枚举/
    可行域图 PD2 同源，enumerate.feasible_indices 单源）；域拒行不再
    进排序/分页面（R5 行级域拒交诊断面承载）。
    """
    assembled = assemble(project, env)
    unit = assembled.units.get(unit_id)
    if unit is None:
        raise InvalidAssemblyError(
            f"枚举目标单元 {unit_id!r} 不在装配图（单单元语义 ADR-005——多单元拒绝在"
            " server 层；core 侧未命中=InvalidAssemblyError）"
        )
    grid = build_grid(
        [spec for spec in unit.manifest.params if spec.grid is not None],
        overrides=env.assumptions,
    )
    # ADR-018 D2：空集=直构程序缺陷（正门 build_condition_set 恒非空——GR-11，M-5）。
    if not conditions.baseline and not conditions.sensitivity:
        raise InvalidAssemblyError(
            "conditions 为空集（枚举逐工况迭代前提失败——正门 build_condition_set "
            "恒非空，空集=直构程序缺陷；GR-11 收口，M-5）"
        )
    plant = execute_graph(
        project.design, assembled.units, conditions, completed_env(env, project.design)
    )
    # 逐工况快照重建→枚举→concat（行序=工况序×网格序）——app_enumeration 承载。
    df = enumerate_across_conditions(
        UpstreamSource(assembled.units, assembled.edges, project.design, plant),
        unit_id, conditions, grid, env)
    chosen = options if options is not None else EnumerationOptions()
    # 批2a：kb 带裕度列（与过滤同源）
    df[MARGIN_COLUMN] = band_margin_column(df, chosen.constraints)
    filtered = apply_constraints(df, chosen.constraints)
    # 批5 AUD-W5：双源可行（域拒行剔出可行集——单源 feasible_indices）
    filtered = FilterResult(
        feasible=feasible_indices(df, filtered.pass_matrix),
        pass_matrix=filtered.pass_matrix,
    )
    ranked = rank(filtered, df, RankingKey(chosen.sort_by, chosen.ascending, grid.fields),
                  chosen.limit if chosen.limit is not None else max(len(filtered.feasible), 1))
    return EnumerationOutcome(
        rows=ranked.rows, total_feasible=ranked.total_feasible, truncated=ranked.truncated,
        grid=grid,
        diagnosis=None if filtered.feasible else _enumeration_diagnosis(
            df, chosen.constraints, filtered.pass_matrix, grid),
        condition_fields=tuple(
            spec.label_zh or spec.field_id for spec in unit.manifest.out_dims),
        domain_rejected=int(df["nan_flag"].sum()))  # 批5 W-1：常规透传（有解路径域拒档亦可见）


def run_joint_enumerate(
    project: ProjectFile,
    unit_ids: Sequence[str],
    conditions: ConditionSet,
    env: RunEnv,
    options: JointEnumerationOptions | None = None,
) -> JointOutcome:
    """联合枚举正门（B4-3/ADR-25）：装配注入+转发（assemble=None 时本正门注入）。"""
    chosen = options if options is not None else JointEnumerationOptions()
    if chosen.assemble is None:  # AssembledGraph 结构满足 AssembleView 协议
        chosen = replace(chosen, assemble=cast("AssembleFn", assemble))
    return _joint_run(project, unit_ids, conditions, env, chosen)


__all__ = [  # app.py 再导出（消费面单入口零改动——B3 R1 先例同款）
    "run_enumeration",
    "run_joint_enumerate",
]
