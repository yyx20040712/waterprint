"""units 路由镜像测试：GET /api/units + GET /api/assumptions（200 形态/确定性）。

输入:  waterprint_server.routers.units 公开符号
输出:  路由契约断言（META1 D2 端点形态的路由面）
"""

from __future__ import annotations

import importlib

_mod = importlib.import_module("waterprint_server.routers.units")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/units"), ("get", "/api/assumptions")}


def test_router_exposes_units_endpoints_wiring() -> None:
    """端点集 == 规格两件（GET /api/units + GET /api/assumptions——恰两件无漂移）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)
