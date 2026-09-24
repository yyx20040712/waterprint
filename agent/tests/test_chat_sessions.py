"""test_chat_sessions——会话存储：追加式 JSONL+滑动窗口+项目绑定+决策纪要。

输入:  tmp_path 沙箱（env 覆盖）+ context 装配
输出:  会话建/读/窗口/绑定/决策断言（B4-4b 子批 1）
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.chat import sessions


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def test_create_and_load(sandbox_env: Path) -> None:
    """建会话落沙箱 sessions/chat/<id>.jsonl；重载回读元信息。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx, title="演示")
    stored = sandbox_env / "sessions" / "chat" / f"{session.session_id}.jsonl"
    assert stored.is_file()
    loaded = sessions.load_session(ctx, session.session_id)
    assert loaded is not None
    assert loaded.session_id == session.session_id
    assert loaded.title == "演示"
    assert loaded.project_id is None


def test_create_session_rejects_bad_explicit_id(sandbox_env: Path) -> None:
    """门一 B1 防御纵深：显式 ID 过分量白名单（../与反斜杠拒——ValueError）。"""
    import pytest as _pytest

    ctx = context.get_context()
    with _pytest.raises(ValueError, match="成分非法"):
        sessions.create_session(ctx, session_id="..\escape")
    with _pytest.raises(ValueError, match="成分非法"):
        sessions.create_session(ctx, session_id="bad$id")


def test_load_missing_returns_none(sandbox_env: Path) -> None:
    ctx = context.get_context()
    assert sessions.load_session(ctx, "no-such-id") is None


def test_append_message_and_history(sandbox_env: Path) -> None:
    """消息追加可回读；turn 计数递增。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    sessions.append_message(session, "user", "建一座三万吨市政厂", turn=1)
    sessions.append_message(
        session, "assistant", "已创建", turn=1,
        tool_steps=[{"name": "wp_create_project", "ok": True}],
    )
    history = sessions.read_history(ctx, session.session_id)
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[1]["tool_steps"] == [{"name": "wp_create_project", "ok": True}]


def test_window_keeps_last_n_turns(sandbox_env: Path) -> None:
    """滑动窗口：30 轮取末 20 轮（窗口外整轮丢弃）。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    for turn in range(1, 31):
        sessions.append_message(session, "user", f"问{turn}", turn=turn)
        sessions.append_message(session, "assistant", f"答{turn}", turn=turn)
    window = sessions.window(ctx, session.session_id, turns=20)
    assert len(window) == 40  # 20 轮 × 2 条
    assert window[0] == {"role": "user", "text": "问11", "tool_steps": []}
    assert window[-1]["text"] == "答30"


def test_bind_project_last_wins(sandbox_env: Path) -> None:
    """项目绑定追加式（binding 记录后读生效）；重绑覆盖。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    sessions.bind_project(ctx, session, "pid-1")
    loaded = sessions.load_session(ctx, session.session_id)
    assert loaded is not None and loaded.project_id == "pid-1"
    sessions.bind_project(ctx, loaded, "pid-2")
    again = sessions.load_session(ctx, session.session_id)
    assert again is not None and again.project_id == "pid-2"


def test_decision_records(sandbox_env: Path) -> None:
    """决策纪要四键落盘可回读。"""
    ctx = context.get_context()
    session = sessions.create_session(ctx)
    sessions.append_decision(
        session, topic="工艺路线", conclusion="AAO", rationale="脱氮需求", turn=2
    )
    decisions = sessions.read_decisions(ctx, session.session_id)
    assert decisions == [
        {"topic": "工艺路线", "conclusion": "AAO", "rationale": "脱氮需求", "turn": 2}
    ]


def test_list_sessions(sandbox_env: Path) -> None:
    """清单面：多会话摘要（标题/轮数）可枚举。"""
    ctx = context.get_context()
    a = sessions.create_session(ctx, title="会话甲")
    sessions.append_message(a, "user", "你好", turn=1)
    sessions.create_session(ctx, title="会话乙")
    items = sessions.list_sessions(ctx)
    assert len(items) == 2
    by_title = {i["title"]: i for i in items}
    assert by_title["会话甲"]["turns"] == 1
    assert by_title["会话乙"]["turns"] == 0
