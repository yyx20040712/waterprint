"""ai_config 路由镜像测试：GET/PUT /api/ai/config（F1 批 2026-09-25）。

输入:  waterprint_server.routers.ai_config 公开符号+隔离 CWD/env 的 client
输出:  路由契约断言（端点集两件/GET 五键形态/PUT 写盘+env 同步+他键行
       保留/空串清除语义/422 域校验四族/api_key 不回显）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（F1 批 2026-09-25；routers/ai_config.py 契约头镜像）
#
# 覆盖用例：
#   W1 路由集恰两件（GET+PUT /api/ai/config——无漂移）；
#   W2 GET 缺省形态：四键未设=unconfigured 五键投影+api_key 键缺席
#      （llm_timeout_s=120 缺省回显）；
#   W3 PUT 三键+超时：200+configured 翻真+.env 读改写（非本批键行
#      原样保留+旧四键行替换）+os.environ 同步（spawn 真值面）；
#   W4 空串清除：base_url=""→configured 翻假+.env 键行删除+env 空串；
#   W5 422 域校验族：前缀/长度×2/超时界外；错误体零 api_key 值回显。
# 隔离：monkeypatch.chdir(tmp)+四键 delenv（PUT 直写 os.environ 由
#   monkeypatch 退出恢复——跨用例零污染）。
# 呈批件：本文件与 test_api_contract.py 增量由锁面流程落库（[HUMAN-LOCK]）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.ai_config")
router = getattr(_mod, "router")

_AI_ENV_KEYS = (
    "WATERPRINT_AI_BASE_URL",
    "WATERPRINT_AI_API_KEY",
    "WATERPRINT_AI_MODEL",
    "WATERPRINT_AI_LLM_TIMEOUT_S",
)


@pytest.fixture
def anyio_backend() -> str:
    """anyio 后端=asyncio（与 server/tests/conftest.py 同值——本件自含可独立跑）。"""
    return "asyncio"


def test_router_exposes_ai_config_endpoints_wiring() -> None:
    """W1：端点集 == 规格两件（GET+PUT /api/ai/config——恰两件无漂移）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed == {("get", "/api/ai/config"), ("put", "/api/ai/config")}


@pytest.fixture
async def config_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[httpx.AsyncClient]:
    """隔离 CWD+四键 env 的 app client（conftest.client 同款装配）。"""
    from waterprint_server.main import create_app
    from waterprint_server.settings import Settings

    monkeypatch.chdir(tmp_path)
    for key in _AI_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    settings = Settings(
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=tmp_path / "data",
        calc_workers=1,
        log_file=str(tmp_path / "ai-config-router.log"),
    )
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
async def test_get_defaults_unconfigured(config_client: httpx.AsyncClient) -> None:
    """W2：四键未设=五键缺省投影（configured 假+timeout 120+api_key 键缺席）。"""
    response = await config_client.get("/api/ai/config")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body == {
        "base_url": "",
        "model": "",
        "has_api_key": False,
        "llm_timeout_s": 120,
        "configured": False,
    }
    assert "api_key" not in body  # 明文字段任何面缺席（R1 红线）


