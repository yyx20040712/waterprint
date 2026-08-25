"""projects 路由镜像测试：CRUD 端点（薄层、路径安全、写锁）。

输入:  waterprint_server.routers.projects 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import importlib

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.projects")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.projects（服务层 M2）",
    ),
]

_EXPECTED = {
    ("post", "/api/projects"),
    ("get", "/api/projects"),
    ("get", "/api/projects/{project_id}"),
    ("put", "/api/projects/{project_id}"),
    ("post", "/api/projects/{project_id}/validate"),
}


def test_router_exposes_five_endpoints_wiring() -> None:
    """端点集 == 规格五件（POST/GET/GET/PUT/POST validate）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰五件无漂移


@pytest.mark.anyio
async def test_project_id_traversal_rejected_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：{id} 含 ../ 或绝对路径 → 4xx 非 500（§18）。"""
    for evil in ("/api/projects/..%2Fevil", "/api/projects/%2e%2e%2fevil"):
        response = await client.get(evil)
        assert 400 <= response.status_code < 500, f"{evil} → {response.status_code}"
        response = await client.put(evil, json={})
        assert 400 <= response.status_code < 500, f"PUT {evil} → {response.status_code}"
