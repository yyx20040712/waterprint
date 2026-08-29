"""概算端点：cost 数据通道（同步取数，最近完成结果集）。

输入:  project_id（路径）+ condition_key（查询可选——缺省="design" 基线档）
输出:  CostResponse（服务层 pydantic 冻结模型——response_model 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE8 D1/D9 2026-08-29；镜像测试 server/tests/test_cost.py）
#
# 【端点集（v1 冻结）】
#   GET /api/cost/{project_id}?condition_key={可选}
#       概算表+指标校核（同步端点——core cost 四模块服务端装配；
#       工况缺省=design 基线档，显式回显于响应 condition_key 字段）
#
# 【行为规格】
#   R1 消费最近完成结果集（services/cost R1 同口径——无结果集=404
#      附"先 POST /api/calc/run"指引）。
#   R2 响应模型=服务层 pydantic 冻结模型（CostResponse 经
#      services.cost 导出——elevation R2 同款先例）。
#   R3 错误面统一经 main 异常映射表（CostSourceNotFoundError→404/
#      InvalidCostRequestError→422——router 零 if 零业务）。
#
# 【测试要求】缺省工况=design、双 GET 字节同、404/422 错误面、
#   端点集恰一件无漂移。
#
# 【参照】FE8 简报 D1/D9；routers/elevation.py 同构先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter, Request

from waterprint_server.services import ServiceContext
from waterprint_server.services import cost as service
from waterprint_server.services.cost import CostResponse

router = APIRouter(prefix="/api/cost", tags=["cost"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get("/{project_id}", response_model=CostResponse)
async def get_cost(
    project_id: str, request: Request, condition_key: str | None = None
) -> CostResponse:
    """概算表+指标校核（最近完成结果集四模块装配；工况缺省=design，R1/R2）。"""
    return service.build_cost_for_project(_ctx(request), project_id, condition_key)
