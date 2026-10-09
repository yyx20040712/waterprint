"""report 路由契约测试：GET /api/calc/projects/{pid}/report。

输入:  waterprint_server.routers.report 端点 + services.report 装配面
输出:  HTTP 契约三面（200 载荷/404 区分文案/stale 流转）+markdown 数学块
       与附录在场断言+sections 两级索引形状

规格说明（B6 计算说明批 2026-10-09 任务书 §二.④——test_unit_detail
  同款路由面模式）：
  - 200 载荷：{project_id, condition_key, stale, design_hash, markdown,
    sections, generated_from.digest10}——markdown 含 $$…$$ 数学块（配对
    偶数）与「公式溯源全表」附录；sections 两级（章 level=1/unit_calc
    单元小节 level=2）；
  - 404 三面：未知项目/无结果集（引导语含 /api/calc/run）/工况不在
    结果集（文案区分）；
  - stale 流转：PUT design 改参→stale=True+design_hash 回显不变
    （结果件真源——compare/unit_detail 同口径）。
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import status

from waterprint_server.routers import report as report_router

_EXPECTED_REPORT = {("get", "/api/calc/projects/{project_id}/report")}

_EXPECTED_CHAPTER_IDS = {
    "design_basis",
    "flow_quality",
    "process_selection",
    "unit_calc",
    "layout",
    "estimate",
    "drawings",
    "formula_appendix",
}


def _cass_project_payload() -> dict[str, object]:
    """inlet→CASS 项目载荷（conftest cass_payload 同源——cost/scene 装配面载体）。"""
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


async def _project_with_result(client) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（结果集就绪——test_unit_detail 同款轮询）。"""
    created = await client.post("/api/projects", json=_cass_project_payload())
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


def test_router_exposes_report_endpoint_wiring() -> None:
    """report 路由件端点集恰一件（45→46 增量无漂移——路由件独立挂载：
    calc 镜像测试端点集冻结断言=人类锁定面，故本端点不入 calc.router）。"""
    observed = {
        (method.lower(), route.path)
        for route in report_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed == _EXPECTED_REPORT


@pytest.mark.anyio
async def test_report_200_payload_shape_and_math_blocks(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：载荷形状+markdown 数学块与附录在场+sections 两级索引。"""
    project_id, _task_id = await _project_with_result(client)
    response = await client.get(f"/api/calc/projects/{project_id}/report")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["project_id"] == project_id
    assert body["condition_key"] == "design"  # 缺省工况=design
    assert body["stale"] is False
    assert body["design_hash"]
    # markdown 数学块：$$ 成对（首现展示块——每公式恰一次）+附录全表在场
    markdown: str = body["markdown"]
    assert markdown.count("$$") >= 2
    assert markdown.count("$$") % 2 == 0
    assert "公式溯源全表" in markdown
    assert "（公式 " in markdown  # 首现块条文中号行
    # sections 两级投影：章 id 集=AST 八章（七章+附录）；CASS 单元小节 level=2
    sections = body["sections"]
    assert {s["id"] for s in sections if s["level"] == 1} == _EXPECTED_CHAPTER_IDS
    unit_sections = [s for s in sections if s["level"] == 2]
    assert unit_sections, "unit_calc 单元小节缺席（两级索引面）"
    assert any(s["id"].startswith("unit_calc-") for s in unit_sections)
    assert any("municipal_cass" in s["title"] for s in unit_sections)
    # 生成来源摘要：digest10=design_hash 前 10 位（exports 同口径）
    assert body["generated_from"]["digest10"] == body["design_hash"][:10]


@pytest.mark.anyio
async def test_report_condition_key_param_and_404_condition(client) -> None:  # type: ignore[no-untyped-def]
    """W-C（R1 回炉）：非 design 工况显式 422（报告锚定=design 单工况
    ——build_report_ast 数值锚定恒取 design，非 design 报告=后续批）；
    未知工况仍 404（工况不在结果集——文案含工况面）。"""
    project_id, _ = await _project_with_result(client)
    response = await client.get(
        f"/api/calc/projects/{project_id}/report",
        params={"condition_key": "avg"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = response.json()["detail"]
    assert "design" in detail and "后续批" in detail  # W-C 指定文案面
    response = await client.get(
        f"/api/calc/projects/{project_id}/report",
        params={"condition_key": "nosuch"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "工况" in response.json()["detail"]


@pytest.mark.anyio
async def test_report_error_faces(client) -> None:  # type: ignore[no-untyped-def]
    """404 两面：未知项目/无结果集（引导 /api/calc/run）+AU-1 路径安全。"""
    response = await client.get("/api/calc/projects/nosuchproject0000/report")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # 项目在但无结果集（未计算）
    created = await client.post("/api/projects", json=_cass_project_payload())
    project_id = created.json()["project_id"]
    response = await client.get(f"/api/calc/projects/{project_id}/report")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]
    # AU-1 路径安全（workflow §4-4）：浅深构造全 4xx 非 500
    for probe in ("../escape", "..%2fescape", "x/../../escape"):
        response = await client.get(f"/api/calc/projects/{probe}/report")
        assert response.status_code < 500


@pytest.mark.anyio
async def test_report_stale_after_design_change(client) -> None:  # type: ignore[no-untyped-def]
    """stale 流转：PUT design 改参→stale=True；design_hash 回显=结果件真源不变。"""
    project_id, _ = await _project_with_result(client)
    url = f"/api/calc/projects/{project_id}/report"
    before = (await client.get(url)).json()
    assert before["stale"] is False
    saved = (await client.get(f"/api/projects/{project_id}")).json()
    project = dict(saved)
    project["design"]["nodes"]["municipal_cass"]["n"] = 3.0  # 设计参数变更
    put = await client.put(f"/api/projects/{project_id}", json=project)
    assert put.status_code == status.HTTP_200_OK
    after = (await client.get(url)).json()
    assert after["stale"] is True  # result_is_stale 同口径（digest 漂移显式）
    assert after["design_hash"] == before["design_hash"]  # 结果件 repro 真源
    # stale 报告仍可读（报告面显式标注——禁静默）：结果集派生内容冻结不变
    # （第 1 章标识表的 content_hash 行=当前项目文件真源〔core build 行为〕，
    # 随 PUT 漂移属预期——比对面剔除该行）。
    def _result_frozen(markdown: str) -> list[str]:
        return [
            line for line in markdown.splitlines() if "content_hash" not in line
        ]

    assert _result_frozen(after["markdown"]) == _result_frozen(before["markdown"])
