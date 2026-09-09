"""calc/design-map 端点镜像测试：FD 可行域引导同步求值（PD6 甲案）。

输入:  POST /api/calc/design-map（项目+单元+轴声明）
输出:  端点契约断言（同步直返形态/422 面/404 面/400 护栏面/约束装配）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.routers.calc")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.calc（FD 批）",
    ),
]


def _vxinglvchi_payload() -> dict[str, object]:
    """V 型滤池单单元项目（约束装配测试载体——kb 输出带覆盖单元）。"""
    return {
        "format_version": "1.0",
        "design": {
            "nodes": {
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0, "BOD5": 200.0, "SS": 250.0,
                    "NH3N": 26.0, "TN": 43.0, "TP": 6.5,
                },
                "municipal_vxinglvchi": {},
            },
            "edges": [
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_vxinglvchi", "port_id": "in"},
                }
            ],
        },
        "view": {},
        "metadata": {
            "format_version": "1.0", "content_hash": "0",
            "engine_version": "0", "data_version": "0",
        },
    }


async def _make_project(client, payload: dict[str, object]) -> str:  # type: ignore[no-untyped-def]
    created = await client.post("/api/projects", json={"project": payload})
    assert created.status_code == 200
    return str(created.json()["project_id"])


@pytest.mark.anyio
async def test_design_map_sync_shape_degraded(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """同步直返形态（PD6 甲案）：CASS ns 轴 11 点 degraded 全字段+双跑同。"""
    project_id = await _make_project(client, cass_payload)
    body = {
        "project_id": project_id,
        "unit_id": "municipal_cass",
        "axes": [{"field_id": "ns"}],
    }
    first = await client.post("/api/calc/design-map", json=body)
    assert first.status_code == 200
    payload = first.json()
    assert payload["unit_id"] == "municipal_cass"
    assert payload["constraint_coverage"] == "degraded"  # 项目未勾约束
    assert payload["stats"]["total"] == 11
    assert payload["axes"][0]["field_id"] == "ns"
    assert payload["axes"][0]["points"] == 11
    assert payload["segments"] is not None and len(payload["segments"]) >= 1
    assert payload["mask"] is None  # 1D 无掩码面
    second = await client.post("/api/calc/design-map", json=body)
    assert second.status_code == 200
    assert first.content == second.content  # 确定性（字节同）


@pytest.mark.anyio
async def test_design_map_constraint_assembly_full(client) -> None:  # type: no-untyped-def
    """约束装配（PD2 server 面）：kb unit_kinds ∩ constraint_choices="on"。"""
    payload = _vxinglvchi_payload()
    payload["design"]["constraint_choices"] = {  # type: ignore[index]
        "vxinglvchi.v_filter_band": "on",
        "vxinglvchi.v_forced_band": "on",
    }
    project_id = await _make_project(client, payload)
    response = await client.post("/api/calc/design-map", json={
        "project_id": project_id,
        "unit_id": "municipal_vxinglvchi",
        "axes": [{"field_id": "v_filter"}],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["constraint_coverage"] == "full"  # 两条输出带约束生效
    assert body["stats"]["feasible"] < body["stats"]["total"]  # band 裁剪面


@pytest.mark.anyio
async def test_design_map_axes_length_422(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """PD6 422 面①：axes 长度 0/3（pydantic 声明面拦截）。"""
    project_id = await _make_project(client, cass_payload)
    for axes in ([], [
        {"field_id": "ns"}, {"field_id": "x_mlss"}, {"field_id": "h2"},
    ]):
        response = await client.post("/api/calc/design-map", json={
            "project_id": project_id, "unit_id": "municipal_cass", "axes": axes,
        })
        assert response.status_code == 422


@pytest.mark.anyio
async def test_design_map_axis_contract_422(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """PD6 422 面②：字段不存在/step 非正/range min≥max/⊆manifest 越界。"""
    project_id = await _make_project(client, cass_payload)
    for axis in (
        {"field_id": "ghost"},
        {"field_id": "ns", "step": 0.0},
        {"field_id": "ns", "step": -0.01},
        {"field_id": "ns", "range": {"min": 0.2, "max": 0.1}},
        {"field_id": "ns", "range": {"min": 0.01, "max": 0.15}},  # ⊄ [0.05,0.15]
    ):
        response = await client.post("/api/calc/design-map", json={
            "project_id": project_id, "unit_id": "municipal_cass", "axes": [axis],
        })
        assert response.status_code == 422, axis
        assert response.json()["error_type"] == "InvalidDesignMapError"


@pytest.mark.anyio
async def test_design_map_guard_400(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """PD6 4xx 护栏面：DesignMapTooLarge→400（细步长超 2500 点）。"""
    project_id = await _make_project(client, cass_payload)
    response = await client.post("/api/calc/design-map", json={
        "project_id": project_id,
        "unit_id": "municipal_cass",
        "axes": [
            {"field_id": "ns", "step": 0.0001},
            {"field_id": "x_mlss", "step": 10.0},
        ],
    })
    assert response.status_code == 400
    assert response.json()["error_type"] == "DesignMapTooLarge"


@pytest.mark.anyio
async def test_design_map_not_found_404(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """PD6 404 面：项目缺（ProjectNotFoundError）/单元不在 design.nodes。"""
    response = await client.post("/api/calc/design-map", json={
        "project_id": "ghost-project",
        "unit_id": "municipal_cass",
        "axes": [{"field_id": "ns"}],
    })
    assert response.status_code == 404
    project_id = await _make_project(client, cass_payload)
    response = await client.post("/api/calc/design-map", json={
        "project_id": project_id,
        "unit_id": "municipal_aao",  # 不在该 CASS 项目 design.nodes
        "axes": [{"field_id": "ns"}],
    })
    assert response.status_code == 404
    assert response.json()["error_type"] == "DesignMapSourceNotFoundError"
