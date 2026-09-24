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


def test_child_env_overrides_only_nonempty() -> None:
    """env 覆盖面：空键不覆盖（os.environ 原样）——三键非空才注入。"""
    from waterprint_server.jobs.ai_chat import _child_env

    env = _child_env("http://x/v1", "", "m-1", 0)
    assert env["WATERPRINT_AI_BASE_URL"] == "http://x/v1"
    assert env["WATERPRINT_AI_MODEL"] == "m-1"
    assert "WATERPRINT_AI_API_KEY" not in env or env["WATERPRINT_AI_API_KEY"] != ""
    assert "WATERPRINT_AI_LLM_TIMEOUT_S" not in env or env["WATERPRINT_AI_LLM_TIMEOUT_S"] != "0"
