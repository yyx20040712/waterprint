"""compare 路由/服务镜像测试：GET /api/calc/compare/{project_id}（矩阵/新鲜度/错误面）。

输入:  waterprint_server.routers.calc compare 端点 + services.compare 公开符号
输出:  路由契约断言（P2 第三批 ADR-018 D5 端点形态的路由面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（P2 第三批 ADR-018；test_trust 同款路由面模式）
#
# 覆盖用例：
#   - 端点集新增恰一件（GET /api/calc/compare/{project_id}——32→33 增量）；
#   - 200 正门：AAO 项目（out_dims 21 条声明面）跑一次计算→condition_keys
#     =sorted 双工况+metrics 行=AAO 声明面（v_o 好氧区容积在场×双工况
#     有限值）+warnings 形状（零计数单元不出）+stale=False+design_hash/
#     task_id 回显（R2~R4）；
#   - 确定性：双 GET 响应 JSON（sort_keys）字节同（R5）；
#   - stale 态：PUT design 改参→stale=True（result_is_stale 同口径）+
#     design_hash 回显不变（结果件真源——ADR-018 D3 比对面记档）；
#   - 错误面：未知项目 404（ProjectNotFoundError）/无结果集 404
#     （CompareSourceNotFoundError——引导语含 /api/calc/run）；
#   - AU-1 路径安全（workflow §4-4 必选项）：../ 浅深构造全 4xx 非 500。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import status

from waterprint_server.routers import calc as calc_router

_EXPECTED_COMPARE = {("get", "/api/calc/compare/{project_id}")}


def _aao_project_payload() -> dict[str, object]:
    """inlet→AAO 项目载荷（AAO=out_dims 21 条声明面——V2 批首例单元）。"""
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


async def _project_with_result(client, payload: dict[str, object] | None = None) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建 AAO 项目并跑一次计算（结果集就绪）。"""
    created = await client.post(
        "/api/projects", json=payload if payload is not None else _aao_project_payload()
    )
    assert created.status_code == status.HTTP_200_OK
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


def test_router_exposes_compare_endpoint_wiring() -> None:
    """calc 路由端点集含 compare 恰一件（32→33 增量无漂移）。"""
    observed = {
        (method.lower(), route.path)
        for route in calc_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed >= _EXPECTED_COMPARE


@pytest.mark.anyio
async def test_compare_matrix_shape_and_metrics(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：矩阵形状+指标行（out_dims 声明面）+新鲜度/溯源回显（R2~R4）。"""
    project_id, task_id = await _project_with_result(client)
    response = await client.get(f"/api/calc/compare/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["task_id"] == task_id
    assert body["stale"] is False
    assert body["design_hash"] and body["engine_version"] and body["data_version"]
    assert body["condition_keys"] == ["avg", "design"]  # sorted 确定性（R5）
    # 指标行=AAO out_dims 声明面（V2 首例 21 条；inlet 无 manifest 不参与）
    units = {row["unit_id"] for row in body["metrics"]}
    assert units == {"municipal_aao"}
    by_field = {(row["unit_id"], row["field_id"]): row for row in body["metrics"]}
    v_o = by_field[("municipal_aao", "v_o")]
    assert v_o["label_zh"] == "好氧区容积"  # 中文名真源投影
    assert set(v_o["values"]) == {"avg", "design"}  # 双工况有限值齐
    assert all(isinstance(value, float) for value in v_o["values"].values())
    assert len(body["metrics"]) == 23  # AAO 全声明面在场（21→23：曝气头数据面批两键）
    # 警告计数形状：unit_id 域 ⊆ 结果集单元域（零计数单元不出——稀疏面）
    for row in body["warnings"]:
        assert row["unit_id"] in {"municipal_aao"}
        assert all(count >= 1 for count in row["counts"].values())


@pytest.mark.anyio
async def test_compare_determinism_double_get(client) -> None:  # type: ignore[no-untyped-def]
    """R5：同结果集双 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _ = await _project_with_result(client)
    first = (await client.get(f"/api/calc/compare/{project_id}")).json()
    second = (await client.get(f"/api/calc/compare/{project_id}")).json()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


@pytest.mark.anyio
async def test_compare_stale_after_design_change(client) -> None:  # type: ignore[no-untyped-def]
    """R4：PUT design 改参→stale=True；design_hash 回显=结果件真源不变
    （ADR-018 D3 比对面——改设计→重算→新结果件 hash 才换，锁定基准过期
    判定正交于 stale 表层）。"""
    project_id, _ = await _project_with_result(client)
    before = (await client.get(f"/api/calc/compare/{project_id}")).json()
    assert before["stale"] is False
    saved = (await client.get(f"/api/projects/{project_id}")).json()
    project = dict(saved)
    project["design"]["nodes"]["municipal_aao"]["n"] = 3.0  # 设计参数变更
    put = await client.put(f"/api/projects/{project_id}", json=project)
    assert put.status_code == status.HTTP_200_OK
    after = (await client.get(f"/api/calc/compare/{project_id}")).json()
    assert after["stale"] is True  # result_is_stale 同口径（digest 漂移）
    assert after["design_hash"] == before["design_hash"]  # 结果件 repro 真源


@pytest.mark.anyio
async def test_compare_error_faces(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404（引导语含 /api/calc/run）+AU-1 路径安全。"""
    response = await client.get("/api/calc/compare/nosuchproject0000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    created = await client.post("/api/projects", json=_aao_project_payload())
    project_id = created.json()["project_id"]
    response = await client.get(f"/api/calc/compare/{project_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]
    for probe in ("../escape", "..%2fescape", "x/../../escape"):
        response = await client.get(f"/api/calc/compare/{probe}")
        assert response.status_code < 500  # AU-1：浅深构造全 4xx 非 500
