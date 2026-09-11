"""trust 路由镜像测试：GET /api/calc/trust/{project_id}（诊断/聚合/降级/错误面）。

输入:  waterprint_server.routers.calc trust 端点 + services.trust 公开符号
输出:  路由契约断言（P2 次批 ADR-012 D8 端点形态的路由面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（P2 次批 ADR-012；test_elevation 同款路由面模式）
#
# 覆盖用例：
#   - 端点集新增恰一件（GET /api/calc/trust/{project_id}——31→32 增量）；
#   - 200 正门：CASS 项目（六指标全）跑一次计算→diagnostics_available
#     =True+loop_params 三键+mass_balance 双工况+effluent 2 标准×6 指标
#     ×工况+margin=(限值−值)/限值 手算对照+repro 三元组/task_id 回显+
#     stale=False+warnings 面与计数一致（R2~R4）；
#   - 确定性：双 GET 响应 JSON（sort_keys）字节同（R5）；
#   - 降级态：删 diag 件→diagnostics_available=False+诊断三面空+
#     warnings 仍在（ADR-012 R1 旧结果语义）；
#   - 错误面：未知项目 404（ProjectNotFoundError）/无结果集 404
#     （TrustSourceNotFoundError——引导语含 /api/calc/run）；
#   - AU-1 路径安全（workflow §4-4 必选项）：../ 浅深构造全 4xx 非 500。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import json
import os

import pytest
from fastapi import status

from waterprint_server.routers import calc as calc_router

_EXPECTED_TRUST = {("get", "/api/calc/trust/{project_id}")}


async def _project_with_result(client) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建六指标 CASS 项目并跑一次计算（结果集+诊断件就绪）。"""
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


def test_router_exposes_trust_endpoint_wiring() -> None:
    """calc 路由端点集含 trust 恰一件（31→32 增量无漂移）。"""
    observed = {
        (method.lower(), route.path)
        for route in calc_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed >= _EXPECTED_TRUST


@pytest.mark.anyio
async def test_trust_report_full_diagnostics(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：诊断四面聚合+裕度手算对照+新鲜度/溯源回显（R2~R5）。"""
    project_id, task_id = await _project_with_result(client)
    response = await client.get(f"/api/calc/trust/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["diagnostics_available"] is True
    assert body["task_id"] == task_id
    assert body["stale"] is False
    assert body["design_hash"] and body["engine_version"] and body["data_version"]
    # 收敛口径三键（ADR-012 D2——loop.* 终值透明）
    assert set(body["loop_params"]) == {
        "loop.tolerance", "loop.max_iterations", "loop.damping",
    }
    # 水量闭合：baseline 双工况面在场（CASS 无回路→convergence 空）
    assert body["convergence"] == []
    condition_keys = {item["condition_key"] for item in body["mass_balance"]}
    assert condition_keys == {"design", "avg"}
    for closure in body["mass_balance"]:
        water = next(line for line in closure["lines"] if line["fluid"] == "WATER")
        assert water["q_sources_total"] > 0.0
        assert water["closure_rel"] == pytest.approx(0.0)
    # 裕度：2 标准×6 指标×工况；margin=(限值−值)/限值 手算对照（真源标准）
    entries = {
        (item["condition_key"], item["standard_id"], item["indicator"]): item
        for item in body["effluent"]
    }
    assert len(entries) == 2 * 6 * 2  # 2 标准 × 6 指标 × 2 工况
    entry = entries[("design", "gb18918.level_a", "BOD5")]
    assert entry["limit"] == 10.0
    assert entry["margin"] == pytest.approx((10.0 - entry["value"]) / 10.0)
    # 警告面与计数一致（R3——六键透传面以键域校验）
    for warning in body["warnings"]:
        assert {"unit_id", "severity", "source", "message"} <= set(warning)
    assert sum(body["warning_counts"].values()) == len(body["warnings"])


@pytest.mark.anyio
async def test_trust_report_deterministic(client) -> None:  # type: ignore[no-untyped-def]
    """确定性：同结果集双 GET 响应 JSON（sort_keys）字节同（R5）。"""
    project_id, _ = await _project_with_result(client)
    first = await client.get(f"/api/calc/trust/{project_id}")
    second = await client.get(f"/api/calc/trust/{project_id}")
    assert json.dumps(first.json(), sort_keys=True) == json.dumps(
        second.json(), sort_keys=True
    )


@pytest.mark.anyio
async def test_trust_degrades_without_diag_file(client) -> None:  # type: ignore[no-untyped-def]
    """降级态：diag 件缺失→diagnostics_available=False+诊断三面空+warnings 仍在。"""
    project_id, task_id = await _project_with_result(client)
    task = (await client.get(f"/api/calc/tasks/{task_id}")).json()
    diag_file = task["result"]["diag_file"]
    assert diag_file, "P2 次批 worker 恒写 diag 件（ADR-012 D1）"
    os.remove(diag_file)
    response = await client.get(f"/api/calc/trust/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["diagnostics_available"] is False
    assert body["loop_params"] == {} and body["convergence"] == []
    assert body["mass_balance"] == [] and body["effluent"] == []
    assert isinstance(body["warnings"], list)  # 总线自有面不受降级影响（R2）


@pytest.mark.anyio
async def test_trust_404_unknown_project(client) -> None:  # type: ignore[no-untyped-def]
    """未知项目 404（ProjectNotFoundError——main 映射表）。"""
    response = await client.get("/api/calc/trust/absent-project")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_trust_404_without_result(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """项目在册无结果集 404（TrustSourceNotFoundError——引导语含 calc/run）。"""
    created = await client.post("/api/projects", json=cass_payload)
    project_id = created.json()["project_id"]
    response = await client.get(f"/api/calc/trust/{project_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]


@pytest.mark.anyio
@pytest.mark.parametrize("depth", ["..", "../..", "../../.."])
async def test_trust_path_traversal_all_4xx(client, depth: str) -> None:  # type: ignore[no-untyped-def]
    """AU-1 路径安全：../ 浅深构造全 4xx 非 500（workflow §4-4 必选项）。"""
    response = await client.get(f"/api/calc/trust/{depth}")
    assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.status_code != status.HTTP_200_OK
