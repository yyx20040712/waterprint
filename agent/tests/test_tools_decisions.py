"""test_tools_decisions——决策组（#24~#25）：纪要落盘+叙述草稿（治理批 2026-11-19）。

输入:  tmp_path 沙箱+会话（sessions 直建）+impl 直调与 dispatch 集成
输出:  record 落盘回读/未知会话拒绝/turn 推导/draft 空与有决策断言
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.chat import sessions, toolspec
from waterprint_agent.tools.decisions import _draft_narrative_impl, _record_decision_impl


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def test_record_happy_roundtrip(sandbox_env: Path) -> None:
    """record 落盘：确认 dict 四键+read_decisions 回读四键（空历史 turn=1）。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx, title="决策演示")
    result = _record_decision_impl(ctx, session.session_id, "工艺路线", "AAO", "脱氮需求")
    assert result == {
        "ok": True,
        "session_id": session.session_id,
        "topic": "工艺路线",
        "turn": 1,
    }
    decisions = sessions.read_decisions(ctx, session.session_id)
    assert decisions == [
        {"topic": "工艺路线", "conclusion": "AAO", "rationale": "脱氮需求", "turn": 1}
    ]


def test_record_turn_follows_latest_message(sandbox_env: Path) -> None:
    """turn 推导=会话消息 max(turn)（空历史=1；有历史=末条轮号）。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    sessions.append_message(session, "user", "第二轮问", turn=2)
    sessions.append_message(session, "assistant", "第二轮答", turn=2)
    result = _record_decision_impl(ctx, session.session_id, "污泥处理", "机械脱水", "占地受限")
    assert result["turn"] == 2


def test_record_unknown_session(sandbox_env: Path) -> None:
    """未知会话：error+hint（不落任何文件）。"""
    ctx = context.get_context()
    result = _record_decision_impl(ctx, "no-such-session", "t", "c", "r")
    assert "error" in result and "hint" in result
    assert not (sandbox_env / "sessions" / "chat").exists() or not list(
        (sandbox_env / "sessions" / "chat").glob("no-such-session*")
    )


def test_draft_empty_decisions(sandbox_env: Path) -> None:
    """draft 空决策：占位文本+count 0+采用指引在场。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    result = _draft_narrative_impl(ctx, session.session_id)
    assert result["decisions_count"] == 0
    assert "暂无决策纪要" in result["draft"]
    assert result["hint"]


def test_draft_with_decisions(sandbox_env: Path) -> None:
    """draft 有决策：草稿含 topic 与 conclusion+count 1。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    sessions.append_decision(session, "工艺路线", "AAO", "脱氮需求", turn=1)
    result = _draft_narrative_impl(ctx, session.session_id)
    assert result["decisions_count"] == 1
    assert "工艺路线" in result["draft"]
    assert "AAO" in result["draft"]


def test_draft_unknown_session(sandbox_env: Path) -> None:
    """draft 未知会话：error+hint（对称校验面）。"""
    ctx = context.get_context()
    result = _draft_narrative_impl(ctx, "no-such-session")
    assert "error" in result and "hint" in result


def test_dispatch_both_tools(sandbox_env: Path) -> None:
    """dispatch 集成：两工具经 toolspec.dispatch（懒加载+run_tool 记账）全链。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx, title="集成")
    recorded = toolspec.dispatch(
        ctx,
        "wp_record_decision",
        {
            "session_id": session.session_id,
            "topic": "工艺路线",
            "conclusion": "AAO",
            "rationale": "脱氮需求",
        },
    )
    assert "error" not in recorded, recorded
    assert recorded["ok"] is True
    drafted = toolspec.dispatch(ctx, "wp_draft_narrative", {"session_id": session.session_id})
    assert "error" not in drafted, drafted
    assert drafted["decisions_count"] == 1
    assert sessions.read_decisions(ctx, session.session_id)[0]["conclusion"] == "AAO"
