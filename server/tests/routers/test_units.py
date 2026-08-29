"""units 路由镜像测试：GET /api/units + GET /api/assumptions（200 形态/确定性）。

输入:  waterprint_server.routers.units 公开符号
输出:  路由契约断言（META1 D2 端点形态的路由面）
"""

from __future__ import annotations

import importlib
import json

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.units")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/units"), ("get", "/api/assumptions")}


def test_router_exposes_units_endpoints_wiring() -> None:
    """端点集 == 规格两件（GET /api/units + GET /api/assumptions——恰两件无漂移）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)


@pytest.mark.anyio
async def test_units_endpoint_returns_catalog_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """GET /api/units 200：36 条；aao 三口/hebing 三入一口/recycle 标记恰两口。"""
    response = await client.get("/api/units")
    assert response.status_code == status.HTTP_200_OK
    units = response.json()["units"]
    assert len(units) == 36
    aao = next(u for u in units if u["unit_id"] == "municipal_aao")
    assert [(p["port_id"], p["fluid"], p["direction"], p["recycle"]) for p in aao["ports"]] == [
        ("in", "WATER", "IN", False),
        ("out", "WATER", "OUT", False),
        ("sludge_out", "SLUDGE", "OUT", False),
    ]
    hebing = next(u for u in units if u["unit_id"] == "sludge_hebing")
    assert sum(1 for p in hebing["ports"] if p["direction"] == "IN") == 3
    assert sum(1 for p in hebing["ports"] if p["direction"] == "OUT") == 1
    recycle = sorted(
        (u["unit_id"], p["port_id"]) for u in units for p in u["ports"] if p["recycle"]
    )
    assert recycle == [("sludge_nongsuo", "sup"), ("sludge_tuoshui", "filtrate")]
    builtin = [u for u in units if u["kind"] == "builtin"]
    assert [u["unit_id"] for u in builtin] == [
        "municipal_input", "junction", "quality_edit", "recycle_junction"
    ]  # 内置四 kind 排末（kind 序）
    assert all(u["name_zh"] for u in units)  # 中文名服务端在册（D1 禁前端映射）


@pytest.mark.anyio
async def test_assumptions_endpoint_returns_registry_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """GET /api/assumptions 200：21 条（六字段取五——tuning_direction 在场）。"""
    response = await client.get("/api/assumptions")
    assert response.status_code == status.HTTP_200_OK
    assumptions = response.json()["assumptions"]
    assert len(assumptions) == 21
    assert assumptions[0]["key"] == "safety.superheight"
    assert assumptions[0]["dim"] == "LENGTH"
    assert all(
        {"key", "default", "dim", "source", "note", "tuning_direction"} <= set(a)
        for a in assumptions
    )


@pytest.mark.anyio
async def test_units_endpoints_double_fetch_byte_identical_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R4 确定性：两端点两次 GET 响应 JSON（sort_keys）字节同。"""
    for path in ("/api/units", "/api/assumptions"):
        first = (await client.get(path)).json()
        second = (await client.get(path)).json()
        assert json.dumps(first, sort_keys=True, ensure_ascii=False) == json.dumps(
            second, sort_keys=True, ensure_ascii=False
        ), f"{path} 双 GET 字节不同（确定性破坏）"
