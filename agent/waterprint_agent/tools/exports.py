"""导出组工具（权威表 #17~#21）：产物导出+设计说明书管线入口。

输入:  MCP 工具调用参数（project_id/unit_id/condition_key/sheet/比例/叙述回填）
输出:  {file_name, path}（导出）/{path, verify_summary, rejected_narratives}
       （说明书）；错误={"error","hint"} 不 raise
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-INTEG-2026-09-13）
#   路径：agent/waterprint_agent/tools/exports.py
#   职责：wp_export_calcbook/#18 audit/wp_export_dxf/wp_export_ifc
#       （flows.export_flow 单一真源+exports_support 确定性命名+八键
#       边车原子写）+wp_export_report（#21 说明书管线——estimate/
#       layout 接线收口 v2 D5① 第 5/6 章）。
#   禁区：顶层禁 import core/server/fastmcp（懒加载铁律）；工具签名
#       冻结（v2 D3 权威表）；禁直连 trace.audit（ADR-020 例外通道
#       保持挂起——audit 经 flows.export_flow("audit") 正门）。
#
# 【行为规格】
#   R1 前置门：一律最近结果集+stale 门（calc/results 共享面——不符
#      即提示重算的错误 dict，禁导出旧结果）。
#   R2 命名：services.exports_support._deterministic_name 确定性口径
#      {pid}-{kind}[-unit][-sheet][-比例]-{cond}-{digest10}+后缀；
#      audit 产物为 HTML——后缀取 CLI 同款 .audit.html（server 表
#      audit→.xlsx 对 HTML 不诚实，记档偏离）。
#   R3 边车：ExportMeta 八键 {file_name}.meta.json 原子写
#      （stale_labeled 恒 False——stale 已被 R1 拒）。
#   R4 #21 管线：narrative_fills 逐段 validate_narrative（违例拒该段
#      入 rejected_narratives）→build_report_ast（estimate=services.cost
#      投影[name_zh 单一真源]，layout=#16 压缩投影）→render_markdown
#      →verify_report 全绿才落盘 reports/{pid}-report-{digest10}.md。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP

    from waterprint_agent.context import AgentContext

from waterprint_agent.tools.calc import atomic_write_bytes
from waterprint_agent.tools.results import _layout_impl, _load_diag, _load_fresh

__all__ = [
    "register",
    "wp_export_audit",
    "wp_export_calcbook",
    "wp_export_dxf",
    "wp_export_ifc",
    "wp_export_report",
]

_DIGEST10 = 10
_HINT_EXPORT = "先 wp_run_calc 产出新鲜结果（改参后旧结果会被拒——重算后再导出）。"
_HINT_DXF = (
    "全厂总图（缺省）或 unit_id 单单元图；sheet=profile 纵断图与 unit_id 互斥；"
    " h/v_scale 为正整数比例分母字符串（如 2000）。"
)
_HINT_REPORT = (
    "narrative_fills 键=slot_id（process_selection/layout_narrative），正文禁数字"
    "（检出即拒该段）；计算章数值由程序锚定，verify 全绿才落盘。"
)


def _export_impl(  # noqa: PLR0913  # 导出选项透传面（flows.export_flow 同款豁免先例）
    ctx: AgentContext,
    project_id: str,
    kind: str,
    *,
    unit_id: str | None = None,
    condition_key: str = "",
    sheet: str | None = None,
    h_scale: str | None = None,
    v_scale: str | None = None,
) -> dict[str, Any]:
    """#17~#20 共体：flows.export_flow 单一真源+确定性命名+八键边车。"""
    from waterprint import flows
    from waterprint_server.services.exports_support import (
        ExportMeta,
        _deterministic_name,
        _sidecar_text,
    )

    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    project, plant, _path = loaded
    name = _deterministic_name(
        project_id, kind, condition_key, plant.repro.design_hash,
        unit_id=None if kind == "ifc" else unit_id,
        sheet=sheet,
        h_scale=int(h_scale) if h_scale else None,
        v_scale=int(v_scale) if v_scale else None,
    )
    if kind == "audit":  # R2：HTML 产物诚实后缀（server 后缀表记档偏离）
        name = Path(name).with_suffix(".audit.html").name
    out = ctx.guard.resolve_in(Path(name), area="exports")
    site = project.design.site
    flows.export_flow(
        kind, project, plant,
        template_dir=ctx.service_ctx.templates_dir, out=out,
        unit_id=unit_id, condition_key=condition_key or None, sheet=sheet,
        h_scale=h_scale, v_scale=v_scale,
        site_design=site,
        assumptions=(
            {entry.key: entry.default for entry in _default_assumptions()}
            | dict(project.design.assumption_overrides)
        ) if kind == "ifc" else None,
    )
    meta = ExportMeta(
        project_id=project_id, kind=kind, condition_key=condition_key,
        file_name=name, design_digest=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version, stale_labeled=False,
    )
    atomic_write_bytes(
        out.with_name(f"{name}.meta.json"), _sidecar_text(meta).encode("utf-8")
    )
    return {"file_name": name, "path": str(out)}


def _default_assumptions() -> tuple[Any, ...]:
    """DEFAULT_ASSUMPTIONS 惰性取（ifc 假设合成视图——services 同口径）。"""
    from waterprint.app import DEFAULT_ASSUMPTIONS

    return tuple(DEFAULT_ASSUMPTIONS)


