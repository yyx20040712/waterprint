"""计算/枚举任务端点：触发、状态、结果分页、方案应用。

输入:  任务请求（项目 id + 工况选择 / 枚举请求：unit_id + 网格 + 约束覆盖）
输出:  任务句柄（task_id）/ 状态 / 分页结果
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_calc.py）
#
# 【端点集（v1 冻结）】
#   POST /api/calc/run                 全流程计算（异步任务，返 task_id）
#   POST /api/calc/enumerate           单单元枚举任务（ADR-005 语义）
#   GET  /api/calc/tasks/{task_id}     状态（queued/running/done/
#                                      cancelled/failed + stale 标志）
#   POST /api/calc/tasks/{task_id}/cancel   取消（协作令牌）
#   GET  /api/calc/tasks/{task_id}/solutions?page=&size=   分页结果
#                                      （默认 200/页 §12.2）
#   POST /api/calc/solutions/apply     方案应用（原子写 design + 新 hash
#                                      + 触发重算 §17.1）
#
# 【行为规格】
#   R1 幂等（§15 工程细节 3）：提交键 = (design_hash, condition/
#      enumerate 语义)——重复提交返回既有 task_id（不重复占进程池）；
#      幂等查重与 stale 标记在同一事件循环临界区内完成。本端点
#      stale 标志为 UI 提示性标记，不作守门依据（守门一律消费时
#      实时比对——services/exports.py R1 统一口径，SENS-B
#      2026-08-23 UF-37）。
#   R2 任务快照绑定：任务启动即绑定 design_hash；运行期间编辑 →
#      任务完成后结果标 stale=true（响应显式字段，禁止静默覆盖 §17.1）。
#   R3 取消协作语义：取消请求 → 令牌置位 → worker 每批迭代检查；
#      已完成结果不受取消影响。
#   R4 结果分页与排序参数透传 solution.ranking；万级枚举结果不整包
#      返回（分页 + 按 arrow 文件按需重载 §16 A6）。
#   R5 方案应用原子性：design 写入 + hash 更新 + 缓存失效 + 触发重算
#      为一个事务性服务调用（services/calculation.py）；失败回滚。
#
# 【测试要求】幂等提交、stale 标志、取消流、分页边界、
#   方案应用原子性（失败不半写）。
#
# 【参照】重写计划 §12.2/§17.1/§16 A6；ADR-005
#
# 【实现注记（SERVER 2026-08-26）】响应模型=服务层冻结 dataclass
#   （SaveOutcome/TaskStatus/SolutionPage/ApplyOutcome——FastAPI 原生
#   支持；禁协议层重复声明漂移面）。TaskStatus 经 services.calculation
#   再导出（routers→jobs 非声明边，分层 §13.4）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from waterprint_server.services import ServiceContext
from waterprint_server.services import calculation as calc_service
from waterprint_server.services import enumeration as enum_service
from waterprint_server.services.calculation import ApplyOutcome, TaskStatus
from waterprint_server.services.enumeration import SolutionPage

router = APIRouter(prefix="/api/calc", tags=["calc"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


class TaskIdResponse(BaseModel):
    """任务句柄（幂等提交返回既有 id）。"""

    task_id: str


class RunRequest(BaseModel):
    """全流程计算请求（工况选择=受检单元列表）。"""

    project_id: str
    conditions: list[str] = Field(default_factory=list)


class EnumerateRequest(BaseModel):
    """单单元枚举请求（R1 ADR-005：多 unit_id 服务层显式 422）。"""

    project_id: str
    unit_ids: list[str] = Field(min_length=1)
    options: dict[str, Any] | None = None


class CancelResponse(BaseModel):
    """取消结果（R3：终态任务不受取消影响）。"""

    cancelled: bool


class ApplyRequest(BaseModel):
    """方案应用请求（R5：事务性服务调用）。"""

    project_id: str
    unit_id: str
    params: dict[str, Any]


@router.post("/run", response_model=TaskIdResponse)
async def run_calculation(body: RunRequest, request: Request) -> TaskIdResponse:
    """全流程计算（异步任务）——幂等键=(design_hash, conditions)。"""
    handle = await calc_service.submit_calculation(_ctx(request), body.project_id, body.conditions)
    return TaskIdResponse(task_id=handle.task_id)


@router.post("/enumerate", response_model=TaskIdResponse)
async def run_enumeration(body: EnumerateRequest, request: Request) -> TaskIdResponse:
    """单单元枚举（ADR-005 语义守护在服务面）。"""
    handle = await enum_service.submit_enumeration(
        _ctx(request), body.project_id, body.unit_ids, body.options
    )
    return TaskIdResponse(task_id=handle.task_id)


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str, request: Request) -> TaskStatus:
    """状态（stale=提示性标记 R1/R2；结果载荷含无解诊断交付面）。"""
    return calc_service.task_status(_ctx(request), task_id)


@router.post("/tasks/{task_id}/cancel", response_model=CancelResponse)
async def cancel_task(task_id: str, request: Request) -> CancelResponse:
    """取消（协作令牌置位；已完成结果不受影响 R3）。"""
    return CancelResponse(cancelled=calc_service.cancel_task(_ctx(request), task_id))


@router.get("/tasks/{task_id}/solutions", response_model=SolutionPage)
async def get_solutions(
    task_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    size: int | None = Query(default=None, ge=1),
    sort: str = Query(default="margin_min"),
) -> SolutionPage:
    """分页结果（默认 200/页经 Settings §12.2；万级不整包回传）。"""
    return enum_service.fetch_solutions(_ctx(request), task_id, page, size, sort)


@router.post("/solutions/apply", response_model=ApplyOutcome)
async def apply_solution(body: ApplyRequest, request: Request) -> ApplyOutcome:
    """方案应用（原子事务：失败回滚不半写 R5）。"""
    return await calc_service.apply_solution(
        _ctx(request), body.project_id, {"unit_id": body.unit_id, "params": body.params}
    )
