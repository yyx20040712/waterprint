"""方案联合枚举端点：多单元寻优新正门（ADR-025——单单元旧门不动）。

输入:  联合枚举请求（项目 id + unit_ids + 网格/约束覆盖）
输出:  任务句柄（task_id——状态/结果经 calc 任务端点族消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 定稿件决策 1——2026-09-20；镜像测试
#   server/tests/routers/test_solution.py）
#
# 【端点集】
#   POST /api/solution/joint-enumerate   联合枚举异步任务（静态预检 422 面
#                                       在服务层——W7 主闸；结果载荷=
#                                       search_semantics+combos+diagnosis
#                                       +budget_usage）
#
# 【行为规格】
#   R1 旧拒绝点不松：单单元枚举语义（POST /api/calc/enumerate 多单元
#      422）保持 ADR-005 执法——本端点=多单元正门（ADR-025 决策 1）。
#   R2 薄协议转换（routers 禁业务——预检/提交全在 services）。
#   R3 任务状态/取消/结果：复用 calc 任务端点族（task_id 同构消费）。
#
# 【参照】.workflow/b4-3/design-final.md；ADR-025
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from waterprint_server.routers.calc import TaskIdResponse, _ctx
from waterprint_server.services import joint_enumeration as joint_service

router = APIRouter(prefix="/api/solution", tags=["solution"])


class JointEnumerateRequest(BaseModel):
    """联合枚举请求（unit_ids 2..max_units——单单元走既有 /api/calc/enumerate
    正门，N=1 不属联合语义[设计定稿 §1；门一 B1 收紧 2026-09-20]）。"""

    project_id: str
    unit_ids: list[str] = Field(min_length=2)
    options: dict[str, Any] | None = None


@router.post("/joint-enumerate", response_model=TaskIdResponse)
async def run_joint_enumeration(body: JointEnumerateRequest, request: Request) -> TaskIdResponse:
    """联合枚举（静态预检 422 在服务面；异步 job 同 worker 制式）。"""
    handle = await joint_service.submit_joint_enumeration(
        _ctx(request), body.project_id, body.unit_ids, body.options
    )
    return TaskIdResponse(task_id=handle.task_id)
