"""site 路由镜像测试：GET /api/site/spacing（三态/降级/错误面/确定性）。

输入:  waterprint_server.routers.site 公开符号+client 装配
输出:  路由契约断言（L4b 端点形态的路由面——间距校核黄红标示数据源）
"""

from __future__ import annotations

import asyncio
import importlib
import json

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.site")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/site/spacing")}

# kb 1.3.0 已追认阈值（Ruling 2026-09-03——site.clearance_general 通用全对 WARN）
_GENERAL_CLEARANCE_M = 6.0


async def _spacing_project(client, *, run_calc: bool, close_pair: bool):  # type: ignore[no-untyped-def]
    """建含 site 摆放的项目（chenshachi+cass 链式双单元——足迹双可算）。

    close_pair=True：两池近摆（净距 clamp 0——通用 WARN 必越）；False：远摆
    （净距 >6 m——合规态）。run_calc=False：未计算降级态（uncalculated 全量）。
    """
    cass_x = 10.0 if close_pair else 500.0
    payload = {
        "project": {
            "format_version": "1.0",
            "design": {
                "nodes": {
                    "inlet": {
                        "kind": "municipal_input",
                        "q_avg_daily": 34760.7 / 86400,
                        "kz": 1.4,
                        "CODCR": 400.0,
                        "BOD5": 200.0,
                        "SS": 250.0,
                        "NH3N": 26.0,
                        "TN": 43.0,
                        "TP": 6.5,
                    },
                    "municipal_chenshachi": {},
                    "municipal_cass": {},
                },
                "edges": [
                    {
                        "src": {"unit_id": "inlet", "port_id": "out"},
                        "dst": {"unit_id": "municipal_chenshachi", "port_id": "in"},
                    },
                    {
                        "src": {"unit_id": "municipal_chenshachi", "port_id": "out"},
                        "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                    },
                ],
                "site": {
                    "structures": {
                        "municipal_chenshachi": {
                            "x": 0.0, "y": 0.0, "rotation": 0.0, "ground_elevation": None,
                        },
                        "municipal_cass": {
                            "x": cass_x, "y": 0.0, "rotation": 0.0, "ground_elevation": None,
                        },
                    },
                },
            },
            "view": {},
            "metadata": {
                "format_version": "1.0",
                "content_hash": "0",
                "engine_version": "0",
                "data_version": "0",
            },
        }
    }
    created = await client.post("/api/projects", json=payload)
    assert created.status_code == status.HTTP_200_OK
    project_id = created.json()["project_id"]
    if not run_calc:
        return project_id, None
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": []}
    )).json()["task_id"]
    body: dict[str, object] = {}
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id


def test_router_exposes_site_endpoints_wiring() -> None:
    """端点集 == 规格一件（GET /api/site/spacing——恰一件无漂移）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)


@pytest.mark.anyio
async def test_spacing_violation_state_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """越限态：近摆双池→violations 恰一对（通用 WARN）+uncalculated 空。"""
    project_id, _task_id = await _spacing_project(client, run_calc=True, close_pair=True)
    response = await client.get("/api/site/spacing", params={"project_id": project_id})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["uncalculated"] == []
    violations = body["violations"]
    assert len(violations) == 1
    row = violations[0]
    assert (row["a"], row["b"]) == ("municipal_cass", "municipal_chenshachi")
    assert row["clearance_m"] == 0.0  # 近摆重叠 clamp 0
    assert row["threshold_m"] == _GENERAL_CLEARANCE_M
    assert row["severity"] == "WARN"
    assert set(row) == {"a", "b", "clearance_m", "threshold_m", "severity"}


@pytest.mark.anyio
async def test_spacing_compliant_state_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """合规态：远摆双池→violations 空+uncalculated 空（阈值恰过=合格）。"""
    project_id, _task_id = await _spacing_project(client, run_calc=True, close_pair=False)
    response = await client.get("/api/site/spacing", params={"project_id": project_id})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["violations"] == []
    assert body["uncalculated"] == []


@pytest.mark.anyio
async def test_spacing_uncalculated_degrades_not_rejects_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """未计算态：无完成计算=200 降级（violations 空+uncalculated 全量——不 404/409）。"""
    project_id, _task_id = await _spacing_project(client, run_calc=False, close_pair=True)
    response = await client.get("/api/site/spacing", params={"project_id": project_id})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["violations"] == []
    assert body["uncalculated"] == ["municipal_cass", "municipal_chenshachi"]  # sorted


@pytest.mark.anyio
async def test_spacing_error_faces_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/工况非法 422（统一错误体 error_type）。"""
    missing = await client.get("/api/site/spacing", params={"project_id": "nosuchproject0000"})
    assert missing.status_code == status.HTTP_404_NOT_FOUND
    assert missing.json()["error_type"] == "ProjectNotFoundError"
    project_id, _task_id = await _spacing_project(client, run_calc=True, close_pair=True)
    invalid = await client.get(
        "/api/site/spacing", params={"project_id": project_id, "condition_key": "zzz"}
    )
    assert invalid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid.json()["error_type"] == "InvalidSpacingRequestError"
    assert "合法" in str(invalid.json()["detail"])
    explicit = await client.get(
        "/api/site/spacing", params={"project_id": project_id, "condition_key": "design"}
    )
    assert explicit.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_spacing_double_fetch_byte_identical_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """确定性：两次 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _task_id = await _spacing_project(client, run_calc=True, close_pair=True)
    first = (await client.get("/api/site/spacing", params={"project_id": project_id})).json()
    second = (await client.get("/api/site/spacing", params={"project_id": project_id})).json()
    assert json.dumps(first, sort_keys=True, ensure_ascii=False) == json.dumps(
        second, sort_keys=True, ensure_ascii=False
    )
