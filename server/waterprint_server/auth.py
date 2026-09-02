"""API token 鉴权依赖：Bearer 通道（19 受保端点）+ SSE 双通道（events 两端点）。

输入:  Request（app.state.ctx.settings.api_token 配置值）+ Authorization 头
       / ？token= 查询参数（仅 SSE）
输出:  verify_token / verify_token_sse 路由依赖 + AuthError（401 面）+
       OpenAPI 双安全 scheme（httpBearer / sseTokenQuery）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（R2A 批1 2026-09-02；终裁 R-1/R-3/N-3/N-4；镜像测试
# server/tests/test_auth.py）
#
# 【公开接口】
#   verify_token     受保非事件端点依赖（main include 七业务路由器挂载）
#   verify_token_sse events 两 SSE 端点专用依赖（header 或 ？token=）
#   AuthError        token 缺失/不符领域异常（main._EXCEPTION_STATUS
#                    →401，自动获得统一错误体 {detail, error_type}）
#
# 【行为规格】
#   R1 通道纪律（终裁 R-1）：受保 19 非事件端点仅认 Authorization:
#      Bearer（带 ？token= 无 header=401）；events 两端点认 header 或
#      ？token=（SSE 客户端 EventSource 无法自定义头的现实通道）。
#   R2 鉴权关语义：api_token 空（+回环绑定=R-6 防线）→全放行（含
#      query 通道）——默认态 24 端点零行为变化。
#   R3 常量时间比对（N-4）：hmac.compare_digest（防时序侧信道逐字节
#      泄漏 token 前缀）。
#   R4 契约面（R-3）：两依赖的安全 scheme 参数（HTTPBearer/APIKeyQuery）
#      自动进入 OpenAPI——受保操作 security=[httpBearer]；events 操作
#      security=[httpBearer, sseTokenQuery]（数组=OR 语义）；units 三
#      静态只读端点不挂依赖（main 侧显式 security=[]）。
#
# 【错误与边界】auto_error=False——凭证缺失/形态错由本层统一抛 AuthError
#   （不用框架默认 401 体——N-3 统一错误体口径）；token 值比对失败与
#   凭证缺失同面 401（不泄漏"哪个通道更接近"信息）。
#
# 【禁止事项】不引入 403 权限分级（无此概念——终裁三.沿册项）；不做
#   限流；不新增端点。
#
# 【测试要求】test_auth.py 13 用例（401 面/放行面/负面通道/启动防线/
#   OpenAPI 安全契约）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import APIKeyQuery, HTTPAuthorizationCredentials, HTTPBearer

# OpenAPI 安全 scheme（R-3 命名=终裁口径）：scheme_name 即契约
# securitySchemes 键；auto_error=False——错误归一 AuthError（N-3）。
_BEARER_SCHEME = HTTPBearer(
    scheme_name="httpBearer",
    auto_error=False,
    description="受保端点静态 token（Authorization: Bearer <token>）",
)
_SSE_QUERY_SCHEME = APIKeyQuery(
    name="token",
    scheme_name="sseTokenQuery",
    auto_error=False,
    description="events SSE 端点专用 ？token= 查询通道（其余端点无效）",
)


class AuthError(Exception):
    """token 缺失/不符（401 面——main._EXCEPTION_STATUS 统一翻译，N-3）。"""


def _configured_token(request: Request) -> str:
    """鉴权开关真源：app.state.ctx.settings.api_token（装配束注入，无全局态）。"""
    token: str = request.app.state.ctx.settings.api_token
    return token


def _token_matches(supplied: str, expected: str) -> bool:
    """常量时间比对（N-4）：UTF-8 字节面 hmac.compare_digest。"""
    return hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))


async def verify_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER_SCHEME)],
) -> None:
    """受保非事件端点鉴权（R-1：仅认 Bearer 头；token 空=放行）。"""
    expected = _configured_token(request)
    if expected == "":
        return  # 鉴权关（R-6 保证此时为回环绑定）——全放行
    supplied = credentials.credentials if credentials is not None else ""
    if not _token_matches(supplied, expected):
        raise AuthError(
            "鉴权失败：受保端点要求 Authorization: Bearer <token>"
            "（?token= 查询通道仅限 events SSE 端点）"
        )


async def verify_token_sse(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER_SCHEME)],
    query_token: Annotated[str | None, Depends(_SSE_QUERY_SCHEME)],
) -> None:
    """events SSE 端点鉴权（R-1 双通道：header 或 ？token= 任一命中即过）。"""
    expected = _configured_token(request)
    if expected == "":
        return  # 鉴权关——含 query 通道全放行
    supplied_header = credentials.credentials if credentials is not None else ""
    ok_header = _token_matches(supplied_header, expected)
    ok_query = query_token is not None and _token_matches(query_token, expected)
    if not (ok_header or ok_query):
        raise AuthError(
            "鉴权失败：SSE 端点要求 Authorization: Bearer 头或 ？token= 查询参数"
        )
