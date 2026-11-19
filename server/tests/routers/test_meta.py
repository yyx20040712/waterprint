"""meta 路由镜像测试：版本握手面+运行角色/配对面+token 回环 reveal 门。

输入:  waterprint_server.routers.meta 公开符号 + services.runtime
输出:  路由契约断言（联机架构第五批 2026-11-19——两态语义/安全红线）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机架构第五批 2026-11-19；用户裁决 Minecraft 式开关模型：
# 联机关=单机〔本地引擎 127.0.0.1 零行为变〕；联机开+服务端=本地引擎
# 照常+0.0.0.0 绑定+token 强制+局域网可连）
#
# 【用例矩阵（8 用例单文件——server 态 fixture 全内聚本文件）】
#   ① 端点集恰两件（GET /api/meta + GET /api/runtime）
#   ② meta 版本三槽：app=ENGINE_VERSION/api=API_SEMANTIC_VERSION/
#      data=三包聚合（b24 面复用——name@version 三段全集）
#   ③ standalone 态（默认 settings）：role=standalone+bind_host=127.0.0.1
#      +lan_addresses 空+token_configured=False+token_reveal=""（回环
#      请求者·未配 token——默认态零行为变回归锚）
#   ④ server 态（0.0.0.0+token）回环请求者：role=server+token_reveal=
#      token 明文（配对卡展示面）+lan_addresses 全非回环 IPv4
#   ⑤ server 态非回环请求者（ASGITransport client 地址注入）：token_
#      reveal 恒 None——X-Forwarded-For 伪装回环头不参判（防骗取）
#   ⑥ 豁免面：server 态（token 开）无 Bearer 匿名 GET 两端点 200
#   ⑦ OpenAPI 安全契约：两操作显式 security=[]（公开面明示）
#   ⑧ token 禁入日志：reveal 路径走过后配置 sink（root handlers 文件）
#      零 token 落盘
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ipaddress
import logging
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, status

from waterprint_server.main import create_app
from waterprint_server.routers.meta import router
from waterprint_server.services.runtime import API_SEMANTIC_VERSION
from waterprint_server.settings import ENGINE_VERSION, Settings

# server 态 token（长度≥16 基线——settings.API_TOKEN_MIN_LENGTH 校验面；
# 测试字面锚同 test_auth 制式）
SERVER_MODE_TOKEN = "b5-server-mode-token-0123456789"
# 非回环请求者对端地址（配对卡不可见面的请求者形态——ASGITransport
# client 注入；192.0.2.0/24 文档段不与本机真实地址冲突）
_LAN_REQUESTER: tuple[str, int] = ("192.0.2.77", 51423)


def test_router_exposes_meta_endpoints_wiring() -> None:
    """①：端点集 == 规格两件（GET /api/meta + GET /api/runtime——恰两件无漂移）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed == {("get", "/api/meta"), ("get", "/api/runtime")}


@pytest.mark.anyio
async def test_meta_versions_three_slots(client: httpx.AsyncClient) -> None:
    """②：meta 三槽=ENGINE_VERSION/API_SEMANTIC_VERSION/三包聚合串。"""
    response = await client.get("/api/meta")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["app_version"] == ENGINE_VERSION
    assert body["api_version"] == API_SEMANTIC_VERSION
    segments = body["data_version"].split("+")
    assert {part.split("@", 1)[0] for part in segments} == {
        "assumptions",
        "coefficients",
        "unit_prices",
    }  # b24 三包化聚合面（load_run_env 单源——包名序非空版本段）


@pytest.mark.anyio
async def test_runtime_standalone_default_state(client: httpx.AsyncClient) -> None:
    """③：standalone 态（默认 settings+回环请求者）——零行为变回归锚。"""
    response = await client.get("/api/runtime")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["role"] == "standalone"
    assert body["bind_host"] == "127.0.0.1"
    assert body["lan_addresses"] == []  # 无监听地址语义（配对卡不展示）
    assert body["token_configured"] is False
    assert body["token_reveal"] == ""  # 回环请求者+未配 token=空串真相


