"""结果组工具（权威表 #11~#16）：结果摘要/诊断回喂/单单元/迹切片/概算/布置。

输入:  MCP 工具调用参数（project_id/unit_id/condition_key/formula_id/limit）
输出:  投影 dict（压缩面+按需回取；错误={"error","hint"} 不 raise）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-INTEG-2026-09-13）
#   路径：agent/waterprint_agent/tools/results.py
#   职责：wp_get_result_summary（#11 压缩核心）/wp_get_diagnostics
#       （#12 三源回喂）/wp_get_unit_detail（#13 单单元全量）/
#       wp_get_trace_excerpt（#14 迹切片）/wp_get_estimate_summary
#       （#15 概算内存投影——flows.estimate_summary_flow）/
#       wp_get_layout_summary（#16 elevation/scene 聚合压缩——K8）。
#   禁区：顶层禁 import core/server/fastmcp（懒加载铁律）；工具签名
#       冻结（v2 D3 权威表）；禁 core L1-L3 直连（契约面）。
#
# 【行为规格】
#   R1 取数门：一律「最近结果集（calc.find_latest_result）+stale 门
#      （calc.fresh_gate——design_hash≠content_hash 即提示重算）」；
#      无结果=错误 dict（先 wp_run_calc）。
#   R2 #16 装配通道：server services elevation/scene 的 build_*_
#      for_project(ctx,pid) 以私有 Manager 结果视图适配器喂养（沙箱
#      results/ 最近结果集呈现为 done calc 任务——私有 Manager 无任务
#      提交是 E2/A3 装配语义，适配器不改 server 代码零提交任务）。
#   R3 压缩口径（K8）：elevation 站位五键+场景计数摘要（重则自压）；
#      #11 逐单元一行（unit_id+warnings+dims）；#14 迹节点限流。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP
    from waterprint.contracts.project_schema import ProjectFile
    from waterprint.contracts.result_schema import PlantResult
    from waterprint.contracts.trust import DiagnosticsReport

    from waterprint_agent.context import AgentContext

from waterprint_agent.tools.calc import (
    diag_path_of,
    find_latest_result,
    fresh_gate,
    read_project,
)

__all__ = [
    "register",
    "wp_get_diagnostics",
    "wp_get_estimate_summary",
    "wp_get_layout_summary",
    "wp_get_result_summary",
    "wp_get_trace_excerpt",
    "wp_get_unit_detail",
]

_DESIGN_KEY = "design"
_HINT_RESULT = "先 wp_run_calc 产出结果集，再读摘要；改参后旧结果会提示重算。"
_HINT_DIAG = "warnings 含调节方向（param_key/affected_unit_ids）；迭代调参见 wp_update_params。"
_HINT_UNIT = "unit_id 以 wp_get_result_summary 的 units 清单为准；condition_key 缺省=design。"
_HINT_TRACE = "unit_id/formula_id 任选其一或组合；limit 控制回取行数（迹全量在审计附件）。"
_HINT_EST = "condition_key 缺省=design（概算基线档）；内存投影无文件面（T4）。"
_HINT_LAYOUT = "condition_key 缺省=design；数据经高程/场景聚合压缩（说明书第 5 章数据源）。"


def _load_fresh(
    ctx: AgentContext, project_id: str
) -> tuple[ProjectFile, PlantResult, Path] | dict[str, Any]:
    """读最近结果+stale 门（R1）——错误返回 {"error","hint"} dict。"""
    from waterprint.contracts.result_schema import InvalidResultError, deserialize

    result_path = find_latest_result(ctx, project_id)
    if result_path is None:
        return {"error": f"项目 {project_id!r} 无结果集（未计算）", "hint": _HINT_RESULT}
    try:
        plant = deserialize(result_path.read_bytes())
    except (OSError, InvalidResultError) as exc:
        return {
            "error": f"最近结果集不可读（文件缺失/损坏——先重算）：{exc}",
            "hint": _HINT_RESULT,
        }
    project = read_project(ctx, project_id)
    stale = fresh_gate(project, plant)
    if stale is not None:
        return {"error": stale, "hint": "先 wp_run_calc 重算后再读结果（旧结果禁静默消费）。"}
    return project, plant, result_path


def _load_diag(result_path: Path) -> DiagnosticsReport | None:
    """诊断件读取（缺失/损坏→None 显式降级——trust 服务同口径）。"""
    from waterprint.contracts.trust import (
        InvalidDiagnosticsError,
        deserialize_diag,
    )

    path = diag_path_of(result_path)
    if not path.is_file():
        return None
    try:
        return deserialize_diag(path.read_bytes())
    except (OSError, InvalidDiagnosticsError):
        return None


def _summary_impl(ctx: AgentContext, project_id: str) -> dict[str, Any]:
    """#11：最近结果压缩核心——达标判定+逐单元一行+闭合偏差。"""
    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    _project, plant, result_path = loaded
    diagnostics = _load_diag(result_path)
    snapshot = plant.conditions[_DESIGN_KEY]
    units = [
        {
            "unit_id": unit_id,
            "warnings": len(snap.warnings),
            "dims": {key: snap.dims[key] for key in sorted(snap.dims)},
        }
        for unit_id, snap in sorted(snapshot.items())
    ]
    margins = [
        {"indicator": item.indicator, "value": item.value, "limit": item.limit,
         "margin": item.margin, "compliant": item.margin >= 0.0}
        for item in (diagnostics.effluent if diagnostics else ())
        if item.condition_key == _DESIGN_KEY
    ]
    closure = None
    if diagnostics:
        for flow in diagnostics.mass_balance:
            if flow.condition_key == _DESIGN_KEY:
                closure = [
                    {"fluid": line.fluid, "closure_rel": line.closure_rel}
                    for line in flow.lines
                ]
    return {
        "project_id": project_id,
        "design_digest": plant.repro.design_hash,
        "engine_version": plant.repro.engine_version,
        "data_version": plant.repro.data_version,
        "compliant": bool(margins) and all(item["compliant"] for item in margins),
        "effluent_design": margins,
        "units": units,
        "mass_closure": closure,
        "warnings_total": sum(
            len(snap.warnings) for view in plant.conditions.values()
            for snap in view.values()
        ),
    }


