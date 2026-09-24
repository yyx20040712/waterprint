"""观测组工具（权威表 #23）：跨结果/跨项目操作概览（agent 自有件聚合）。

输入:  沙箱 results/ 区扫描（limit 上限）
输出:  最近结果清单+stale 计数+诊断摘要聚合 dict
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 3 2026-09-24）
#   路径：agent/waterprint_agent/tools/overview.py
#   职责：wp_get_ops_overview（#23）——agent 沙箱自有 results/*.result.json
#       聚合视图（最近 N 件+counts{total,stale}+诊断摘要）；results.py
#       500/500 顶墙故立独立模块（chat/ 同款新模块先例）。
#   禁区：禁 import server 侧 build_ops_chain（agent 沙箱任务表恒空——
#       勘察事实 #5，本工具只聚合 agent 自有件）；禁逐操作事件流语义
#       （粒度=逐结果文件——server ops-chain 互补非替代）。
#
# 【行为规格】
#   R1 清单：results/*.result.json 按 mtime 降序取 limit（缺省 20——
#      knowledge 检索上限同锚）；逐件投影 {project_id, file, mtime, stale}。
#   R2 聚合计数：total=全量件数；stale=结果 snapshot design 与当前项目
#      文件 digest 失配件数（calc 工具 stale 门同源判定——结果文件内
#      design_digest 与 projects/{pid}.wp.json metadata.content_hash 比对）。
#   R3 诊断摘要：每件配对 .diag.json 的 warning 计数（缺失=None 不编造）。
#   R4 职责边界（防重复资产）：wp_get_result_summary=单项目单次压缩摘要；
#      wp_get_diagnostics=单项目诊断细节；本工具=跨项目聚合概览——
#      docstring 与提示文案明示三面互斥。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP

    from waterprint_agent.context import AgentContext

__all__ = ["register", "wp_get_ops_overview"]

_DEFAULT_LIMIT = 20  # knowledge 检索上限同锚（既有先例值）

_HINT_OVERVIEW = (
    "跨项目概览（最近结果+stale 计数+诊断摘要）；单项目细节用"
    " wp_get_result_summary/wp_get_diagnostics；limit 缺省 20。"
)


def _stale_of(ctx: AgentContext, result_path: Any, result_digest: str) -> bool:
    """R2：结果 digest 与当前项目文件 content_hash 失配判定（stale 门同源）。"""
    from pathlib import Path

    project_id = result_path.name.split("-")[0]
    project_file = ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    if not project_file.is_file():
        return True  # 项目已删=孤儿结果（stale 语义面）
    try:
        current = json.loads(project_file.read_text(encoding="utf-8"))["metadata"]["content_hash"]
    except (ValueError, KeyError, OSError):
        return True  # 不可读=保守判失配（宁误报不漏报）
    return current != result_digest


def _overview_impl(ctx: AgentContext, limit: int = _DEFAULT_LIMIT) -> dict[str, Any]:
    """#23：results 区聚合（mtime 降序 limit 件+counts+诊断摘要）。"""
    from waterprint_agent.tools.calc import diag_path_of, results_dir

    files = sorted(
        results_dir(ctx).glob("*.result.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    items: list[dict[str, Any]] = []
    stale_count = 0
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            digest = str(
                payload.get("design_digest") or payload.get("repro", {}).get("design_hash", "")
            )
        except (ValueError, OSError):
            continue  # 损坏件跳过不计清单（诚实面：不编造）
        stale = _stale_of(ctx, path, digest)
        stale_count += 1 if stale else 0
        diag = diag_path_of(path)
        warnings_total = None
        if diag.is_file():
            try:
                diag_payload = json.loads(diag.read_text(encoding="utf-8"))
                warnings_total = len(diag_payload.get("warnings", []))
            except (ValueError, OSError):
                warnings_total = None
        items.append(
            {
                "project_id": path.name.split("-")[0],
                "file": path.name,
                "mtime": path.stat().st_mtime,
                "stale": stale,
                "warnings_total": warnings_total,
            }
        )
    bounded = max(limit, 1)
    return {
        "count": min(len(items), bounded),
        "total_results": len(items),
        "stale_results": stale_count,
        "results": items[:bounded],
        "scope": "agent-sandbox（跨项目概览；单项目细节走 summary/diagnostics）",
    }


def register(mcp: FastMCP) -> None:
    """工具注册面（main.get_mcp 装配调用）。"""
    mcp.tool(wp_get_ops_overview)


async def wp_get_ops_overview(limit: int = _DEFAULT_LIMIT) -> dict[str, Any]:
    """跨项目操作概览（最近结果清单+stale 计数+诊断摘要——观测面聚合）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx,
        "wp_get_ops_overview",
        {"limit": limit},
        lambda: _overview_impl(ctx, limit),
        hint=_HINT_OVERVIEW,
    )
