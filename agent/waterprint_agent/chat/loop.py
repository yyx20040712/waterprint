"""编排环（ADR-019 只编排不算数）：LLM 步→工具步→回填→终止/上限/降级。

输入:  AgentContext+ChatSession+用户文本+LLM 可调用（测试可注入）
输出:  TurnResult（assistant 文本/truncated/steps/degraded）+事件流（emit 回调）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/loop.py
#   职责：多轮对话编排环——while 语义（LLM 调用→工具执行→结果回填
#       →循环至零 tool_calls 终止）；迭代上限+降级回退+事件流发射；
#       单发入口 single_shot（NL 入口重建——B4-4a 三话术验收口径沿承）。
#   禁区：禁计算逻辑（一切数值经 toolspec.dispatch→impl——ADR-019）；
#       禁静默截断/静默失败（上限=truncated 标记+降级=note+banner 事件）；
#       禁密钥入事件/会话（config 只进 llm 调用参数）。
#
# 【行为规格】
#   R1 环步：上限=config.max_iterations（12——社区区间中值）；达限=
#      截断 assistant 消息+truncated:true；正常终止=零 tool_calls。
#   R2 降级：三键未配置=直接降级；连续 2 次 LlmUnavailableError=
#      降级——两路均走 _run_fallback（关键词直译：建项+计算+可选报告）。
#   R3 上下文：system（prompts.system_prompt）+window(config.window_turns)
#      投影（近 20 轮全文，窗口外丢弃无摘要——设计终裁 W2）；工具结果
#      回填截断 4000 字符（设计终裁 §二）。
#   R4 事件：emit 回调逐事件调用（turn_start/llm_step/tool_start/
#      tool_result/assistant_text/fallback/turn_end）——CLI 印 stdout、
#      worker 桥转 SSE、测试收集。
#   R5 绑定：wp_create_project 成功→bind_project（会话-项目 1:1）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from waterprint_agent.chat import fallback, prompts, sessions, toolspec
from waterprint_agent.chat.llm import ChatConfig, LlmUnavailableError, chat_completion

if TYPE_CHECKING:  # 仅类型面
    from waterprint_agent.chat.llm import LlmReply
    from waterprint_agent.chat.sessions import ChatSession
    from waterprint_agent.context import AgentContext

__all__ = ["run_turn", "single_shot"]

Emit = Callable[[dict[str, Any]], None]
LlmFn = Callable[[ChatConfig, list[dict[str, Any]], list[dict[str, Any]]], "LlmReply"]
_RESULT_PREVIEW_CHARS = 4000  # 工具结果回填截断（设计终裁 §二推导标注）
_DEGRADE_AFTER_FAILURES = 2  # 连续不可用降级阈（社区「优雅收敛」纪律）


def _last_user_message(ctx: AgentContext, session: ChatSession) -> dict[str, Any]:
    """会话末条 user 消息（降级链回读——调用前必已落盘）。"""
    history = sessions.read_history(ctx, session.session_id)
    for item in reversed(history):
        if item["role"] == "user":
            return item
    return {"text": "", "turn": 1}


def _no_emit(_event: dict[str, Any]) -> None:
    """缺省事件汇（丢弃——显式传 emit 才有观测面）。"""


def _truncate(result: dict[str, Any]) -> dict[str, Any]:
    """工具结果回填预览（超长=截断+标记——防上下文爆容）。"""
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) <= _RESULT_PREVIEW_CHARS:
        return result
    return {"_truncated": True, "preview": text[:_RESULT_PREVIEW_CHARS]}


def _next_turn(ctx: AgentContext, session: ChatSession) -> int:
    history = sessions.read_history(ctx, session.session_id)
    if not history:
        return 1
    return max(int(item["turn"]) for item in history) + 1


def _context_messages(
    window_items: list[dict[str, Any]],
    config: ChatConfig,
    user_text: str,
    project_id: str | None,
) -> list[dict[str, Any]]:
    """R3：system+窗口投影+本轮 user（窗口取于 user 落盘前——防双计）。"""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": prompts.system_prompt(project_id, degraded=False)}
    ]
    for item in window_items:
        content = str(item["text"])
        steps = item.get("tool_steps") or []
        if steps and item["role"] == "assistant":
            trace = "、".join(
                f"{step.get('name')}({'成功' if step.get('ok') else '失败'})" for step in steps
            )
            content = f"〔本轮工具步：{trace}〕{content}"
        messages.append({"role": str(item["role"]), "content": content})
    messages.append({"role": "user", "content": user_text})
    return messages


def _tool_call_messages(reply: LlmReply) -> dict[str, Any]:
    """assistant 工具调用消息（OpenAI 协议形态）。"""
    return {
        "role": "assistant",
        "content": reply.content or "",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments, ensure_ascii=False),
                },
            }
            for call in reply.tool_calls
        ],
    }


def run_turn(  # noqa: PLR0913  # 编排注入面（llm/config/emit 三可注入项——测试与桥层依赖，exports dxf 五选项同款先例）
    ctx: AgentContext,
    session: ChatSession,
    user_text: str,
    *,
    llm: LlmFn | None = None,
    config: ChatConfig | None = None,
    emit: Emit = _no_emit,
) -> dict[str, Any]:
    """跑一轮对话（R1-R5——返回 {assistant,truncated,steps,degraded}）。"""
    config = config or ChatConfig.from_env()
    if llm is None:
        llm = chat_completion
    turn = _next_turn(ctx, session)
    base_window = sessions.window(ctx, session.session_id, turns=config.window_turns)
    sessions.append_message(session, "user", user_text, turn=turn)
    emit({"type": "turn_start", "session_id": session.session_id, "turn": turn})
    if not config.available():
        emit({"type": "fallback", "reason": "config"})
        return _run_fallback(
            ctx,
            session,
            emit,
            note="未配置AI 接口三键（base_url/api_key/model）——关键词直译模式",
        )
    messages = _context_messages(base_window, config, user_text, session.project_id)
    tools = toolspec.tools_schema()
    tool_steps: list[dict[str, Any]] = []
    failures = 0
    steps = 0
    for step in range(1, config.max_iterations + 1):
        steps = step
        emit({"type": "llm_step", "step": step})
        try:
            reply = llm(config, messages, tools)
        except LlmUnavailableError as exc:
            failures += 1
            if failures >= _DEGRADE_AFTER_FAILURES:
                emit({"type": "fallback", "reason": "llm_unavailable"})
                return _run_fallback(
                    ctx,
                    session,
                    emit,
                    note=f"AI 接口连续不可用（{exc}）——关键词直译模式",
                )
            continue
        failures = 0
        if reply.tool_calls:
            messages.append(_tool_call_messages(reply))
            for call in reply.tool_calls:
                emit({"type": "tool_start", "name": call.name, "arguments": call.arguments})
                result = toolspec.dispatch(ctx, call.name, call.arguments)
                ok = "error" not in result
                preview = _truncate(result)
                emit({"type": "tool_result", "name": call.name, "ok": ok, "summary": preview})
                tool_steps.append({"name": call.name, "ok": ok})
                if call.name == "wp_create_project" and ok and result.get("project_id"):
                    sessions.bind_project(ctx, session, str(result["project_id"]))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(preview, ensure_ascii=False, default=str),
                    }
                )
            continue
        text = reply.content.strip()
        sessions.append_message(session, "assistant", text, turn=turn, tool_steps=tool_steps)
        emit({"type": "assistant_text", "text": text})
        emit({"type": "turn_end", "truncated": False, "steps": steps})
        return {"assistant": text, "truncated": False, "steps": steps, "degraded": False}
    text = "已达单轮工具调用上限，本轮截断。请基于当前进度继续提问，或调整参数后重试。"
    sessions.append_message(
        session, "assistant", text, turn=turn, truncated=True, tool_steps=tool_steps
    )
    emit({"type": "turn_end", "truncated": True, "steps": steps})
    return {"assistant": text, "truncated": True, "steps": steps, "degraded": False}


def _run_fallback(
    ctx: AgentContext, session: ChatSession, emit: Emit, *, note: str
) -> dict[str, Any]:
    """降级链（R2）：关键词直译——建项+计算+可选双报告；非设计域=显式拒绝。

    用户文本与轮号从会话末条 user 消息回读（调用前必已落盘）。"""
    sessions.append_note(session, note)
    last_user = _last_user_message(ctx, session)
    user_text, turn = last_user["text"], int(last_user["turn"])
    plan = fallback.parse(str(user_text))
    tool_steps: list[dict[str, Any]] = []
    if plan is None:
        text = (
            "降级模式只支持设计类话术（例如「设计一座日处理 3 万吨的市政污水处理厂」）。"
            "请恢复AI 接口配置后重试，或换一句设计需求。"
        )
        sessions.append_message(session, "assistant", text, turn=turn, tool_steps=tool_steps)
        emit({"type": "turn_end", "truncated": False, "steps": 0})
        return {"assistant": text, "truncated": False, "steps": 0, "degraded": True}
    pieces: list[str] = [f"降级模式：{note}"]
    if plan.note:
        pieces.append(plan.note)
    for name, template in _fallback_tool_sequence(plan):
        arguments = dict(template)
        if arguments.get("project_id") is None and session.project_id:
            arguments["project_id"] = session.project_id
        emit({"type": "tool_start", "name": name, "arguments": arguments})
        result = toolspec.dispatch(ctx, name, arguments)
        ok = "error" not in result
        emit({"type": "tool_result", "name": name, "ok": ok, "summary": _truncate(result)})
        tool_steps.append({"name": name, "ok": ok})
        if name == "wp_create_project" and ok and result.get("project_id"):
            sessions.bind_project(ctx, session, str(result["project_id"]))
            pieces.append(f"已按模板建项（{result['project_id']}）")
        elif name == "wp_run_calc" and ok:
            pieces.append(_calc_summary_line(result))
        elif name.startswith("wp_export") and ok:
            path = result.get("path") or result.get("export_path") or ""
            if path:
                pieces.append(f"已导出 {path}")
    text = "。".join(pieces) + "。"
    sessions.append_message(session, "assistant", text, turn=turn, tool_steps=tool_steps)
    emit({"type": "assistant_text", "text": text})
    emit({"type": "turn_end", "truncated": False, "steps": len(tool_steps)})
    return {"assistant": text, "truncated": False, "steps": len(tool_steps), "degraded": True}


def _fallback_tool_sequence(plan: fallback.FallbackPlan) -> list[tuple[str, dict[str, Any]]]:
    """降级工具序列（建项→计算→可选双报告——plan.seed 域内恒定序）。"""
    sequence: list[tuple[str, dict[str, Any]]] = [
        ("wp_create_project", {"name": plan.name, "seed": plan.seed}),
        ("wp_run_calc", {"project_id": None, "conditions": None}),  # project_id 由环绑定态补
    ]
    if plan.wants_report:
        sequence.append(("wp_export_calcbook", {"project_id": None}))
        sequence.append(
            (
                "wp_export_report",
                {"project_id": None, "condition_key": "design", "narrative_fills": None},
            )
        )
    return sequence


def _calc_summary_line(result: dict[str, Any]) -> str:
    """计算结果单行摘要（数值全来自工具返回——禁编造）。"""
    digest = str(result.get("design_digest") or "")
    path = str(result.get("result_path") or "")
    parts = ["全厂计算完成"]
    if digest:
        parts.append(f"结果摘要 {digest[:10]}")
    if path:
        parts.append(f"落盘 {path}")
    return "，".join(parts) if len(parts) > 1 else parts[0]


def single_shot(
    ctx: AgentContext, text: str, *, config: ChatConfig | None = None, emit: Emit = _no_emit
) -> tuple[ChatSession, dict[str, Any]]:
    """单发入口（NL 入口重建①）：新会话跑一轮——B4-4a 三话术验收口径。"""
    session = sessions.create_session(ctx, title=text[:24])
    result = run_turn(ctx, session, text, config=config, emit=emit)
    return session, result
