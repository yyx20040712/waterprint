"""SSE 进度端点：任务进度与状态事件流（每客户端独立流）。

输入:  任务订阅（task_id / 项目全局通道）
输出:  text/event-stream（进度/状态/stale 通知事件+keepalive 心跳行）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_events.py+
#   test_sse_limits.py〔B6〕）
#
# 【端点集（v1 冻结）】
#   GET /api/events/tasks/{task_id}      单任务进度流
#   GET /api/events/projects/{id}        项目事件流（stale 通知/任务完成）
#
# 【行为规格】
#   R1 数据通路：进程池 worker → 进度队列 → asyncio 桥接 → SSE
#      （§12.2）；事件 JSON 化（{type, task_id, percent, message,
#      condition_key}）。
#   R2 反代缓冲对策：响应头 X-Accel-Buffering: no + chunked
#      （§11 R5）；断线客户端清理（订阅释放，无泄漏句柄）。
#   R3 无跨客户端状态：每连接独立流（§17.3）；事件不重放历史
#      （连接即当前），状态查询走 tasks 端点。
#   R4 背压：客户端不消费 → 丢弃最旧进度事件（保序最新状态），
#      状态变更事件不丢。
#   R5 心跳（B6 D6，两端点统一）：订阅流静默超 sse_heartbeat_seconds
#      → manager yield None 哨兵 → 本层映射 ": keepalive\n\n"（SSE 规范
#      comment 行——EventSource 忽略，webapp 零改；计时点在 queue.get=
#      取消安全点）；None=关。nginx 300s 读超时静默掐断由此消除。
#   R6 限流占位（B6 D3/D4）：订阅占位 reserve_* 在端点体返回前（响应
#      未 start——超限 429 可干净送达）；断开回收 release_* 在 _stream
#      finally；建连闸 sse_connect_gate 由 main include 级依赖序挂载于
#      verify_token_sse 之前（D3 必改1——401 风暴前置压制）。
#   R7 端点 docstring 冻结：两函数 docstring 逐字进 openapi description
#      （字节 sha 锁）——行为注记只写本规格头，不动函数 docstring。
#
# 【测试要求】事件格式、断连清理、背压丢弃语义、X-Accel 头存在
#   （test_events.py）；限流四维/心跳帧格式/断开回收（test_sse_limits.py）。
#
# 【参照】重写计划 §12.2/§11 R5/§17.3；.workflow/briefs/task-B6-brief.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import read_project
from waterprint_server.settings import validate_component

router = APIRouter(prefix="/api/events", tags=["events"])

# R2：反代缓冲对策头（nginx X-Accel-Buffering 禁缓冲——chunked 直通）。
_SSE_HEADERS = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


async def sse_connect_gate(request: Request) -> None:
    """B6 D3 必改1 建连闸：速率令牌+全局阈探测（main include 级依赖序
    首位——先于 verify_token_sse；零路径参=openapi 零波面）。"""
    limiter = _ctx(request).sse_limiter
    if limiter is not None:
        limiter.check_connect()


def _stream(
    source: AsyncIterator[Any], *, release: Callable[[], None] | None = None
) -> AsyncIterator[str]:
    """事件 JSON 化（R1）+心跳 comment 行映射（R5）+断开计数回收（R6）。"""
    async def generated() -> AsyncIterator[str]:
        try:
            async for event in source:
                if event is None:  # manager 静默超时哨兵（B6 D6 心跳）
                    yield ": keepalive\n\n"
                    continue
                payload = asdict(event)  # Event dataclass（routers 不直连 jobs 类型面——Any 桥接）
                yield f"event: {payload['type']}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            if release is not None:  # 连接关闭=限流占位回收（B6 D4）
                release()

    return generated()


@router.get("/tasks/{task_id}")
async def task_events(task_id: str, request: Request) -> StreamingResponse:
    """单任务进度流（每连接独立；断线清理在 manager.events finally）。

    AUDIT2 I-2：开流前置探测（原静默 200 空流挂起——与 GET tasks 404
    口径不一致，AU-1 矩阵偏差全集中本对端点）：分量校验（ValueError→
    422，与 projects 路径分量面同源）+注册表探测（UnknownTaskError→
    404）。任务在提交响应返回前即同步在册——正常订阅序不受扰。
    """
    validate_component(task_id)
    ctx = _ctx(request)
    ctx.manager.status(task_id)  # 未知任务=UnknownTaskError（404 面）
    limiter = ctx.sse_limiter
    if limiter is not None:
        limiter.reserve_task(task_id)  # B6 D4：全局+每任务 check+add 同步临界区
    return StreamingResponse(
        _stream(
            ctx.manager.events(task_id),
            release=None if limiter is None else lambda: limiter.release_task(task_id),
        ),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/projects/{project_id}")
async def project_events(project_id: str, request: Request) -> StreamingResponse:
    """项目事件流（stale 通知/任务完成——连接即当前，不重放历史）。

    AUDIT2 I-2：同 task 流前置探测——分量校验 422+项目存在性 404。
    """
    validate_component(project_id)
    ctx = _ctx(request)
    read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    limiter = ctx.sse_limiter
    if limiter is not None:
        limiter.reserve_project(project_id)
    return StreamingResponse(
        _stream(
            ctx.manager.project_events(project_id),
            release=None if limiter is None else lambda: limiter.release_project(project_id),
        ),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