def _warning_view(warning: Any, unit_id: str, fallback_cond: str) -> dict[str, Any]:
    """Warning 六键投影（#12/#13 共用——trust.WarningEntry 同形）。"""
    return {
        "unit_id": unit_id,
        "severity": warning.severity.value,
        "source": warning.source,
        "message": warning.message,
        "param_key": warning.param_key,
        "condition_key": warning.condition_key or fallback_cond,
        "affected_unit_ids": list(warning.affected_unit_ids),
    }


def _diagnostics_impl(ctx: AgentContext, project_id: str) -> dict[str, Any]:
    """#12：三源回喂——warnings 六键清单+convergence/mass_balance/effluent。"""
    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    _project, plant, result_path = loaded
    diagnostics = _load_diag(result_path)
    warnings = [
        _warning_view(warning, unit_id, condition_key)
        for condition_key in sorted(plant.conditions)
        for unit_id in sorted(plant.conditions[condition_key])
        for warning in plant.conditions[condition_key][unit_id].warnings
    ]
    counts: dict[str, int] = {}  # 按级计数（仅在场级——trust R3 同口径）
    for entry in warnings:
        counts[entry["severity"]] = counts.get(entry["severity"], 0) + 1
    return {
        "project_id": project_id,
        "design_digest": plant.repro.design_hash,
        "diagnostics_available": diagnostics is not None,
        "loop_params": dict(diagnostics.loop_params) if diagnostics else {},
        "convergence": [
            {"condition_key": it.condition_key, "loop_nodes": list(it.loop_nodes),
             "iterations": it.iterations, "final_residual": it.final_residual}
            for it in diagnostics.convergence
        ] if diagnostics else [],
        "mass_balance": [
            {"condition_key": flow.condition_key,
             "lines": [{"fluid": ln.fluid, "q_sources_total": ln.q_sources_total,
                        "q_sinks_total": ln.q_sinks_total, "closure_rel": ln.closure_rel}
                       for ln in flow.lines],
             "unit_imbalances": [{"unit_id": u.unit_id, "fluid": u.fluid,
                                  "q_in": u.q_in, "q_out": u.q_out,
                                  "delta_rel": u.delta_rel}
                                 for u in flow.unit_imbalances]}
            for flow in diagnostics.mass_balance
        ] if diagnostics else [],
        "effluent": [
            {"condition_key": it.condition_key, "standard_id": it.standard_id,
             "indicator": it.indicator, "value": it.value,
             "limit": it.limit, "margin": it.margin}
            for it in diagnostics.effluent
        ] if diagnostics else [],
        "warnings": warnings,
        "warning_counts": counts,
    }


