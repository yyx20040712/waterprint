"""SSE 限流镜像测试（B6 批：四维限流+心跳帧+断开回收+旋钮面）。

输入:  waterprint_server.sse_limits / routers.events / jobs.manager 公开符号
输出:  限流契约断言（低阈值旋钮验证逻辑——D9 必改3：不真实挂满 100 连接）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 批 2026-09-06，简报 D9 八例）
#   ①全局上限命中→429+统一错误体+Retry-After（旋钮调低 3）
#   ②每任务上限→超限 RateLimitedError（低阈 2——端点直调面）
#   ③每项目上限→429（低阈 2）
#   ④断开释放→计数回收→新连接放行（终态流耗尽即回收实证）
#   ⑤鉴权关下身份无关维度全额生效（api_token="" 显式态）
#   ⑥建立速率超桶→429、桶内放行（低 rate 旋钮；过闸后置 404=放行证）
#   ⑦心跳帧格式（短间隔 0.1s 断言 comment 行出现在流中）
#   ⑧旋钮默认值+None=关闭回退+<1 fail fast（配置值生效单列）
# 挂流形态：ASGITransport 体缓冲=项目流（无限订阅）后台 create_task
#   挂起即持占位；终态任务流=有限体可整读（回收断言载体）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from pydantic import ValidationError
from starlette.requests import Request

from waterprint_server.jobs.manager import Manager, TaskRequest
from waterprint_server.main import create_app
from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import create_project
from waterprint_server.settings import Settings, ensure_directories
from waterprint_server.sse_limits import RateLimitedError, SseLimiter

_mod = importlib.import_module("waterprint_server.routers.events")
_sse = importlib.import_module("waterprint_server.sse_limits")

_TERMINAL = {"done", "failed", "cancelled"}


@asynccontextmanager
async def _client_with(
    test_settings: Settings, **knobs: int | str | None
) -> AsyncIterator[httpx.AsyncClient]:
    """旋钮覆写版 client（conftest client 同构——model_copy 免重校验自担面）。"""
    settings = test_settings.model_copy(update=dict(knobs))
    executor = ThreadPoolExecutor(max_workers=test_settings.calc_workers)
    application = create_app(settings, executor=executor)
    try:
        async with application.router.lifespan_context(application):
            transport = httpx.ASGITransport(app=application)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                yield client
    finally:
        executor.shutdown(wait=True)


async def _create_project(client: httpx.AsyncClient, cass_payload: dict[str, object]) -> str:
    """建项目（项目流挂接载体——test_events 同款）。"""
    created = await client.post("/api/projects", json={"project": cass_payload})
    return str(created.json()["project_id"])


async def _hold_streams(
    client: httpx.AsyncClient, url: str, count: int
) -> list[asyncio.Task[httpx.Response]]:
    """后台挂起 N 条无限流（建连完成即占位——ASGITransport 体缓冲挂起态）。"""
    tasks = [asyncio.create_task(client.get(url)) for _ in range(count)]
    await asyncio.sleep(0.2)  # 端点体 reserve 收尾窗口
    return tasks


async def _release_streams(tasks: list[asyncio.Task[httpx.Response]]) -> None:
    """断开挂起流（cancel→ASGI 协程取消→generator finally 释放占位）。"""
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(0.2)  # 释放传播窗口


def _scope(ctx: ServiceContext, path: str) -> dict[str, Any]:
    """端点直调 scope（test_events 直调同款——绕路由/依赖，触端点体 reserve）。"""
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "app": SimpleNamespace(state=SimpleNamespace(ctx=ctx)),
    }


def _limiter(**knobs: int | None) -> SseLimiter:
    """四维旋钮直构（None 维不启用——直调面装配束专用）。"""
    return SseLimiter(
        max_connections=knobs.get("max_connections"),
        max_subscribers_per_task=knobs.get("max_subscribers_per_task"),
        max_subscribers_per_project=knobs.get("max_subscribers_per_project"),
        connect_rate_per_second=knobs.get("connect_rate_per_second"),
    )


@pytest.mark.anyio
async def test_global_cap_429_with_error_body_and_retry_after(
    test_settings: Settings, cass_payload: dict[str, object]
) -> None:
    """①：全局上限（低阈 3）→第 4 连接 429+统一错误体+Retry-After 头。"""
    async with _client_with(test_settings, sse_max_connections=3) as client:
        project_id = await _create_project(client, cass_payload)
        url = f"/api/events/projects/{project_id}"
        held = await _hold_streams(client, url, 3)
        try:
            extra = await client.get(url)
            assert extra.status_code == 429
            body = extra.json()
            assert body["error_type"] == "RateLimitedError"  # 统一错误体（N-3 口径）
            assert "全局连接数已达上限" in body["detail"]
            assert int(extra.headers["Retry-After"]) >= 1  # 建议性头（D5）
        finally:
            await _release_streams(held)


@pytest.mark.anyio
async def test_per_task_cap_raises_on_third_subscriber(
    service_ctx: ServiceContext,
) -> None:
    """②：每任务上限（低阈 2）→第 3 订阅 reserve 抛 RateLimitedError（端点直调面）。"""
    handle = await service_ctx.manager.submit(
        TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p"})
    )
    ctx = ServiceContext(
        settings=service_ctx.settings,
        manager=service_ctx.manager,
        sse_limiter=_limiter(max_subscribers_per_task=2),
    )
    path = f"/api/events/tasks/{handle.task_id}"
    first = await _mod.task_events(task_id=handle.task_id, request=Request(_scope(ctx, path)))
    second = await _mod.task_events(task_id=handle.task_id, request=Request(_scope(ctx, path)))
    assert first.status_code == 200 and second.status_code == 200  # 阈内放行
    with pytest.raises(RateLimitedError):  # 第 3 订阅超阈（check+add 临界区）
        await _mod.task_events(task_id=handle.task_id, request=Request(_scope(ctx, path)))


@pytest.mark.anyio
async def test_per_project_cap_429(
    test_settings: Settings, cass_payload: dict[str, object]
) -> None:
    """③：每项目上限（低阈 2，全局默认 100 不扰）→第 3 连接 429（端点体面）。"""
    async with _client_with(test_settings, sse_max_subscribers_per_project=2) as client:
        project_id = await _create_project(client, cass_payload)
        url = f"/api/events/projects/{project_id}"
        held = await _hold_streams(client, url, 2)
        try:
            extra = await client.get(url)
            assert extra.status_code == 429
            body = extra.json()
            assert body["error_type"] == "RateLimitedError"
            assert "每项目订阅数已达上限" in body["detail"]
        finally:
            await _release_streams(held)


@pytest.mark.anyio
async def test_disconnect_releases_slot_for_new_connection(
    service_ctx: ServiceContext, test_settings: Settings
) -> None:
    """④：断开释放→计数回收→新连接放行（终态流耗尽即回收——直调整读实证）。"""
    handle = await service_ctx.manager.submit(
        TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p"})
    )
    for _ in range(100):  # 合成载荷快速失败亦合法（test_events 先例）——终态即可
        if service_ctx.manager.status(handle.task_id).state in _TERMINAL:
            break
        await asyncio.sleep(0.05)
    ctx = ServiceContext(
        settings=service_ctx.settings,
        manager=service_ctx.manager,
        sse_limiter=_limiter(max_connections=1),
    )
    path = f"/api/events/tasks/{handle.task_id}"
    first = await _mod.task_events(task_id=handle.task_id, request=Request(_scope(ctx, path)))
    chunks = [chunk async for chunk in first.body_iterator]  # 终态快照一条即收→finally 释放
    assert chunks and "event: state" in chunks[0]
    second = await _mod.task_events(task_id=handle.task_id, request=Request(_scope(ctx, path)))
    assert second.status_code == 200  # 回收后新连接放行（全局占位重新可用）
    with pytest.raises(RateLimitedError):  # cap=1 再占即满（回收后计数正确非清零失效）
        await _mod.task_events(task_id=handle.task_id, request=Request(_scope(ctx, path)))
    _ = test_settings  # 装配束真源（settings.manager 共享——显式引用可读性）


@pytest.mark.anyio
async def test_limits_active_when_auth_disabled(
    test_settings: Settings, cass_payload: dict[str, object]
) -> None:
    """⑤：鉴权关（api_token=""）下四维身份无关全额生效（D2——匿名不绕闸）。"""
    async with _client_with(test_settings, api_token="", sse_max_connections=2) as client:
        project_id = await _create_project(client, cass_payload)
        url = f"/api/events/projects/{project_id}"
        held = await _hold_streams(client, url, 2)
        try:
            extra = await client.get(url)  # 无任何凭证（匿名）
            assert extra.status_code == 429
            assert extra.json()["error_type"] == "RateLimitedError"
        finally:
            await _release_streams(held)


@pytest.mark.anyio
async def test_connect_rate_bucket_429_within_burst_pass(
    test_settings: Settings,
) -> None:
    """⑥：建连速率超桶→429；桶内放行（低 rate=1→突发 2；过闸后置 404=放行证）。"""
    async with _client_with(test_settings, sse_connect_rate_per_second=1) as client:
        url = "/api/events/tasks/ghost-task-rate"  # 幽灵任务：过闸后 404（不占订阅面）
        first = await client.get(url)
        second = await client.get(url)
        third = await client.get(url)
        assert first.status_code == 404 and second.status_code == 404  # 桶内放行
        assert third.status_code == 429  # 桶空（突发 2 耗尽）
        body = third.json()
        assert body["error_type"] == "RateLimitedError"
        assert "建连速率超限" in body["detail"]
        assert int(third.headers["Retry-After"]) >= 1


@pytest.mark.anyio
async def test_heartbeat_comment_frame_in_stream(
    service_ctx: ServiceContext, test_settings: Settings
) -> None:
    """⑦：心跳帧格式（0.1s 短间隔——静默项目流首帧即 ': keepalive\\n\\n'）。"""
    _ = service_ctx  # fixture 建 Manager（无心跳）——本例自建心跳 Manager 对照
    ensure_directories(test_settings)
    executor = ThreadPoolExecutor(max_workers=1)
    manager = Manager(
        executor,
        cancel_dir=test_settings.exports_dir / "tasks" / "cancel",
        loop=asyncio.get_running_loop(),
        max_concurrent=1,
        sse_heartbeat_seconds=0.1,
    )
    manager.start()
    try:
        ctx = ServiceContext(settings=test_settings, manager=manager)
        outcome = create_project(ctx, {"project": None})
        response = await _mod.project_events(
            project_id=outcome.project_id,
            request=Request(_scope(ctx, f"/api/events/projects/{outcome.project_id}")),
        )
        frame = await asyncio.wait_for(response.body_iterator.__anext__(), timeout=10)
        assert frame == ": keepalive\n\n"  # SSE 规范 comment 行（EventSource 忽略）
        assert frame.startswith(":") and "\n\n" in frame
        await response.body_iterator.aclose()
    finally:
        await manager.shutdown(1.0)
        executor.shutdown(wait=True)


def test_knob_defaults_none_escape_and_fail_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """⑧：五旋钮默认值精确断言+None=关闭回退+<1 fail fast（配置值生效单列）。"""
    for name in (
        "SSE_MAX_CONNECTIONS",
        "SSE_MAX_SUBSCRIBERS_PER_TASK",
        "SSE_MAX_SUBSCRIBERS_PER_PROJECT",
        "SSE_CONNECT_RATE_PER_SECOND",
        "SSE_HEARTBEAT_SECONDS",
    ):
        monkeypatch.delenv(f"WATERPRINT_{name}", raising=False)
    defaults = Settings(_env_file=None)
    assert defaults.sse_max_connections == 100
    assert defaults.sse_max_subscribers_per_task == 5
    assert defaults.sse_max_subscribers_per_project == 10
    assert defaults.sse_connect_rate_per_second == 10
    assert defaults.sse_heartbeat_seconds == 30
    knobs = (
        "sse_max_connections",
        "sse_max_subscribers_per_task",
        "sse_max_subscribers_per_project",
        "sse_connect_rate_per_second",
        "sse_heartbeat_seconds",
    )
    off = defaults.model_copy(update=dict.fromkeys(knobs))
    limiter = _sse.SseLimiter.from_settings(off)  # type: ignore[arg-type]
    for index in range(50):  # None=四维全关（逃生门回退——远超默认阈不拒）
        limiter.check_connect()
        limiter.reserve_task(f"t{index}")
        limiter.reserve_project(f"p{index}")
    with pytest.raises(ValidationError):  # 心跳 0=热循环（fail fast）
        Settings(_env_file=None, sse_heartbeat_seconds=0)
    with pytest.raises(ValidationError):  # 全局阈 0=闸死（fail fast）
        Settings(_env_file=None, sse_max_connections=0)
