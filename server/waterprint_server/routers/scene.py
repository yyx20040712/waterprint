"""场景图端点：三维视图数据通道（同步取数，最近完成结果集）。

输入:  project_id（路径）+ condition_key（查询可选——缺省=排序首键回显）
输出:  SceneGraph（core 冻结 dataclass——response_model 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE1 D1 2026-08-28；镜像测试 server/tests/routers/test_scene.py）
#
# 【端点集（v1 冻结）】
#   GET /api/scene/{project_id}?condition_key={可选}
#       三维场景图（同步端点——<100ms 纯投影，无任务化语义；工况缺省=
#       结果工况排序首键，显式回显于响应 condition_key 字段）
#
# 【行为规格】
#   R1 消费最近完成结果集（services/scene R1 同口径——消费时实时取，
#      无结果集=404 附"先 POST /api/calc/run"指引）。
#   R2 响应模型=服务层冻结 dataclass（SceneGraph 经 services.scene 再
#      导出——calc.py"响应模型=服务层冻结 dataclass"注记先例，禁协议层
#      重复声明漂移面；FastAPI 原生 dataclass 支持）。
#   R3 错误面统一经 main 异常映射表（SceneSourceNotFoundError→404/
#      InvalidSceneRequestError→422——router 零 if 零业务）。
#
# 【测试要求】缺省工况回显、双 GET 字节同、404/422 错误面、
#   端点集恰一件无漂移。
#
# 【参照】重写计划 §10.5/§12.2/§13.4；FE1 简报 D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter, Request

from waterprint_server.services import ServiceContext
from waterprint_server.services import scene as service
from waterprint_server.services.scene import SceneGraph

router = APIRouter(prefix="/api/scene", tags=["scene"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get("/{project_id}", response_model=SceneGraph)
async def get_scene(
    project_id: str, request: Request, condition_key: str | None = None
) -> SceneGraph:
    """场景图（最近完成结果集纯投影；工况缺省=排序首键回显，R1/R2）。"""
    return service.build_scene_for_project(_ctx(request), project_id, condition_key)
