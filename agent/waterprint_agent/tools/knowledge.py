"""知识组工具（权威表 #1~#3）：单元目录/单单元清单/知识检索。

输入:  MCP 工具调用参数（category/unit_id/query/source）
输出:  投影 dict（JSON schema 友好；错误={"error","hint"} 不 raise）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13）
#   路径：agent/waterprint_agent/tools/knowledge.py
#   职责：wp_list_units（#1 目录投影）/wp_get_unit_manifest（#2 manifest
#       裁剪投影）/wp_query_knowledge（#3 constraint_kb+coefficients 检索）。
#   禁区：顶层禁 import core/server/fastmcp（懒加载铁律——重依赖一律
#       函数体内）；工具签名冻结（技能文档按此写，勿改形）。
#
# 【行为规格】
#   R1 数据真源：#1/#2 经 server services.units（manifest 逐字投影）+
#       waterprint.app.discover_units（norm_refs/constraint_refs 取数）；
#       #3 经 services.constraints（kb 八键条目）与 app.load_coefficients
#       （值/单位/来源四字段）——agent 面零数值字面量。
#   R2 投影口径：#1 行={unit_id,name_zh,line} 恰 36 基线（32 包+4 内置）；
#       #2 参数六键+端口+规范/约束引用（去 i18n_key/removal_refs/
#       condition_mappings 内部键）；#3 命中 limit 20+截断标记。
#   R3 错误兜底：未知 category/unit_id/source → {"error","hint"} dict
#       （经 context.run_tool 统一记会话日志）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP

    from waterprint_agent.context import AgentContext

__all__ = ["register", "wp_get_unit_manifest", "wp_list_units", "wp_query_knowledge"]

_KNOWLEDGE_LIMIT: int = 2 * 10  # 20（命中上限——token 友好口径，§3 预裁决）
_HINT_LIST = (
    "用 wp_list_units 无参调用查看全量 36 单元目录；category 取业务线"
    "（municipal/mine_water/sludge/conveyance）。"
)
_HINT_MANIFEST = (
    "unit_id 以 wp_list_units 返回的目录为准；内置 kind（municipal_input/junction/"
    "quality_edit/recycle_junction）亦可查。"
)
_HINT_QUERY = (
    "source 取 constraints（约束知识库）或 coefficients（经验系数库）；"
    "query 建议用单元名/参数名/指标名片段。"
)


def register(mcp: FastMCP) -> None:
    """工具注册面（main.get_mcp 装配调用）。"""
    mcp.tool(wp_list_units)
    mcp.tool(wp_get_unit_manifest)
    mcp.tool(wp_query_knowledge)


def _list_units_impl(category: str | None) -> dict[str, Any]:
    """#1：services.units.list_units 投影（36 基线/业务线过滤）。"""
    from waterprint_server.services import units as units_service

    catalog = units_service.list_units()
    lines = sorted({entry.business_line for entry in catalog.units})
    if category is not None and category not in lines:
        return {"error": f"未知业务线 category：{category!r}", "hint": f"有效值：{lines}"}
    units = [
        {"unit_id": entry.unit_id, "name_zh": entry.name_zh, "line": entry.business_line}
        for entry in catalog.units
        if category is None or entry.business_line == category
    ]
    return {"count": len(units), "units": units, "lines": lines}


