"""运行时信息端点：GET /api/meta + GET /api/runtime（静态只读自省面）。

输入:  Request（app.state.ctx.settings——装配束注入，无全局态）
输出:  MetaInfo/RuntimeInfo（服务层冻结模型直投——routers 零业务）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机架构第五批 2026-11-19；镜像测试 server/tests/routers/
# test_meta.py）
#
# 【端点集】
#   GET /api/meta      版本握手信息（app/data/api 三槽——客户端模式
#                      〔下一批〕握手比对面；standalone 态同形可达）
#   GET /api/runtime   运行角色与配对面（role/bind_host/lan_addresses/
#                      token_configured/token_reveal——token 明文仅
#                      回环请求者，非回环恒 null）
#
# 【行为规格】
#   R1 豁免面（units 三静态只读端点先例）：两端点不挂 token 依赖+
#      OpenAPI 显式 security=[]——本机 UI 无 token 冷启动可达（配对卡
#      读 token 的鸡-蛋面），LAN 匿名者仅得 role/地址非回环恒 null
#      reveal（services.runtime R3 红线）。
#   R2 请求者地址只取 request.client（对端 socket 面）——X-Forwarded-For
#      类 headers 不参判（反代伪装回环骗 token 封死）；client 取不到
#      （测试外罕见）按空串=fail-closed 不 reveal。
#   R3 零日志：本件与 services.runtime 均不落任何日志（token 禁入
#      日志红线——测试钉死配置 sink）。
#
# 【测试要求】路由集恰两件、两态语义、回环 reveal 门、豁免+security=[]。
#
# 【参照】任务书联机架构第五批；routers/units.py 豁免先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter, Request

from waterprint_server.services.runtime import (
    MetaInfo,
    RuntimeInfo,
    build_meta,
    build_runtime,
)

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta", response_model=MetaInfo)
async def get_meta(request: Request) -> MetaInfo:
    """版本握手信息（应用版本+数据包三包聚合+API 语义版本）。"""
    return build_meta(request.app.state.ctx.settings)


@router.get("/runtime", response_model=RuntimeInfo)
async def get_runtime(request: Request) -> RuntimeInfo:
    """运行角色与配对面（token_reveal 仅回环请求者——headers 不参判）。"""
    client = request.client
    return build_runtime(
        request.app.state.ctx.settings,
        requester_host=client.host if client is not None else "",
    )
