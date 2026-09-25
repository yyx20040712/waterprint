"""联合枚举阶段件：冻结前缀 StageContext + 基线上下文 + 逐级枚举求值。

输入:  基线 plant 快照（execute_graph 产物）+ 网格 + 单元级约束 + 代理份额
输出:  StageOutcome（枚举行 pandas.DataFrame+可行索引+逐行阶段代理分+约束矩阵）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 定稿件 §一 B1/§二；镜像测试 tests/solution/test_joint_units.py）
#
# 【公开接口】
#   class StageContext(不可变)：unit_id/prefix（冻结前缀 unit_id→参数）/
#       condition（搜索工况）/baseline_energy（前缀单元基线能耗和——B1
#       冻结口径）/grid/constraints/share（阶段代理裕度份额，registry
#       solution.joint.stage_proxy_weights）
#   class BaselineSource(不可变)：units/edges/design/plant 四字段束
#       （beam 装配与基线执行产物——app_enumeration.UpstreamSource 同构
#       不同语义：本源=联合枚举基线快照，B1 回路冻结口径载体）
#   baseline_context(source, unit_id, condition, env) -> UnitContext：
#       基线上下文重建（UF-42 投影表反解入流股——与单单元上游快照
#       同构管道【不同语义】：单单元冻结的是不受决策影响的上游；本处
#       回路反馈边与前缀上游流量一律取基线设计快照=方向相反的已知
#       近似[终裁 B1]，输出标注 loop_semantics:'frozen'；L3 层序禁
#       solution→app_enumeration 上行，重建逻辑本件内实现）
#   evaluate_stage(unit, stage, context, env) -> StageOutcome：逐级枚举
#       （enumerate_solutions 同管线 R2 逐行 compute 绕过缓存）+单元级
#       约束过滤+双源可行（行非 NaN ∧ 约束通过——PD2 同源口径）+逐行
#       阶段代理分
#   stage_proxies(frame, feasible, share, baseline_energy) -> Mapping：
#       代理分=share×裕度归一+(1−share)×能耗归一（min-max 逐阶段归一；
#       无区分度分量=1/2 中位——禁编造区分度）
#   energy_estimate(dims, baseline_energy) -> float：能耗代理估计=
#       B4-2a 三键（e_aeration/e_pump/e_stir）和+前缀基线贡献
#
# 【行为规格】
#   R1 冻结前缀不可变（frozen dataclass——中途改值=程序缺陷）。
#   R2 评估口径=逐行 unit.compute（enumerate_solutions 单实现双用——
#      禁双轨实质=唯一计算源）。
#   R3 代理分确定性：同 frame 同份额同输出（min-max 归一+固定中位）。
#   R4 阶段层不做全厂真值（末段复验归 beam——本件只产候选与代理）。
#
# 【测试要求】裕度/能耗分量方向、无区分度中位、三键和+基线贡献、
#   前缀冻结。
#
# 【参照】.workflow/b4-3/design-final.md §一 B1/§二；ADR-025 决策 3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isnan
from typing import Any, Protocol, final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（enumerate 同款）

from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Unit, UnitContext
from waterprint.solution.constraints import Constraint, apply_constraints
from waterprint.solution.enumerate import enumerate_solutions
from waterprint.solution.grid import Grid, build_grid


class InvalidJointEnumerationError(Exception):
    """联合枚举输入非法（重复/未在图/无网格/环境缺键）——GR-11 族，本包定义。"""


class AssembledView(Protocol):
    """装配产物视图协议（结构满足 app_assembly.AssembledGraph——类注入防环）。"""

    design: DesignState
    units: Mapping[str, Unit]
    edges: tuple[Edge, ...]


class AssembleFn(Protocol):
    """装配函数协议（app_assembly.assemble 注入面——solution 层序禁上行）。"""

    def __call__(self, project: ProjectFile, env: RunEnv) -> AssembledView: ...


class GraphExecutor(Protocol):
    """图执行器协议（graph.execute_graph 注入/包根中继面——W6 直调既有编排）。"""

    def __call__(
        self, design: DesignState, units: Mapping[str, Unit],
        conditions: ConditionSet, env: RunEnv,
    ) -> PlantResult: ...


# B4-2a 能耗 dims 三键（app_energy._POWER_FIELDS 键集同源——单元自报口径）
_ENERGY_KEYS: tuple[str, ...] = ("e_aeration", "e_pump", "e_stir")
_MARGIN_COLUMN: str = "margin_min"
_NAN_COLUMN: str = "nan_flag"
_MIDPOINT: float = 1 / 2  # 无区分度分量中位（幂底式 1/2——魔法数白名单形态）


@dataclass(frozen=True)
@final
class BaselineSource:
    """基线取数面（不可变）：装配产物与基线执行结果四字段束（beam 构造）。"""

    units: Mapping[str, Unit]
    edges: tuple[Edge, ...]
    design: DesignState
    plant: PlantResult


@dataclass(frozen=True)
@final
class StageContext:
    """阶段上下文（不可变）：冻结前缀+搜索工况+阶段求值参数束。"""

    unit_id: str
    prefix: Mapping[str, Mapping[str, float]]
    condition: OperatingCondition
    baseline_energy: float = 0.0
    grid: Grid | None = None
    constraints: tuple[Constraint, ...] = ()
    share: float = 1.0


@dataclass(frozen=True)
@final
class StageOutcome:
    """阶段产出（不可变）：枚举行+可行索引+代理分+约束矩阵（诊断面）。"""

    unit_id: str
    frame: pandas.DataFrame
    feasible: tuple[int, ...]
    proxies: Mapping[int, float]
    pass_matrix: pandas.DataFrame | None

    @property
    def empty(self) -> bool:
        """首空级判定：无任何可行候选行。"""
        return not self.feasible


class _NullSink:
    """空迹收集器（阶段枚举行迹由 enumerate 内部空 sink 承载——同源语义）。"""

    def record(self, node: object) -> None:
        """丢弃记录（结构满足 TraceSink 协议）。"""


def energy_estimate(dims: Mapping[str, float], baseline_energy: float) -> float:
    """能耗代理估计：B4-2a 三键和+前缀基线贡献（B1 冻结口径）。"""
    return baseline_energy + sum(
        value for key, value in dims.items() if key in _ENERGY_KEYS and not isnan(value)
    )


def _normalized(values: Sequence[float]) -> list[float]:
    """min-max 归一到 0~1（无区分度或含 NaN=中位 1/2——R3 禁编造区分度）。"""
    low, high = min(values), max(values)
    if high <= low or any(isnan(value) for value in values):
        return [_MIDPOINT] * len(values)
    return [(value - low) / (high - low) for value in values]


def stage_proxies(
    frame: pandas.DataFrame, feasible: Sequence[int], share: float, baseline_energy: float
) -> dict[int, float]:
    """逐可行行阶段代理分：share×裕度归一+(1−share)×能耗归一（确定性）。

    空可行集=空代理分早退（无可行行即无候选——beam 首空级诊断面承接）。
    """
    if not feasible:
        return {}
    margins = [float(frame.iloc[index][_MARGIN_COLUMN]) for index in feasible]
    energies = [
        energy_estimate(frame.iloc[index].to_dict(), baseline_energy) for index in feasible
    ]
    margin_part = _normalized(margins)
    energy_part = [1.0 - value for value in _normalized(energies)]  # 能耗越小越好（倒置）
    return {
        index: share * margin_part[position] + (1.0 - share) * energy_part[position]
        for position, index in enumerate(feasible)
    }


def _water(flat: Mapping[str, float], prefix: str) -> WaterFlow:
    """水股反解（UF-42 三键槽——app_enumeration 同构口径）。"""
    return WaterFlow(q_avg_daily=flat[f"{prefix}.q_avg_daily"], kz=flat[f"{prefix}.kz"])


def _sludge(flat: Mapping[str, float], prefix: str) -> SludgeFlow:
    """泥股反解（三键槽——同上）。"""
    return SludgeFlow(
        q_wet=flat[f"{prefix}.q_wet"],
        ds=flat[f"{prefix}.ds"],
        moisture=flat[f"{prefix}.moisture"],
    )


def baseline_context(
    source: BaselineSource, unit_id: str, condition: OperatingCondition, env: RunEnv
) -> UnitContext:
    """基线上下文重建（B1 口径：入流股一律取基线设计快照反解——规格头注记）。"""
    snapshots = source.plant.conditions[ConditionSet.key(condition)]
    inflows: dict[PortRef, WaterFlow | SludgeFlow] = {}
    inqualities: dict[PortRef, WaterQuality] = {}
    for edge in (item for item in source.edges if item.dst.unit_id == unit_id):
        snapshot = snapshots[edge.src.unit_id]
        flat, prefix = snapshot.outflows, f"{edge.src.unit_id}.{edge.src.port_id}"
        inflows[edge.dst] = (
            _water(flat, prefix)
            if f"{prefix}.q_avg_daily" in flat
            else _sludge(flat, prefix)
        )
        inqualities[edge.dst] = WaterQuality(
            {
                dotted.rsplit(".", 1)[-1]: value
                for dotted, value in snapshot.outqualities.items()
                if dotted.startswith(f"{prefix}.")
            }
        )
    params = {
        spec.field_id: spec.default for spec in source.units[unit_id].manifest.params
    }
    for key, value in source.design.nodes.get(unit_id, {}).items():
        if key != "kind":
            params[key] = float(value)
    return UnitContext(
        unit_id=unit_id,
        inflows=inflows,
        inqualities=inqualities,
        params=params,
        condition=condition,
        assumptions=env.assumptions,
        trace=_NullSink(),
    )


def grid_of(specs: Sequence[Any], assumptions: Mapping[str, float]) -> Grid:
    """阶段网格构建（guard_base=False——联合枚举预算=max_total_rows 独立护栏）。"""
    return build_grid(list(specs), overrides=assumptions, guard_base=False)


def search_conditions(
    conditions: ConditionSet, all_outer: bool
) -> tuple[OperatingCondition, ...]:
    """搜索工况族：默认 design 档；all_outer=全 ConditionSet（W5）。"""
    if all_outer:
        return tuple(conditions.iter_all())
    return (conditions.baseline[0],)


def baseline_energy_of(
    source: BaselineSource, prefix_units: Sequence[str], condition_key: str
) -> float:
    """前缀单元基线能耗和（B1 冻结口径——B4-2a e_* 三键同源）。"""
    total = 0.0
    for unit_id in prefix_units:
        dims = source.plant.conditions[condition_key][unit_id].dims
        total += sum(
            float(dims[key]) for key in _ENERGY_KEYS if key in dims
        )
    return total


def baseline_run(
    design: DesignState, assembled: AssembledView, conditions: ConditionSet,
    env: RunEnv, execute: GraphExecutor,
) -> BaselineSource:
    """基线执行（全工况一次——beam 编排消费；executor=注入的既有编排）。"""
    plant = execute(design, assembled.units, conditions, env)
    return BaselineSource(
        units=assembled.units, edges=assembled.edges, design=design, plant=plant
    )


def _feasible_of(frame: pandas.DataFrame, matrix: pandas.DataFrame | None) -> tuple[int, ...]:
    """双源可行：行非 NaN ∧ 约束通过（PD2 同源口径；无约束=NaN 单源）。"""
    passed = range(len(frame)) if matrix is None else (
        index for index in range(len(frame)) if bool(matrix.iloc[index].all())
    )
    return tuple(
        index for index in passed if not bool(frame.iloc[index][_NAN_COLUMN])
    )


def evaluate_stage(
    unit: Unit, stage: StageContext, context: UnitContext, env: RunEnv
) -> StageOutcome:
    """逐级枚举正门：enumerate_solutions 同管线+约束过滤+代理分（R2/R4）。"""
    if stage.grid is None:
        raise ValueError(
            "StageContext.grid 缺失（阶段求值前提——beam 装配面程序缺陷，GR-11）"
        )
    frame = enumerate_solutions(stage.grid, context, unit, env)
    matrix = (
        apply_constraints(frame, stage.constraints).pass_matrix
        if stage.constraints
        else None
    )
    feasible = _feasible_of(frame, matrix)
    return StageOutcome(
        unit_id=stage.unit_id,
        frame=frame,
        feasible=feasible,
        proxies=stage_proxies(frame, feasible, stage.share, stage.baseline_energy),
        pass_matrix=matrix,
    )


__all__ = [
    "AssembleFn",
    "AssembledView",
    "BaselineSource",
    "GraphExecutor",
    "InvalidJointEnumerationError",
    "StageContext",
    "StageOutcome",
    "baseline_context",
    "baseline_energy_of",
    "baseline_run",
    "energy_estimate",
    "evaluate_stage",
    "grid_of",
    "search_conditions",
    "stage_proxies",
]
