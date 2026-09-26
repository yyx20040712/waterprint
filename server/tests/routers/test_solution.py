"""solution 路由镜像测试：联合枚举新正门 + 旧拒绝点仍在（B4-3 TDD 序 4）。

输入:  /api/solution/joint-enumerate 端点 + calc 旧枚举端点
输出:  新正门 200 全链/静态预检 422/旧 enumerate 多单元 422 仍在
"""

from __future__ import annotations

import asyncio

import pytest

pytestmark = [pytest.mark.anyio]


async def _wait_terminal(client, task_id: str) -> dict[str, object]:  # type: ignore[no-untyped-def]
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed", "cancelled"}:
            return body  # type: ignore[no-any-return]
        await asyncio.sleep(0.1)
    raise TimeoutError(task_id)


async def _create_project(client, payload) -> str:  # type: ignore[no-untyped-def]
    created = await client.post("/api/projects", json={"project": payload})
    assert created.status_code == 200
    return str(created.json()["project_id"])


def _joint_payload() -> dict[str, object]:
    """两目标项目（inlet→aao→cass——路由全链载体）。"""
    return {
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
                "municipal_cass": {},
            },
            "edges": [
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": "municipal_aao", "port_id": "in"}},
                {"src": {"unit_id": "municipal_aao", "port_id": "out"},
                 "dst": {"unit_id": "municipal_cass", "port_id": "in"}},
            ],
        },
        "view": {},
        "metadata": {
            "format_version": "1.0", "content_hash": "0",
            "engine_version": "0", "data_version": "0",
        },
    }


_GRIDS = {
    "municipal_aao": [{"field_id": "n", "values": [2.0, 3.0]}],
    "municipal_cass": [{"field_id": "n_pool", "values": [2.0, 3.0]}],
}


async def test_joint_enumerate_full_chain_200(client) -> None:  # type: ignore[no-untyped-def]
    """新正门 200 全链：提交→done→结果含语义标注+组合+预算四键。"""
    project_id = await _create_project(client, _joint_payload())
    submitted = await client.post(
        "/api/solution/joint-enumerate",
        json={
            "project_id": project_id,
            "unit_ids": ["municipal_cass", "municipal_aao"],  # 乱序→拓扑重排
            "options": {"grids": _GRIDS},
        },
    )
    assert submitted.status_code == 200
    final = await _wait_terminal(client, str(submitted.json()["task_id"]))
    assert final["state"] == "done", final
    result = final["result"]
    assert result["search_semantics"] == {
        "structure": "staged_beam", "optimality": "beam_approx",
        "loop_semantics": "frozen", "pruning_bias": "baseline_context",
    }
    assert result["combos"], "真实数据包下可行组合非空"
    top = result["combos"][0]
    assert set(top["params"]) == {"municipal_aao", "municipal_cass"}
    assert top["feasible"] is True and "sensitivity_degraded" in top
    assert "cost_opex_yuan_a" in top["metrics"] and "failed_conditions" in top
    usage = result["budget_usage"]
    assert usage["rows_evaluated"] == 6 and usage["full_plant_evals"] == len(
        result["combos"]
    )
    assert usage["truncated"] is False and usage["elapsed_ms"] >= 0


async def test_joint_enumerate_precheck_422(client) -> None:  # type: ignore[no-untyped-def]
    """静态预检 422：max_total_rows 项目覆盖收紧→事前拒（无任务产生）。"""
    payload = _joint_payload()
    payload["design"]["assumption_overrides"] = {
        "solution.joint.max_total_rows": 3.0
    }
    project_id = await _create_project(client, payload)
    rejected = await client.post(
        "/api/solution/joint-enumerate",
        json={"project_id": project_id,
              "unit_ids": ["municipal_aao", "municipal_cass"],
              "options": {"grids": _GRIDS}},
    )
    assert rejected.status_code == 422
    assert "静态预检" in str(rejected.json()["detail"])


async def test_joint_enumerate_empty_units_422(client) -> None:  # type: ignore[no-untyped-def]
    """unit_ids 空集=pydantic 422 面（min_length=1）。"""
    project_id = await _create_project(client, _joint_payload())
    rejected = await client.post(
        "/api/solution/joint-enumerate",
        json={"project_id": project_id, "unit_ids": []},
    )
    assert rejected.status_code == 422


async def test_old_enumerate_multi_unit_still_422(client) -> None:  # type: ignore[no-untyped-def]
    """旧拒绝点仍在：/api/calc/enumerate 多 unit_id=422（ADR-005 执法不松）。"""
    project_id = await _create_project(client, _joint_payload())
    rejected = await client.post(
        "/api/calc/enumerate",
        json={"project_id": project_id,
              "unit_ids": ["municipal_aao", "municipal_cass"]},
    )
    assert rejected.status_code == 422
    assert "单单元" in str(rejected.json()["detail"]) or "ADR-005" in str(
        rejected.json()["detail"]
    )


async def test_joint_enumerate_worker_carries_capex(client) -> None:  # type: ignore[no-untyped-def]
    """批2b 端到端第四真键（test_capex_server_draft 转正——[HUMAN-LOCK]
    2026-09-26 用户「全部追认」授权落地）：worker 注入 capex_data_dir→
    全链 done→top 组合 metrics 含 cost_capex_yuan 正值（三真键照旧）。"""
    project_id = await _create_project(client, _joint_payload())
    submitted = await client.post(
        "/api/solution/joint-enumerate",
        json={
            "project_id": project_id,
            "unit_ids": ["municipal_cass", "municipal_aao"],
            "options": {"grids": _GRIDS},
        },
    )
    assert submitted.status_code == 200, submitted.text
    final = await _wait_terminal(client, str(submitted.json()["task_id"]))
    assert final["state"] == "done", final
    result = final["result"]
    assert result["combos"], "真实数据包下可行组合非空"
    top = result["combos"][0]
    assert "cost_opex_yuan_a" in top["metrics"]  # 三真键照旧
    assert "cost_capex_yuan" in top["metrics"]  # 批2b 第四真键（worker 注入面）
    assert top["metrics"]["cost_capex_yuan"] > 0.0
