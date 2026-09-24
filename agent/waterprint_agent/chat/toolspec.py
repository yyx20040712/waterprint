"""工具清单（LLM function-calling schema 表——21 工具与 MCP 面同源）。

输入:  AgentContext+工具调用（name+arguments dict）
输出:  OpenAI tools schema 列表+dispatch（经 context.run_tool 记账+错误兜底）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/toolspec.py
#   职责：编排环工具面唯一清单——23 工具（MCP 面同源）的 JSON schema
#       声明+懒加载分发（impl 直调——ADR-019 工具面唯一，审 B1 处置）。
#   禁区：禁顶层 import tools 各模块（懒加载铁律——dispatch 时经
#       importlib 触达）；禁在本层新增计算逻辑（只编排）；禁改各 impl
#       签名（工具面=MCP 既有 21 件原样复用，导出组经 extra 固定 kwargs
#       适配通用 _export_impl 的 kind 面）。
#
# 【行为规格】
#   R1 清单：_SPEC 表=(名称,模块,impl 名,参数键序,固定 kwargs,一句话
#      描述)——与 MCP 七组 23 工具一一对应（新增工具=表加行+schema 段）。
#   R2 分发：dispatch(ctx,name,arguments)→kwargs=参数键序取值（缺省
#      None 透传）∪固定 kwargs；经 run_tool 包装（会话日志 span+异常/
#      error 键兜底）；未知工具=错误 dict 不 raise。
#   R3 schema：tools_schema()=[{type:function,function:{name,
#      description,parameters}}]——parameters 从 _PARAMS 取（无参工具
#      =空 properties）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面
    from waterprint_agent.context import AgentContext

__all__ = ["TOOL_NAMES", "dispatch", "tools_schema"]

# (工具名, tools 模块, impl 名, 参数键序, 固定 kwargs, 一句话描述)
_SPEC: tuple[tuple[str, str, str, tuple[str, ...], dict[str, Any], str], ...] = (
    (
        "wp_list_units",
        "knowledge",
        "_list_units_impl",
        ("category",),
        {},
        "列出工艺单元目录（可按业务线过滤）",
    ),
    (
        "wp_get_unit_manifest",
        "knowledge",
        "_get_unit_manifest_impl",
        ("unit_id",),
        {},
        "读单元参数清单（参数键/单位/规范引用）",
    ),
    (
        "wp_query_knowledge",
        "knowledge",
        "_query_knowledge_impl",
        ("query", "source"),
        {},
        "检索知识库（约束/系数）",
    ),
    (
        "wp_create_project",
        "projects",
        "_create_impl",
        ("name", "seed"),
        {},
        "建项目（blank 或 golden 四种子模板）",
    ),
    (
        "wp_get_project_outline",
        "projects",
        "_outline_impl",
        ("project_id",),
        {},
        "读项目摘要（节点/边/进水/工况）",
    ),
    (
        "wp_validate_design",
        "projects",
        "_validate_impl",
        ("project_id",),
        {},
        "设计结构校验（零计算三查）",
    ),
    (
        "wp_update_params",
        "projects",
        "_update_params_impl",
        ("project_id", "patches"),
        {},
        "批量改参（清单式部分接受）",
    ),
    (
        "wp_run_calc",
        "calc",
        "_run_calc_impl",
        ("project_id", "conditions"),
        {},
        "全厂计算并落盘结果",
    ),
    (
        "wp_run_enumeration",
        "calc",
        "_run_enumeration_impl",
        ("project_id", "unit_id", "top_n"),
        {},
        "单单元枚举（可行方案空间）",
    ),
    (
        "wp_run_design_map",
        "calc",
        "_run_design_map_impl",
        ("project_id", "unit_id"),
        {},
        "单单元可行域图",
    ),
    (
        "wp_get_result_summary",
        "results",
        "_summary_impl",
        ("project_id",),
        {},
        "读结果压缩摘要（达标判定+六指标）",
    ),
    (
        "wp_get_diagnostics",
        "results",
        "_diagnostics_impl",
        ("project_id",),
        {},
        "读诊断回喂（警告清单+质量闭合）",
    ),
    (
        "wp_get_unit_detail",
        "results",
        "_unit_detail_impl",
        ("project_id", "unit_id", "condition_key"),
        {},
        "读单单元全量结果切片",
    ),
    (
        "wp_get_trace_excerpt",
        "results",
        "_trace_impl",
        ("project_id", "unit_id", "formula_id", "limit"),
        {},
        "读计算迹切片",
    ),
    (
        "wp_get_estimate_summary",
        "results",
        "_estimate_impl",
        ("project_id", "condition_key"),
        {},
        "读工程概算摘要",
    ),
    (
        "wp_get_layout_summary",
        "results",
        "_layout_impl",
        ("project_id", "condition_key"),
        {},
        "读高程/场景聚合摘要",
    ),
    (
        "wp_export_calcbook",
        "exports",
        "_export_impl",
        ("project_id",),
        {"kind": "calcbook"},
        "导出计算书（xlsx）",
    ),
    (
        "wp_export_audit",
        "exports",
        "_export_impl",
        ("project_id",),
        {"kind": "audit"},
        "导出公式溯源审计报告（HTML）",
    ),
    (
        "wp_export_dxf",
        "exports",
        "_export_impl",
        ("project_id", "unit_id", "condition_key", "sheet", "h_scale", "v_scale"),
        {"kind": "dxf"},
        "导出 DXF 图纸（全厂/单单元/纵断）",
    ),
    (
        "wp_export_ifc",
        "exports",
        "_export_impl",
        ("project_id", "condition_key"),
        {"kind": "ifc"},
        "导出 IFC 三维模型",
    ),
    (
        "wp_export_report",
        "exports",
        "_export_report_impl",
        ("project_id", "condition_key", "narrative_fills"),
        {},
        "生成设计说明书（Markdown，verify 全绿才落盘）",
    ),
    (
        "wp_run_joint_enumeration",
        "solution",
        "_run_joint_enumeration_impl",
        ("project_id", "unit_ids", "top_n"),
        {},
        "全厂联合枚举（跨单元寻优 top-N——护栏拒绝返回 rejected+reason）",
    ),
    (
        "wp_get_ops_overview",
        "overview",
        "_overview_impl",
        ("limit",),
        {},
        "跨项目操作概览（最近结果+stale 计数+诊断摘要）",
    ),
)

_TOOL_HINT = "参数以工具 schema 为准；错误返回含 error+hint 两键，按 hint 调整后重试。"

# 参数 schema 面（键→类型+简述；无参工具不在表=空 properties）
_PARAMS: dict[str, dict[str, Any]] = {
    "category": {"type": "string", "description": "业务线过滤（可空=全量）"},
    "unit_id": {"type": "string", "description": "单元 ID（wp_list_units 查）"},
    "query": {"type": "string", "description": "检索词"},
    "source": {"type": "string", "description": "知识源（constraints/coefficients/assumptions）"},
    "name": {"type": "string", "description": "项目显示名"},
    "seed": {
        "type": "string",
        "description": (
            "种子（blank/municipal_34760/municipal_loop_34760/municipal_recycle_34760/mine_43836）"
        ),
    },
    "project_id": {"type": "string", "description": "项目 ID"},
    "patches": {
        "type": "array",
        "description": "改参清单 [{unit_id,key,value}]",
        "items": {"type": "object"},
    },
    "conditions": {"type": ["string", "null"], "description": "工况键列表（空=勾选集）"},
    "top_n": {"type": "integer", "description": "摘要行数上限"},
    "formula_id": {"type": "string", "description": "公式 ID 过滤"},
    "limit": {"type": "integer", "description": "截断上限"},
    "condition_key": {"type": "string", "description": "工况键（design/avg 等）"},
    "narrative_fills": {
        "type": ["object", "null"],
        "description": "叙述槽填文（process_selection/layout_narrative）",
    },
    "sheet": {"type": ["string", "null"], "description": "DXF 图纸形态（profile=纵断）"},
    "h_scale": {"type": ["string", "null"], "description": "DXF 横向比例"},
    "v_scale": {"type": ["string", "null"], "description": "DXF 纵向比例"},
}

_BY_NAME: dict[str, tuple[str, str, tuple[str, ...], dict[str, Any], str]] = {
    row[0]: (row[1], row[2], row[3], row[4], row[5]) for row in _SPEC
}
TOOL_NAMES: tuple[str, ...] = tuple(_BY_NAME)


def tools_schema() -> list[dict[str, Any]]:
    """OpenAI tools schema 全集（R3）。"""
    schema: list[dict[str, Any]] = []
    for name, _module, _impl, keys, _extra, description in _SPEC:
        properties = {key: _PARAMS[key] for key in keys if key in _PARAMS}
        schema.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {"type": "object", "properties": properties},
                },
            }
        )
    return schema


def dispatch(ctx: AgentContext, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """分发到 impl（R2——run_tool 包装+懒加载+未知工具错误 dict）。

    impl 签名异形族自适应：首参名为 ctx 者收装配束（tools 大多数），
    否则纯参数面（knowledge 组 #1~#2 无沙箱依赖）——签名探测免逐表
    维护 takes_ctx 旗标。"""
    import inspect

    from waterprint_agent import context as agent_context

    spec = _BY_NAME.get(name)
    if spec is None:
        return {"error": f"未知工具：{name!r}", "hint": f"有效工具：{', '.join(TOOL_NAMES)}"}
    module_name, impl_name, keys, extra, _description = spec
    module = importlib.import_module(f"waterprint_agent.tools.{module_name}")
    impl = getattr(module, impl_name)
    kwargs: dict[str, Any] = {key: arguments.get(key) for key in keys}
    kwargs.update(extra)
    takes_ctx = next(iter(inspect.signature(impl).parameters), "") == "ctx"
    call = (lambda: impl(ctx, **kwargs)) if takes_ctx else (lambda: impl(**kwargs))
    return agent_context.run_tool(ctx, name, dict(arguments), call, hint=_TOOL_HINT)
