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
async def test_duplicate_submit_is_idempotent_wiring(
    client, cass_payload, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：同 (design_hash, condition) 重复提交返回同一 task_id。

    AU-9/R1-4④：进程池"只占一次"补派发计数直接断言（替身计数==1——
    幂等键命中即不重复入队派发，不占第二个执行位）。
    """
    import time

    import waterprint_server.jobs.manager as manager_mod

    dispatches: list[str] = []

    def counting_task(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        dispatches.append(str(payload["task_id"]))
        time.sleep(1 / 2)  # 保持非终态窗口（第二次提交落在幂等窗口内）
        return {"state": "done", "project_id": payload.get("project_id", "")}

    monkeypatch.setattr(manager_mod, "run_task", counting_task)
    created = await client.post("/api/projects", json={"project": cass_payload})
    assert created.status_code == 200
    project_id = created.json()["project_id"]
    body = {"project_id": project_id, "conditions": []}
    first = await client.post("/api/calc/run", json=body)
    second = await client.post("/api/calc/run", json=body)
    assert first.status_code == second.status_code == 200
    assert first.json()["task_id"] == second.json()["task_id"]  # 同 task_id
    final = await _wait_terminal(client, first.json()["task_id"])
    assert final["state"] in {"done", "failed"}
    assert len(dispatches) == 1  # 派发计数恰 1（幂等键命中不重复占池）


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


@pytest.mark.anyio
async def test_solutions_sort_cost_rejected_not_crash_wiring(
    client, cass_payload
) -> None:  # type: ignore[no-untyped-def]
    """AUDIT2 C-3：sort=cost 白名单含 cost 但列集无 cost 列——422 拒非 500。

    探针实录（2026-08-30）：done 枚举任务上 sort=cost → 500
    Internal Server Error（enumeration.py 白名单 ∪{cost} 而 feather 行集
    无 cost 列，sort_values KeyError）。修复口径：白名单=列集 ∪
    {margin_min}（cost 是导出侧概念非方案列——超集成员收口）。
    """
    created = await client.post("/api/projects", json={"project": cass_payload})
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/enumerate", json={"project_id": project_id, "unit_ids": ["municipal_cass"]}
    )).json()["task_id"]
    final = await _wait_terminal(client, task_id)
    assert final["state"] == "done"
    assert final["result"] is not None
    bad = await client.get(f"/api/calc/tasks/{task_id}/solutions", params={"sort": "cost"})
    assert bad.status_code == 422  # 修复前 500（探针实录）——白名单外显式拒
    assert "cost" in str(bad.json()["detail"])  # 拒因消息含被拒键（白名单面口径）


@pytest.mark.anyio
async def test_apply_solution_param_domain_guarded_wiring(
    client, cass_payload
) -> None:  # type: ignore[no-untyped-def]
    """AUDIT2 C-4：apply 参数域服务端守护（数值+已知键+grid 档位）。

    探针实录（2026-08-30）：{"n":"垃圾字符串值"} 与未知键均 200 入档，
    且此后该项目所有 calc failed（InvalidAssemblyError 未命中档位）——
    服务端边界与 ADR-005「值全 number」不符。修复口径：值=有限数值
    （bool/str/NaN 拒）+键=单元目录已知参数+grid 声明时值须命中档位。
    """
    created = await client.post("/api/projects", json={"project": cass_payload})
    project_id = created.json()["project_id"]

    # 字符串值 → 422（修复前 200 入档）
    str_value = await client.post("/api/calc/solutions/apply", json={
        "project_id": project_id, "unit_id": "municipal_cass",
        "params": {"n_pool": "垃圾字符串值"},
    })
    assert str_value.status_code == 422
    assert str_value.json()["error_type"] == "InvalidSolutionRefError"

    # 未知键 → 422（修复前 200 入档）
    unknown_key = await client.post("/api/calc/solutions/apply", json={
        "project_id": project_id, "unit_id": "municipal_cass",
        "params": {"ghost_key_never": 3},
    })
    assert unknown_key.status_code == 422
    assert "不在" in str(unknown_key.json()["detail"])  # 拒因含合法面指引

    # bool 值 → 422（既有面维持——bool 冒充 int 拒）
    bool_value = await client.post("/api/calc/solutions/apply", json={
        "project_id": project_id, "unit_id": "municipal_cass",
        "params": {"n_pool": True},
    })
    assert bool_value.status_code == 422

    # grid 档位外值 → 422（探针后续 calc failed 的 InvalidAssemblyError 前置到提交面）
    off_grid = await client.post("/api/calc/solutions/apply", json={
        "project_id": project_id, "unit_id": "municipal_cass",
        "params": {"n_pool": 7},
    })
    assert off_grid.status_code == 422
    assert "档位" in str(off_grid.json()["detail"])

    # 拒绝后项目档零污染（三次拒绝不入档——C-4 后果链切断实证）
    project_doc = (await client.get(f"/api/projects/{project_id}")).json()
    overrides = project_doc["design"]["nodes"]["municipal_cass"]
    assert overrides == {}, "拒绝的 apply 不得写入 design.nodes"
