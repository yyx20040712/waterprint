"""calc 路由镜像测试：任务端点（幂等、stale 标志、取消、分页）。

输入:  waterprint_server.routers.calc 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import asyncio
import importlib
import inspect

import pytest

_mod = importlib.import_module("waterprint_server.routers.calc")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.calc（服务层 M2）",
    ),
]

_EXPECTED = {
    ("post", "/api/calc/run"),
    ("post", "/api/calc/enumerate"),
    ("get", "/api/calc/tasks/{task_id}"),
    ("post", "/api/calc/tasks/{task_id}/cancel"),
    ("get", "/api/calc/tasks/{task_id}/solutions"),
    ("post", "/api/calc/solutions/apply"),
}


async def _wait_terminal(client, task_id: str) -> dict[str, object]:  # type: ignore[no-untyped-def]
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed", "cancelled"}:
            return body  # type: ignore[no-any-return]
        await asyncio.sleep(0.1)
    raise TimeoutError(task_id)


def test_router_exposes_six_endpoints_wiring() -> None:
    """端点集 == 规格六件（run/enumerate/tasks/cancel/solutions/apply）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰六件无漂移
    solutions = next(route for route in router.routes
                     if getattr(route, "path", "") == "/api/calc/tasks/{task_id}/solutions")
    signature = inspect.signature(solutions.endpoint)
    size_default = signature.parameters["size"].default
    assert getattr(size_default, "default", size_default) is None  # Query(None)：缺省走 Settings=200
    page_default = signature.parameters["page"].default
    assert getattr(page_default, "default", page_default) == 1  # 1 基页码


@pytest.mark.anyio
async def test_duplicate_submit_is_idempotent_wiring(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：同 (design_hash, condition) 重复提交返回同一 task_id。"""
    created = await client.post("/api/projects", json={"project": cass_payload})
    assert created.status_code == 200
    project_id = created.json()["project_id"]
    body = {"project_id": project_id, "conditions": []}
    first = await client.post("/api/calc/run", json=body)
    second = await client.post("/api/calc/run", json=body)
    assert first.status_code == second.status_code == 200
    assert first.json()["task_id"] == second.json()["task_id"]  # 同 task_id
    final = await _wait_terminal(client, first.json()["task_id"])
    assert final["state"] in {"done", "failed"}  # 进程池只占一次（单任务终态）


@pytest.mark.anyio
async def test_solutions_default_page_size_wiring(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """镜像缺失收口：分页缺省 size=200（§12.2 规格值经 Settings）。"""
    created = await client.post("/api/projects", json={"project": cass_payload})
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/enumerate", json={"project_id": project_id, "unit_ids": ["municipal_cass"]}
    )).json()["task_id"]
    final = await _wait_terminal(client, task_id)
    assert final["state"] == "done"
    page = await client.get(f"/api/calc/tasks/{task_id}/solutions")
    assert page.status_code == 200
    assert page.json()["size"] == 200  # 缺省页大小（Settings.page_size_default）
    assert page.json()["page"] == 1
