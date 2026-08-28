"""scene 路由镜像测试：GET /api/scene/{project_id}（缺省工况/错误面/确定性）。

输入:  waterprint_server.routers.scene 公开符号
输出:  路由契约断言（FE1 D1 端点形态的路由面）
"""

from __future__ import annotations

import asyncio
import importlib
import json

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.scene")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/scene/{project_id}")}


async def _project_with_result(client) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（结果集就绪——scene 消费前提）。"""
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
                    "municipal_cass": {},
                },
                "edges": [
                    {
                        "src": {"unit_id": "inlet", "port_id": "out"},
                        "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                    }
                ],
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
    project_id = created.json()["project_id"]
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


def test_router_exposes_scene_endpoint_wiring() -> None:
    """端点集 == 规格一件（GET /api/scene/{project_id}）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰一件无漂移


@pytest.mark.anyio
async def test_scene_returns_graph_with_default_condition_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：scene_version 回显+nodes 非空+instance_count≥1+缺省工况=排序首键回显。"""
    project_id, task_id = await _project_with_result(client)
    tasks = (await client.get(f"/api/calc/tasks/{task_id}")).json()
    expected_default = sorted(tasks["result"]["condition_keys"])[0]
    response = await client.get(f"/api/scene/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["scene_version"] == "waterprint-scene-1/y-up/m"  # R4 版本回显
    assert body["condition_key"] == expected_default  # 缺省=排序首键（显式回显）
    assert body["nodes"]  # 场景非空
    assert all(node["instance_count"] >= 1 for node in body["nodes"])  # 实例声明面
    assert body["root"]  # root 序非空
    assert set(body["root"]) <= {node["node_id"] for node in body["nodes"]}  # root⊆nodes
    explicit = await client.get(f"/api/scene/{project_id}", params={"condition_key": "design"})
    assert explicit.status_code == status.HTTP_200_OK
    assert explicit.json()["condition_key"] == "design"  # 显式工况透传


@pytest.mark.anyio
async def test_scene_double_fetch_byte_identical_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R1 确定性继承：两次 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _task_id = await _project_with_result(client)
    first = (await client.get(f"/api/scene/{project_id}")).json()
    second = (await client.get(f"/api/scene/{project_id}")).json()
    assert json.dumps(first, sort_keys=True, ensure_ascii=False) == json.dumps(
        second, sort_keys=True, ensure_ascii=False
    )


@pytest.mark.anyio
async def test_scene_error_faces_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404/工况非法 422（统一错误体 error_type）。"""
    missing = await client.get("/api/scene/nosuchproject0000")
    assert missing.status_code == status.HTTP_404_NOT_FOUND
    assert missing.json()["error_type"] == "ProjectNotFoundError"
    created = await client.post("/api/projects", json={})
    project_id = created.json()["project_id"]
    no_result = await client.get(f"/api/scene/{project_id}")
    assert no_result.status_code == status.HTTP_404_NOT_FOUND
    assert no_result.json()["error_type"] == "SceneSourceNotFoundError"  # 先重算指引
    assert "/api/calc/run" in str(no_result.json()["detail"])
    project_id, _task_id = await _project_with_result(client)
    invalid = await client.get(f"/api/scene/{project_id}", params={"condition_key": "zzz"})
    assert invalid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid.json()["error_type"] == "InvalidSceneRequestError"  # 透传 KeyError 文本
    assert "合法" in str(invalid.json()["detail"])
