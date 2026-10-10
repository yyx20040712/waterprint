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
#   R4 #21 管线（R1 回炉 W-F 收敛）：stale 门→narrative_fills 逐段
#      validate_narrative（违例拒该段入 rejected_narratives——守卫留
#      MCP 侧语义）→server services.report.assemble_report 共享真源
#      （narrative_fills 参数化上移；diag/cost/layout 装配与 md/PDF
#      端点单源；layout 投影复制件退役）→verify 全绿（服务闸）才落盘
#      reports/{pid}-report-{digest10}.md。返回面如实（d1-W-2 注释
#      勘正——B6 R2 微收尾）：成功面键零变化（{path, verify_summary,
#      rejected_narratives}）；verify 失败面 failures 结构化键已退役
#      （R1 自裁申报④——现返 {"error","hint"} 平面，失败明细经服务闸
#      异常消息承载）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP

    from waterprint_agent.context import AgentContext

from waterprint_agent.tools.calc import atomic_write_bytes
from waterprint_agent.tools.results import _load_fresh, _SandboxResultView

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


def _export_report_impl(
    ctx: AgentContext, project_id: str, condition_key: str,
    narrative_fills: dict[str, str] | None,
) -> dict[str, Any]:
    """#21：说明书管线（W-F 收敛）——stale 门→叙述守卫→server 装配共享
    真源（narrative_fills 参数化）→verify 全绿（服务闸）→落盘 reports/。"""
    import dataclasses

    from waterprint.report.anchors import validate_narrative
    from waterprint_server.services import report as report_service
    from waterprint_server.services.cost import (
        CostSourceNotFoundError,
        InvalidCostRequestError,
    )
    from waterprint_server.services.elevation import (
        ElevationSourceNotFoundError,
        InvalidElevationRequestError,
    )
    from waterprint_server.services.scene import (
        InvalidSceneRequestError,
        SceneSourceNotFoundError,
    )

    loaded = _load_fresh(ctx, project_id)  # R1 stale 门（MCP 侧语义保持）
    if isinstance(loaded, dict):
        return loaded
    _, plant, result_path = loaded
    # 叙述守卫（MCP 侧语义——拒绝/接受流留本面，装配消费 accepted）
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
    # 装配单源（services.report.assemble_report——diag/cost/layout 与
    # md/PDF 端点同真源；view 携 diag_file 伴生键喂诊断取数面）
    view = _SandboxResultView(project_id, plant, result_path)
    service_ctx = dataclasses.replace(ctx.service_ctx, manager=view)
    try:
        assembled = report_service.assemble_report(
            service_ctx, project_id, condition_key or None,
            narrative_fills=accepted,
        )
    except (
        report_service.ReportSourceNotFoundError,
        report_service.ReportEntryNotFoundError,
    ) as exc:  # 两源门同体（结果集缺席/工况单元不在——同 HINT_EXPORT 引导）
        return {"error": str(exc), "hint": _HINT_EXPORT}
    except (
        report_service.ReportConditionUnsupportedError,
        report_service.ReportVerifyError,
    ) as exc:  # 报告面同体（非 design 工况/verify 闸——同 HINT_REPORT 引导）
        return {"error": str(exc), "hint": _HINT_REPORT}
    except (
        CostSourceNotFoundError,
        InvalidCostRequestError,
        ElevationSourceNotFoundError,
        InvalidElevationRequestError,
        SceneSourceNotFoundError,
        InvalidSceneRequestError,
    ) as exc:  # 装配子服务错误面（原 #16 布置聚合 error dict 通道的异常形）
        return {"error": str(exc), "hint": _HINT_EXPORT}
    check = assembled.check
    out = ctx.guard.resolve_in(
        Path(f"{project_id}-report-{assembled.design_hash[:_DIGEST10]}.md"),
        area="reports",
    )
    atomic_write_bytes(out, assembled.markdown.encode("utf-8"))
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
