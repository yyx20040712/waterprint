"""可信度诊断装配域：回路统计收集 + 水量闭合/出水裕度纯投影（ADR-012）。

输入:  executor 采集（DiagSink）+ PlantResult + AssembledGraph（拓扑/端口流体）
       + 工况集（flow_case 取值口径）+ 出水标准族
输出:  DiagCollector / _mass_balance_of / _effluent_of / build_diagnostics
       （app.run_full_calc 消费——app_assembly 拆分先例同构第四例）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（P2 次批 ADR-012 D5/D6；镜像测试 tests/app/test_app_trust.py）
#
# 【公开接口】（app.py 消费；跨件私有引用沿 executor_assembly 先例）
#   class DiagCollector：DiagSink 协议实现——record_loop 收集回路统计，
#       loops 属性清单（工况序=上报序）
#   class TrustContext：诊断装配上下文（graph/conditions/standards/env
#       参数打包件——run_full_calc 一次装配）
#   _mass_balance_of(plant, graph, conditions) -> tuple[FlowClosure, ...]
#       纯投影：拓扑重建单元入流（PlantResult.outflows+edges）——
#       executor 零触碰（ADR-012 D5）
#   _effluent_of(plant, standards) -> tuple[IndicatorMargin, ...]
#       纯投影：plant.summary × 标准 × quality.margin
#   build_diagnostics(plant, ctx, collector) -> DiagnosticsReport
#
# 【行为口径】
#   R1 流量取值按工况 flow_case：DESIGN→q_design、AVG→q_avg_daily
#      （WaterFlow.q_design 派生槽恒在投影表 UF-42）；SLUDGE 恒 q_wet。
#   R2 单元入流=Σ入边 src 出端口值（recycle 边同计——终态自洽）；出流=
#      Σ该单元 manifest OUT 端口投影值（缺值端口跳过——未输出面不计入）。
#   R3 厂级闭合：源单元（无入边）Σ出流 vs 汇单元（无出边）Σ出流，按
#      流体分线；closure_rel=|Δ|/max(两边,1.0)（分母下限 1.0 同 loop
#      R1 工程惯例）；全零流体线不发线（空面合法）。
#   R4 单元偏差清单：有入边单元×流体，delta_rel=|Σ入−Σ出|/max(|Σ入|,
#      1.0)；全零（q_in=q_out=0）跳过；按 |delta_rel| 降序、unit_id/
#      fluid 升序破平——泥线减量单元残差=工艺性事实（面板注记非错误）。
#   R5 裕度：summary 指标有则录无则略（矿井线缺 BOD5 等——_summary_of
#      同口径）；standards 空 → effluent 空元组（合法）。
#   R6 loop_params=env.engine_params loop.* 终值（口径透明：面板展示
#      容差/上限/阻尼实际生效值）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 0/1（分母下限
#   1.0 同 loop.py R1 口径）。
#
# 【测试要求】手算闭合用例（线性图+分流）/工况取值口径（design vs avg）
#   /缺值端口跳过/源汇判定/裕度空标准/全零线不发。
#
# 【参照】ADR-012；app_assembly.py（拆分先例）；contracts/trust.py
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, final

from waterprint.app_assembly import AssembledGraph
from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.ports import Direction, Edge, FluidKind
from waterprint.contracts.quality import EffluentStandard, margin
from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.trust import (
    ClosureLine,
    DiagnosticsReport,
    FlowClosure,
    IndicatorMargin,
    LoopRunStats,
    UnitImbalance,
)
from waterprint.graph.executor_dsl import InvalidExecutionError

_LOOP_KEYS: Final[tuple[str, ...]] = (
    "loop.tolerance", "loop.max_iterations", "loop.damping"
)


@final
class TrustContext:
    """诊断装配上下文（run_full_calc 一次装配、投影只读——参数打包件）。"""

    __slots__ = ("conditions", "env", "graph", "standards")

    def __init__(
        self, graph: AssembledGraph, conditions: ConditionSet,
        standards: tuple[EffluentStandard, ...], env: RunEnv,
    ) -> None:
        self.graph = graph
        self.conditions = conditions
        self.standards = standards
        self.env = env


def _flow_field(fluid: FluidKind, condition: OperatingCondition) -> str:
    """流量取值字段（R1 口径：DESIGN→q_design / AVG→q_avg_daily；泥恒 q_wet）。"""
    if fluid is not FluidKind.WATER:
        return "q_wet"
    if condition.flow_case is FlowCase.DESIGN:
        return "q_design"
    if condition.flow_case is FlowCase.AVG:
        return "q_avg_daily"
    raise InvalidExecutionError(
        f"未知流量档 {condition.flow_case!r}（FlowCase 冻结二值 design/avg"
        "——ADR-007；扩档须同步本口径）"
    )


@final
class DiagCollector:
    """DiagSink 协议实现：回路统计收集（上报序=工况执行序）。"""

    def __init__(self) -> None:
        self.loops: list[LoopRunStats] = []

    def record_loop(
        self, condition_key: str, loop_nodes: tuple[str, ...],
        iterations: int, final_residual: float,
    ) -> None:
        """收集一条成功收敛回路统计（发散路径不进此面——异常面）。"""
        self.loops.append(
            LoopRunStats(
                condition_key=condition_key, loop_nodes=loop_nodes,
                iterations=iterations, final_residual=final_residual,
            )
        )


def _unit_out_total(
    values: Mapping[str, float], unit_id: str, ports_out: tuple[str, ...],
    fluid: FluidKind, condition: OperatingCondition,
) -> float:
    """单元单流体线出流合计（R2：manifest OUT 端口投影值，缺值跳过）。"""
    field = _flow_field(fluid, condition)
    total = 0.0
    for port in ports_out:
        value = values.get(f"{unit_id}.{port}.{field}")
        if value is not None:
            total += value
    return total


def _line_totals(
    values: Mapping[str, float], unit_ids: tuple[str, ...],
    out_ports: Mapping[str, tuple[str, ...]], fluid: FluidKind,
    condition: OperatingCondition,
) -> float:
    """一组单元（源或汇）单流体线出流合计（R3）。"""
    return sum(
        (
            _unit_out_total(values, unit_id, out_ports.get(unit_id, ()), fluid, condition)
            for unit_id in unit_ids
        ),
        start=0.0,
    )


def _unit_in_total(
    values: Mapping[str, float], edges_in: tuple[Edge, ...],
    fluid_of_port: Mapping[tuple[str, str], FluidKind], fluid: FluidKind,
    condition: OperatingCondition,
) -> float:
    """单元单流体线入流合计（R2：入边 src 出端口值，recycle 同计）。"""
    field = _flow_field(fluid, condition)
    total = 0.0
    for edge in edges_in:
        # 端口不在 manifest 流体表=装配缺陷面（assemble 边校验应已拒）
        #——诊断侧保守跳过不计入（fail-visible 归装配层守卫）。
        if fluid_of_port.get((edge.src.unit_id, edge.src.port_id)) is not fluid:
            continue
        value = values.get(f"{edge.src.unit_id}.{edge.src.port_id}.{field}")
        if value is not None:
            total += value
    return total


def _mass_balance_of(
    plant: PlantResult, graph: AssembledGraph, conditions: ConditionSet,
) -> tuple[FlowClosure, ...]:
    """水量闭合审计纯投影（R2/R3/R4——executor 零触碰）。"""
    condition_of: dict[str, OperatingCondition] = {
        ConditionSet.key(condition): condition for condition in conditions.iter_all()
    }
    incoming: dict[str, list[Edge]] = {}
    outgoing: set[str] = set()
    for edge in graph.edges:
        incoming.setdefault(edge.dst.unit_id, []).append(edge)
        outgoing.add(edge.src.unit_id)
    out_ports: dict[str, tuple[str, ...]] = {}
    fluid_of_port: dict[tuple[str, str], FluidKind] = {}
    for unit_id, unit in graph.units.items():
        out_ports[unit_id] = tuple(
            port.port_id for port in unit.manifest.ports
            if port.direction is Direction.OUT
        )
        for port in unit.manifest.ports:
            fluid_of_port[(unit_id, port.port_id)] = port.fluid
    closures: list[FlowClosure] = []
    for condition_key, snapshot in plant.conditions.items():
        condition = condition_of.get(condition_key)
        if condition is None:
            continue  # 键与工况集对不上=装配缺陷面，诊断侧保守跳过
        values: dict[str, float] = {
            key: item
            for unit in snapshot.values()
            for key, item in unit.outflows.items()
        }
        sources = tuple(unit_id for unit_id in snapshot if unit_id not in incoming)
        sinks = tuple(unit_id for unit_id in snapshot if unit_id not in outgoing)
        lines: list[ClosureLine] = []
        imbalances: list[UnitImbalance] = []
        for fluid in FluidKind:
            sources_total = _line_totals(
                values, sources, out_ports, fluid, condition
            )
            sinks_total = _line_totals(values, sinks, out_ports, fluid, condition)
            if sources_total == 0.0 and sinks_total == 0.0:
                continue  # R3 全零流体线不发线
            lines.append(
                ClosureLine(
                    fluid=fluid.value,
                    q_sources_total=sources_total,
                    q_sinks_total=sinks_total,
                    closure_rel=abs(sinks_total - sources_total)
                    / max(abs(sources_total), abs(sinks_total), 1.0),
                )
            )
            for unit_id, edges_in in incoming.items():
                if unit_id not in snapshot:
                    continue
                q_in = _unit_in_total(
                    values, tuple(edges_in), fluid_of_port, fluid, condition
                )
                q_out = _unit_out_total(
                    values, unit_id, out_ports.get(unit_id, ()), fluid, condition
                )
                if q_in == 0.0 and q_out == 0.0:
                    continue  # R4 全零跳过（未激活线）
                imbalances.append(
                    UnitImbalance(
                        unit_id=unit_id, fluid=fluid.value, q_in=q_in, q_out=q_out,
                        delta_rel=abs(q_in - q_out) / max(abs(q_in), 1.0),
                    )
                )
        closures.append(
            FlowClosure(
                condition_key=condition_key,
                lines=tuple(lines),
                unit_imbalances=tuple(
                    sorted(
                        imbalances,
                        key=lambda item: (-item.delta_rel, item.unit_id, item.fluid),
                    )
                ),
            )
        )
    return tuple(closures)


def _effluent_of(
    plant: PlantResult, standards: tuple[EffluentStandard, ...],
) -> tuple[IndicatorMargin, ...]:
    """出水裕度纯投影（R5：summary 指标有则录无则略；空标准→空元组）。"""
    entries: list[IndicatorMargin] = []
    for condition_key, fields in plant.summary.items():
        for standard in standards:
            for indicator in sorted(standard.limits):
                value = fields.get(indicator)
                if value is None:
                    continue
                entries.append(
                    IndicatorMargin(
                        condition_key=condition_key,
                        standard_id=standard.standard_id,
                        indicator=indicator,
                        value=value,
                        limit=standard.limits[indicator],
                        margin=margin(value, standard, indicator),
                    )
                )
    return tuple(entries)


def build_diagnostics(
    plant: PlantResult, ctx: TrustContext, collector: DiagCollector,
) -> DiagnosticsReport:
    """诊断报告组装正门（convergence 采集 + 闭合/裕度投影 + 口径记录）。"""
    return DiagnosticsReport(
        convergence=tuple(collector.loops),
        loop_params={
            key: ctx.env.engine_params[key].value for key in _LOOP_KEYS
        },
        mass_balance=_mass_balance_of(plant, ctx.graph, ctx.conditions),
        effluent=_effluent_of(plant, ctx.standards),
        repro=plant.repro,
    )
