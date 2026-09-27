"""联合枚举编排器主题段（beam.py 预算墙拆件——批6g 结构债）。

输入:  ProjectFile+unit_ids+ConditionSet+RunEnv+选项（beam 正门传入）
输出:  _JointSearch 编排器+JointOutcome/JointEnumerationTooLarge/
       estimate_rows 定义面（beam 再导出——公开面不变）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批6g 2026-09-26 拆件：beam.py 批5 拆件后 481 行、腾位目标
#   ≤450 仍差 31 行——wave6 §批6g 授权「主题段迁兄弟件（relax 先例）」；
#   ADR-024 拆件配方的单元包外模块裁定面=master plan 预裁拆法）。
#   语义自 beam 逐字迁入（B3 R1 整域逐字搬运先例）：编排器主题段
#   _ordered_targets+_JointSearch+_Prefix 族+_SEARCH_SEMANTICS+其运行
#   期构造消费的三公开名（JointOutcome/JointEnumerationTooLarge/
#   estimate_rows——定义面随段迁移使本件自持零回导，beam 再导出保
#   公开 import 路径与 __init__ 五名不变）；行为等价烤验=双跑 diff=0。
#
# 【公开接口】（包内私有面——不经子包 __init__ 再导出，消费=beam 单点；
#   relax.py 同款口径）
#   _ordered_targets(unit_ids, assembled, design) -> tuple[str, ...]
#       目标单元拓扑序（design.edges 上的 Kahn——输入序稳定破坏平局）
#   _JointSearch（编排器——进程内一次性实例，计数器承载双轴预算与
#       看门狗）：grids/static_precheck/_estimated_rows/within_budget/
#       multiplier/baseline/_timeout_hit/_stage_outcomes/_empty_stage_
#       payload/_extend/staged/_eval_context/final_eval/outcome
#   _PrefixParams/_Prefix：beam 传播原子类型别名（staged 前缀序列）
#   JointOutcome(不可变)/JointEnumerationTooLarge/estimate_rows：
#       产出 schema/静态预检超限异常/行估计公式（beam 公开面经再导出
#       保持——tests/消费面零改动）
#
# 【行为规格】与 beam 原实现同源（R1 分层 beam/R2 逐行绕缓存/R3 工况
#   口径/R4 双轴预算/R7 诊断分载——全文语义注记见 beam.py 规格头，
#   本件不重复持有防双源）。
#
# 【层序注记】solution→waterprint.graph import 现场=包根 __init__
#   （execute_graph 直调——W6；§1c 登记 independence=true），本件经
#   包根中继取用与 beam 原位同款（包内兄弟件，节点粒度 (f) 规则豁免）。
#
# 【测试要求】经 beam 全链测试覆盖（本件拆件非独立规格面——relax/
#   final_eval 先例）。
#
# 【参照】.workflow/b4-3/design-final.md；AGENTS §2 预算墙+§11 拆件配方；
#   .workflow/backend-calc-complete/wave6-master-plan.md §批6g
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING, Any, Final, final

from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.run_env import RunEnv
from waterprint.solution.grid import Grid
from waterprint.solution.joint_enumeration import diagnose as joint_diagnose
from waterprint.solution.joint_enumeration import execute_graph
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
    InvalidJointEnumerationError,
)

if TYPE_CHECKING:  # 选项类型面（beam 定义——运行期零导入防环，relax 先例）
    from waterprint.solution.joint_enumeration.beam import JointEnumerationOptions

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


__all__ = [
    "JointEnumerationTooLarge",
    "JointOutcome",
    "estimate_rows",
]