def _unit_detail_impl(
    ctx: AgentContext, project_id: str, unit_id: str, condition_key: str | None
) -> dict[str, Any]:
    """#13：单单元全量切片（工况缺省=design）。"""
    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    _project, plant, _path = loaded
    chosen = condition_key if condition_key is not None else _DESIGN_KEY
    view = plant.conditions.get(chosen)
    if view is None:
        return {
            "error": f"工况 {chosen!r} 不在结果集（合法 {sorted(plant.conditions)}）",
            "hint": _HINT_UNIT,
        }
    snap = view.get(unit_id)
    if snap is None:
        return {
            "error": f"单元 {unit_id!r} 不在工况 {chosen!r} 结果快照",
            "hint": _HINT_UNIT,
        }
    return {
        "project_id": project_id,
        "unit_id": unit_id,
        "condition_key": chosen,
        "outflows": dict(snap.outflows),
        "outqualities": dict(snap.outqualities),
        "dims": dict(snap.dims),
        "warnings": [
            _warning_view(w, unit_id, chosen) for w in snap.warnings
        ],
        "formula_ids": list(snap.formula_ids),
    }


def _trace_impl(
    ctx: AgentContext, project_id: str, unit_id: str | None,
    formula_id: str | None, limit: int,
) -> dict[str, Any]:
    """#14：迹切片（单元/公式过滤+limit 截断——全量在审计附件）。"""
    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    _project, plant, _path = loaded
    matched = [  # 单元/公式双过滤（None=通配）
        node for node in plant.trace
        if (unit_id is None or node.unit_id == unit_id)
        and (formula_id is None or node.formula_id == formula_id)]
    window = matched[: max(limit, 0)]
    return {
        "project_id": project_id,
        "total_matched": len(matched),
        "returned": len(window),
        "nodes": [
            {"formula_id": node.formula_id, "unit_id": node.unit_id,
             "condition_key": node.condition_key, "output": node.output,
             "norm_ref": node.norm_ref, "inputs": dict(node.inputs)}
            for node in window
        ],
    }


def _estimate_impl(
    ctx: AgentContext, project_id: str, condition_key: str
) -> dict[str, Any]:
    """#15：概算摘要（flows.estimate_summary_flow——内存投影 T4 无文件面）。"""
    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    from waterprint import flows

    _project, plant, _path = loaded
    outcome = flows.estimate_summary_flow(
        plant, condition_key=condition_key,
        data_dir=ctx.service_ctx.settings.data_dir,
    )
    sheet = outcome.sheet
    return {
        "project_id": project_id,
        "condition_key": condition_key,
        "grand_total": sheet.grand_total,
        "levels": {
            "detail_subtotal": sheet.detail_subtotal,
            "equipment_subtotal": sheet.equipment_subtotal,
            "construction_subtotal": sheet.construction_subtotal,
            "subtotal": sheet.subtotal,
            "reserve_subtotal": sheet.reserve_subtotal,
            "grand_total": sheet.grand_total,
        },
        "detail_row_count": len(sheet.detail_rows),
        "top_rows": [
            {"price_key": row.price_key, "unit": row.unit,
             "quantity": row.quantity, "unit_price": row.unit_price,
             "amount": row.amount}
            for row in sheet.detail_rows[:10]
        ],
        "indicators": [
            {"indicator_key": reading.indicator_key, "value": reading.value,
             "band": list(reading.band), "status": reading.status,
             "reason": reading.reason}
            for reading in outcome.report.readings
        ],
        "checked": outcome.report.checked,
    }


class _SandboxResultView:  # Manager 鸭子面（仅查询两法——R2 适配器）
    """#16 Manager 结果视图适配器：沙箱最近结果集呈现为 done calc 任务。

    server services elevation/scene 取数面=task_ids_for_project→status
    （两查询方法）——私有 Manager 无任务提交（E2/A3），本适配器以只读
    视图喂养；不写注册表、不提交任务、不改 server 代码。"""

    def __init__(self, project_id: str, plant: PlantResult, result_file: Path) -> None:
        from waterprint_server.services.calculation import TaskStatus

        self._project_id = project_id
        self._task_id = f"agentview-{plant.repro.design_hash[:10]}"
        self._status = TaskStatus(
            task_id=self._task_id,
            kind="calc",
            state="done",
            progress=1.0,
            stage="serialize",
            condition_key=None,
            stale=False,
            error=None,
            error_type=None,
            result={
                "result_file": str(result_file),
                "design_hash": plant.repro.design_hash,
                "engine_version": plant.repro.engine_version,
                "data_version": plant.repro.data_version,
            },
            project_id=project_id,
        )

    def task_ids_for_project(self, project_id: str) -> tuple[str, ...]:
        """项目的全部任务 id（视图内恒至多一条——注册序）。"""
        return (self._task_id,) if project_id == self._project_id else ()

    def status(self, task_id: str) -> Any:
        """状态快照（视图内唯一任务；未知名=KeyError 契约面由消费方先过滤）。"""
        if task_id != self._task_id:
            raise KeyError(task_id)
        return self._status


