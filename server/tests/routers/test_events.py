"""events 路由镜像测试：SSE 端点（响应头、断连清理、背压）。

输入:  waterprint_server.routers.events 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import asyncio
import importlib
from types import SimpleNamespace

import pytest
from starlette.requests import Request

_mod = importlib.import_module("waterprint_server.routers.events")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.events（服务层 M2）",
    ),
]

_EXPECTED = {
    ("get", "/api/events/tasks/{task_id}"),
    ("get", "/api/events/projects/{project_id}"),
}


def test_router_exposes_two_streams_wiring() -> None:
    """端点集 == 规格两件（tasks/{id} 与 projects/{id}）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed == _EXPECTED  # 恰两件无漂移


@pytest.mark.anyio
async def test_sse_headers_present_wiring(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：SSE 响应头 X-Accel-Buffering: no（§11 R5 反代缓冲对策）。

    tasks 流经终态任务（有限流：连接即当前快照一条即收——R3 不重放）；
    ASGITransport 不做增量流转发（体缓冲实测挂起），项目通道头经端点
    直调断言（test_project_stream_headers_and_disconnect_wiring）。
    """
    created = await client.post("/api/projects", json={"project": cass_payload})
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": []}
    )).json()["task_id"]
    for _ in range(300):  # 先到终态（流=单事件有限体）
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.1)
    response = await client.get(f"/api/events/tasks/{task_id}")
    assert response.status_code == 200
    assert response.headers["x-accel-buffering"] == "no"  # 反代缓冲对策头
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: state" in response.text  # 事件格式（JSON 化 data 行）
    assert task_id in response.text


@pytest.mark.anyio
async def test_project_stream_headers_and_disconnect_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R1/R2 镜像缺失收口：项目通道 SSE 头（端点直调）+ 断连订阅释放。"""
    from waterprint_server.jobs.manager import TaskRequest

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "method": "GET",
        "path": "/api/events/projects/p",
        "headers": [],
        "query_string": b"",
        "app": SimpleNamespace(state=SimpleNamespace(ctx=service_ctx)),
    }
    response = await _mod.project_events(project_id="p", request=Request(scope))
    assert response.headers["x-accel-buffering"] == "no"  # 项目通道同款头（R2）
    assert response.media_type == "text/event-stream"

    handle = await service_ctx.manager.submit(
        TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p"})
    )
    stream = service_ctx.manager.events(handle.task_id)
    first = await anext(stream)  # 订阅建立（queued 状态事件）
    assert first.task_id == handle.task_id
    record = service_ctx.manager._tasks[handle.task_id]  # noqa: SLF001  # 泄漏断言面
    assert len(record.subscribers) == 1  # 在册
    await stream.aclose()  # 客户端断连
    assert len(record.subscribers) == 0  # 订阅释放（finally 清理——无泄漏句柄）
    await asyncio.sleep(0.2)  # 环内收尾（断连不扰状态机——合成载荷快速失败亦合法）
    final = service_ctx.manager.status(handle.task_id)
    assert final.state in {"queued", "running", "failed", "cancelled"}
    assert len(record.subscribers) == 0  # 终态迁移后仍无残留订阅（无泄漏句柄）
