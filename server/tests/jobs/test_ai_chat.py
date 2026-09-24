"""ai_chat runner 镜像测试：子进程桥解析面（仿进程——B4-4b CI 覆盖率补）。

输入:  仿 Popen（stdout=JSONL 事件流/退出码可控）+载荷
输出:  事件收割/终态/失败分类/非法行容错断言
"""

from __future__ import annotations

import io
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from waterprint_server.jobs import ai_chat as runner

_BASE_PAYLOAD: Mapping[str, Any] = {
    "kind": "ai_chat",
    "task_id": "t-1",
    "session_id": "sessjobs000000000000000000000000ff",
    "message": "建一座污水厂",
    "data_dir": ".",
    "artifacts_dir": ".",
}


class _FakeProcess:
    """仿子进程（stdout= StringIO 事件流；wait 返回注入退出码）。"""

    def __init__(self, lines: list[str], return_code: int = 0) -> None:
        self.stdout = io.StringIO("".join(line + "\n" for line in lines))
        self.stderr = io.StringIO("boom" if return_code else "")
        self._return_code = return_code
        self.terminated = False

    def wait(self, timeout: float = 0) -> int:
        return self._return_code

    def poll(self) -> int | None:
        return self._return_code if self.terminated else None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.terminated = True


class _ProgressSink:
    """仿进度队列（_report 面 put 协议）。"""

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def put(self, message: dict[str, Any]) -> None:
        self.messages.append(message)


def _patch_spawn(monkeypatch, lines: list[str], return_code: int = 0) -> _FakeProcess:
    fake = _FakeProcess(lines, return_code)

    def _fake_popen(*args: Any, **kwargs: Any) -> _FakeProcess:
        return fake

    monkeypatch.setattr(runner.subprocess, "Popen", _fake_popen)
    return fake


def test_stream_happy_path(monkeypatch, tmp_path: Path) -> None:
    """事件流→进度收割+turn_summary 终态（消息文件即用即清）。"""
    events = [
        json.dumps({"type": "turn_start", "session_id": "s", "turn": 1}),
        json.dumps({"type": "tool_start", "name": "wp_run_calc"}),
        "not-json-line",  # R4 非法行容错跳过
        json.dumps({"type": "tool_result", "name": "wp_run_calc", "ok": True}),
        json.dumps({"type": "turn_summary", "session_id": "s", "truncated": False}),
    ]
    _patch_spawn(monkeypatch, events)
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    sink = _ProgressSink()
    result = runner._run_ai_chat(payload, None, sink)  # noqa: SLF001  # runner 私有面直测（仿进程单测）
    assert result["state"] == "done"
    # turn_summary 载荷 session_id（'s'）覆盖载荷缺省——终态原文透传语义
    assert result["truncated"] is False
    stages = [message["stage"] for message in sink.messages]
    assert "对话开始" in stages
    assert "调用工具 wp_run_calc" in stages
    assert "工具完成 wp_run_calc" in stages
    leftovers = list(tmp_path.glob("ai-chat-*.msg"))
    assert leftovers == []  # 消息文件即用即清


def test_stream_nonzero_exit_runtime_error(monkeypatch, tmp_path: Path) -> None:
    """W4 分类：非零退出→RuntimeError（500 面——非载荷非法）。"""
    _patch_spawn(monkeypatch, [], return_code=2)
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    with pytest.raises(RuntimeError, match="退出码 2"):
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）

            payload, None, None)


def test_payload_gate_rejects_bad_session(monkeypatch, tmp_path: Path) -> None:
    """B1 纵深：IPC 面 session_id 成分二道闸（../拒→InvalidTaskPayloadError）。"""
    from waterprint_server.jobs.worker import InvalidTaskPayloadError

    _patch_spawn(monkeypatch, [])
    payload = {**_BASE_PAYLOAD, "session_id": "../escape", "artifacts_dir": str(tmp_path)}
    with pytest.raises(InvalidTaskPayloadError, match="成分非法"):
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）

            payload, None, None)


def test_missing_uv_rejected(monkeypatch, tmp_path: Path) -> None:
    """uv 缺失：422 面（部署前置条件缺失——可解释拒绝）。"""
    from waterprint_server.jobs.worker import InvalidTaskPayloadError

    monkeypatch.setattr(runner, "which", lambda name: None)
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    with pytest.raises(InvalidTaskPayloadError, match="uv"):
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）

            payload, None, None)
