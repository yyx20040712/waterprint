"""ai_chat 路由镜像测试：三端点形态+502/422 映射（B4-4b 子批 2 TDD；
b28 AUDIT-#11 收编统一映射——错误体带 error_type 的有意变化钉面）。

输入:  /api/ai/sessions 三端点（client fixture——临时 Settings 无 agent 目录）
输出:  清单/历史 502（CLI 不可达）+坏 ID 422+发言 200 task_id——
      502/422 错误体经 main_lib 统一 handler 生成（error_type 在场）
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.anyio]


async def test_list_sessions_unreachable_502(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """R2 只读面 502：agent CLI 不可达（临时 data_dir 无 agent 目录）。

    b28（AUDIT-#11）：直抛 HTTPException 收编——错误体经统一映射 handler
    生成（error_type=AiChatReadError；状态码 502 不变，旧体无 error_type 键）。
    """
    response = await client.get("/api/ai/sessions")
    assert response.status_code == 502
    assert "agent CLI" in response.json()["detail"]
    assert response.json()["error_type"] == "AiChatReadError"  # b28 统一错误体


async def test_history_bad_id_422(client) -> None:  # type: ignore[no-untyped-def]
    """R2 分量校验：路径注入 ID → 422（先于子进程调用；经 main_lib
    ValueError 兜底行统一翻译——b28 双轨归一）。"""
    response = await client.get("/api/ai/sessions/bad%24id/messages")  # $ 非法分量字符
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValueError"  # b28 统一错误体


async def test_send_message_returns_task_id(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """发言面：200+task_id（runner 假 uv 缺失=快速失败，不 spawn 真子进程）。"""
    monkeypatch.setattr("waterprint_server.jobs.ai_chat.which", lambda name: None)
    response = await client.post(
        "/api/ai/sessions/sess-router/messages", json={"message": "建一座污水厂"}
    )
    assert response.status_code == 200
    assert response.json()["task_id"]


async def test_send_message_blank_rejected(client) -> None:  # type: ignore[no-untyped-def]
    """发言面：空消息 422（pydantic min_length——空白话术无语义）。"""
    response = await client.post("/api/ai/sessions/sess-router/messages", json={"message": ""})
    assert response.status_code == 422


async def test_send_message_bad_session_id_422(client) -> None:  # type: ignore[no-untyped-def]
    """b28（AUDIT-#11）：发言面坏会话 ID→422 经 main_lib ValueError 兜底行
    统一翻译（原路由级 except ValueError 直抛收编——状态码不变、错误体
    带 error_type）。"""
    response = await client.post(
        "/api/ai/sessions/bad%24id/messages", json={"message": "建一座污水厂"}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValueError"


async def test_ai_chat_endpoints_in_openapi(client) -> None:  # type: ignore[no-untyped-def]
    """契约面：三端点入 OpenAPI（37→40 破面锚——契约测试计数在锁面另断言）。"""
    schema = (await client.get("/openapi.json")).json()
    paths = schema["paths"]
    assert "/api/ai/sessions" in paths
    assert "/api/ai/sessions/{session_id}/messages" in paths
    assert set(paths["/api/ai/sessions/{session_id}/messages"]) == {"get", "post"}
