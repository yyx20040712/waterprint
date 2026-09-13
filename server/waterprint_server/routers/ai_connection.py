"""AI 接入端点：GET /api/ai/connection + POST /api/ai/connection/setup（AI2）。

输入:  无请求体无路径参（setup 写目标=服务端推导固定工作区路径——零用户输入面）
输出:  AiConnectionStatus/AiConnectionSetupResult（服务层冻结模型直投——
      routers response_model 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（AI2-CONNECT 2026-09-13；镜像测试 server/tests/routers/
# test_ai_connection.py）
#
# 【端点集（v1 冻结）】
#   GET  /api/ai/connection          接入状态四项检查+ready 聚合
#   POST /api/ai/connection/setup    一键接入（两份工作区配置 merge 原子写）
#
# 【行为规格】
#   R1 零业务薄封装：业务全部在 services.ai_connection（exports 先例）；
#      本层零 if 零 responses 声明（UvNotFoundError→400 经 main 统一映射）。
#   R2 鉴权面沿册：include 级 Depends(verify_token)（main 装配——与既有
#      业务 router 同款，token 空默认=开）。
#
# 【测试要求】路由集恰两件、200 形态、setup 写入翻绿、uv 缺失 400、
#   token 非空无 Bearer=401。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter, Request

from waterprint_server.services import ServiceContext
from waterprint_server.services import ai_connection as service
from waterprint_server.services.ai_connection import (
    AiConnectionSetupResult,
    AiConnectionStatus,
)

router = APIRouter(prefix="/api/ai", tags=["ai-connection"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get("/connection", response_model=AiConnectionStatus)
async def get_connection_status(request: Request) -> AiConnectionStatus:
    """接入状态四项检查（配置/agent 模块/uv/沙箱——ready 聚合直投）。"""
    return service.connection_status(_ctx(request))


@router.post("/connection/setup", response_model=AiConnectionSetupResult)
async def setup_connection(request: Request) -> AiConnectionSetupResult:
    """一键接入：两份工作区 .zcode/config.json merge 式原子写 server 条目。"""
    return service.setup_connection(_ctx(request))