def _report_layout_rows(layout: dict[str, Any]) -> dict[str, Any]:
    """#16 压缩投影 → 说明书第 5 章布置数据块行（D5③ 程序注入结论）。"""
    stations = layout["stations"]
    pumps = layout["pump_stations"]
    return {
        "高程工况": layout["condition_key"],
        "基准面注记": layout["datum_note"],
        "纵断站位数": len(stations),
        "首站水面标高（m）": stations[0]["water_level"] if stations else None,
        "末站水面标高（m）": stations[-1]["water_level"] if stations else None,
        "最大埋深（m）": max((s["bury_depth"] for s in stations), default=None),
        "提升泵站": "、".join(p["unit_id"] for p in pumps) or "全程自流",
        "场景节点数": layout["scene"]["node_count"],
    }


def _export_report_impl(
    ctx: AgentContext, project_id: str, condition_key: str,
    narrative_fills: dict[str, str] | None,
) -> dict[str, Any]:
    """#21：说明书管线（D5）——narrative 守卫→AST（estimate/layout 接线）
    →渲染→verify 全绿→落盘 reports/。"""
    import dataclasses

    from waterprint_server.services import cost as cost_service

    from waterprint_agent.report.anchors import validate_narrative
    from waterprint_agent.report.build import build_report_ast
    from waterprint_agent.report.checks import verify_report
    from waterprint_agent.report.render_md import render_markdown

    loaded = _load_fresh(ctx, project_id)
    if isinstance(loaded, dict):
        return loaded
    project, plant, result_path = loaded
    diagnostics = _load_diag(result_path)
    # 概算（services.cost 投影——name_zh 单一真源；适配器同 #16 通道）。
    from waterprint_agent.tools.results import _SandboxResultView

    view = _SandboxResultView(project_id, plant, result_path)
    cost = cost_service.build_cost_for_project(
        dataclasses.replace(ctx.service_ctx, manager=view),
        project_id, condition_key,
    )
    layout = _layout_impl(ctx, project_id, condition_key)
    if "error" in layout:  # 布置聚合错误面（#16 同源）
        return layout
    rejected: dict[str, list[dict[str, str]]] = {}
    accepted: dict[str, str] = {}
    for slot_id, text in (narrative_fills or {}).items():
        violations = validate_narrative(str(text))
        if violations:
            rejected[str(slot_id)] = [
                {"rule": v.rule, "excerpt": v.excerpt} for v in violations
            ]
        else:
            accepted[str(slot_id)] = str(text)
    ast = build_report_ast(
        project, plant, diagnostics=diagnostics,
        estimate=cost.sheet, layout=_report_layout_rows(layout),
    )
    markdown = render_markdown(ast, narrative_fills=accepted)
    check = verify_report(markdown, plant)
    if not check.ok:
        return {
            "error": "说明书数值锚定断言未全绿（禁落盘）",
            "hint": _HINT_REPORT,
            "failures": list(check.failures),
        }
    out = ctx.guard.resolve_in(
        Path(f"{project_id}-report-{plant.repro.design_hash[:_DIGEST10]}.md"),
        area="reports",
    )
    atomic_write_bytes(out, markdown.encode("utf-8"))
    return {
        "path": str(out),
        "verify_summary": {
            "ok": check.ok,
            "anchors_checked": check.anchors_checked,
            "lines_checked": check.lines_checked,
            "narrative_zones": check.narrative_zones,
        },
        "rejected_narratives": rejected,
    }


def register(mcp: FastMCP) -> None:
    """工具注册面（main.get_mcp 装配调用）。"""
    mcp.tool(wp_export_calcbook)
    mcp.tool(wp_export_audit)
    mcp.tool(wp_export_dxf)
    mcp.tool(wp_export_ifc)
    mcp.tool(wp_export_report)


async def wp_export_calcbook(project_id: str) -> dict[str, Any]:
    """导出计算书（xlsx——正式模板渲染）落沙箱 exports/。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_export_calcbook", {"project_id": project_id},
        lambda: _export_impl(ctx, project_id, "calcbook"), hint=_HINT_EXPORT,
    )


async def wp_export_audit(project_id: str) -> dict[str, Any]:
    """导出公式溯源审计报告（HTML——flows.audit_render_flow 正门）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_export_audit", {"project_id": project_id},
        lambda: _export_impl(ctx, project_id, "audit"), hint=_HINT_EXPORT,
    )


async def wp_export_dxf(  # noqa: PLR0913  # dxf 选项透传面（server 同款五选项）
    project_id: str, *, unit_id: str | None = None,
    condition_key: str = "design", sheet: str | None = None,
    h_scale: str | None = None, v_scale: str | None = None,
) -> dict[str, Any]:
    """导出 DXF 图纸（全厂总图缺省/单单元/纵断 profile——site 装配）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_export_dxf",
        {"project_id": project_id, "unit_id": unit_id,
         "condition_key": condition_key, "sheet": sheet,
         "h_scale": h_scale, "v_scale": v_scale},
        lambda: _export_impl(
            ctx, project_id, "dxf", unit_id=unit_id,
            condition_key=condition_key, sheet=sheet,
            h_scale=h_scale, v_scale=v_scale,
        ),
        hint=_HINT_DXF,
    )


async def wp_export_ifc(
    project_id: str, condition_key: str = "design"
) -> dict[str, Any]:
    """导出 IFC BIM 模型（全厂三维——假设合成+site 装配）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_export_ifc",
        {"project_id": project_id, "condition_key": condition_key},
        lambda: _export_impl(ctx, project_id, "ifc", condition_key=condition_key),
        hint=_HINT_EXPORT,
    )


async def wp_export_report(
    project_id: str, condition_key: str = "design",
    narrative_fills: dict[str, str] | None = None,
) -> dict[str, Any]:
    """生成设计说明书（Markdown）：计算章程序锚定+叙述槽守卫+verify 全绿才落盘。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_export_report",
        {"project_id": project_id, "condition_key": condition_key,
         "narrative_fills": narrative_fills},
        lambda: _export_report_impl(ctx, project_id, condition_key, narrative_fills),
        hint=_HINT_REPORT,
    )
