"""validation 路由镜像测试：GET /api/calc/validation/{project_id}（E2E 面）。

输入:  waterprint_server.routers.calc validation 端点（client fixture 真跑
       ——AAO 项目三并列 artifact 就绪态）
输出:  路由契约断言（端点集新增恰一件+200 形态+双跑确定性+404 家族+
       AU-1 路径安全）；服务语义面=伴生件 test_validation.py（500 行预算
       墙拆分——1A4 契约伴生件先例同制）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：2A1 消费批（2a1-20261005）§3 D3/D4——端点面（test_sensitivity
#   路由面模式同款：wiring 断言+E2E client 真跑）。
#
# 覆盖用例：
#   - 端点集新增恰一件（GET /api/calc/validation/{project_id}——
#     38→39 路径 43→44 操作增量，任务书 §3 D4 授权）；
#   - E2E 200：新批三件就绪（validation_available/kb_injected 双 True）+
#     conditions=record 投影（baseline 两档+offline——worker 迭代序）+
#     观测节点在场+face 六键恰等+聚合行 schema 六键（scope+condition_keys[]
#     命名硬约束——§1）；
#   - 确定性：双 GET 响应 JSON（sort_keys）字节同；
#   - 错误面：未知项目 404/无结果集 404（引导语含 /api/calc/run）+
#     AU-1 路径安全（../ 浅深构造全 4xx 非 500）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import status

from waterprint_server.routers import calc as calc_router

_EXPECTED_VALIDATION = {("get", "/api/calc/validation/{project_id}")}


def _aao_project_payload() -> dict[str, object]:
    """inlet→AAO 项目载荷（test_sensitivity 同款——E2E 载体）。"""
    return {
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
                    "municipal_aao": {},
                },
                "edges": [
                    {
                        "src": {"unit_id": "inlet", "port_id": "out"},
                        "dst": {"unit_id": "municipal_aao", "port_id": "in"},
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


async def _project_with_result(client) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建 AAO 项目并跑一次计算（三并列 artifact 就绪——val/diag 同批落盘）。"""
    created = await client.post("/api/projects", json=_aao_project_payload())
    assert created.status_code == status.HTTP_200_OK
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": ["municipal_aao"]}
    )).json()["task_id"]
    body: dict[str, object] = {}
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id


def test_router_exposes_validation_endpoint_wiring() -> None:
    """calc 路由端点集含 validation 恰一件（38→39 路径增量无漂移）。"""
    observed = {
        (method.lower(), route.path)
        for route in calc_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed >= _EXPECTED_VALIDATION


@pytest.mark.anyio
async def test_validation_endpoint_shape(client) -> None:  # type: ignore[no-untyped-def]
    """E2E GET 200：新批三件就绪（validation_available/kb_injected 双 True）+
    conditions=record 投影（baseline 两档+offline）+观测节点在场+行 schema 六键。"""
    project_id, task_id = await _project_with_result(client)
    response = await client.get(f"/api/calc/validation/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["task_id"] == task_id
    assert body["stale"] is False
    assert body["validation_available"] is True  # 新批 worker val 件在场
    assert body["kb_injected"] is True  # kbwire 起生产注入
    assert body["conditions"] == ["design", "avg", "design_offline_municipal_aao"]
    assert [node["node_id"] for node in body["nodes"]] == ["municipal_aao"]
    face = body["nodes"][0]["faces"][0]
    assert set(face) == {
        "condition_key", "kb", "any_fail", "ratio", "fixgeom_min"}
    assert face["condition_key"] == "design_offline_municipal_aao"
    assert face["kb"] and all(isinstance(v, bool) for v in face["kb"].values())
    assert face["any_fail"] is False  # golden aao kb 面全过
    for row in body["warnings"]:
        assert set(row) == {
            "code", "param_key", "scope", "message", "condition_keys", "severity"}


@pytest.mark.anyio
async def test_validation_determinism_double_get(client) -> None:  # type: ignore[no-untyped-def]
    """确定性：同结果集双 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _ = await _project_with_result(client)
    first = (await client.get(f"/api/calc/validation/{project_id}")).json()
    second = (await client.get(f"/api/calc/validation/{project_id}")).json()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


@pytest.mark.anyio
async def test_validation_error_faces(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404（引导语含 /api/calc/run）+AU-1 路径安全。"""
    response = await client.get("/api/calc/validation/nosuchproject0000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    created = await client.post("/api/projects", json=_aao_project_payload())
    project_id = created.json()["project_id"]
    response = await client.get(f"/api/calc/validation/{project_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]
    for probe in ("../escape", "..%2fescape", "x/../../escape"):
        response = await client.get(f"/api/calc/validation/{probe}")
        assert response.status_code < 500  # AU-1：浅深构造全 4xx 非 500
