"""exports 路由镜像测试：导出端点（stale 守门、文件名安全）。

输入:  waterprint_server.routers.exports 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import asyncio
import importlib

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.exports")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.exports（服务层 M2/M3）",
    ),
]

_EXPECTED = {
    ("post", "/api/exports/calcbook"),
    ("post", "/api/exports/audit"),
    ("post", "/api/exports/dxf"),
    ("post", "/api/exports/estimate"),
    ("get", "/api/exports"),
}


async def _project_with_result(client) -> str:  # type: ignore[no-untyped-def]
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
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id  # type: ignore[no-any-return]


def test_router_exposes_five_endpoints_wiring() -> None:
    """端点集 == 规格五件（calcbook/audit/dxf/estimate/列表）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰五件无漂移


@pytest.mark.anyio
async def test_stale_result_returns_409_with_context_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：结果集三元组过期且未 force → 409 附输入版本信息与摘要值。"""
    project_id, task_id = await _project_with_result(client)
    tasks = (await client.get(f"/api/calc/tasks/{task_id}")).json()
    result_digest = tasks["result"]["design_hash"]  # 结果集三元组摘要真值
    project = (await client.get(f"/api/projects/{project_id}")).json()
    project["design"]["assumption_overrides"] = {"safety.superheight": 0.3}
    saved = await client.put(f"/api/projects/{project_id}", json=project)
    assert saved.status_code == 200 and saved.json()["design_changed"] is True
    stale = await client.post("/api/exports/calcbook", json={"project_id": project_id})
    assert stale.status_code == status.HTTP_409_CONFLICT
    detail = str(stale.json()["detail"])
    assert "输入版本" in detail  # 附输入版本信息
    assert result_digest[:6] in detail  # 摘要值锁定（AU-6/R1-4②——非仅关键词）
    forced = await client.post(
        "/api/exports/calcbook", json={"project_id": project_id}, params={"force": "true"}
    )
    assert forced.status_code == status.HTTP_200_OK  # force=1 导出旧结果（文件流）
    metas = await client.get("/api/exports", params={"project_id": project_id})
    assert any(meta["stale_labeled"] for meta in metas.json())  # 旧三元组显式标注


@pytest.mark.anyio
async def test_traversal_export_rejected_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """AU-1/R1-1 路由面：condition_key/items kind 穿越 → 422 且产物零新增落盘。"""
    import os

    project_id, _task_id = await _project_with_result(client)
    exports_dir = test_settings.exports_dir
    before_listing = sorted(os.listdir(exports_dir))
    before_files = sorted(str(p) for p in exports_dir.parent.parent.rglob("*"))
    shallow = await client.post(
        "/api/exports/calcbook",
        json={"project_id": project_id, "condition_key": "a/../../evil"},
    )
    assert shallow.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT  # 越界即拒
    deep = await client.post(
        "/api/exports/calcbook",
        json={"project_id": project_id, "condition_key": "b/" + "../" * 10 + "deep"},
    )
    assert deep.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    batch = await client.post(
        "/api/exports/calcbook",
        json={
            "project_id": project_id,
            "options": {"items": [{"kind": "calcbook/../../evil", "condition_key": ""}]},
        },
    )
    assert batch.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert sorted(os.listdir(exports_dir)) == before_listing  # exports_dir 零新增
    assert sorted(str(p) for p in exports_dir.parent.parent.rglob("*")) == before_files
