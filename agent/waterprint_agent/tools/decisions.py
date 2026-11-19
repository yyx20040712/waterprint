"""决策组工具（权威表 #24~#25）：设计决策纪要落盘+说明书叙述草稿（治理批 2026-11-19）。

输入:  AgentContext+session_id（loop 强制注入）+决策四键面
输出:  记录确认 dict / 叙述草稿 dict（draft+decisions_count+hint）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（治理批 2026-11-19 轨道丙接线）
#   路径：agent/waterprint_agent/tools/decisions.py
#   职责：#24 wp_record_decision——设计决策纪要四键落盘
#       （sessions.append_decision 真源；session_id 由 loop 强制注入
#       当前会话——防跨会话写）；#25 wp_draft_narrative——决策纪要
#       →说明书 process_selection 叙述草稿（narrative.draft_process_selection
#       纯模板零计算，产物经 wp_export_report 的 narrative_fills 人工采用）。
#       旧终裁 §五「环内函数非工具」随本批 supersession 调整为工具面暴露
#       （sessions.append_decision/read_decisions 与 draft 原挂空无运行期
#       消费者——治理批接线）。
#   禁区：禁顶层 import chat 包各模块（懒加载铁律——函数体内首触；
#       tools→chat 包内边无契约禁止——agent/pyproject 契约仅限 core
#       L1-L3 子包与 web 框架）；禁数值计算
#       与编造数字（叙述真源=narrative 纯模板）；禁直写报告文件
#       （落盘决策归 sessions，导出归 wp_export_report）。
#
# 【行为规格】
#   R1 记录：load_session 校验会话在场（None→error+hint 不落盘）；
#      turn=会话消息 max(turn)（空历史=1）；append_decision 四键
#      （topic/conclusion/rationale/turn）；返回 {ok, session_id, topic, turn}。
#   R2 草稿：会话在场校验同 R1；decisions=read_decisions 全量；
#      text=narrative.draft_process_selection(decisions)；返回
#      {draft, decisions_count, hint（采用指引——narrative_fills 入口
#      与数字拒收口径）}。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from waterprint_agent.context import AgentContext

__all__ = ["_draft_narrative_impl", "_record_decision_impl"]

_MISSING_SESSION_HINT = (
    "会话由系统自动注入（session_id 无需填写）；当前会话不存在——"
    "先在本会话内重试，不要手填其他会话的 ID。"
)
_ADOPT_HINT = (
    "草稿经 wp_export_report 的 narrative_fills.process_selection 传入采用；"
    "草稿若含数字会被 verify 拒——人工核改后采用。"
)


def _record_decision_impl(
    ctx: AgentContext, session_id: str, topic: str, conclusion: str, rationale: str
) -> dict[str, Any]:
    """#24：决策纪要四键落盘（R1——跨轮持久，供 system 注入与说明书叙述）。"""
    from waterprint_agent.chat import sessions

    session = sessions.load_session(ctx, session_id)
    if session is None:
        return {"error": f"会话不存在：{session_id!r}", "hint": _MISSING_SESSION_HINT}
    history = sessions.read_history(ctx, session_id)
    turn = max(int(item["turn"]) for item in history) if history else 1
    sessions.append_decision(session, topic, conclusion, rationale, turn)
    return {"ok": True, "session_id": session_id, "topic": topic, "turn": turn}


def _draft_narrative_impl(ctx: AgentContext, session_id: str) -> dict[str, Any]:
    """#25：决策纪要→process_selection 叙述草稿（R2——narrative 纯模板）。"""
    from waterprint_agent.chat import narrative, sessions

    session = sessions.load_session(ctx, session_id)
    if session is None:
        return {"error": f"会话不存在：{session_id!r}", "hint": _MISSING_SESSION_HINT}
    decisions = sessions.read_decisions(ctx, session_id)
    return {
        "draft": narrative.draft_process_selection(decisions),
        "decisions_count": len(decisions),
        "hint": _ADOPT_HINT,
    }