@pytest.fixture
def server_mode_settings(test_settings: Settings) -> Settings:
    """server 态 Settings（0.0.0.0+token——R2A R-6 对外绑定必配 token）。"""
    return test_settings.model_copy(
        update={"host": "0.0.0.0", "api_token": SERVER_MODE_TOKEN}
    )


@pytest.fixture
async def server_mode_app(
    server_mode_settings: Settings,
) -> AsyncIterator[tuple[FastAPI, ThreadPoolExecutor]]:
    """server 态 app+lifespan 显式启停（conftest client 同构装配）。"""
    executor = ThreadPoolExecutor(max_workers=server_mode_settings.calc_workers)
    application = create_app(server_mode_settings, executor=executor)
    async with application.router.lifespan_context(application):
        yield application, executor
    executor.shutdown(wait=True)


@pytest.mark.anyio
async def test_runtime_server_mode_loopback_reveal(
    server_mode_app: tuple[FastAPI, ThreadPoolExecutor],
) -> None:
    """④：server 态回环请求者——role=server+token 明文 reveal（配对卡）。"""
    application, _ = server_mode_app
    transport = httpx.ASGITransport(app=application)  # 缺省 client=127.0.0.1（回环）
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/api/runtime")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["role"] == "server"
    assert body["bind_host"] == "0.0.0.0"
    assert body["token_configured"] is True
    assert body["token_reveal"] == SERVER_MODE_TOKEN
    for address in body["lan_addresses"]:
        assert not ipaddress.ip_address(address).is_loopback  # 全非回环 IPv4


@pytest.mark.anyio
async def test_runtime_token_hidden_from_lan_requester(
    server_mode_app: tuple[FastAPI, ThreadPoolExecutor],
) -> None:
    """⑤：非回环请求者 token_reveal 恒 None——XFF 伪装回环头不参判。"""
    application, _ = server_mode_app
    transport = httpx.ASGITransport(
        app=application, client=_LAN_REQUESTER  # 对端 socket=局域网地址
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get(
            "/api/runtime",
            headers={"X-Forwarded-For": "127.0.0.1"},  # 伪装回环——必须无效
        )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_reveal"] is None
    assert SERVER_MODE_TOKEN not in response.text  # 响应面零 token 泄漏


@pytest.mark.anyio
async def test_meta_runtime_exempt_without_token(
    server_mode_app: tuple[FastAPI, ThreadPoolExecutor],
) -> None:
    """⑥：豁免面——server 态（token 开）匿名 GET 两端点 200（units 先例）。"""
    application, _ = server_mode_app
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        for path in ("/api/meta", "/api/runtime"):
            response = await ac.get(path)
            assert response.status_code == status.HTTP_200_OK, path


def test_openapi_security_public_explicit() -> None:
    """⑦：OpenAPI 安全契约——两操作显式空 security（公开面明示非未声明）。"""
    import waterprint_server.main as main_mod

    schema = main_mod.app.openapi()
    for path in ("/api/meta", "/api/runtime"):
        assert schema["paths"][path]["get"]["security"] == [], path


@pytest.mark.anyio
async def test_token_never_logged(
    server_mode_app: tuple[FastAPI, ThreadPoolExecutor],
) -> None:
    """⑧：token 禁入日志——reveal 路径走过后配置 sink 零 token 落盘。

    探针记录先落一条（保证 sink 文件在场非空），再断言全 sink 文件
    不含 token 串（模块零日志调用+路由零日志调用的行为级钉死）。
    """
    application, _ = server_mode_app
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        await ac.get("/api/runtime")  # 回环 reveal 路径（token 值经过内存面）
    logging.getLogger("test.meta.probe").info("meta token log probe record")
    sinks = [
        Path(handler.baseFilename)
        for handler in logging.getLogger().handlers
        if hasattr(handler, "baseFilename")
    ]
    assert sinks, "配置 sink 不在场（_configure_logging 契约漂移）"
    for sink in sinks:
        if sink.is_file():
            assert SERVER_MODE_TOKEN not in sink.read_text(encoding="utf-8"), str(sink)
