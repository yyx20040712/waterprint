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
from waterprint.geometry import SCENE_VERSION  # 测试面专用 core 真源引用（test_cost.py 先例）

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
    assert body["scene_version"] == SCENE_VERSION  # R4 版本回显（core 真源常量——L5a 步进 -2，禁字面漂移）
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


@pytest.mark.anyio
async def test_scene_stale_flag_on_design_edit_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """AUDIT2 C-1：PUT 改档不重算→响应 stale=True（R4 显式提示非静默）。

    scene 与 elevation/cost 同族口径（三读端点一致收口）；响应模型=
    服务层 SceneResponse（core.SceneGraph 四字段+stale——core 零触碰，
    服务层拥有新鲜度语义）。
    """
    project_id, _task_id = await _project_with_result(client)
    fresh = await client.get(f"/api/scene/{project_id}")
    assert fresh.status_code == status.HTTP_200_OK
    assert fresh.json()["stale"] is False  # 新鲜结果集
    project_doc = (await client.get(f"/api/projects/{project_id}")).json()
    for node_value in project_doc["design"]["nodes"].values():
        if isinstance(node_value, dict) and "q_avg_daily" in node_value:
            node_value["q_avg_daily"] = 0.2
            break
    put = await client.put(f"/api/projects/{project_id}", json=project_doc)
    assert put.status_code == status.HTTP_200_OK
    assert put.json()["design_changed"] is True
    stale = await client.get(f"/api/scene/{project_id}")
    assert stale.status_code == status.HTTP_200_OK
    assert stale.json()["stale"] is True  # 旧快照+显式过期旗标
