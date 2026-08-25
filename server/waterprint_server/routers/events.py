"""SSE 进度端点：任务进度与状态事件流（每客户端独立流）。

输入:  任务订阅（task_id / 项目全局通道）
输出:  text/event-stream（进度/状态/stale 通知事件）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_events.py）
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
#
# 【测试要求】事件格式、断连清理、背压丢弃语义、X-Accel 头存在。
#
# 【参照】重写计划 §12.2/§11 R5/§17.3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from waterprint_server.services import ServiceContext

router = APIRouter(prefix="/api/events", tags=["events"])

# R2：反代缓冲对策头（nginx X-Accel-Buffering 禁缓冲——chunked 直通）。
_SSE_HEADERS = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


def _stream(source: AsyncIterator[Any]) -> AsyncIterator[str]:
    """事件 JSON 化（R1：data: 单行 JSON——type/task_id/percent/message）。"""
    async def generated() -> AsyncIterator[str]:
        async for event in source:
            payload = asdict(event)  # Event dataclass（routers 不直连 jobs 类型面——Any 桥接）
            yield f"event: {payload['type']}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return generated()


@router.get("/tasks/{task_id}")
async def task_events(task_id: str, request: Request) -> StreamingResponse:
    """单任务进度流（每连接独立；断线清理在 manager.events finally）。"""
    return StreamingResponse(
        _stream(_ctx(request).manager.events(task_id)),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.get("/projects/{project_id}")
async def project_events(project_id: str, request: Request) -> StreamingResponse:
    """项目事件流（stale 通知/任务完成——连接即当前，不重放历史）。"""
    return StreamingResponse(
        _stream(_ctx(request).manager.project_events(project_id)),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
