"""间距校核端点：布置摆放黄红标示数据通道（同步取数，最近完成结果集）。

输入:  project_id（查询必填）+ condition_key（查询可选——缺省=排序首键）
输出:  SpacingReportResponse（violations+uncalculated——服务层模型）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（L4b 2026-09-03；镜像测试 server/tests/routers/test_site.py）
#
# 【端点集（v1 冻结）】
#   GET /api/site/spacing?project_id={必填}&condition_key={可选}
#       间距校核报告（同步端点——纯装配无任务化语义；未计算=降级
#       uncalculated 全量返回 200 非 404/409——编辑器部分可用语义）
#
# 【行为规格】
#   R1 消费最近完成结果集足迹+kb spacing_check 阈值（services/site R1
#      同口径——core spacing_report 纯函数装配器）。
#   R2 响应模型=服务层 pydantic 冻结模型（SpacingReportResponse——
#      units「响应模型=服务层冻结模型」先例，禁协议层重复声明漂移面）。
#   R3 错误面统一经 main 异常映射表（ProjectNotFoundError→404/
#      InvalidSpacingRequestError→422——router 零 if 零业务）；鉴权=
#      verify_token 鉴权族挂载（main include——units 静态目录族外）。
#
# 【测试要求】三态（越限/合规/未计算降级）、404/422 错误面、
#   双 GET 字节同、端点集恰一件无漂移。
#
# 【参照】L4 简报 §一 L4b/§三预裁 8；routers/scene.py 同构先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter, Request

from waterprint_server.services import ServiceContext
from waterprint_server.services import site as service
from waterprint_server.services.site import SpacingReportResponse

router = APIRouter(prefix="/api/site", tags=["site"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get("/spacing", response_model=SpacingReportResponse)
async def get_spacing(
    project_id: str, request: Request, condition_key: str | None = None
) -> SpacingReportResponse:
    """间距校核（最近结果足迹+kb 阈值装配；未计算=降级全量非拒）。"""
    return service.build_spacing_for_project(_ctx(request), project_id, condition_key)
