"""上传体积闸消费面（ENG2 D3）：定长超限 413 / 合法定长放行 / 无定长放行。

输入:  httpx ASGITransport 定长与流式请求体（max_upload_mb=1 覆盖）
输出:  体积闸行为断言（§18 上传面——settings.max_upload_mb 接线消费面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（ENG2 D3）
#
# 【用例三件】
#   ① 超限=413：Settings 覆盖 max_upload_mb=1 + 构造 >10**6 字节定长
#      body → status_code==413 且响应体 error_type=="PayloadTooLargeError"
#      （实值断言——非仅状态码）；
#   ② 合法定长请求不受扰（既有端点冒烟：POST /api/projects 小定长 200）；
#   ③ 无 Content-Length 场景：httpx 流式 content=（chunked 无定长）可
#      构造——断言放行（头缺席=放行规格；结构炸弹由深度闸 _check_depth
#      常驻守）；若测面不可构造则记档省略（不造假）。
#
# 【接线面】依赖层（routers/projects 两端点 Depends）而非中间件——避开
#   Starlette 用户中间件在 ExceptionMiddleware 之外的处理器次序陷阱。
# 【纪律】本文件随 lock_tests.py 同步入锁（用户总授权 2026-08-23，
#   实现报告详列该锁定动作）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from waterprint_server.main import create_app
from waterprint_server.settings import Settings

pytestmark = [pytest.mark.anyio]


@pytest.fixture
async def gate_client(test_settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """max_upload_mb=1 覆盖版 client（其余同 conftest client——ThreadPool 注入面）。"""
    settings = test_settings.model_copy(update={"max_upload_mb": 1})
    executor = ThreadPoolExecutor(max_workers=1)
    application = create_app(settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    executor.shutdown(wait=True)


async def test_oversized_body_rejected_with_413(gate_client: httpx.AsyncClient) -> None:
    """①超限=413：>10**6 字节定长 body → 413 + error_type 实值断言。"""
    padding = "x" * (10**2 * 10**2 * 10**2 + 10**2)  # >1MB（幂积口径同实现面）
    body = ('{"project": null, "padding": "' + padding + '"}').encode("utf-8")
    assert len(body) > 10**2 * 10**2 * 10**2  # 前提：确已超 1MB 上限
    response = await gate_client.post(
        "/api/projects", content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["error_type"] == "PayloadTooLargeError"


async def test_legal_fixed_body_undisturbed(gate_client: httpx.AsyncClient) -> None:
    """②合法定长请求不受扰：小定长 JSON 走既有创建端点冒烟 200。"""
    response = await gate_client.post("/api/projects", json={"project": None})
    assert response.status_code == 200
    assert response.json()["project_id"]


async def test_chunked_without_content_length_allowed(gate_client: httpx.AsyncClient) -> None:
    """③无 Content-Length（httpx 流式 content= 构造 chunked）→ 放行。"""
    payload = b'{"project": null}'

    async def stream() -> AsyncIterator[bytes]:
        yield payload[:5]
        yield payload[5:]

    response = await gate_client.post(
        "/api/projects", content=stream(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json()["project_id"]