def _layout_impl(
    ctx: AgentContext, project_id: str, condition_key: str | None
) -> dict[str, Any]:
    """#16：elevation/scene 服务聚合→压缩摘要（K8 重则自压）。"""
    import dataclasses

    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    _project, plant, result_path = loaded
    from waterprint_server.services import elevation as elevation_service
    from waterprint_server.services import scene as scene_service

    view = _SandboxResultView(project_id, plant, result_path)
    service_ctx = dataclasses.replace(ctx.service_ctx, manager=view)
    elevation = elevation_service.build_elevation_for_project(
        service_ctx, project_id, condition_key
    )
    scene = scene_service.build_scene_for_project(
        service_ctx, project_id, condition_key
    )
    stations = [
        {"unit_id": s.unit_id, "water_level": s.water_level, "crest_elev": s.crest_elev,
         "bury_depth": s.bury_depth, "design_flow": s.design_flow}
        for s in elevation.stations
    ]
    return {
        "project_id": project_id,
        "condition_key": elevation.condition_key,
        "conditions": list(elevation.conditions),
        "datum_note": elevation.datum_note,
        "stations": stations,
        "pump_stations": [
            {"unit_id": pm.unit_id, "static_head": pm.static_head, "total_head": pm.total_head,
             "design_flow": pm.design_flow, "condition_key": pm.condition_key}
            for pm in elevation.pump_stations
        ],
        "drop_warning_count": len(elevation.drop_warnings),
        "warning_count": len(elevation.warnings),
        "scene": {
            "scene_version": scene.scene_version,
            "condition_key": scene.condition_key,
            "node_count": len(scene.nodes),
            "root": list(scene.root),
        },
    }


def register(mcp: FastMCP) -> None:
    """工具注册面（main.get_mcp 装配调用）。"""
    mcp.tool(wp_get_result_summary)
    mcp.tool(wp_get_diagnostics)
    mcp.tool(wp_get_unit_detail)
    mcp.tool(wp_get_trace_excerpt)
    mcp.tool(wp_get_estimate_summary)
    mcp.tool(wp_get_layout_summary)


async def wp_get_result_summary(project_id: str) -> dict[str, Any]:
    """结果压缩核心：达标判定+逐单元一行+质量闭合（≤1.5k token 口径）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_get_result_summary", {"project_id": project_id},
        lambda: _summary_impl(ctx, project_id), hint=_HINT_RESULT,
    )


async def wp_get_diagnostics(project_id: str) -> dict[str, Any]:
    """诊断回喂：warnings 六键清单（含调节方向）+convergence/mass_balance/effluent。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_get_diagnostics", {"project_id": project_id},
        lambda: _diagnostics_impl(ctx, project_id), hint=_HINT_DIAG,
    )


async def wp_get_unit_detail(
    project_id: str, unit_id: str, condition_key: str | None = None
) -> dict[str, Any]:
    """单单元全量结果切片（端口流量/水质/尺寸/警告/公式集）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_get_unit_detail",
        {"project_id": project_id, "unit_id": unit_id, "condition_key": condition_key},
        lambda: _unit_detail_impl(ctx, project_id, unit_id, condition_key),
        hint=_HINT_UNIT,
    )


async def wp_get_trace_excerpt(
    project_id: str, unit_id: str | None = None, formula_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """计算迹切片（按单元/公式 ID 抽取，limit 截断）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_get_trace_excerpt",
        {"project_id": project_id, "unit_id": unit_id, "formula_id": formula_id,
         "limit": limit},
        lambda: _trace_impl(ctx, project_id, unit_id, formula_id, limit),
        hint=_HINT_TRACE,
    )


async def wp_get_estimate_summary(
    project_id: str, condition_key: str = "design"
) -> dict[str, Any]:
    """工程概算摘要：grand_total+分级小计+指标校核（内存投影）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_get_estimate_summary",
        {"project_id": project_id, "condition_key": condition_key},
        lambda: _estimate_impl(ctx, project_id, condition_key), hint=_HINT_EST,
    )


async def wp_get_layout_summary(
    project_id: str, condition_key: str | None = None
) -> dict[str, Any]:
    """高程/场景聚合摘要（纵断站位+提升泵站+场景节点——说明书第 5 章数据源）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_get_layout_summary",
        {"project_id": project_id, "condition_key": condition_key},
        lambda: _layout_impl(ctx, project_id, condition_key), hint=_HINT_LAYOUT,
    )
