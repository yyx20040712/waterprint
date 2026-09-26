"""联合枚举主编排：分层 beam + 静态预检 + 双轴预算（末段复验归 final_eval）。

输入:  ProjectFile+unit_ids+ConditionSet+RunEnv+选项（网格/约束覆盖+出水标准族）
输出:  JointOutcome（search_semantics+combos+diagnosis+budget_usage）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 终裁定稿 .workflow/b4-3/design-final.md——2026-09-20；
#   镜像测试 tests/solution/test_beam.py+benchmark/test_bench_joint.py）
#
# 【公开接口】
#   run_joint_enumerate(project, unit_ids, conditions, env, options)
#       -> JointOutcome（ADR-025 决策 1~6 落地正门；app 再导出=server
#       单入口 UF-33）
#   class JointEnumerationOptions(不可变)：grids（unit_id→轴声明覆盖，
#       缺省=manifest grid 档）/constraints（unit_id→单元级约束，server
#       装配 constraint_kb 同单单元源）/standards（出水标准族，worker 注入）
#       /assemble（类注入防环面——app 正门装配注入）/capex_data_dir
#       （批2b capex 装配数据目录——worker 注入 data_dir 同源单价包）
#   class JointOutcome(不可变)：search_semantics 四键（W3/W4/B1）+combos
#       +diagnosis+budget_usage{rows_evaluated,full_plant_evals,elapsed_ms,
#       truncated}（W1 截断：先到闸即停+部分结果诚实返回不报错）
#   class JointEnumerationTooLarge(Exception)：静态预检超限（rows>
#       max_total_rows 或 N>max_units）——422 面（W7 事前拒绝优于事后
#       截断；双闸定序：rows 静态预检为主，timeout 运行兜底）
#   estimate_rows(grid_sizes, beam_width, multiplier) -> float：g·(k^N−1)/(k−1)·W_s（k=1→g·N）
#
# 【行为规格】
#   R1 交付结构=分层序列化 beam（决策 2）：拓扑序逐单元枚举（基线上下文
#      冻结——B1 口径）→top-k 冻结传播→末段 k 组合全厂真值复验（W6 终裁：
#      直调 execute_graph 既有编排，不新写拓扑序不构成双轨）。
#   R2 评估口径=逐行 unit.compute 绕过缓存（决策 3）；CacheKey 挂账 B12。
#   R3 工况=基线搜索+末段全 ConditionSet 复验（决策 4；validation_
#      conditions 选择器 0=「all」/1=all_outer——后者静态预检乘 W_s，W5）。
#   R4 护栏键 solution.joint.* 全量经 assumption() 取值（W8 零魔法数）；
#      预算双轴 rows+full_plant_evals（N2）分别计费，静态 422+截断标注。
#   R5~R6 末段硬门/真键映射/降权标记=final_eval 件规格（W9/W10/W12/N6）。
#   R7 诊断分层：首空级=stage_conflicts（既有 diagnose 委托+前缀注记）；
#      末空级=relax_grid_specs 一次放宽（range 域面，离散档诚实原样）。
#      【批5 事由分叉（AUD-W7/P2）】末空级诊断三支：timeout 截断
#      （timeout_truncated=True——截断态不启动重试）/预算拒（放宽后
#      行估计超限 skip）/无域可放（名义放宽=离散档原样不重试）；放宽
#      重试回路迁 relax.py 伴生件（本件 500 行贴墙拆件——真实/名义
#      放宽区分与 RetryOutcome 事由面见该件规格头）。
#   R8 回路冻结=基线快照已知近似（决策 6/B1）；B12 后升级不动点迭代。
#
# 【层序注记】solution→waterprint.graph 唯一 import 现场=包根
#   joint_enumeration/__init__.py（execute_graph 直调——W6；§1c 登记
#   independence=true）。app_assembly=类注入防环（options.assemble，
#   app 正门注入点——assumptions_design_map 类注入先例）。
#
# 【测试要求】两单元小网格全链/静态预检 422/k=1 边界/超预算拒/截断语义。
# 【参照】.workflow/b4-3/design-final.md 全文；ADR-025
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from time import monotonic
from typing import Any, Final, final

from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.quality import EffluentStandard
from waterprint.contracts.run_env import RunEnv
from waterprint.solution.constraints import Constraint
from waterprint.solution.grid import Grid
from waterprint.solution.joint_enumeration import diagnose as joint_diagnose
from waterprint.solution.joint_enumeration import execute_graph
from waterprint.solution.joint_enumeration import relax as joint_relax
from waterprint.solution.joint_enumeration import stage as joint_stage
from waterprint.solution.joint_enumeration.final_eval import (
    ComboResult,
    EvalContext,
    JointGuards,
    capex_kit_of,
    completed_env,
    design_baseline_metrics,
    design_condition,
    evaluate_combo,
    joint_guards,
    merged_summary,
)
from waterprint.solution.joint_enumeration.ranking import (
    degraded_aware_order,
    prefix_order_key,
)
from waterprint.solution.joint_enumeration.stage import (
    AssembledView,
    AssembleFn,
    InvalidJointEnumerationError,
)

_SEARCH_SEMANTICS: Final[dict[str, str]] = {
    "structure": "staged_beam",
    "optimality": "beam_approx",
    "loop_semantics": "frozen",
    "pruning_bias": "baseline_context",
}
_PrefixParams = tuple[tuple[str, dict[str, float]], ...]  # (unit_id, 行参数) 序列；beam 传播原子
_Prefix = tuple[_PrefixParams, float]


class JointEnumerationTooLarge(Exception):  # noqa: N818  # GridTooLarge 先例（名承载 422 语义）
    """静态预检超限（rows>max_total_rows / N>max_units）——W7 事前拒绝。"""


@dataclass(frozen=True)
@final
class JointEnumerationOptions:
    """联合枚举选项（不可变）：网格/单元级约束覆盖+出水标准族。"""

    grids: Mapping[str, tuple[Mapping[str, Any], ...]] = field(default_factory=dict)
    constraints: Mapping[str, tuple[Constraint, ...]] = field(default_factory=dict)
    standards: tuple[EffluentStandard, ...] = ()
    assemble: AssembleFn | None = None  # 类注入防环（app 正门装配面注入）
    capex_data_dir: Path | None = None  # 批2b：capex 装配数据目录（worker 注入）

    def __post_init__(self) -> None:
        """映射归一（裸 str 拒——I-2 同款防线）。"""
        if isinstance(self.grids, str) or isinstance(self.constraints, str):
            raise TypeError(
                "JointEnumerationOptions.grids/constraints 须为映射，不接受裸 str"
                f"（逐字符拆解为伪键）：得到 {self.grids!r}/{self.constraints!r}"
            )
        object.__setattr__(self, "grids", dict(self.grids))
        object.__setattr__(self, "constraints", dict(self.constraints))


@dataclass(frozen=True)
@final
class JointOutcome:
    """联合枚举产出（不可变）：语义标注+组合+诊断+预算用量。"""

    search_semantics: Mapping[str, str]
    combos: tuple[ComboResult, ...]
    diagnosis: Mapping[str, Any] | None
    budget_usage: Mapping[str, Any]


def estimate_rows(
    grid_sizes: Sequence[int], beam_width: float, multiplier: int
) -> float:
    """分级枚举行估计：g·(k^N−1)/(k−1)·W_s（k=1→g·N——N1 边界式补）。"""
    width, units, largest = int(beam_width), len(grid_sizes), max(grid_sizes)
    if width == 1:
        return float(largest * units * multiplier)
    return float(largest * (width**units - 1) / (width - 1) * multiplier)


def _ordered_targets(
    unit_ids: Sequence[str], assembled: AssembledView, design: DesignState
) -> tuple[str, ...]:
    """目标单元拓扑序（design.edges 上的 Kahn——输入序稳定破坏平局）。"""
    graph: dict[str, set[str]] = {unit_id: set() for unit_id in unit_ids}
    seen: set[str] = set()
    for unit_id in unit_ids:
        if unit_id in seen:
            raise InvalidJointEnumerationError(f"unit_ids 重复：{unit_id!r}（GR-14 拒）")
        seen.add(unit_id)
        if unit_id not in assembled.units:
            raise InvalidJointEnumerationError(
                f"联合枚举目标单元 {unit_id!r} 不在装配图（core 侧未命中="
                "InvalidAssemblyError——单单元面同口径）"
            )
        if unit_id not in design.nodes:
            raise InvalidJointEnumerationError(
                f"联合枚举目标单元 {unit_id!r} 不在 design.nodes（内置源点不可寻优）"
            )
    for edge in assembled.edges:
        if edge.dst.unit_id in graph and edge.src.unit_id in graph:
            graph[edge.dst.unit_id].add(edge.src.unit_id)
    ordered: list[str] = []
    remaining = list(unit_ids)
    while remaining:
        ready = [u for u in remaining if graph[u] <= set(ordered)]
        if not ready:
            raise InvalidJointEnumerationError(
                f"目标单元子图有环（联合枚举拓扑序前提失败）：{remaining}"
            )
        chosen = ready[0]
        ordered.append(chosen)
        remaining.remove(chosen)
    return tuple(ordered)


@final
class _JointSearch:
    """编排器（进程内一次性实例——计数器承载双轴预算与看门狗）。"""

    def __init__(
        self, project: ProjectFile, unit_ids: Sequence[str], conditions: ConditionSet,
        env: RunEnv, options: JointEnumerationOptions,
    ) -> None:
        self.guards: JointGuards = joint_guards(env.assumptions)
        self.project = project
        self.conditions = conditions
        self.env = completed_env(env)
        self.options = options
        if options.assemble is None:
            raise InvalidJointEnumerationError(
                "JointEnumerationOptions.assemble 未注入（类注入防环面——"
                "经 waterprint.app 正门调用，直调须显式传装配函数）"
            )
        self.assembled = options.assemble(project, self.env)
        self.capex_kit = capex_kit_of(options.capex_data_dir)  # 批2b 装载一次
        self.targets = _ordered_targets(unit_ids, self.assembled, project.design)
        self.rows_evaluated = self.full_evals = 0  # 双轴预算计数器（int 链式同值）
        self.truncated = False
        self._started = monotonic()

    def grids(self) -> dict[str, Grid]:
        """逐目标网格（请求覆盖∪manifest 档——resolve_grid_specs 批5 迁 stage）。"""
        return {
            unit_id: joint_stage.grid_of(
                joint_stage.resolve_grid_specs(
                    unit_id, self.assembled, self.options.grids.get(unit_id)
                ),
                self.env.assumptions,
            )
            for unit_id in self.targets
        }

    def static_precheck(self, grids: Mapping[str, Grid]) -> None:
        """W7 静态预检：rows≤max_total_rows 且 N≤max_units（事前 422 主闸）。"""
        if len(self.targets) > self.guards.max_units:
            raise JointEnumerationTooLarge(
                f"目标单元数 {len(self.targets)} 超 max_units="
                f"{self.guards.max_units:g}（solution.joint.max_units——N3 硬域"
                "由 rows 公式天然守域）"
            )
        rows = self._estimated_rows(grids)
        if rows > self.guards.max_rows:
            raise JointEnumerationTooLarge(
                f"分级枚举行估计 {rows:g} 超预算 max_total_rows="
                f"{self.guards.max_rows:g}（g={max(g.total for g in grids.values())},"
                f" k={self.guards.beam_width:g}, N={len(grids)}, "
                f"W_s={self.multiplier()}——W7 静态预检；建议缩小网格/降低 "
                "beam_width/减少单元）"
            )

    def _estimated_rows(self, grids: Mapping[str, Grid]) -> float:
        """静态行估计（静态预检与放宽重试预算共用——批5 单源）。"""
        return estimate_rows(
            [grid.total for grid in grids.values()], self.guards.beam_width,
            self.multiplier(),
        )

    def within_budget(self, grids: Mapping[str, Grid]) -> bool:
        """放宽重试预算预检（不抛——批5 AUD-W7 skip 事由分叉）。"""
        return self._estimated_rows(grids) <= self.guards.max_rows

    def multiplier(self) -> int:
        """W_s：all_outer=全工况数；默认「all」搜索=基线 design 单工况。"""
        if self.guards.all_outer:
            return sum(1 for _ in self.conditions.iter_all())
        return 1

    def baseline(self) -> tuple[joint_stage.BaselineSource, dict[str, float]]:
        """基线执行（全工况一次）+design 工况真键基线（归一化基准+capex 并键）。"""
        source = joint_stage.baseline_run(
            self.project.design, self.assembled, self.conditions, self.env,
            execute_graph,
        )
        summary = merged_summary(source.plant, self.assembled.edges, self.env)
        return source, design_baseline_metrics(
            summary, self.conditions,
            plant=source.plant, capex_kit=self.capex_kit,
        )

    def _timeout_hit(self) -> bool:
        """看门狗（timeout_s 运行兜底——W1 双闸第二闸）。"""
        return (monotonic() - self._started) > self.guards.timeout_s

    def _stage_outcomes(
        self, source: joint_stage.BaselineSource, unit_id: str, grid: Grid,
        search_conditions: Sequence[OperatingCondition],
    ) -> tuple[joint_stage.StageOutcome, ...]:
        """逐搜索工况求值（all_outer=多帧——行数计费含 W_s）。"""
        position = self.targets.index(unit_id)
        constraints = self.options.constraints.get(unit_id, ())
        return tuple(
            joint_stage.evaluate_stage(
                self.assembled.units[unit_id],
                joint_stage.StageContext(
                    unit_id=unit_id,
                    prefix={},
                    condition=condition,
                    baseline_energy=joint_stage.baseline_energy_of(
                        source, self.targets[:position],
                        ConditionSet.key(design_condition(self.conditions)),
                    ),
                    grid=grid,
                    constraints=constraints,
                    share=self.guards.share,
                ),
                joint_stage.baseline_context(source, unit_id, condition, self.env),
                self.env,
            )
            for condition in search_conditions
        )

    def _empty_stage_payload(
        self, outcome: joint_stage.StageOutcome, unit_id: str, prefix: _PrefixParams,
        grid: Grid,
    ) -> dict[str, Any]:
        """首空级诊断载荷：约束面走既有 diagnose；无约束=域拒注记（R7）。"""
        frozen = {unit: dict(params) for unit, params in prefix}
        constraints = self.options.constraints.get(unit_id, ())
        if outcome.pass_matrix is not None:
            return joint_diagnose.stage_conflicts(
                outcome.pass_matrix, {c.key: c for c in constraints}, grid, frozen
            )
        return {
            "minimal_conflicts": [],
            "fail_counts": {"domain_nan_rows": len(outcome.frame)},
            "suggestions": [],
            "frozen_prefix": frozen,
            "note": "阶段全行域拒（NaN）且无单元级约束面——无冲突集可求",
        }

    def _extend(
        self, prefixes: Sequence[_Prefix], outcome: joint_stage.StageOutcome,
        feasible: set[int], proxies: Mapping[int, float], grid: Grid,
    ) -> list[tuple[_PrefixParams, float]]:
        """top-k 冻结传播：前缀×可行行扩展+累计代理分排序截断。"""
        extended: list[tuple[_PrefixParams, float]] = []
        for params, score in prefixes:
            for index in sorted(feasible):
                row = outcome.frame.iloc[index]
                row_params = {field: float(row[field]) for field in grid.fields}
                extended.append((
                    (*params, (outcome.unit_id, row_params)), score + proxies[index],
                ))
        extended.sort(key=lambda item: (-item[1], prefix_order_key(item[0])))
        return extended[: int(self.guards.beam_width)]

    def staged(
        self, source: joint_stage.BaselineSource, grids: Mapping[str, Grid]
    ) -> tuple[_Prefix, ...] | Mapping[str, Any]:
        """beam 主循环：逐级 top-k 冻结传播；首空级返回诊断载荷（联合类型）。"""
        search_conditions = joint_stage.search_conditions(self.conditions, self.guards.all_outer)
        prefixes: list[_Prefix] = [((), 0.0)]
        for unit_id in self.targets:
            outcomes = self._stage_outcomes(
                source, unit_id, grids[unit_id], search_conditions
            )
            self.rows_evaluated += len(prefixes) * grids[unit_id].total * len(
                search_conditions
            )
            feasible = set(outcomes[0].feasible)
            for outcome in outcomes[1:]:
                feasible &= set(outcome.feasible)  # all_outer：全工况可行交集（保守）
            if not feasible:
                return self._empty_stage_payload(
                    outcomes[0], unit_id, prefixes[0][0], grids[unit_id]
                )
            proxies = {
                index: sum(o.proxies.get(index, 0.0) for o in outcomes) / len(outcomes)
                for index in feasible
            }
            prefixes = self._extend(
                prefixes, outcomes[0], feasible, proxies, grids[unit_id]
            )
            if self._timeout_hit():
                self.truncated = True
                break
        return tuple(prefixes)

    def _eval_context(self, baseline: Mapping[str, float]) -> EvalContext:
        """末段复验上下文（final_eval 消费束）。"""
        return EvalContext(
            project=self.project, assembled=self.assembled, execute=execute_graph,
            conditions=self.conditions, env=self.env,
            standards=self.options.standards, baseline=baseline,
            weights=self.guards.weights, capex_kit=self.capex_kit,
        )

    def final_eval(
        self, prefixes: Sequence[_PrefixParams], baseline: Mapping[str, float]
    ) -> list[ComboResult]:
        """末段 k 组合全厂复验（双轴第二轴+看门狗——截断诚实标注）。"""
        context = self._eval_context(baseline)
        combos: list[ComboResult] = []
        for params in prefixes:
            if self.full_evals >= self.guards.max_evals or self._timeout_hit():
                self.truncated = True
                break
            combos.append(evaluate_combo(context, params))
            self.full_evals += 1
        return combos

    def outcome(
        self, combos: Sequence[ComboResult], diagnosis: Mapping[str, Any] | None
    ) -> JointOutcome:
        """产出组装：降权感知排序（W10——可行组合含降权标记）+预算回填。"""
        feasible = [combo for combo in combos if combo.feasible]
        scored = [
            (float(combo.score or 0.0), combo.sensitivity_degraded,
             prefix_order_key(tuple(sorted(combo.params.items()))))
            for combo in feasible
        ]
        order = degraded_aware_order(scored)
        return JointOutcome(
            search_semantics=dict(_SEARCH_SEMANTICS),
            combos=tuple(feasible[index] for index in order),
            diagnosis=diagnosis,
            budget_usage={
                "rows_evaluated": self.rows_evaluated, "full_plant_evals": self.full_evals,
                "elapsed_ms": round((monotonic() - self._started) * 10**2 * 10),
                "truncated": self.truncated,
            },
        )


def run_joint_enumerate(
    project: ProjectFile, unit_ids: Sequence[str], conditions: ConditionSet,
    env: RunEnv, options: JointEnumerationOptions | None = None,
) -> JointOutcome:
    """联合枚举正门（ADR-025）：静态预检→基线→分层 beam→末段复验→排序。"""
    chosen = options if options is not None else JointEnumerationOptions()
    if not conditions.baseline and not conditions.sensitivity:
        raise InvalidJointEnumerationError(
            "conditions 为空集（正门 build_condition_set 恒非空——M-5 同口径）"
        )
    search = _JointSearch(project, unit_ids, conditions, env, chosen)
    grids = search.grids()
    search.static_precheck(grids)
    source, baseline = search.baseline()
    staged = search.staged(source, grids)
    if isinstance(staged, Mapping):  # 首空级：分层诊断交付（空组合=合法终态）
        return search.outcome((), {"kind": "stage_empty", "stage": staged})
    combos = search.final_eval([params for params, _ in staged], baseline)
    if not any(combo.feasible for combo in combos):
        skip_reason: str | None = None
        if not search.truncated:  # 截断态不启动放宽重试（复验未完成非域拒结论）
            widened = joint_relax.relaxed_grids(chosen.grids, search.guards.relax_factor)
            if widened:  # 真实域扩才重试（名义放宽=离散档原样诚实跳过）
                retry = joint_relax.retry_joint(
                    search, replace(chosen, grids={**chosen.grids, **widened}), baseline
                )
                if retry.outcome is not None:
                    return retry.outcome
                skip_reason = retry.skip_reason
        return search.outcome(
            combos, _final_infeasible_diagnosis(search.truncated, skip_reason)
        )
    return search.outcome(combos, None)


def _final_infeasible_diagnosis(truncated: bool, skip_reason: str | None) -> dict[str, Any]:
    """末空级诊断载荷（批5 事由分叉：timeout 维度/预算拒/无域可放——AUD-W7）。"""
    payload: dict[str, Any] = {
        "kind": "final_infeasible", "relaxed": False, "timeout_truncated": truncated,
    }
    if truncated:
        payload["note"] = (
            "末段因 timeout 截断——复验未完成即返（非域拒结论；截断态不启动放宽重试）"
        )
    elif skip_reason == "budget":
        payload["note"] = (
            "末段组合全不可行且存在可放宽 range 域，但放宽后行估计超 "
            "max_total_rows——静态预检口径统一执法不重试"
        )
    else:
        payload["note"] = (
            "末段组合全不可行且无可放宽 range 域（离散档网格无连续域——"
            "名义放宽不重试）"
        )
    return payload


__all__ = [
    "JointEnumerationOptions",
    "JointEnumerationTooLarge",
    "JointOutcome",
    "estimate_rows",
    "run_joint_enumerate",
]
