"""ai_chat 服务镜像测试：只读面域异常+提交载荷+纯 helper（B4-4b 子批 2 TDD）。

输入:  service_ctx（真 Manager）+monkeypatch（which→None 防真子进程）
输出:  提交句柄 kind/幂等/ID 分量拒绝/阶段标签/env 覆盖断言
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint_server.services import ai_chat as chat_service
from waterprint_server.services.ai_chat import AiChatReadError

pytestmark = [pytest.mark.anyio]


async def test_readonly_agent_cli_unavailable(service_ctx, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """只读面：agent CLI 不可达（临时 data_dir 无 agent 目录）→AiChatReadError。"""
    with pytest.raises(AiChatReadError, match="agent CLI"):
        chat_service.list_sessions(service_ctx)
    with pytest.raises(AiChatReadError, match="agent CLI"):
        chat_service.read_history(service_ctx, "s1")


async def test_readonly_bad_session_id_rejected(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """历史面 ID 分量校验：路径注入拒（422 面由 router 映射——此处 ValueError）。"""
    with pytest.raises(ValueError):
        chat_service.read_history(service_ctx, "../escape")



def test_list_sessions_parses_agent_output(monkeypatch) -> None:
    """只读面解析：agent CLI stdout JSON 数组→清单投影（仿子过程）。"""
    monkeypatch.setattr(
        chat_service, "_run_readonly",
        lambda ctx, *args: '[{"session_id": "s1", "title": "演示", "turns": 2}]' + chr(10),
    )
    items = chat_service.list_sessions(service_ctx_stub())  # type: ignore[no-untyped-call]
    assert items == [{"session_id": "s1", "title": "演示", "turns": 2}]


def test_list_sessions_malformed_rejected(monkeypatch) -> None:
    """只读面防御：非 JSON 输出→AiChatReadError（不编造清单）。"""
    monkeypatch.setattr(chat_service, "_run_readonly", lambda ctx, *args: "oops")
    with pytest.raises(AiChatReadError, match="解析失败"):
        chat_service.list_sessions(service_ctx_stub())  # type: ignore[no-untyped-call]


def test_read_history_tolerates_bad_lines(monkeypatch) -> None:
    """历史面容错：JSONL 非法行跳过+空行跳过（append-only 半行窗口）。"""
    monkeypatch.setattr(
        chat_service, "_run_readonly",
        lambda ctx, *args: (
            '{"role": "user", "text": "hi", "turn": 1}' + chr(10) + chr(10) + "bad" + chr(10)
        ),
    )
    items = chat_service.read_history(service_ctx_stub(), "sess-ok")  # type: ignore[no-untyped-call]
    assert items == [{"role": "user", "text": "hi", "turn": 1}]


def test_readonly_subprocess_timeout(monkeypatch) -> None:
    """R2：子过程超时→AiChatReadError（20s wall 上限族）。"""
    import subprocess as _sp

    def _slow(command, **kwargs):
        raise _sp.TimeoutExpired(cmd="x", timeout=1)

    monkeypatch.setattr(
        chat_service, "_agent_cli_command", lambda ctx, *args: ["uv", "--version"]
    )
    monkeypatch.setattr(chat_service.subprocess, "run", _slow)
    with pytest.raises(AiChatReadError, match="超时"):
        chat_service._run_readonly(  # noqa: SLF001  # 只读面私有直测（仿子过程）
            service_ctx_stub(), "--list-sessions"
        )  # type: ignore[no-untyped-call]


def service_ctx_stub():
    """最小 ctx 桩（只读面测试不触 Manager——settings 面足够）。"""
    from waterprint_server.services import ServiceContext
    from waterprint_server.settings import Settings

    return ServiceContext.__new__(ServiceContext)  # 测试桩：只读面仅用 settings 属性



async def test_submit_returns_task_handle(service_ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """提交正门：kind=ai_chat 任务句柄（runner 假 uv 缺失=快速失败，不 spawn）。"""
    monkeypatch.setattr("waterprint_server.jobs.ai_chat.which", lambda name: None)
    handle = await chat_service.submit_ai_chat_turn(service_ctx, "sess-1", "建一座污水厂")
    assert handle.task_id
    status = service_ctx.manager.status(handle.task_id)
    assert status.kind == "ai_chat"
    assert status.state in {"queued", "running", "done", "failed"}


async def test_submit_repeat_message_new_task(service_ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """门一 W3-d1：同会话同消息重发=新任务（「继续/重算」不得被同指纹幂等吞没）。"""
    monkeypatch.setattr("waterprint_server.jobs.ai_chat.which", lambda name: None)
    first = await chat_service.submit_ai_chat_turn(service_ctx, "sess-2", "计算一下")
    second = await chat_service.submit_ai_chat_turn(service_ctx, "sess-2", "计算一下")
    assert first.task_id != second.task_id


async def test_submit_payload_carries_settings(service_ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """R3 载荷面：settings 三键+超时透传（worker env 注入素材）。"""
    captured: dict[str, object] = {}
    real_submit = service_ctx.manager.submit

    async def spy_submit(request, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(dict(request.payload))
        return await real_submit(request, **kwargs)  # type: ignore[misc]

    monkeypatch.setattr(service_ctx.manager, "submit", spy_submit)
    monkeypatch.setattr("waterprint_server.jobs.ai_chat.which", lambda name: None)
    from waterprint_server.services import ServiceContext

    tuned = service_ctx.settings.model_copy(
        update={"ai_base_url": "http://example/v1", "ai_model": "neutral-name",
                "ai_api_key": "sk-secret-material"}
    )
    tuned_ctx = ServiceContext(settings=tuned, manager=service_ctx.manager)
    await chat_service.submit_ai_chat_turn(tuned_ctx, "sess-3", "话术")
    assert captured["kind"] == "ai_chat"
    assert captured["session_id"] == "sess-3"
    # 门一 W1-k2：三键禁经载荷（registry 落盘面=密钥落盘）——env 单通道
    assert "ai_api_key" not in captured
    assert "ai_base_url" not in captured
    assert "ai_model" not in captured


def test_stage_labels_neutral() -> None:
    """阶段标签面：事件→中文标签（零数据零密钥——日志安全面）。"""
    assert chat_service is not None  # 模块在位（标签函数在 jobs 面，服务面只读断言）
    from waterprint_server.jobs.ai_chat import _stage_label

    assert _stage_label({"type": "turn_start"}) == "对话开始"
    assert _stage_label({"type": "tool_start", "name": "wp_run_calc"}) == "调用工具 wp_run_calc"
    assert (
        _stage_label({"type": "tool_result", "name": "wp_run_calc", "ok": False})
        == "工具失败 wp_run_calc"
    )
    assert _stage_label({"type": "fallback"}) == "降级模式"
    assert _stage_label({"type": "unknown"}) == "对话进行中"


def test_child_env_is_os_environ_copy(monkeypatch) -> None:
    """env 单通道（门一 W1-k2）：子进程 env=os.environ 快照（三键经 main
    setdefault 归一化注入——载荷禁携密钥的运行面闭合）。"""
    from waterprint_server.jobs.ai_chat import _child_env

    monkeypatch.setenv("WATERPRINT_AI_BASE_URL", "http://x/v1")
    monkeypatch.setenv("WATERPRINT_AI_MODEL", "m-1")
    env = _child_env()
    assert env["WATERPRINT_AI_BASE_URL"] == "http://x/v1"
    assert env["WATERPRINT_AI_MODEL"] == "m-1"
