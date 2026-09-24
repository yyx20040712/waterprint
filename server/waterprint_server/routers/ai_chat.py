"""对话 pane 中继端点（B4-4b 子批 2）：会话清单/历史/发言三面。

输入:  HTTP（会话 ID/消息文本——Bearer 鉴权层覆盖）
输出:  会话清单 JSON/历史 JSONL 语义数组/TaskIdResponse（对话轮异步任务）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 2 2026-09-24；镜像测试 server/tests/routers/test_ai_chat.py）
#
# 【端点集】
#   GET  /api/ai/sessions                      会话清单（agent CLI 子进程读）
#   GET  /api/ai/sessions/{session_id}/messages 会话历史（同上）
#   POST /api/ai/sessions/{session_id}/messages 发言→ai_chat 任务（task_id
#                                              经既有任务端点族+SSE 消费）
#
# 【行为规格】
#   R1 薄协议转换（routers 禁业务——只读/提交全在 services）。
#   R2 只读面 502：AiChatReadError（子进程超时/退出码）映射 502（上游
#      依赖失败——非本服务缺陷）；分量校验 ValueError→422。
#   R3 同步 def 端点（只读两面）——FastAPI 线程池承载（子进程阻塞不让
#      事件环饿死）；POST 为 async（manager.submit await）。
# 【禁止事项】禁解析会话文件；禁对话逻辑入 router。
# 【测试要求】三端点形态+502/422 映射+任务句柄 kind。
# 【参照】.workflow/b4-4b/design-final.md §四
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from waterprint_server.routers.calc import TaskIdResponse, _ctx
from waterprint_server.services import ai_chat as chat_service
from waterprint_server.services.ai_chat import AiChatReadError

router = APIRouter(prefix="/api/ai", tags=["ai-chat"])


class ChatMessageIn(BaseModel):
    """发言请求（消息非空——空白话术无语义）。"""

    message: str = Field(min_length=1)


class ChatSessionSummary(BaseModel):
    """会话清单项（agent CLI 投影原样——字段面跟随上游演进）。"""

    session_id: str
    title: str = ""
    created_at: str = ""
    project_id: str | None = None
    turns: int = 0


class ChatHistoryMessage(BaseModel):
    """历史消息项（role/text/turn/truncated/tool_steps 五键投影）。"""

    role: str
    text: str
    turn: int = 0
    truncated: bool = False
    tool_steps: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/sessions", response_model=list[ChatSessionSummary])
def list_sessions(request: Request) -> list[ChatSessionSummary]:
    """会话清单（同步 def——线程池承载子进程阻塞）。"""
    try:
        return [ChatSessionSummary(**item) for item in chat_service.list_sessions(_ctx(request))]
    except AiChatReadError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/messages", response_model=list[ChatHistoryMessage])
def read_messages(session_id: str, request: Request) -> list[ChatHistoryMessage]:
    """会话历史（R2——ID 分量校验 422 面）。"""
    try:
        items = chat_service.read_history(_ctx(request), session_id)
    except AiChatReadError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return [ChatHistoryMessage(**item) for item in items]


@router.post("/sessions/{session_id}/messages", response_model=TaskIdResponse)
async def send_message(session_id: str, body: ChatMessageIn, request: Request) -> TaskIdResponse:
    """发言（异步对话轮——task_id 走既有任务端点族+SSE）。"""
    try:
        handle = await chat_service.submit_ai_chat_turn(_ctx(request), session_id, body.message)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return TaskIdResponse(task_id=handle.task_id)
