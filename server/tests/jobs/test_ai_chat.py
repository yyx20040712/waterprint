"""ai_chat runner 镜像测试：子进程桥解析面（仿进程——B4-4b CI 覆盖率补；
b28 AUDIT-#13：三处 process.wait 超时→AiChatBridgeTimeoutError 领域化钉面；
b28 回炉：顽固进程收割防重入钉面）。

输入:  仿 Popen（stdout=JSONL 事件流/退出码可控）+载荷
输出:  事件收割/终态/失败分类/非法行容错/宽限超时领域错误/防重入断言
"""

from __future__ import annotations

import io
import json
import subprocess
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
    # P0-C（fix-plan 批3）：repo_root 显式载荷键（services 单点推导注入）
    "repo_root": ".",
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


class _ZombieProcess(_FakeProcess):
    """僵尸子进程（wait 恒超时——terminate/kill 后仍不退的极端面仿体）。"""

    def wait(self, timeout: float = 0) -> int:
        raise subprocess.TimeoutExpired(cmd="uv", timeout=timeout)


def test_final_wait_timeout_maps_domain_error(monkeypatch, tmp_path: Path) -> None:
    """b28（AUDIT-#13）：终态收割 process.wait 超时→AiChatBridgeTimeoutError
    （错误形态 error_type 入 DOMAIN_ERROR_CODES 名义族——error_code 非 None；
    旧形态 TimeoutExpired 裸穿=error_code None 游离）。"""
    from fastapi import status as http_status

    from waterprint_server.main_lib import DOMAIN_ERROR_CODES

    zombie = _ZombieProcess([json.dumps({"type": "turn_summary", "session_id": "s"})])
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: zombie)
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    with pytest.raises(runner.AiChatBridgeTimeoutError, match="终态收割超时"):
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）
            payload, None, None)
    # 名义族接线：502=上游依赖失败族（与只读面 AiChatReadError 同码）
    assert DOMAIN_ERROR_CODES["AiChatBridgeTimeoutError"] == http_status.HTTP_502_BAD_GATEWAY


def test_cancel_wait_timeout_maps_domain_error(monkeypatch, tmp_path: Path) -> None:
    """b28（AUDIT-#13）三处之②：取消路径 terminate 后宽限 wait 超时→同款
    领域错误（R3 行边界取消协作面同收编）。"""
    zombie = _ZombieProcess([json.dumps({"type": "turn_start", "session_id": "s"})])
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: zombie)
    token = tmp_path / "t-1.cancel"  # 取消令牌=标记文件在场
    token.write_text("", encoding="utf-8")
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    with pytest.raises(runner.AiChatBridgeTimeoutError, match="终止宽限超时"):
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）
            payload, token, None)


def test_cleanup_wait_timeout_maps_domain_error(monkeypatch, tmp_path: Path) -> None:
    """b28（AUDIT-#13）三处之③：异常路径兜底收割 wait 超时→同款领域错误
    （kill 后仍不退的极端面——领域错误替换在途原异常上抛，raise from
    TimeoutExpired 保留收割失败因果链；本枝仅在异常在途时可达）。"""

    class _BrokenStdout:
        def __iter__(self):  # type: ignore[no-untyped-def]
            raise ValueError("stdout 通道断裂（注入）")

    class _BrokenPipeProcess(_ZombieProcess):
        def __init__(self) -> None:  # stdout 断裂在迭代首步（先于任何 wait）
            super().__init__([])
            self.stdout = _BrokenStdout()  # type: ignore[assignment]

    broken = _BrokenPipeProcess()
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: broken)
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    with pytest.raises(runner.AiChatBridgeTimeoutError, match="兜底收割超时") as caught:
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）
            payload, None, None)
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)  # 因果链在


class _StubbornAfterEof(_FakeProcess):
    """顽固子进程（reviewer b28 回炉实测形态）：kill 后 poll() 恒 None
    不退——旧码 finally 对其重复完整收割（4 wait/3 kill）且文案谎报已收割。"""

    def __init__(self, lines: list[str]) -> None:
        super().__init__(lines)
        self.wait_calls = 0
        self.kill_calls = 0

    def wait(self, timeout: float = 0) -> int:
        self.wait_calls += 1
        raise subprocess.TimeoutExpired(cmd="uv", timeout=timeout)

    def kill(self) -> None:
        self.kill_calls += 1  # 信号被吞——poll 仍 None（顽固面）

    def poll(self) -> int | None:
        return None


def test_stubborn_child_reap_no_reentry(monkeypatch, tmp_path: Path) -> None:
    """b28 回炉（reviewer major）：kill 后 poll 恒 None 的顽固进程——终态
    收割超时后 finally 不得重复完整收割（旧缺陷 4 wait/3 kill 占四个宽限
    窗且终报谎报"已 kill 收割"）；防重入后恰 2 wait（首收割+kill 后宽限
    各一）/1 kill，在途"终态收割"领域错误原样透传且文案如实未收割。"""
    stubborn = _StubbornAfterEof([json.dumps({"type": "turn_summary", "session_id": "s"})])
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: stubborn)
    payload = {**_BASE_PAYLOAD, "artifacts_dir": str(tmp_path)}
    with pytest.raises(runner.AiChatBridgeTimeoutError, match="终态收割超时") as caught:
        runner._run_ai_chat(  # noqa: SLF001  # runner 私有面直测（仿进程单测）
            payload, None, None)
    assert stubborn.wait_calls == 2  # 首收割 1+kill 后宽限 1——finally 零加窗
    assert stubborn.kill_calls == 1  # kill 单源——finally 不再补刀（旧形态 3 kill）
    message = str(caught.value)
    assert "已 kill 收割" not in message  # 未收割不谎报（旧文案失实）
    assert "未收割" in message  # 文案如实指认 kill 后进程未退


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


def test_bridge_command_uses_repo_root(monkeypatch, tmp_path: Path) -> None:
    """P0-C 回归锚：桥命令 --directory=repo_root/agent（非 data_dir/agent）。"""
    captured: dict[str, Any] = {}

    def _capture_popen(command: list[str], **kwargs: Any) -> _FakeProcess:
        captured["command"] = command
        return _FakeProcess(
            [json.dumps({"type": "turn_summary", "session_id": "s", "truncated": False})]
        )

    monkeypatch.setattr(runner.subprocess, "Popen", _capture_popen)
    repo_root = tmp_path / "repo"
    data_dir = repo_root / "data"
    payload = {
        **_BASE_PAYLOAD,
        "repo_root": str(repo_root),
        "data_dir": str(data_dir),
        "artifacts_dir": str(tmp_path),
    }
    result = runner._run_ai_chat(payload, None, None)  # noqa: SLF001  # 桥命令构造面直测
    assert result["state"] == "done"
    command = captured["command"]
    assert str(repo_root / "agent") in command
    assert str(data_dir) not in command  # data_dir 不得再冒充仓库根


def test_missing_repo_root_contract_error(monkeypatch, tmp_path: Path) -> None:
    """P0-C 契约：缺 repo_root 键=fail-fast 显式报错（防第三处静默错位）。"""
    _patch_spawn(monkeypatch, [])
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "repo_root"}
    payload["artifacts_dir"] = str(tmp_path)
    with pytest.raises(RuntimeError, match="repo_root"):
        runner._run_ai_chat(payload, None, None)  # noqa: SLF001  # 契约面直测
