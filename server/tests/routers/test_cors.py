"""CORS 配置面镜像测试：客户端模式生产通道（联机架构第六批）。

输入:  waterprint_server.main（CORS 装配）+ settings.parse_allowed_origins
输出:  CORS 契约断言（开发白名单 ∪ 配置面/token 门禁独立/形态 fail fast）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机架构第六批 2026-11-19；用户裁决厚客户端模型：界面本地
# 加载，数据/计算走远程服务器——浏览器态客户端经跨 origin fetch 访问
# API，CORS 是生产通道非开发便利）
#
# 【用例矩阵（7 用例单文件——fixture 自内聚，test_meta server 态同制式）】
#   ① 开发白名单回归锚：5173 两 origin 预检放行（R5 语义不破）
#   ② 客户端缺省桌面源：http://127.0.0.1:8620（b7 约定端口）实际请求
#      回显 allow-origin
#   ③ 非白名单 origin 拒：预检 400 + 实际请求零 CORS 头（浏览器面阻断）
#   ④ 配置面增补：env/Settings 增补自定义 origin 放行+开发白名单保持
#      （并集语义非替换）
#   ⑤ token 门禁独立于 CORS：server 态（token 开）白名单 origin 带
#      Bearer 200 / 无 token 401（CORS 放行不豁免鉴权）
#   ⑥ 形态 fail fast：无 scheme/带 path 条目构造即 ValidationError
#   ⑦ 解析容错：尾逗号/空白段剔除（parse_allowed_origins 纯函数面）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi import FastAPI, status
from pydantic import ValidationError

from waterprint_server.main import _DEV_ORIGINS, create_app
from waterprint_server.settings import Settings, parse_allowed_origins

# server 态 token（长度≥16 基线——test_meta 同制式字面锚）
SERVER_MODE_TOKEN = "b6-client-mode-token-456789abcd"
# 非白名单 origin（192.0.2.0/24 文档段——不与白名单/本机地址冲突）
_FOREIGN_ORIGIN = "http://192.0.2.99:9999"
# 配置面自定义 origin（客户端自托管静态源形态）
_CONFIGURED_ORIGIN = "http://192.168.50.18:5173"


async def _make_client(
    settings: Settings,
) -> AsyncIterator[tuple[httpx.AsyncClient, ThreadPoolExecutor]]:
    """server 态 app+lifespan 显式启停（conftest client 同构装配）。"""
    executor = ThreadPoolExecutor(max_workers=settings.calc_workers)
    application = create_app(settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            yield client, executor
    executor.shutdown(wait=True)


@pytest.mark.anyio
async def test_dev_whitelist_regression_anchor(
    client: httpx.AsyncClient,
) -> None:
    """①：开发白名单两 origin 预检放行（R5 开发语义零变）。"""
    for origin in _DEV_ORIGINS:
        response = await client.options(
            "/api/projects",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == status.HTTP_200_OK, origin
        assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.anyio
async def test_default_desktop_client_origin_allowed(
    client: httpx.AsyncClient,
) -> None:
    """②：缺省桌面源（127.0.0.1:8620——b7 约定端口）实际请求回显。"""
    response = await client.get("/api/meta", headers={"Origin": "http://127.0.0.1:8620"})
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.headers.get("access-control-allow-origin") == "http://127.0.0.1:8620"
    )


@pytest.mark.anyio
async def test_foreign_origin_rejected(client: httpx.AsyncClient) -> None:
    """③：非白名单 origin 拒——预检 400+实际请求零 CORS 头（浏览器面阻断）。"""
    preflight = await client.options(
        "/api/projects",
        headers={
            "Origin": _FOREIGN_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == status.HTTP_400_BAD_REQUEST
    assert "access-control-allow-origin" not in preflight.headers
    actual = await client.get("/api/projects", headers={"Origin": _FOREIGN_ORIGIN})
    # 非预检请求本体仍被处理（CORS 是浏览器执行面非服务器鉴权面）——
    # 但零 CORS 回显头=浏览器拒读响应
    assert "access-control-allow-origin" not in actual.headers


@pytest.mark.anyio
async def test_configured_origin_union_with_dev_whitelist(
    test_settings: Settings,
) -> None:
    """④：配置面增补 origin 放行+开发白名单保持（并集非替换）。"""
    settings = test_settings.model_copy(
        update={"allowed_origins": f" {_CONFIGURED_ORIGIN} , "}
    )
    async for client, _executor in _make_client(settings):
        for origin in (*_DEV_ORIGINS, _CONFIGURED_ORIGIN):
            response = await client.options(
                "/api/projects",
                headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
            )
            assert response.status_code == status.HTTP_200_OK, origin
            assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.anyio
async def test_token_gate_independent_of_cors(test_settings: Settings) -> None:
    """⑤：token 门禁独立——白名单 origin 带 Bearer 200/无 token 401。"""
    settings = test_settings.model_copy(
        update={"host": "0.0.0.0", "api_token": SERVER_MODE_TOKEN}
    )
    async for client, _executor in _make_client(settings):
        allowed = await client.get(
            "/api/projects",
            headers={
                "Origin": "http://127.0.0.1:8620",
                "Authorization": f"Bearer {SERVER_MODE_TOKEN}",
            },
        )
        assert allowed.status_code == status.HTTP_200_OK
        assert (
            allowed.headers.get("access-control-allow-origin")
            == "http://127.0.0.1:8620"
        )
        anonymous = await client.get(
            "/api/projects", headers={"Origin": "http://127.0.0.1:8620"}
        )
        assert anonymous.status_code == status.HTTP_401_UNAUTHORIZED


def test_allowed_origins_shape_fail_fast() -> None:
    """⑥：形态 fail fast——无 scheme/带 path 条目构造即 ValidationError。"""
    for bad in ("127.0.0.1:8620", "http://host.example/path", "ftp://host.example", "not a url"):
        with pytest.raises(ValidationError):
            Settings(allowed_origins=bad)


def test_parse_allowed_origins_tolerance() -> None:
    """⑦：解析容错——尾逗号/空白段剔除（纯函数面）。"""
    assert parse_allowed_origins(" http://a.example , http://b.example ,, ") == (
        "http://a.example",
        "http://b.example",
    )
    assert parse_allowed_origins("") == ()
    assert parse_allowed_origins("http://127.0.0.1:8620") == (
        "http://127.0.0.1:8620",
    )