def _get_unit_manifest_impl(unit_id: str) -> dict[str, Any]:
    """#2：discover_units manifest 裁剪投影（内部键去除；内置 kind 兼并）。"""
    from waterprint.app import discover_units
    from waterprint_server.services import units as units_service

    catalog = units_service.list_units()
    by_id = {entry.unit_id: entry for entry in catalog.units}
    discovered = discover_units()
    manifest = discovered.get(unit_id)
    if manifest is not None:  # 包单元（32 注册表键）
        spec = manifest[0]
        return {
            "unit_id": unit_id,
            "name_zh": by_id[unit_id].name_zh,
            "business_line": spec.business_line,
            "kind": "unit",
            "version": spec.version,
            "params": [
                {
                    "field_id": param.field_id,
                    "dim": str(param.dim),
                    "default": param.default,
                    "range": None
                    if param.range is None
                    else {"min": param.range[0], "max": param.range[1]},
                    "grid": None if param.grid is None else list(param.grid),
                    "label_zh": param.label_zh,
                }
                for param in spec.params
            ],
            "ports": [
                {
                    "port_id": port.port_id,
                    "fluid": str(port.fluid.value),
                    "direction": str(port.direction.value),
                    "recycle": port.recycle,
                }
                for port in spec.ports
            ],
            "norm_refs": list(spec.norm_refs),
            "constraint_refs": list(spec.constraint_refs),
        }
    builtin = by_id.get(unit_id)  # 内置 kind 4（builtin 投影——services D7 声明面）
    if builtin is not None and builtin.kind == "builtin":
        return {
            "unit_id": unit_id,
            "name_zh": builtin.name_zh,
            "business_line": builtin.business_line,
            "kind": "builtin",
            "params": [param.model_dump(mode="json") for param in builtin.params],
            "ports": [port.model_dump(mode="json") for port in builtin.ports],
            "norm_refs": [],
            "constraint_refs": [],
        }
    return {"error": f"未知单元 unit_id：{unit_id!r}", "hint": _HINT_MANIFEST}


def _query_knowledge_impl(
    ctx: AgentContext, query: str, source: str
) -> dict[str, Any]:
    """#3：constraint_kb（键/标签/表达式检索）或 coefficients（键检索）。"""
    if source == "constraints":
        from waterprint_server.services import constraints as constraints_service

        catalog = constraints_service.list_constraints(ctx.settings.data_dir)
        needle = query.casefold()
        hits = [
            entry
            for entry in catalog.entries
            if needle in entry.key.casefold()
            or needle in entry.label.casefold()
            or needle in entry.expression.casefold()
        ]
        return {
            "source": "constraints",
            "query": query,
            "total_hits": len(hits),
            "limit": _KNOWLEDGE_LIMIT,
            "truncated": len(hits) > _KNOWLEDGE_LIMIT,
            "hits": [entry.model_dump(mode="json") for entry in hits[:_KNOWLEDGE_LIMIT]],
        }
    if source == "coefficients":
        from waterprint.app import load_coefficients

        coefficients = load_coefficients(ctx.settings.data_dir / "coefficients")
        needle = query.casefold()
        keys = [key for key in coefficients.keys() if needle in key.casefold()]  # noqa: SIM118  # keys=自定义前缀列举法（非 dict.keys——Coefficients 无 __iter__）
        hits = [
            {
                "key": key,
                "value": coefficients.get(key).value,
                "unit": coefficients.get(key).unit,
                "source": coefficients.get(key).source,
                "note": coefficients.get(key).note,
            }
            for key in keys[:_KNOWLEDGE_LIMIT]
        ]
        return {
            "source": "coefficients",
            "query": query,
            "data_version": coefficients.data_version,
            "total_hits": len(keys),
            "limit": _KNOWLEDGE_LIMIT,
            "truncated": len(keys) > _KNOWLEDGE_LIMIT,
            "hits": hits,
        }
    return {"error": f"未知 source：{source!r}", "hint": _HINT_QUERY}


async def wp_list_units(category: str | None = None) -> dict[str, Any]:
    """单元目录（36 基线，可按业务线 category 过滤；行={unit_id,name_zh,line}）。"""
    from waterprint_agent import context as agent_context

    return agent_context.run_tool(
        agent_context.get_context(), "wp_list_units", {"category": category},
        lambda: _list_units_impl(category), hint=_HINT_LIST,
    )


async def wp_get_unit_manifest(unit_id: str) -> dict[str, Any]:
    """单单元参数清单（参数键/单位/grid 档位/规范与约束引用——内部键已裁剪）。"""
    from waterprint_agent import context as agent_context

    return agent_context.run_tool(
        agent_context.get_context(), "wp_get_unit_manifest", {"unit_id": unit_id},
        lambda: _get_unit_manifest_impl(unit_id), hint=_HINT_MANIFEST,
    )


async def wp_query_knowledge(
    query: str, source: Literal["constraints", "coefficients"] = "constraints"
) -> dict[str, Any]:
    """知识检索（constraints=约束知识库键/内容检索；coefficients=经验系数键检索）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_query_knowledge", {"query": query, "source": source},
        lambda: _query_knowledge_impl(ctx, query, source), hint=_HINT_QUERY,
    )
