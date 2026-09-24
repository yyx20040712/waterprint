"""test_chat_loop——编排环：工具往返/迭代上限/降级回退/窗口/事件序。

输入:  tmp_path 沙箱+注入式假 LLM（无网络依赖）
输出:  环语义断言（B4-4b 子批 1——迭代上限 12/连续 2 失败降级/绑定捕获）
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.chat import sessions
from waterprint_agent.chat.llm import ChatConfig, LlmReply, LlmUnavailableError, ToolCall
from waterprint_agent.chat.loop import run_turn


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def _config(available: bool = True) -> ChatConfig:
    if available:
        return ChatConfig(base_url="http://unused/v1", api_key="k", model="m")
    return ChatConfig()


def test_tool_roundtrip_and_binding(sandbox_env: Path) -> None:
    """假 LLM 先发一次工具调用再收尾：结果/事件序/建项绑定捕获。"""
    calls: list[tuple[list[dict], list[dict]]] = []

    def fake_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        calls.append((list(messages), list(tools)))
        if len(calls) == 1:
            return LlmReply(
                content="",
                tool_calls=(
                    ToolCall(id="c1", name="wp_list_units", arguments={"category": None}),
                ),
            )
        return LlmReply(content="已看完单元目录，共收录主流工艺单元。", tool_calls=())

    ctx = context.get_context()
    session = sessions.create_session(ctx, title="往返")
    events: list[dict] = []
    result = run_turn(
        ctx, session, "看下有哪些单元", llm=fake_llm, config=_config(),
        emit=events.append,
    )
    assert result["assistant"].startswith("已看完")
    assert result["truncated"] is False
    assert result["steps"] == 2
    types = [e["type"] for e in events]
    assert types[0] == "turn_start"
    assert "tool_start" in types and "tool_result" in types
    assert types[-1] == "turn_end"
    tool_evt = next(e for e in events if e["type"] == "tool_result")
    assert tool_evt["ok"] is True
    # 会话落盘：user+assistant 两条，assistant 带工具步
    history = sessions.read_history(ctx, session.session_id)
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[1]["tool_steps"] == [{"name": "wp_list_units", "ok": True}]


def test_iteration_cap_marks_truncated(sandbox_env: Path) -> None:
    """假 LLM 永远发工具调用：步数=上限 12+truncated 标记（禁静默截断）。"""

    def loop_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        return LlmReply(
            content="",
            tool_calls=(ToolCall(id="c", name="wp_list_units", arguments={}),),
        )

    ctx = context.get_context()
    session = sessions.create_session(ctx)
    events: list[dict] = []
    result = run_turn(ctx, session, "反复查目录", llm=loop_llm, config=_config(), emit=events.append)
    assert result["truncated"] is True
    assert result["steps"] == 12
    assert sum(1 for e in events if e["type"] == "tool_result") == 12
    history = sessions.read_history(ctx, session.session_id)
    assert history[-1]["truncated"] is True


def test_degrade_after_two_consecutive_failures(sandbox_env: Path) -> None:
    """连续 2 次不可用→降级关键词直译：市政话术走种子建项+计算全链。"""
    attempts: list[int] = []

    def broken_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        attempts.append(1)
        raise LlmUnavailableError("LLM 端点不可达（URLError）")

    ctx = context.get_context()
    session = sessions.create_session(ctx)
    events: list[dict] = []
    result = run_turn(
        ctx, session, "设计一座日处理 3 万吨的市政污水处理厂",
        llm=broken_llm, config=_config(), emit=events.append,
    )
    assert attempts == [1, 1]  # 恰两次尝试后降级
    assert result["degraded"] is True
    fallback_evt = next(e for e in events if e["type"] == "fallback")
    assert fallback_evt["reason"] == "llm_unavailable"
    # 降级链执行了建项+计算（工具事件在场）
    tool_names = [e["name"] for e in events if e["type"] == "tool_start"]
    assert "wp_create_project" in tool_names
    assert "wp_run_calc" in tool_names
    assert session.project_id  # 绑定捕获


def test_unconfigured_falls_back_directly(sandbox_env: Path) -> None:
    """三键未配置：零 LLM 调用直接降级（fail-fast 不空转）。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)

    def must_not_call(*args: object, **kwargs: object) -> LlmReply:
        raise AssertionError("未配置时不得调用 LLM")

    result = run_turn(
        ctx, session, "设计市政污水厂 3 万吨，给我报告",
        llm=must_not_call, config=_config(available=False), emit=lambda e: None,
    )
    assert result["degraded"] is True
    assert session.project_id
    # 会话留降级注记
    raw = (sandbox_env / "sessions" / "chat" / f"{session.session_id}.jsonl").read_text(
        encoding="utf-8"
    )
    assert '"record": "note"' in raw


def test_window_caps_context(sandbox_env: Path) -> None:
    """30 轮历史：LLM 收到的 messages=system+末 20 轮（窗口外丢弃）。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    for turn in range(1, 31):
        sessions.append_message(session, "user", f"问{turn}", turn=turn)
        sessions.append_message(session, "assistant", f"答{turn}", turn=turn)
    seen: list[list[dict]] = []

    def final_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        seen.append(list(messages))
        return LlmReply(content="好的", tool_calls=())

    run_turn(ctx, session, "新问题", llm=final_llm, config=_config(), emit=lambda e: None)
    assert len(seen[0]) == 1 + 20 * 2 + 1  # system+40 窗口+本轮 user
    assert seen[0][1]["content"] == "问11"  # 窗口起点=第 11 轮


def test_fallback_rejects_out_of_domain(sandbox_env: Path) -> None:
    """降级模式遇非设计域话术：显式拒绝文本（不瞎猜）。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    result = run_turn(
        ctx, session, "讲个笑话", llm=None, config=_config(available=False), emit=lambda e: None,
    )
    assert result["degraded"] is True
    assert "降级" in result["assistant"]
    history = sessions.read_history(ctx, session.session_id)
    assert len(history) == 2  # user+assistant（零工具步）
