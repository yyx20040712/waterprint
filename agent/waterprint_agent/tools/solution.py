"""方案组工具（权威表 #22）：全厂联合枚举（进程内同步——core 正门复用）。

输入:  MCP 工具调用参数（project_id/unit_ids/top_n）
输出:  top-N 组合投影 dict（错误={"error","hint"} 不 raise——护栏拒绝=可解释回显）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 3 2026-09-24）
#   路径：agent/waterprint_agent/tools/solution.py
#   职责：wp_run_joint_enumeration（#22）——联合枚举进程内同步执行
#       （core app 正门 run_joint_enumerate 与 server worker 同一装配
#       口径：build_condition_set+load_effluent_standards+RunEnv）；
#       护栏（JointEnumerationTooLarge/InvalidJointEnumerationError）
#       捕获转 rejected dict（422 语义在 core 层复用——审 B3 处置）。
#   禁区：禁新计算逻辑（一切数值经 core 正门——ADR-019）；禁 L1-L3
#       直连（白名单=waterprint.app）；禁网络调用（agent 无 http 面）。
#
# 【行为规格】
#   R1 装配：conditions=design.checked_units（build_condition_set 正门）；
#      standards=constraint_kb/constraints.json（ADR-012 D6 装载门）；
#      env=flows.build_env_flow（calc 工具同源）。
#   R2 投影：combos 截 top_n（缺省 5）——params/feasible/score/metrics
#      逐组合 asdict；附 budget_usage+diagnosis+search_semantics 摘要。
#   R3 护栏拒绝：TooLarge/Invalid 族→{"status":"rejected","reason":原文}
#      ——不穿透 MCP（对齐 update_params 可解释回显先例）。
#   R4 unit_ids 域：len≥2（单单元走既有 wp_run_enumeration——联合语义
#      下界，B4-3 收紧口径同源）；未知单元由 core 二道闸拒。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP

    from waterprint_agent.context import AgentContext

__all__ = ["register", "wp_run_joint_enumeration"]

_MIN_JOINT_UNITS = 2  # 联合语义下界（B4-3 收紧口径同源——单单元走既有正门）

_HINT_JOINT = (
    "unit_ids 须为项目内 ≥2 个可调单元（wp_get_project_outline 查；单单元枚举走"
    " wp_run_enumeration）；top_n 缺省 5。规模护栏拒绝时看 reason（缩网格/降"
    " beam_width/减单元）。"
)


def _run_joint_enumeration_impl(
    ctx: AgentContext, project_id: str, unit_ids: list[str], top_n: int = 5
) -> dict[str, Any]:
    """#22：联合枚举进程内同步（core 正门+护栏捕获转 dict）。"""
    from dataclasses import asdict as _asdict
    from pathlib import Path

    from waterprint import app as core
    from waterprint import flows

    from waterprint_agent.tools.calc import read_project

    # flows 装配面（calc 工具同源——conditions/standards 构造一致）

    if len(unit_ids) < _MIN_JOINT_UNITS:
        return {
            "status": "rejected",
            "reason": f"unit_ids 数 {len(unit_ids)} <2（单单元枚举请用 wp_run_enumeration）",
        }
    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    project = read_project(ctx, project_id)
    pack = ctx.service_ctx.settings.data_dir
    env = flows.build_env_flow(pack, project)
    conditions = flows.build_condition_flow(project, list(project.design.checked_units))
    standards = flows.build_standards_flow(pack)
    options = core.JointEnumerationOptions(standards=standards)
    try:
        outcome = core.run_joint_enumerate(project, unit_ids, conditions, env, options)
    except Exception as exc:  # 护栏族统一收敛（R3——TooLarge/Invalid 不穿透）
        return {"status": "rejected", "reason": f"{type(exc).__name__}: {exc}"}
    combos = [_asdict(combo) for combo in outcome.combos[: max(top_n, 1)]]
    return {
        "status": "ok",
        "project_id": project_id,
        "unit_ids": list(unit_ids),
        "top": combos,
        "total_combos": len(outcome.combos),
        "budget_usage": dict(outcome.budget_usage),
        "diagnosis": dict(outcome.diagnosis) if outcome.diagnosis else None,
        "search_semantics": dict(outcome.search_semantics),
    }


def register(mcp: FastMCP) -> None:
    """工具注册面（main.get_mcp 装配调用）。"""
    mcp.tool(wp_run_joint_enumeration)


async def wp_run_joint_enumeration(
    project_id: str, unit_ids: list[str], top_n: int = 5
) -> dict[str, Any]:
    """全厂联合枚举（跨单元寻优 top-N——护栏拒绝返回 status=rejected+reason）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx,
        "wp_run_joint_enumeration",
        {"project_id": project_id, "unit_ids": unit_ids, "top_n": top_n},
        lambda: _run_joint_enumeration_impl(ctx, project_id, unit_ids, top_n),
        hint=_HINT_JOINT,
    )
