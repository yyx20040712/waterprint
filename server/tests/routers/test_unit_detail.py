"""unit_detail 路由契约测试：GET /api/calc/projects/{pid}/units/{uid}/results。

输入:  waterprint_server.routers.calc unit_detail 端点 + services.unit_detail
输出:  HTTP 契约三面（200 载荷/404 区分错误文案/stale 流转）+行模型对账断言

规格说明（B2 结果与方案批 2026-10-09 任务书 §二.①——形源
  agent wp_get_unit_detail；test_compare 同款路由面模式）：
  - 200 载荷含 stale/design_hash 回显+out_dims 满行（label_zh/dim 服务端
    联表——FE 不自带副本）；超集键（compute 实产⊃out_dims）不呈现；
  - 404 三面：未知项目/无结果集（引导语含 /api/calc/run）/工况或单元不在
    结果快照（文案区分）；
  - stale 流转：PUT design 改参→stale=True+design_hash 回显不变
    （结果件真源——compare 同口径）。
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import status
from waterprint import app as core

from waterprint_server.routers import unit_detail as unit_detail_router

_EXPECTED_UNIT_DETAIL = {
    ("get", "/api/calc/projects/{project_id}/units/{unit_id}/results")
}


def _aao_project_payload() -> dict[str, object]:
    """inlet→AAO 项目载荷（AAO=out_dims 33 条声明面——test_compare 同源；D1 批+4）。"""
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
    """创建 AAO 项目并跑一次计算（结果集就绪）。"""
    created = await client.post("/api/projects", json=_aao_project_payload())
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


def test_router_exposes_unit_detail_endpoint_wiring() -> None:
    """unit_detail 路由件端点集恰一件（44→45 增量无漂移——路由件独立挂载：
    calc 镜像测试端点集冻结断言=人类锁定面，故本端点不入 calc.router；
    R1 W-断言：>= 收敛为恰等——与「恰一件」注释及 calc 镜像冻结制式一致）。"""
    observed = {
        (method.lower(), route.path)
        for route in unit_detail_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed == _EXPECTED_UNIT_DETAIL


@pytest.mark.anyio
async def test_unit_detail_200_payload_shape(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：载荷形状（行模型=out_dims 满行+端口流量水质段+溯源回显）。"""
    project_id, task_id = await _project_with_result(client)
    response = await client.get(
        f"/api/calc/projects/{project_id}/units/municipal_aao/results"
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["project_id"] == project_id
    assert body["unit_id"] == "municipal_aao"
    assert body["condition_key"] == "design"  # 缺省工况=design（形源同口径）
    assert body["task_id"] == task_id
    assert body["stale"] is False
    assert body["design_hash"] and body["engine_version"] and body["data_version"]
    # 行模型对账：行集==manifest out_dims 键集（服务端联表单源——超集键不呈现）
    manifest = core.discover_units()["municipal_aao"][0]
    expected_fields = [spec.field_id for spec in manifest.out_dims]
    assert [row["field_id"] for row in body["rows"]] == expected_fields
    by_field = {row["field_id"]: row for row in body["rows"]}
    v_o = by_field["v_o"]
    assert v_o["label_zh"] == "好氧区容积"  # 中文名真源投影（compare 同锚）
    assert v_o["dim"]  # dim 三元组在场
    assert isinstance(v_o["value"], float) and v_o["value"] > 0.0
    # 端口流量水质段+警告/公式数据面（agent 形源同形）
    assert isinstance(body["outflows"], dict)
    assert isinstance(body["outqualities"], dict)
    assert isinstance(body["warnings"], list)
    assert isinstance(body["formula_ids"], list) and body["formula_ids"]


@pytest.mark.anyio
async def test_unit_detail_condition_key_param_and_404_condition(client) -> None:  # type: ignore[no-untyped-def]
    """?condition_key=avg 显式工况可用；未知工况 404（文案含合法面）。"""
    project_id, _ = await _project_with_result(client)
    response = await client.get(
        f"/api/calc/projects/{project_id}/units/municipal_aao/results",
        params={"condition_key": "avg"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["condition_key"] == "avg"
    response = await client.get(
        f"/api/calc/projects/{project_id}/units/municipal_aao/results",
        params={"condition_key": "nosuch"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "工况" in response.json()["detail"]


@pytest.mark.anyio
async def test_unit_detail_error_faces(client) -> None:  # type: ignore[no-untyped-def]
    """404 三面：未知项目/无结果集（引导 /api/calc/run）/单元不在快照+AU-1。"""
    # 未知项目
    response = await client.get(
        "/api/calc/projects/nosuchproject0000/units/municipal_aao/results"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # 项目在但无结果集（未计算）
    created = await client.post("/api/projects", json=_aao_project_payload())
    project_id = created.json()["project_id"]
    response = await client.get(
        f"/api/calc/projects/{project_id}/units/municipal_aao/results"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]
    # 结果集在但单元不在快照（inlet 无 manifest 但在快照——用未在项目单元）
    done_id, _ = await _project_with_result(client)
    response = await client.get(
        f"/api/calc/projects/{done_id}/units/municipal_cass/results"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "单元" in response.json()["detail"]  # 错误体文案区分（工况 vs 单元）
    # AU-1 路径安全（workflow §4-4）：浅深构造全 4xx 非 500
    for probe in ("../escape", "..%2fescape", "x/../../escape"):
        response = await client.get(
            f"/api/calc/projects/{probe}/units/municipal_aao/results"
        )
        assert response.status_code < 500


@pytest.mark.anyio
async def test_unit_detail_stale_after_design_change(client) -> None:  # type: ignore[no-untyped-def]
    """stale 流转：PUT design 改参→stale=True；design_hash 回显=结果件真源不变。"""
    project_id, _ = await _project_with_result(client)
    url = f"/api/calc/projects/{project_id}/units/municipal_aao/results"
    before = (await client.get(url)).json()
    assert before["stale"] is False
    saved = (await client.get(f"/api/projects/{project_id}")).json()
    project = dict(saved)
    project["design"]["nodes"]["municipal_aao"]["n"] = 3.0  # 设计参数变更
    put = await client.put(f"/api/projects/{project_id}", json=project)
    assert put.status_code == status.HTTP_200_OK
    after = (await client.get(url)).json()
    assert after["stale"] is True  # result_is_stale 同口径（digest 漂移）
    assert after["design_hash"] == before["design_hash"]  # 结果件 repro 真源
