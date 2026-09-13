"""ai_connection 路由镜像测试：GET /api/ai/connection + POST setup（AI2）。

输入:  waterprint_server.routers.ai_connection 公开符号+tmp 伪工作区 client
输出:  路由契约断言（端点集两件/四项状态形态/setup 200 写入/uv 缺失 400/401 面）
"""

from __future__ import annotations

import importlib
import json
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.ai_connection")
_service = importlib.import_module("waterprint_server.services.ai_connection")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/ai/connection"), ("post", "/api/ai/connection/setup")}


def test_router_exposes_ai_connection_endpoints_wiring() -> None:
    """端点集 == 规格两件（GET /api/ai/connection + POST /setup——恰两件无漂移）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)


def _workspace_settings(tmp_path: Path):  # type: ignore[no-untyped-def]
    """伪工作区 Settings（data_dir=<tmp>/ws/waterprint/data——上溯推导面隔离）。"""
    from waterprint_server.settings import Settings

    repo_root = tmp_path / "ws" / "waterprint"
    (repo_root / "data").mkdir(parents=True)
    package = repo_root / "agent" / "waterprint_agent"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    return Settings(
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=repo_root / "data",
        calc_workers=1,
        log_file=str(tmp_path / "ai-connection-router.log"),
    )


@pytest.fixture
async def ai_client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    """伪工作区 app client（conftest.client 同款装配——data_dir 指向上溯结构）。"""
    from waterprint_server.main import create_app

    settings = _workspace_settings(tmp_path)
    executor = ThreadPoolExecutor(max_workers=1)
    application = create_app(settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    executor.shutdown(wait=True)


@pytest.mark.anyio
async def test_get_status_400_on_bad_workspace_layout(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """FIX-3 路由面：data_dir 偏离部署形态（无 agent 锚）=400 统一错误体
    （error_type=WorkspaceLayoutError——锚点校验拒写面）。"""
    from waterprint_server.main import create_app
    from waterprint_server.settings import Settings

    stray = tmp_path / "elsewhere"
    (stray / "data").mkdir(parents=True)
    settings = Settings(
        projects_dir=tmp_path / "projects-x",
        exports_dir=tmp_path / "exports-x",
        data_dir=stray / "data",
        calc_workers=1,
        log_file=str(tmp_path / "ai-connection-anchor.log"),
    )
    executor = ThreadPoolExecutor(max_workers=1)
    application = create_app(settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            response = await async_client.get("/api/ai/connection")
    executor.shutdown(wait=True)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error_type"] == "WorkspaceLayoutError"
    assert "data_dir" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_connection_status_four_checks_wiring(
    ai_client, tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """GET 200：四项+聚合 ready 六键形态（uv 打桩伪路径——真机面零依赖）。"""
    monkeypatch.setattr(_service, "which", lambda _name: "/fake/bin/uv.exe")
    response = await ai_client.get("/api/ai/connection")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert set(body) == {
        "config_written",
        "config_paths",
        "agent_importable",
        "uv_path",
        "sandbox_root",
        "ready",
    }
    assert body["agent_importable"] is True  # 伪工作区 agent 包在场
    assert body["uv_path"] == "/fake/bin/uv.exe"
    assert body["ready"] is False  # 配置未写（config_written 假——聚合诚实）


@pytest.mark.anyio
async def test_post_setup_writes_workspace_configs_wiring(
    ai_client, tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """POST setup 200：两份配置原子写入+waterprint 条目固定 schema。"""
    monkeypatch.setattr(_service, "which", lambda _name: "/fake/bin/uv.exe")
    response = await ai_client.post("/api/ai/connection/setup")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    repo_root = tmp_path / "ws" / "waterprint"
    assert body["written_paths"] == [
        str(repo_root / ".zcode" / "config.json"),
        str(repo_root.parent / ".zcode" / "config.json"),
    ]
    entry = body["server_entry"]
    assert entry["command"] == "/fake/bin/uv.exe"
    assert entry["args"][1:2] == ["--directory"] and entry["args"][3:] == ["waterprint-mcp"]
    document = json.loads(
        (repo_root / ".zcode" / "config.json").read_text(encoding="utf-8")
    )
    assert document["mcp"]["servers"]["waterprint"]["command"] == "/fake/bin/uv.exe"
    # setup 后状态面翻绿（同 client 复查——status 与 setup 同真源）
    status_response = await ai_client.get("/api/ai/connection")
    assert status_response.json()["ready"] is True


@pytest.mark.anyio
async def test_post_setup_uv_missing_400_wiring(
    ai_client, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """uv 缺失=400 统一错误体 {detail, error_type=UvNotFoundError}。"""
    monkeypatch.setattr(_service, "which", lambda _name: None)
    response = await ai_client.post("/api/ai/connection/setup")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error_type"] == "UvNotFoundError"
    assert "uv" in body["detail"]


@pytest.mark.anyio
async def test_ai_connection_requires_token_when_configured(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """鉴权面沿册：token 非空时无 Bearer=401（include 级依赖与既有 router 同款）。"""
    from waterprint_server.main import create_app
    from waterprint_server.settings import Settings

    repo_root = tmp_path / "ws2" / "waterprint"
    (repo_root / "data").mkdir(parents=True)
    settings = Settings(
        projects_dir=tmp_path / "projects2",
        exports_dir=tmp_path / "exports2",
        data_dir=repo_root / "data",
        calc_workers=1,
        api_token="a" * 16,
        log_file=str(tmp_path / "ai-connection-auth.log"),
    )
    executor = ThreadPoolExecutor(max_workers=1)
    application = create_app(settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            monkeypatch.setattr(_service, "which", lambda _name: "/fake/bin/uv.exe")
            denied = await async_client.get("/api/ai/connection")
            assert denied.status_code == status.HTTP_401_UNAUTHORIZED
    executor.shutdown(wait=True)
