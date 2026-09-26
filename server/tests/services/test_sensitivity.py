"""sensitivity 路由/服务镜像测试：GET /api/calc/sensitivity/{project_id}（幅度/新鲜度/错误面）。

输入:  waterprint_server.routers.calc sensitivity 端点 + services.sensitivity 公开符号
输出:  路由契约断言（批6e 全工况投影端点的路由面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批6e——wave6-master-plan §批6e；test_compare 同款路由面模式）
#
# 覆盖用例：
#   - 端点集新增恰一件（GET /api/calc/sensitivity/{project_id}——42→43
#     增量，wave6 批次编排批 6 授权破面）；
#   - 200 正门：AAO 项目（conditions=["municipal_aao"] 受检单元）跑一次
#     计算→condition_keys=["design_offline_municipal_aao"]（前缀过滤）+
#     baseline_key="design"+rows=summary 平键全量（field_id 字典序）+
#     deltas 全 0.0（当前零单元声明检修降级——pool.all_pools DSL 引擎
#     就绪而 manifest condition_mappings 空=诚实现状非缺陷，b6e 设计档
#     §一.2）+stale=False+design_hash/task_id 回显；
#   - 无受检单元面：conditions=[] → condition_keys=[]（无 offline 工况
#     ——rows 仍呈 design 基线面，FE 消费面降级）；
#   - 确定性：双 GET 响应 JSON（sort_keys）字节同；
#   - stale 态：PUT design 改参→stale=True（result_is_stale 同口径——§12
#     输入变更标 stale 禁静默覆盖）+design_hash 回显不变（结果件真源）；
#   - 错误面：未知项目 404（ProjectNotFoundError）/无结果集 404
#     （SensitivitySourceNotFoundError——引导语含 /api/calc/run）；
#   - AU-1 路径安全（workflow §4-4 必选项）：../ 浅深构造全 4xx 非 500。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import status
from waterprint.contracts.result_schema import PlantResult, ReproTriple

from waterprint_server.routers import calc as calc_router
from waterprint_server.services import sensitivity as sensitivity_module
from waterprint_server.services.sensitivity import build_sensitivity_for_project

_EXPECTED_SENSITIVITY = {("get", "/api/calc/sensitivity/{project_id}")}


def _aao_project_payload() -> dict[str, object]:
    """inlet→AAO 项目载荷（test_compare 同款——AAO=out_dims 声明面首例单元）。"""
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


async def _project_with_result(
    client, conditions: list[str]  # type: ignore[no-untyped-def]
) -> tuple[str, str]:
    """创建 AAO 项目并按受检单元集跑一次计算（结果集就绪）。"""
    created = await client.post("/api/projects", json=_aao_project_payload())
    assert created.status_code == status.HTTP_200_OK
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": conditions}
    )).json()["task_id"]
    body: dict[str, object] = {}
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id


def test_router_exposes_sensitivity_endpoint_wiring() -> None:
    """calc 路由端点集含 sensitivity 恰一件（42→43 增量无漂移）。"""
    observed = {
        (method.lower(), route.path)
        for route in calc_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed >= _EXPECTED_SENSITIVITY


@pytest.mark.anyio
async def test_sensitivity_report_shape_and_deltas(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：幅度行（summary 平键全量）+零差现状+新鲜度/溯源回显。"""
    project_id, task_id = await _project_with_result(client, ["municipal_aao"])
    response = await client.get(f"/api/calc/sensitivity/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["task_id"] == task_id
    assert body["stale"] is False
    assert body["design_hash"] and body["engine_version"] and body["data_version"]
    assert body["baseline_key"] == "design"
    assert body["condition_keys"] == ["design_offline_municipal_aao"]
    # 行=summary design 基线键域全量（field_id 字典序——23 平键族）
    fields = [row["field_id"] for row in body["rows"]]
    assert fields == sorted(fields)
    assert {"cost_opex_yuan_a", "power_total_kwh_d", "carbon_intensity_kgco2e_m3",
            "BOD5", "TN"} <= set(fields)
    by_field = {row["field_id"]: row for row in body["rows"]}
    opex = by_field["cost_opex_yuan_a"]
    assert set(opex["values"]) == {"design_offline_municipal_aao"}
    assert all(isinstance(v, float) for v in opex["values"].values())
    # 零差现状：单元侧无检修降级声明（condition_mappings 空）——
    # design_offline 与 design 同值，deltas 恒 0.0（诚实面）
    assert opex["deltas"] == {"design_offline_municipal_aao": 0.0}
    assert opex["design_value"] == opex["values"]["design_offline_municipal_aao"]
    assert "cost_capex_yuan" not in by_field  # capex 不在 summary 平键链（设计档 §一.3）


@pytest.mark.anyio
async def test_sensitivity_no_checked_units_empty_conditions(client) -> None:  # type: ignore[no-untyped-def]
    """无受检单元面：conditions=[] → condition_keys=[]（rows 仍呈基线面）。"""
    project_id, _ = await _project_with_result(client, [])
    response = await client.get(f"/api/calc/sensitivity/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["condition_keys"] == []
    assert body["rows"], "rows=design 基线键域（无条件时仍在场）"
    assert all(row["values"] == {} and row["deltas"] == {} for row in body["rows"])


@pytest.mark.anyio
async def test_sensitivity_determinism_double_get(client) -> None:  # type: ignore[no-untyped-def]
    """确定性：同结果集双 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _ = await _project_with_result(client, ["municipal_aao"])
    first = (await client.get(f"/api/calc/sensitivity/{project_id}")).json()
    second = (await client.get(f"/api/calc/sensitivity/{project_id}")).json()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


@pytest.mark.anyio
async def test_sensitivity_stale_after_design_change(client) -> None:  # type: ignore[no-untyped-def]
    """§12 快照绑定：PUT design 改参→stale=True；design_hash 回显=结果件
    真源不变（输入变更标 stale 禁静默覆盖——服务端不重算不覆盖）。"""
    project_id, _ = await _project_with_result(client, ["municipal_aao"])
    before = (await client.get(f"/api/calc/sensitivity/{project_id}")).json()
    assert before["stale"] is False
    saved = (await client.get(f"/api/projects/{project_id}")).json()
    project = dict(saved)
    project["design"]["nodes"]["municipal_aao"]["n"] = 3.0  # 设计参数变更
    put = await client.put(f"/api/projects/{project_id}", json=project)
    assert put.status_code == status.HTTP_200_OK
    after = (await client.get(f"/api/calc/sensitivity/{project_id}")).json()
    assert after["stale"] is True  # result_is_stale 同口径（digest 漂移）
    assert after["design_hash"] == before["design_hash"]  # 结果件 repro 真源
    assert after["rows"] == before["rows"]  # 快照内容不随输入变更静默改写


def test_sensitivity_corrupt_result_404_face(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """损坏结果件→404 面（门一 k1-W5 回炉）：deserialize 全解析失败族
    （UTF-8/JSON/结构/非有限值——result_schema R6 归一 InvalidResultError）
    与文件缺失（OSError）同归 SensitivitySourceNotFoundError，无 500 泄漏。"""
    from waterprint.contracts.result_schema import InvalidResultError

    result_file = tmp_path / "corrupt.json"
    result_file.write_bytes(b"{not-json")
    monkeypatch.setattr(sensitivity_module, "read_project", lambda ctx, pid: object())
    monkeypatch.setattr(
        sensitivity_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", {"result_file": str(result_file)}),
    )
    with pytest.raises(sensitivity_module.SensitivitySourceNotFoundError) as excinfo:
        build_sensitivity_for_project(None, "p1")  # type: ignore[arg-type]
    assert "先重算" in str(excinfo.value)
    monkeypatch.setattr(sensitivity_module, "deserialize", lambda data: (_ for _ in ()).throw(
        InvalidResultError("结构非法")))
    with pytest.raises(sensitivity_module.SensitivitySourceNotFoundError):
        build_sensitivity_for_project(None, "p1")  # type: ignore[arg-type]
    monkeypatch.setattr(
        sensitivity_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", {"result_file": str(tmp_path / "absent.json")}),
    )
    monkeypatch.setattr(sensitivity_module, "deserialize", lambda data: None)
    with pytest.raises(sensitivity_module.SensitivitySourceNotFoundError):
        build_sensitivity_for_project(None, "p1")  # type: ignore[arg-type]


def test_sensitivity_sparse_key_domain_drift(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """键域漂移双分支（门一 d1-W2 回炉）：condition_keys 取 plant.conditions
    前缀过滤而值取 plant.summary——两映射不同源的稀疏面须各自诚实：
    ①conditions 在而 summary 缺行→键入 condition_keys 而 values/deltas 空；
    ②summary 在而 conditions 缺→键不入 condition_keys（行值亦无该键）。"""
    plant = PlantResult(
        conditions={
            "design": {}, "design_offline_ghost": {},  # ghost 在 conditions
            # design_offline_orphan 不在 conditions（summary 侧孤儿）
        },
        summary={
            "design": {"cost_opex_yuan_a": 100.0},
            "design_offline_orphan": {"cost_opex_yuan_a": 130.0},
        },
        trace=(),
        repro=ReproTriple("h", "e", "d"),
    )
    result_file = tmp_path / "result.json"
    result_file.write_bytes(b"{}")  # 内容无关——deserialize 已替身
    monkeypatch.setattr(sensitivity_module, "read_project", lambda ctx, pid: object())
    monkeypatch.setattr(
        sensitivity_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", {"result_file": str(result_file)}),
    )
    monkeypatch.setattr(sensitivity_module, "deserialize", lambda data: plant)
    monkeypatch.setattr(sensitivity_module, "result_is_stale", lambda latest, project: False)
    report = build_sensitivity_for_project(None, "p1")  # type: ignore[arg-type]
    assert report.condition_keys == ("design_offline_ghost",)  # 分支①：conditions 真源
    assert len(report.rows) == 1
    assert report.rows[0].values == {} and report.rows[0].deltas == {}
    assert report.rows[0].design_value == 100.0  # 分支②：orphan 不入任何面


@pytest.mark.anyio
async def test_sensitivity_error_faces(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404（引导语含 /api/calc/run）+AU-1 路径安全。"""
    response = await client.get("/api/calc/sensitivity/nosuchproject0000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    created = await client.post("/api/projects", json=_aao_project_payload())
    project_id = created.json()["project_id"]
    response = await client.get(f"/api/calc/sensitivity/{project_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]
    for probe in ("../escape", "..%2fescape", "x/../../escape"):
        response = await client.get(f"/api/calc/sensitivity/{probe}")
        assert response.status_code < 500  # AU-1：浅深构造全 4xx 非 500
