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


def test_truncate_keeps_head_and_tail() -> None:
    """_truncate 头尾保留：总预算 4000，头 2800+尾 1000+中间省略标记（含字符数）。"""
    import json

    from waterprint_agent.chat.loop import (
        _RESULT_KEEP_HEAD_CHARS,
        _RESULT_KEEP_TAIL_CHARS,
        _truncate,
    )

    payload = {"blob": "甲" * 9000}
    preview = _truncate(payload)
    assert preview["_truncated"] is True
    text = preview["preview"]
    raw = json.dumps(payload, ensure_ascii=False, default=str)
    omitted = len(raw) - _RESULT_KEEP_HEAD_CHARS - _RESULT_KEEP_TAIL_CHARS
    # 独立性质锚：头部前缀/尾部后缀原样在场+省略计数（不依赖实现同款公式）
    assert text.startswith(raw[:200])
    assert text.endswith(raw[-200:])
    assert f"〔中间截去 {omitted} 字符〕" in text
    assert text == (
        raw[:_RESULT_KEEP_HEAD_CHARS]
        + f"……〔中间截去 {omitted} 字符〕……"
        + raw[-_RESULT_KEEP_TAIL_CHARS:]
    )


def test_record_decision_call_injects_session(sandbox_env: Path) -> None:
    """LLM 发 wp_record_decision（session_id 传错值）：环强制覆盖+落决策+不跨会话写。"""
    events: list[dict] = []
    seen: list[list[dict]] = []

    def fake_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        seen.append([dict(m) for m in messages])
        if not any(e["type"] == "tool_result" for e in events):
            return LlmReply(
                content="",
                tool_calls=(
                    ToolCall(
                        id="c1",
                        name="wp_record_decision",
                        arguments={
                            "session_id": "attacker-other-session",
                            "topic": "工艺路线",
                            "conclusion": "AAO",
                            "rationale": "脱氮需求",
                        },
                    ),
                ),
            )
        return LlmReply(content="决策已记录。", tool_calls=())

    ctx = context.get_context()
    session = sessions.create_session(ctx, title="决策注入")
    result = run_turn(
        ctx, session, "把这轮取舍记成决策", llm=fake_llm, config=_config(),
        emit=events.append,
    )
    assert result["assistant"] == "决策已记录。"
    tool_evt = next(e for e in events if e["type"] == "tool_result")
    assert tool_evt["ok"] is True  # 覆盖注入生效（若按错误 ID 分发则 error）
    decisions = sessions.read_decisions(ctx, session.session_id)
    assert decisions == [
        {"topic": "工艺路线", "conclusion": "AAO", "rationale": "脱氮需求", "turn": 1}
    ]
    # 跨会话写未发生（伪造 ID 无会话文件产生）
    assert not (sandbox_env / "sessions" / "chat" / "attacker-other-session.jsonl").exists()
    # 历史保真：assistant 工具调用消息记录注入后的参数（=实际执行参数）
    assistant_calls = seen[1][2]["tool_calls"]
    import json as _json

    recorded_args = _json.loads(assistant_calls[0]["function"]["arguments"])
    assert recorded_args["session_id"] == session.session_id
    assert recorded_args["session_id"] != "attacker-other-session"


def test_system_message_carries_decisions(sandbox_env: Path) -> None:
    """有历史决策的会话：LLM 收到的首条 system 含决策块与「跨轮持久」字样。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    sessions.append_message(session, "user", "上一轮问题", turn=1)
    sessions.append_message(session, "assistant", "上一轮回答", turn=1)
    sessions.append_decision(session, "工艺路线", "AAO", "脱氮需求", turn=1)
    seen: list[list[dict]] = []

    def fake_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        seen.append(list(messages))
        return LlmReply(content="好的", tool_calls=())

    run_turn(ctx, session, "新问题", llm=fake_llm, config=_config(), emit=lambda e: None)
    system = seen[0][0]["content"]
    assert "〔决策纪要（跨轮持久）〕" in system
    assert "工艺路线：AAO（依据：脱氮需求）" in system


def test_system_decisions_capped_at_eight(sandbox_env: Path) -> None:
    """决策超 8 条：system 保留最新 8 条（最早隐去）+尾注「另有 N 条更早决策未列出」。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    for index in range(10):
        sessions.append_decision(
            session, f"主题{index}", f"结论{index}", f"依据{index}", turn=1
        )
    seen: list[list[dict]] = []

    def fake_llm(config: ChatConfig, messages: list[dict], tools: list[dict]) -> LlmReply:
        seen.append(list(messages))
        return LlmReply(content="好的", tool_calls=())

    run_turn(ctx, session, "新问题", llm=fake_llm, config=_config(), emit=lambda e: None)
    system = seen[0][0]["content"]
    assert "主题9：结论9（依据：依据9）" in system  # 最新条在场（被推翻性新决策不丢）
    assert "主题2：结论2（依据：依据2）" in system  # 保留窗内最早一条
    assert "主题0" not in system and "主题1" not in system  # 最早两条隐去
    assert "另有 2 条更早决策未列出——wp_draft_narrative 可取全量草稿" in system


def test_decisions_block_boundaries() -> None:
    """决策块边界：恰 8 条无尾注；空依据省括号；超长行 120 字符确定性截断。"""
    from waterprint_agent.chat import prompts

    def item(topic: str, conclusion: str, rationale: str) -> dict:
        return {"topic": topic, "conclusion": conclusion, "rationale": rationale}

    eight = [item(f"t{i}", f"c{i}", f"r{i}") for i in range(8)]
    block8 = prompts.system_prompt(None, False, eight)
    assert "t7：c7（依据：r7）" in block8
    assert "另有" not in block8  # 恰 8 条=无尾注
    no_rationale = prompts.system_prompt(None, False, [item("t", "c", "")])
    assert "t：c" in no_rationale
    assert "（依据：" not in no_rationale  # 空依据省括号
    long_line = prompts.system_prompt(None, False, [item("甲" * 200, "c", "")])
    kept = next(ln for ln in long_line.splitlines() if ln.startswith("甲"))
    assert len(kept) == 122  # 120 字符+省略号 2 字符（确定性截断）