@pytest.mark.anyio
async def test_put_roundtrip_writes_env_and_preserves_other_lines(
    config_client: httpx.AsyncClient, tmp_path: Path
) -> None:
    """W3：三键+超时 PUT→200 翻真+.env 他键行保留+env 四键同步。"""
    (tmp_path / ".env").write_text(
        "WATERPRINT_LOG_LEVEL=DEBUG\nOTHER_TOOL_KEY=keepme\nWATERPRINT_AI_MODEL=stale-model\n",
        encoding="utf-8",
    )
    response = await config_client.put(
        "/api/ai/config",
        json={
            "base_url": "https://api.example.com/v1",
            "model": "m-test",
            "api_key": "sk-test-secret",
            "llm_timeout_s": 300,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["configured"] is True
    assert body["has_api_key"] is True
    assert "sk-test-secret" not in response.text  # 密钥零回显（响应面）
    # .env：他键行原样+旧四键行替换为本批四行
    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "WATERPRINT_LOG_LEVEL=DEBUG" in env_text
    assert "OTHER_TOOL_KEY=keepme" in env_text
    assert "stale-model" not in env_text
    assert "WATERPRINT_AI_BASE_URL=https://api.example.com/v1" in env_text
    assert "WATERPRINT_AI_MODEL=m-test" in env_text
    assert "WATERPRINT_AI_API_KEY=sk-test-secret" in env_text
    assert "WATERPRINT_AI_LLM_TIMEOUT_S=300" in env_text
    # 运行时生效：进程 env 同步（spawn 子通道真值——不重启即生效）
    assert os.environ["WATERPRINT_AI_BASE_URL"] == "https://api.example.com/v1"
    assert os.environ["WATERPRINT_AI_API_KEY"] == "sk-test-secret"
    # GET 复查=PUT 后真值
    reread = (await config_client.get("/api/ai/config")).json()
    assert reread["configured"] is True
    assert reread["llm_timeout_s"] == 300


@pytest.mark.anyio
async def test_put_empty_string_clears_key(
    config_client: httpx.AsyncClient, tmp_path: Path
) -> None:
    """W4：空串=清除——configured 翻假+.env 键行删除+env 空串。"""
    await config_client.put(
        "/api/ai/config",
        json={"base_url": "https://api.example.com/v1", "model": "m", "api_key": "sk-x"},
    )
    response = await config_client.put("/api/ai/config", json={"base_url": ""})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["configured"] is False  # base_url 缺=降级态
    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "WATERPRINT_AI_BASE_URL" not in env_text  # 空值键行删除（R3）
    assert os.environ["WATERPRINT_AI_BASE_URL"] == ""  # env 空串清除语义（R4）


@pytest.mark.anyio
async def test_put_domain_validation_422_family(config_client: httpx.AsyncClient) -> None:
    """W5：域校验族 422+统一错误体（前缀/长度×2/超时界外）。"""
    cases = (
        {"base_url": "ftp://bad.example.com"},
        {"base_url": "https://" + "x" * 501},
        {"model": "m" * 101},
        {"api_key": "k" * 501},
        {"llm_timeout_s": 4},
        {"llm_timeout_s": 901},
    )
    for payload in cases:
        response = await config_client.put("/api/ai/config", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, payload
        body = response.json()
        assert "detail" in body and "error_type" in body  # 统一错误体形态
    # 密钥值零回显（错误消息面——R2 消息零值嵌入）
    long_key = "k" * 501
    response = await config_client.put("/api/ai/config", json={"api_key": long_key})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert long_key not in response.text



@pytest.mark.anyio
async def test_put_control_chars_rejected_no_env_injection(
    config_client: httpx.AsyncClient, tmp_path: Path
) -> None:
    """回炉 B-1：值内换行/控制字符=422 且 .env 零注入（行注入面封死）。"""
    cases = (
        {"base_url": "http://a.com\nWATERPRINT_SECRET=evil"},
        {"base_url": "http://a.com\r\nX=1"},
        {"api_key": "k\x00x"},
        {"model": "m\x7fdel"},
    )
    for payload in cases:
        response = await config_client.put("/api/ai/config", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, payload
        assert "控制字符" in response.json()["detail"]
    env_text = (
        (tmp_path / ".env").read_text(encoding="utf-8")
        if (tmp_path / ".env").is_file()
        else ""
    )
    assert "WATERPRINT_SECRET" not in env_text  # 注入键零落盘
    assert "X=1" not in env_text


@pytest.mark.anyio
async def test_put_scheme_case_and_host_checks(config_client: httpx.AsyncClient) -> None:
    """回炉 N-8：大写 scheme 放行；裸 scheme（无主机部）422。"""
    ok = await config_client.put(
        "/api/ai/config", json={"base_url": "HTTP://Example.com/v1", "model": "m", "api_key": "k"}
    )
    assert ok.status_code == status.HTTP_200_OK
    assert ok.json()["configured"] is True
    for bad in ("http://", "https:///", "HTTP://"):
        response = await config_client.put("/api/ai/config", json={"base_url": bad})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, bad


@pytest.mark.anyio
async def test_put_non_utf8_env_file_guided_error(
    config_client: httpx.AsyncClient, tmp_path: Path
) -> None:
    """回炉 W-7：.env 非 UTF-8=422 引导转存（原 UnicodeDecodeError 炸 500 面）。"""
    (tmp_path / ".env").write_bytes("WATERPRINT_AI_MODEL=旧\n".encode("gbk"))
    response = await config_client.put("/api/ai/config", json={"model": "m"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "UTF-8" in response.json()["detail"]
