"""token 鉴权镜像测试：Bearer 通道/SSE 双通道/豁免面/启动防线（R2A 批1）。

输入:  waterprint_server 鉴权依赖（main include 挂载）+ Settings 校验面
输出:  鉴权契约断言（401 面/放行面/负面通道/OpenAPI 安全契约）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（R2A 批1 2026-09-02；终裁 R-1/R-3/R-5/R-6/R-7+N-3/N-4；
#   R 轮 R-1 2026-09-02 补 ⑭ SSE Bearer 正向用例+⑧ 派生表达式）
#
# 【用例矩阵（终裁 D8+R-1，14 用例单文件——conftest 一行不改，
#   auth fixture 全内聚本文件）】
#   ① 鉴权开无 token→401（统一错误体 {detail, error_type}=AuthError）
#   ② 错 token→401
#   ③ 对 token Bearer 头→200
#   ④ SSE 无 token→401
#   ⑤ SSE ？token= 对值→200（httpx stream 拿状态码即断，不等流结束）
#   ⑥ units 三静态只读端点豁免（无 token→200）
#   ⑦ host=0.0.0.0+空 token→Settings 构造即 ValidationError（fail fast）
#   ⑧ token 过短（<16）→ValidationError；恰 16 过界
#   ⑨ 普通 API 带 ？token= 无 header→401（R-1 负面必选：query 通道
#      严格限定 events 两端点）
#   ⑩ Bearer 前缀错误（Basic）→401
#   ⑪ 空 Authorization 头→401
#   ⑫ 鉴权关（token 空+回环）匿名→200（默认态零行为变化回归锚）
#   ⑬ OpenAPI 安全契约（R-3：httpBearer/sseTokenQuery 双 scheme；
#      受保 19 操作 [httpBearer]；events 双通道 OR；units 显式 []）
#   ⑭ SSE Authorization: Bearer 头→200（R 轮 R-1 必改：⑤ 的 header 侧
#      对偶，tasks 终态流通道；A 二审运行时已实证接线正确——直绿锁既有
#      事实，CP2 先例形态，报告如实记档无红相）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi import status
from pydantic import ValidationError

from waterprint_server.main import create_app
from waterprint_server.settings import API_TOKEN_MIN_LENGTH, Settings

# 鉴权开态 token（长度 34≥16 基线；字母数字+连字符——测试字面锚，真源=
# settings.API_TOKEN_MIN_LENGTH 校验面）。
TEST_TOKEN = "r2a1-authed-token-0123456789abcdef"


def _auth_header() -> dict[str, str]:
    """对 token 请求头（受保非事件端点唯一合法通道——R-1）。"""
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


@pytest.fixture
def authed_settings(test_settings: Settings) -> Settings:
    """鉴权开态 Settings（token 注入；值合法——model_copy 免重校验自担面）。"""
    return test_settings.model_copy(update={"api_token": TEST_TOKEN})


@pytest.fixture
async def authed_client(
    authed_settings: Settings,
) -> AsyncIterator[httpx.AsyncClient]:
    """鉴权开态 client（conftest client 同构：ASGITransport+显式 lifespan+ThreadPool）。"""
    executor = ThreadPoolExecutor(max_workers=authed_settings.calc_workers)
    application = create_app(authed_settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    executor.shutdown(wait=True)


async def _await_terminal_task(client: httpx.AsyncClient, project_id: str) -> str:
    """提交全流程计算并等终态（SSE 200 用例的有限流载体——终态任务连接即收）。"""
    task_id = (
        await client.post(
            "/api/calc/run",
            json={"project_id": project_id, "conditions": []},
            headers=_auth_header(),
        )
    ).json()["task_id"]
    for _ in range(300):
        body = (
            await client.get(f"/api/calc/tasks/{task_id}", headers=_auth_header())
        ).json()
        if body.get("state") in {"done", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.1)
    return task_id


@pytest.mark.anyio
async def test_protected_no_token_401(authed_client: httpx.AsyncClient) -> None:
    """①：鉴权开无 token→401（统一错误体——N-3 对齐 _register_handlers 形态）。"""
    response = await authed_client.get("/api/projects")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["error_type"] == "AuthError"
    assert "detail" in body  # 冻结错误体 {detail, error_type}（401 自动同形）


@pytest.mark.anyio
async def test_protected_wrong_token_401(authed_client: httpx.AsyncClient) -> None:
    """②：错 token→401（compare_digest 常量时间比对——N-4）。"""
    response = await authed_client.get(
        "/api/projects", headers={"Authorization": "Bearer wrong-token-value-xyz"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error_type"] == "AuthError"


@pytest.mark.anyio
async def test_protected_valid_token_200(authed_client: httpx.AsyncClient) -> None:
    """③：对 token Bearer 头→200（正门不回归）。"""
    response = await authed_client.get("/api/projects", headers=_auth_header())
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_sse_no_token_401(authed_client: httpx.AsyncClient) -> None:
    """④：SSE 端点无任何凭证→401（include 级依赖先于 handler——404 探测不达）。"""
    response = await authed_client.get("/api/events/tasks/ghost-task-xyz")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error_type"] == "AuthError"


@pytest.mark.anyio
async def test_sse_query_token_200(
    authed_client: httpx.AsyncClient, cass_payload: dict[str, object]
) -> None:
    """⑤：SSE ？token= 对值→200（终裁 R-1 双通道；httpx stream 拿状态码即断）。"""
    created = await authed_client.post(
        "/api/projects", json={"project": cass_payload}, headers=_auth_header()
    )
    project_id = created.json()["project_id"]
    task_id = await _await_terminal_task(authed_client, project_id)
    async with authed_client.stream(
        "GET", f"/api/events/tasks/{task_id}?token={TEST_TOKEN}"
    ) as response:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_sse_bearer_header_200(
    authed_client: httpx.AsyncClient, cass_payload: dict[str, object]
) -> None:
    """⑭：SSE Authorization: Bearer 头→200（⑤ 的 header 侧对偶——R 轮 R-1 补）。"""
    created = await authed_client.post(
        "/api/projects", json={"project": cass_payload}, headers=_auth_header()
    )
    project_id = created.json()["project_id"]
    task_id = await _await_terminal_task(authed_client, project_id)
    async with authed_client.stream(
        "GET", f"/api/events/tasks/{task_id}", headers=_auth_header()
    ) as response:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_units_exempt_no_token_200(authed_client: httpx.AsyncClient) -> None:
    """⑥：units 三静态只读端点豁免（终裁 D3——无 token 匿名 200）。"""
    for path in ("/api/units", "/api/assumptions", "/api/constraints"):
        response = await authed_client.get(path)
        assert response.status_code == status.HTTP_200_OK, path


def test_offloopback_host_empty_token_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """⑦：host=0.0.0.0+空 token→构造即 ValidationError（R-6 fail fast）。"""
    monkeypatch.delenv("WATERPRINT_API_TOKEN", raising=False)
    monkeypatch.delenv("WATERPRINT_HOST", raising=False)
    with pytest.raises(ValidationError, match="api_token"):
        Settings(_env_file=None, host="0.0.0.0")
    # 回环集合三形态（R-6：{127.0.0.1, ::1, localhost}）+空 token=合法
    for loopback in ("127.0.0.1", "::1", "localhost"):
        assert Settings(_env_file=None, host=loopback).api_token == ""


def test_short_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """⑧：token 过短→ValidationError（R-7：API_TOKEN_MIN_LENGTH=16 熵下界；
    恰长过界——R 轮派生表达式与实现侧真源同纪律）。"""
    monkeypatch.delenv("WATERPRINT_API_TOKEN", raising=False)
    with pytest.raises(ValidationError, match="长度"):
        Settings(_env_file=None, api_token="a" * (API_TOKEN_MIN_LENGTH - 1))
    assert (
        Settings(_env_file=None, api_token="b" * API_TOKEN_MIN_LENGTH).api_token
        == "b" * API_TOKEN_MIN_LENGTH
    )


@pytest.mark.anyio
async def test_query_token_on_normal_api_401(authed_client: httpx.AsyncClient) -> None:
    """⑨：普通 API 带 ？token= 无 header→401（R-1 负面：query 通道不扩大）。"""
    response = await authed_client.get(f"/api/projects?token={TEST_TOKEN}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_wrong_authorization_scheme_401(authed_client: httpx.AsyncClient) -> None:
    """⑩：Bearer 前缀错误（Basic 携对值）→401。"""
    response = await authed_client.get(
        "/api/projects", headers={"Authorization": f"Basic {TEST_TOKEN}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_empty_authorization_header_401(authed_client: httpx.AsyncClient) -> None:
    """⑪：空 Authorization 头→401（非 Bearer 形态即拒）。"""
    response = await authed_client.get("/api/projects", headers={"Authorization": ""})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_auth_disabled_allows_anonymous(client: httpx.AsyncClient) -> None:
    """⑫：鉴权关（token 空+回环默认）匿名→200（默认态零行为变化回归锚）。"""
    response = await client.get("/api/projects")
    assert response.status_code == status.HTTP_200_OK


def test_openapi_security_contract() -> None:
    """⑬：OpenAPI 安全契约（R-3：双 scheme/受保 19/events OR/units 显式 []）。"""
    import waterprint_server.main as main_mod

    schema = main_mod.app.openapi()
    schemes = schema.get("components", {}).get("securitySchemes", {})
    assert schemes["httpBearer"]["type"] == "http"
    assert schemes["httpBearer"]["scheme"] == "bearer"
    assert schemes["sseTokenQuery"]["type"] == "apiKey"
    assert schemes["sseTokenQuery"]["in"] == "query"
    assert schemes["sseTokenQuery"]["name"] == "token"
    # 受保非事件操作：仅 httpBearer（19 面抽样两处）
    for path, method in (("/api/projects", "get"), ("/api/calc/run", "post")):
        assert schema["paths"][path][method]["security"] == [{"httpBearer": []}]
    # events 两操作：双通道 OR 语义（security 数组=任一满足）
    sse_security = schema["paths"]["/api/events/tasks/{task_id}"]["get"]["security"]
    assert {"httpBearer", "sseTokenQuery"} == {
        key for entry in sse_security for key in entry
    }
    # units 三操作：显式空 security（公开面明示——区别于未声明）
    for path in ("/api/units", "/api/assumptions", "/api/constraints"):
        assert schema["paths"][path]["get"]["security"] == []
