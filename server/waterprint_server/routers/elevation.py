"""高程纵断端点：elevation 数据通道（同步取数，最近完成结果集）。

输入:  project_id（路径）+ condition_key（查询可选——缺省=排序首键回显）
输出:  ElevationResponse（服务层 pydantic 冻结模型——response_model 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE7 D1/D10 2026-08-29；镜像测试 server/tests/test_elevation.py）
#
# 【端点集（v1 冻结）】
#   GET /api/elevation/{project_id}?condition_key={可选}
#       高程纵断+提升计划（同步端点——纯投影无任务化语义；工况缺省=
#       结果工况排序首键，显式回显于响应 condition_key 字段）
#
# 【行为规格】
#   R1 消费最近完成结果集（services/elevation R1 同口径——消费时实时
#      取，无结果集=404 附"先 POST /api/calc/run"指引）。
#   R2 响应模型=服务层 pydantic 冻结模型（ElevationResponse 经
#      services.elevation 导出——units.py"响应模型=服务层冻结模型"注记
#      先例，禁协议层重复声明漂移面）。
#   R3 错误面统一经 main 异常映射表（ElevationSourceNotFoundError→404/
#      InvalidElevationRequestError→422——router 零 if 零业务）。
#
# 【测试要求】缺省工况回显、双 GET 字节同、404/422 错误面、
#   端点集恰一件无漂移。
#
# 【参照】FE7 简报 D1/D10；routers/scene.py 同构先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter, Request

from waterprint_server.services import ServiceContext
from waterprint_server.services import elevation as service
from waterprint_server.services.elevation import ElevationResponse

router = APIRouter(prefix="/api/elevation", tags=["elevation"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get("/{project_id}", response_model=ElevationResponse)
async def get_elevation(
    project_id: str, request: Request, condition_key: str | None = None
) -> ElevationResponse:
    """高程纵断（最近完成结果集纯投影；工况缺省=排序首键回显，R1/R2）。"""
    return service.build_elevation_for_project(_ctx(request), project_id, condition_key)
