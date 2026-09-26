"""联合枚举末段复验件：全厂真值评估面（terminal 六指标+summary 合成+硬门）。

输入:  merged 瞬态 DesignState+装配图+ConditionSet+RunEnv+标准族+基线指标
输出:  ComboResult（可行性/降权标记/真键指标/得分）+护栏快照+环境补齐
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 定稿件 W6/W9/W10/W12/N6；beam.py 500 行预算拆件
#   2026-09-20——宪法 §2「超限拆文件」，任务书「每文件 ≤500 行（超=拆件）」
#   授权；镜像测试=tests/solution/test_beam.py 末段面断言）
#
# 【公开接口】
#   terminal_summary(plant, edges)：出水六指标投影（自 app._summary_of
#       迁入单源——app.py 顶部 import 别名消费，B4 双胞胎禁令）
#   merged_summary(plant, edges, env)：summary 合成（run_full_calc
#       D10/B4-2abc 同序纯投影：六指标→能耗→进水负荷→opex→碳）
#   completed_env(env)：engine_params loop.* 补齐（app._completed_env
#       同语义本件化——L3 禁上行 import app）
#   design_condition(conditions)：design 基线工况（[0] 锚——GR-20）
#   class JointGuards + joint_guards(assumptions)：solution.joint.*
#       护栏快照（registry 取值一次，R4 零魔法数）
#   class EvalContext(不可变) + evaluate_combo(context, params)
#       -> ComboResult：单组合末段真值=merged 瞬态 DesignState→
#       execute_graph 全厂一次（含全工况）→summary→R5 硬门（baseline
#       design/avg 越限=不可行；sensitivity 失守=降权标记 W10；opex
#       design 工况缺席=sparse 判不在场→不可行 N6/W12）→R6 真键指标
#       （design 主+avg 附带+出水六指标 FE 达标面）→排序分
#   capex_kit_of(data_dir)/capex_grand_total(kit, plant, condition)
#       （批2b 第四真键：cost_capex_yuan=概算 grand_total——AUD-W11
#       断层修复，装配链 services/cost.py R3 同款；kit 缺席=capex 键
#       恒缺 N6 重分配承接，core 直调向后兼容）
#   capex_estimate(kit, plant, condition_key)/capex_annualized(sheet,
#       coefficients)（批6c LCC 折旧面 2026-09-26——AUD-W11 后半：直线法
#       双键展示维度 cost_capex_annualized_yuan_a=equip/L_e+other/L_c；
#       不进 objective〔_METRIC_KEYS/权重/baseline 零变更——结构性排除〕；
#       factor.lcc.* sparse（opex 前缀列举先例）+kit 缺席随 capex 双缺）
#   class ComboResult(不可变)：params/feasible/sensitivity_degraded/
#       failed_conditions/metrics/score（W11 schema 面）
#
# 【行为规格】
#   R1 全厂真值唯一源=execute_graph（W6 终裁：直调既有编排不新写拓扑
#      序不构成双轨）；逐组合全工况一次。
#   R2 纯投影：summary 消费既有聚合器（app_energy/app_influent/
#      app_opex/app_carbon §1a 外根伴生件——UF-33 挂账维持）。
#   R3 确定性：同输入同 ComboResult（可复算）。
#
# 【测试要求】经 beam 全链测试覆盖（本件拆件非独立规格面）。
#
# 【参照】.workflow/b4-3/design-final.md §一 W6/W9/W10/W12/N6；ADR-025
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, final

from waterprint.app_carbon import carbon_summary_of
from waterprint.app_energy import energy_summary_of
from waterprint.app_influent import influent_summary_of
from waterprint.app_opex import opex_summary_of
from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.ports import Edge
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.quality import EffluentStandard
from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.run_env import CoefficientsView, EngineParam, RunEnv
from waterprint.cost import (  # 包根再导出面（批2b 同层边 import 收敛——§1c 声明承载）
    EstimateSheet,
    FeeRule,
    FieldMapping,
    PriceBook,
    build_estimate,
    load_fee_rules,
    load_field_mapping,
    load_prices,
    takeoff_quantities,
)
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS, assumption
from waterprint.solution.joint_enumeration.ranking import plant_objective
from waterprint.solution.joint_enumeration.stage import (
    AssembledView,
    GraphExecutor,
    InvalidJointEnumerationError,
)

# ── registry 键（R4 零魔法数——solution.joint.* 全量）──────────────
_KEY_BEAM: Final[str] = "solution.joint.beam_width"
_KEY_MAX_UNITS: Final[str] = "solution.joint.max_units"
_KEY_MAX_ROWS: Final[str] = "solution.joint.max_total_rows"
_KEY_TIMEOUT: Final[str] = "solution.joint.timeout_s"
_KEY_MAX_EVALS: Final[str] = "solution.joint.max_full_plant_evals"
_KEY_RELAX: Final[str] = "solution.joint.relax_factor"
_KEY_SHARE: Final[str] = "solution.joint.stage_proxy_weights"
_KEY_W_OPEX: Final[str] = "solution.joint.objective_weight_opex"
_KEY_W_ENERGY: Final[str] = "solution.joint.objective_weight_energy"
_KEY_W_CARBON: Final[str] = "solution.joint.objective_weight_carbon"
_KEY_W_CAPEX: Final[str] = "solution.joint.objective_weight_capex"
_KEY_VALIDATION: Final[str] = "solution.joint.validation_conditions"
_ALL_OUTER: Final[float] = 1.0  # validation_conditions 选择阈值（0=all/1=all_outer）
_LOOP_KEYS: Final[tuple[str, ...]] = (
    "loop.tolerance", "loop.max_iterations", "loop.damping",
)
_UNIT_PRICES_DIR: Final[str] = "unit_prices"  # 单价包目录名（services/cost.py R3 同款）
_FIELD_MAPPING_NAME: Final[str] = "field_mapping.yaml"  # 装配 DSL 文件名（同款）
# W12+批2b 真键映射（排序别名→指标键；avg 工况附带面用平键前缀；capex 键
# 非 summary 平键——evaluate_combo 装配后并入，avg 附带面不产出）
_METRIC_KEYS: Final[dict[str, str]] = {
    "opex": "cost_opex_yuan_a",
    "energy": "power_total_kwh_d",
    "carbon": "carbon_intensity_kgco2e_m3",
    "capex": "cost_capex_yuan",
}
# 批6c LCC 展示维度（设计件 b6c-design.md §三——不入 _METRIC_KEYS=不进
# objective/基线/排序，score 结构性排除；消费系数 factor.lcc.* 双键）
_LCC_PREFIX: Final[str] = "factor.lcc."
_KEY_LIFE_CIVIL: Final[str] = "factor.lcc.life_civil_structure_a"
_KEY_LIFE_EQUIP: Final[str] = "factor.lcc.life_equipment_a"
_COST_CAPEX_ANNUALIZED: Final[str] = "cost_capex_annualized_yuan_a"
_AVG_PREFIX: Final[str] = "avg."
_SUMMARY_INDICATORS: Final[tuple[str, ...]] = (
    "BOD5", "CODCR", "SS", "NH3N", "TN", "TP",
)


@dataclass(frozen=True)
@final
class ComboResult:
    """末段复验组合（不可变）：参数+可行性+降权标记+指标+得分（W11）。"""

    params: Mapping[str, Mapping[str, float]]
    feasible: bool
    sensitivity_degraded: bool
    failed_conditions: tuple[str, ...]
    metrics: Mapping[str, float]
    score: float | None = None


@dataclass(frozen=True)
@final
class JointGuards:
    """护栏快照（registry 取值一次——运行期只读）。"""

    beam_width: float
    max_units: float
    max_rows: float
    timeout_s: float
    max_evals: float
    relax_factor: float
    share: float
    weights: dict[str, float]
    all_outer: bool


def joint_guards(assumptions: Mapping[str, float]) -> JointGuards:
    """R4：全量经 assumption() 取值（覆盖优先——项目假设管道）+守卫域断言。"""
    guards = JointGuards(
        beam_width=assumption(_KEY_BEAM, assumptions),
        max_units=assumption(_KEY_MAX_UNITS, assumptions),
        max_rows=assumption(_KEY_MAX_ROWS, assumptions),
        timeout_s=assumption(_KEY_TIMEOUT, assumptions),
        max_evals=assumption(_KEY_MAX_EVALS, assumptions),
        relax_factor=assumption(_KEY_RELAX, assumptions),
        share=assumption(_KEY_SHARE, assumptions),
        weights={
            "opex": assumption(_KEY_W_OPEX, assumptions),
            "energy": assumption(_KEY_W_ENERGY, assumptions),
            "carbon": assumption(_KEY_W_CARBON, assumptions),
            "capex": assumption(_KEY_W_CAPEX, assumptions),
        },
        all_outer=assumption(_KEY_VALIDATION, assumptions) >= _ALL_OUTER,
    )
    _assert_guard_domain(guards)
    return guards


def _assert_guard_domain(guards: JointGuards) -> None:
    """守卫域断言（批5 N10/P2：beam_width<1 等下界缺失曾无校验——构造期拒）。"""
    problems: list[str] = []
    if guards.beam_width < 1:
        problems.append(f"beam_width>=1（得到 {guards.beam_width:g}）")
    if guards.max_units < 1:
        problems.append(f"max_units>=1（得到 {guards.max_units:g}）")
    if guards.max_rows <= 0:
        problems.append(f"max_rows>0（得到 {guards.max_rows:g}）")
    if guards.timeout_s < 0:
        problems.append(f"timeout_s>=0（得到 {guards.timeout_s:g}——0=即截断合法）")
    if guards.max_evals < 1:
        problems.append(f"max_evals>=1（得到 {guards.max_evals:g}）")
    if guards.relax_factor <= 1:
        problems.append(f"relax_factor>1（得到 {guards.relax_factor:g}——放宽语义）")
    if not 0 <= guards.share <= 1:
        problems.append(f"share∈[0,1]（得到 {guards.share:g}——阶段代理份额）")
    negative = sorted(k for k, v in guards.weights.items() if v < 0)
    if negative or sum(guards.weights.values()) <= 0:
        problems.append(f"weights 各键>=0 且和>0（得到 {guards.weights}）")
    if problems:
        raise InvalidJointEnumerationError(
            "solution.joint.* 守卫域违例（项目假设覆盖越域——GR-11 构造期拒）："
            + "；".join(problems)
        )


def terminal_summary(
    plant: PlantResult, edges: tuple[Edge, ...]
) -> dict[str, dict[str, float]]:
    """出水六指标投影（自 app._summary_of 迁入——B4 双胞胎禁令单源化）。

    terminal=该工况快照序最后一个无出边单元；值=outqualities 六指标族
    交集（有则录无则略——矿井线 BOD5 缺/污泥线终端无水质键→空映射合法）。
    """
    sources = {edge.src.unit_id for edge in edges}
    summary: dict[str, dict[str, float]] = {}
    for condition_key, snapshot in plant.conditions.items():
        terminal = next((u for u in reversed(list(snapshot)) if u not in sources), "")
        out = snapshot[terminal].outqualities if terminal else {}
        summary[condition_key] = {
            indicator: value
            for indicator in _SUMMARY_INDICATORS
            if (value := out.get(f"{terminal}.out.{indicator}")) is not None
        }
    return summary


def merged_summary(
    plant: PlantResult, edges: tuple[Edge, ...], env: RunEnv
) -> dict[str, dict[str, float]]:
    """summary 合成（run_full_calc D10/B4-2abc 同序纯投影——诊断面不构）。"""
    base = terminal_summary(plant, edges)
    merged = {key: dict(fields) for key, fields in base.items()}

    def _absorb(extra: Mapping[str, Mapping[str, float]]) -> None:
        for key, fields in extra.items():
            merged.setdefault(key, {}).update(fields)

    _absorb(energy_summary_of(plant))
    _absorb(influent_summary_of(plant, edges, env.coefficients, base))
    _absorb(opex_summary_of(merged, env.coefficients))
    _absorb(carbon_summary_of(merged, env.coefficients))
    return merged


def completed_env(env: RunEnv) -> RunEnv:
    """engine_params 补齐（app._completed_env 同语义本件化——L3 禁上行）。"""
    if all(key in env.engine_params for key in _LOOP_KEYS):
        return env
    defaults = {item.key: item for item in DEFAULT_ASSUMPTIONS}
    merged = dict(env.engine_params)
    for key in _LOOP_KEYS:
        entry = defaults.get(key)
        if entry is None or key not in env.assumptions:
            raise InvalidJointEnumerationError(
                f"假设缺 {key!r}（合成视图投影前提失败——UF-08 同源口径）"
            )
        merged[key] = EngineParam(
            value=env.assumptions[key], source=entry.source, note=entry.note
        )
    return replace(env, engine_params=merged)


def design_condition(conditions: ConditionSet) -> OperatingCondition:
    """design 基线工况（build_condition_set 恒 design/avg 两档——[0] 锚）。"""
    return conditions.baseline[0]


@dataclass(frozen=True)
@final
class _CapexKit:
    """capex 装配束（不可变）：单价包+费率+字段映射——装载一次逐组合复用。"""

    book: PriceBook
    fees: tuple[FeeRule, ...]
    mapping: FieldMapping


def capex_kit_of(data_dir: Path | None) -> _CapexKit | None:
    """capex 装配束装载（批2b 第四真键）。

    None→None（缺席语义：capex 键恒缺，N6 权重重分配承接——core 直调
    向后兼容）；data_dir 在场经 services/cost.py R3 同款链装载（beam 入口
    一次，逐组合纯内存复用）。装载失败（数据包缺/键失联/单位不一致）=
    领域异常直上（GR-08 程序缺陷口径——入口早爆优于逐组合静默）。
    """
    if data_dir is None:
        return None
    unit_prices = data_dir / _UNIT_PRICES_DIR
    book = load_prices(unit_prices)
    fees = load_fee_rules(unit_prices / _FIELD_MAPPING_NAME, book)
    mapping = load_field_mapping(unit_prices / _FIELD_MAPPING_NAME)
    return _CapexKit(book=book, fees=fees, mapping=mapping)


def capex_estimate(
    kit: _CapexKit | None, plant: PlantResult, condition_key: str
) -> EstimateSheet:
    """概算表装配（design 口径真值）：takeoff→build_estimate（批6c 单次化）。

    批2b capex_grand_total 的装配体——grand_total 与 LCC 年折旧（批6c）同源
    单次装配复用（逐组合双取数免重复装配）。
    """
    if kit is None:
        raise InvalidJointEnumerationError(
            "capex_estimate 无装配束（kit 缺席——调用面前置 capex_kit 判在场）"
        )
    items = takeoff_quantities(
        plant, condition_key, price_book=kit.book, field_mapping=kit.mapping
    )
    return build_estimate(
        items, kit.book, kit.fees, repro=plant.repro, condition_key=condition_key
    )


def capex_grand_total(
    kit: _CapexKit | None, plant: PlantResult, condition_key: str
) -> float:
    """概算总造价（design 口径真值）：capex_estimate 薄壳（批2b 公开面零变）。"""
    return float(capex_estimate(kit, plant, condition_key).grand_total)


def capex_annualized(
    sheet: EstimateSheet, coefficients: CoefficientsView
) -> float | None:
    """批6c LCC 展示维度：直线折旧年额（factor.lcc.* 双键 sparse——任一缺=None）。

    equip_base=equipment_subtotal（设备购置费小计）/other_base=grand_total−
    equipment_subtotal（其余资本化全量：建安非设备+间接+预备+税——递延并入，
    资本摊销同径；安装费归并注记 b6c-rulings ③⑥）；残值率 0 简化（各方案
    同口径可比）；判在场=前缀列举（app_opex R1 先例——系数包无 LCC 族合法）。
    """
    lives = set(coefficients.keys(_LCC_PREFIX))
    if not {_KEY_LIFE_CIVIL, _KEY_LIFE_EQUIP} <= lives:
        return None
    equipment_base = sheet.equipment_subtotal
    other_base = sheet.grand_total - sheet.equipment_subtotal
    return (
        equipment_base / coefficients.get(_KEY_LIFE_EQUIP).value
        + other_base / coefficients.get(_KEY_LIFE_CIVIL).value
    )


def design_baseline_metrics(
    summary: Mapping[str, Mapping[str, float]], conditions: ConditionSet,
    plant: PlantResult | None = None, capex_kit: _CapexKit | None = None,
) -> dict[str, float]:
    """design 工况真键基线（归一化基准——缺键 0.0 由 N6 重分配承接）。

    批2b：plant+capex_kit 双在场→并 capex 基线（AUD-W11 断层根因——
    概算不在 summary 平键链，基线经基线 plant 装配取数）；缺席→三键照旧。
    """
    design_key = ConditionSet.key(design_condition(conditions))
    baseline = {
        name: summary.get(design_key, {}).get(key, 0.0)
        for name, key in _METRIC_KEYS.items() if name != "capex"
    }
    if plant is not None and capex_kit is not None:
        baseline["capex"] = capex_grand_total(capex_kit, plant, design_key)
    return baseline


@dataclass(frozen=True)
@final
class EvalContext:
    """末段复验上下文（不可变）：装配+工况+环境+标准+基线+权重+capex 束。"""

    project: ProjectFile
    assembled: AssembledView
    execute: GraphExecutor
    conditions: ConditionSet
    env: RunEnv
    standards: tuple[EffluentStandard, ...]
    baseline: Mapping[str, float]
    weights: Mapping[str, float]
    capex_kit: _CapexKit | None = None  # 批2b：None=capex 键缺席（向后兼容）


def merged_design(
    project: ProjectFile, params: Sequence[tuple[str, Mapping[str, float]]]
) -> DesignState:
    """merged 瞬态 DesignState（combo 参数并入节点——瞬态不落盘）。"""
    nodes = {key: dict(value) for key, value in project.design.nodes.items()}
    for unit_id, row_params in params:
        nodes.setdefault(unit_id, {}).update(row_params)
    return project.design.model_copy(update={"nodes": nodes})


def compliance_of(
    summary: Mapping[str, Mapping[str, float]], standards: Sequence[EffluentStandard],
    baseline_keys: frozenset[str],
) -> tuple[bool, tuple[str, ...]]:
    """R5 硬门：baseline 越限=不可行；sensitivity 失守=降权标记载荷（W10）。"""
    failed: list[str] = []
    for condition_key, fields in summary.items():
        for standard in standards:
            breached = [
                indicator for indicator in sorted(standard.limits)
                if (value := fields.get(indicator)) is not None
                and value > standard.limits[indicator]
            ]
            if breached:
                failed.append(
                    f"{condition_key}:{standard.standard_id}:{'+'.join(breached)}"
                )
    baseline_failed = [
        item for item in failed if item.split(":", 1)[0] in baseline_keys
    ]
    return (not baseline_failed), tuple(failed)


def metrics_of(
    summary: Mapping[str, Mapping[str, float]], conditions: ConditionSet
) -> dict[str, float]:
    """R6 指标面：三真键 design 主+avg 附带+出水六指标（design 工况）。"""
    design_key = ConditionSet.key(design_condition(conditions))
    avg_key = ConditionSet.key(conditions.baseline[1])
    metrics: dict[str, float] = {}
    for key in _METRIC_KEYS.values():
        for prefix, source_key in (("", design_key), (_AVG_PREFIX, avg_key)):
            value = summary.get(source_key, {}).get(key)
            if value is not None:
                metrics[f"{prefix}{key}"] = value
    metrics.update(
        {key: value for key, value in summary.get(design_key, {}).items()
         if key in _SUMMARY_INDICATORS}
    )
    return metrics


def evaluate_combo(
    context: EvalContext, params: Sequence[tuple[str, Mapping[str, float]]]
) -> ComboResult:
    """单组合末段真值：全厂一次（含全工况）→summary→硬门+指标+得分（R1）。"""
    plant = context.execute(
        merged_design(context.project, params), context.assembled.units,
        context.conditions, context.env,
    )
    summary = merged_summary(plant, context.assembled.edges, context.env)
    baseline_keys = frozenset(
        ConditionSet.key(c) for c in context.conditions.baseline
    )
    feasible, failed = compliance_of(summary, context.standards, baseline_keys)
    metrics = metrics_of(summary, context.conditions)
    if context.capex_kit is not None:  # 批2b 第四真键+批6c LCC 展示维度（design 口径）
        sheet = capex_estimate(
            context.capex_kit, plant,
            ConditionSet.key(design_condition(context.conditions)),
        )
        metrics[_METRIC_KEYS["capex"]] = float(sheet.grand_total)
        annualized = capex_annualized(sheet, context.env.coefficients)
        if annualized is not None:  # factor.lcc.* sparse（批6c）
            metrics[_COST_CAPEX_ANNUALIZED] = annualized
    if feasible and _METRIC_KEYS["opex"] not in metrics:
        feasible = False  # N6/W12：opex design 工况缺席=sparse 判不在场→不可行
        failed = (*failed, f"{ConditionSet.key(design_condition(context.conditions))}"
                           ":opex_absent")
    degraded = feasible and any(
        item.split(":", 1)[0] not in baseline_keys for item in failed
    )
    alias_values = {
        name: metrics[key] for name, key in _METRIC_KEYS.items() if key in metrics
    }
    return ComboResult(
        params={unit_id: dict(row) for unit_id, row in params},
        feasible=feasible,
        sensitivity_degraded=degraded,
        failed_conditions=failed,
        metrics=metrics,
        score=plant_objective([alias_values], context.baseline, context.weights)[0],
    )


__all__ = [
    "ComboResult",
    "EvalContext",
    "JointGuards",
    "capex_annualized",
    "capex_estimate",
    "capex_grand_total",
    "capex_kit_of",
    "completed_env",
    "compliance_of",
    "design_condition",
    "evaluate_combo",
    "joint_guards",
    "merged_design",
    "merged_summary",
    "metrics_of",
    "terminal_summary",
]
