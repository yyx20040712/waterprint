"""test_sessionlog——jsonl 会话日志：事件序号/追加/脱敏条款。

输入:  tmp_path 沙箱根 + 含正式路径/env 值的 payload 样本
输出:  序号单调/行级 flush/哈希脱敏断言（AI1-TRACK-B §3 D7）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from waterprint_agent.sessionlog import SessionLog

_SID = "sess-0001"
_FORMAL = Path(r"E:\class\智水蓝图\waterprint\core\tests\golden\golden_data\x.json")


@pytest.fixture
def log(tmp_path: Path) -> SessionLog:
    root = tmp_path / "sb"
    (root / "sessions").mkdir(parents=True)
    return SessionLog(root)


def test_append_seq_monotonic(log: SessionLog) -> None:
    """事件序号：同会话 1,2,3 单调递增；行含六键。"""
    assert log.append(_SID, "user", "instruction", {"text": "设计一个厂"}) == 1
    assert log.append(_SID, "agent", "instruction", {"text": "开始"}) == 2
    assert log.append(_SID, "tool", "tool_call", {"tool": "wp_list_units"}) == 3
    events = log.events(_SID)
    assert [e["seq"] for e in events] == [1, 2, 3]
    for event in events:
        assert set(event) == {"ts", "session_id", "seq", "actor", "type", "payload"}
        assert event["session_id"] == _SID


def test_append_line_flush(log: SessionLog) -> None:
    """同步追加+行级 flush：append 返回后文件即刻可读（无缓冲滞留）。"""
    log.append(_SID, "tool", "tool_result", {"tool": "wp_create_project", "ok": True})
    raw = (log._root / "sessions" / f"{_SID}.jsonl").read_text(encoding="utf-8")
    assert json.loads(raw.splitlines()[0])["type"] == "tool_result"


def test_seq_continues_across_instances(log: SessionLog, tmp_path: Path) -> None:
    """实例重建后序号续接（按既有文件行数恢复——不回卷覆盖）。"""
    log.append(_SID, "user", "instruction", {"text": "a"})
    log.append(_SID, "user", "instruction", {"text": "b"})
    reborn = SessionLog(tmp_path / "sb")
    assert reborn.append(_SID, "user", "instruction", {"text": "c"}) == 3


def test_sanitize_formal_path_hashed(log: SessionLog) -> None:
    """脱敏①：正式区绝对路径原文不落盘——哈希标记替代。"""
    log.append(_SID, "tool", "tool_call", {"tool": "wp_create_project", "seed_path": str(_FORMAL)})
    content = (log._root / "sessions" / f"{_SID}.jsonl").read_text(encoding="utf-8")
    assert str(_FORMAL).lower() not in content.lower()
    assert "{path:" in content


def test_sanitize_sandbox_path_relative(log: SessionLog, tmp_path: Path) -> None:
    """脱敏②：沙箱内绝对路径落相对形态（不带沙箱根原文）。"""
    inside = log._root / "projects" / "abc.wp.json"
    log.append(_SID, "tool", "tool_result", {"tool": "wp_create_project", "path": str(inside)})
    content = (log._root / "sessions" / f"{_SID}.jsonl").read_text(encoding="utf-8")
    assert str(inside).lower() not in content.lower()
    assert "projects/abc.wp.json" in content.replace("\\", "/")


def test_sanitize_env_value_masked(log: SessionLog, monkeypatch) -> None:
    """脱敏③：环境变量值不落盘（占位替代）。"""
    monkeypatch.setenv("WATERPRINT_TEST_SECRET", "s3cr3t-token-value-42")
    log.append(
        _SID, "agent", "instruction", {"text": "token 是 s3cr3t-token-value-42 请查收"}
    )
    content = (log._root / "sessions" / f"{_SID}.jsonl").read_text(encoding="utf-8")
    assert "s3cr3t-token-value-42" not in content
    assert "<env:" in content


def test_sanitize_nested_structures(log: SessionLog) -> None:
    """脱敏递归：嵌套 dict/list 中的路径与 Path 对象同面处理。"""
    log.append(
        _SID,
        "tool",
        "param_patch",
        {"detail": {"files": [str(_FORMAL), Path("plain.txt")], "note": [_FORMAL.parent]},
        },
    )
    events = log.events(_SID)
    payload_text = json.dumps(events[0]["payload"], ensure_ascii=False)
    assert str(_FORMAL).lower() not in payload_text.lower()
    assert "{path:" in payload_text
    assert "plain.txt" in payload_text  # 相对路径原样保留


def test_session_id_component_guard(log: SessionLog) -> None:
    """会话 id 白名单守卫：分隔符/点分量注入拒绝（日志文件名拼界面）。"""
    with pytest.raises(ValueError):
        log.append("../evil", "user", "instruction", {"text": "x"})
    with pytest.raises(ValueError):
        log.append("a/b", "user", "instruction", {"text": "x"})
