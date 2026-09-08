"""PROFILE2/3 纵断导出 server 接线测试：sheet 通道+比例定制+批量解锁。

输入:  client wiring 夹具+_project_with_result（test_exports 同源辅助——
       辅助函数经 import 复用非复制）
输出:  sheet=profile 经既有 dxf 端点（零新端点 openapi 恒 27）导出流
       断言+PROFILE3 批量面解锁句柄断言+h/v 形态整批原子 422+命名段锚。
"""

from __future__ import annotations

import pytest
from fastapi import status

from tests.routers.test_exports import (
    _project_with_result,  # 同源辅助复用（非复制第二真源）
)


@pytest.mark.anyio
async def test_profile_sheet_export_flow_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """PROFILE2：dxf 端点 sheet=profile 纵断导出流（零新端点——options 通道）。

    断：200 文件流+落盘文件名含 -profile- 分量（与总图同 kind 同 unit
    形态必然互异——FE9 R1 同名覆盖缺陷防再发）+DXF 头魔面。
    """
    project_id, _task_id = await _project_with_result(client)
    resp = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {"sheet": "profile"},  # 纵断通道（PROFILE2 PD3）
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert b"AC1032" in resp.content[:512]  # DXF R2018 头魔面
    saved = list(test_settings.exports_dir.glob("*profile*.dxf"))
    assert len(saved) == 1 and "-dxf-profile-" in saved[0].name  # 命名互异锚


@pytest.mark.anyio
async def test_profile_sheet_batch_accepted_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """PROFILE3（PD2 改写·原 PROFILE2 422 拒形态）：批量面 sheet 解锁——
    多项含纵断项=转任务句柄（task_id 非空 JSON；worker 透传面由 jobs 用例锚）。"""
    project_id, _task_id = await _project_with_result(client)
    resp = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {
                "sheet": "profile",
                "items": [  # 多项=批量转任务路径（R2）——不再 422（PD2 解锁）
                    {"kind": "dxf", "condition_key": "design"},
                    {"kind": "dxf", "condition_key": "design", "unit_id": "municipal_cass"},
                ],
            },
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json().get("task_id")  # 批量转任务句柄（非文件流）


@pytest.mark.anyio
async def test_item_level_sheet_batch_accepted_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """PROFILE3（PD2 改写·原 P2A2-1 回归钉演化）：item 级 sheet 并入归一——
    顶层零 sheet+item 携带=批量转任务（禁静默吞错语义沿承：归一进 payload
    而非忽略；422 拒形态随批量解锁改为支持形态）。"""
    project_id, _task_id = await _project_with_result(client)
    resp = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {
                "items": [  # 顶层零 sheet——item 级携带（P2A2-1 缺陷形态）
                    {"kind": "dxf", "condition_key": "design", "sheet": "profile"},
                    {"kind": "dxf", "condition_key": "design", "unit_id": "municipal_cass"},
                ]
            },
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json().get("task_id")


@pytest.mark.anyio
async def test_scale_form_422_atomic_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """PROFILE3（PD6）：h/v 形态预校验=整批原子 422（任一 item 畸形整批拒，
    消息含 item 索引定位；'abc'/'0'/'-100' 三形态[空串=提取层归 None 缺省
沿 unit_id 先例]；域上限留 core 终闸）。"""
    project_id, _task_id = await _project_with_result(client)
    for bad in ("abc", "0", "-100"):
        resp = await client.post(
            "/api/exports/dxf",
            json={
                "project_id": project_id,
                "condition_key": "design",
                "options": {
                    "sheet": "profile",
                    "items": [
                        {"kind": "dxf", "condition_key": "design"},
                        {"kind": "dxf", "condition_key": "design",
                         "unit_id": "municipal_cass", "h_scale": bad},
                    ],
                },
            },
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        detail = resp.json()["detail"]
        assert "h_scale" in detail and "items[1]" in detail


@pytest.mark.anyio
async def test_scale_custom_naming_segment_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """PROFILE3（PD4）：单产物比例透传 200+命名段（-h2000v200 非默认出段；
    默认零段保快照锚——本用例锚定制形态）。"""
    project_id, _task_id = await _project_with_result(client)
    resp = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {"sheet": "profile", "h_scale": "2000", "v_scale": "200"},
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert b"AC1032" in resp.content[:512]
    saved = list(test_settings.exports_dir.glob("*h2000v200*.dxf"))
    assert len(saved) == 1 and "-dxf-profile-h2000v200-" in saved[0].name


@pytest.mark.anyio
async def test_route_mutex_collected_at_intake_422_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R 轮（D1-G1-03/A2-G1-02）：sheet×unit 互斥=收单即拒（批级或项级
    共存整批原子 422——不放行到 worker 必败项）。"""
    project_id, _task_id = await _project_with_result(client)
    for label, options in (
        ("批级", {"sheet": "profile", "unit_id": "municipal_cass"}),
        ("项级", {"items": [{"kind": "dxf", "condition_key": "design",
                             "sheet": "profile", "unit_id": "municipal_cass"}]}),
    ):
        resp = await client.post(
            "/api/exports/dxf",
            json={"project_id": project_id, "condition_key": "design",
                  "options": options},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, label
        assert "互斥" in resp.json()["detail"]


@pytest.mark.anyio
async def test_route_scale_bad_types_and_escapes_422_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R 轮（D1-G1-01/05+A2-G1-01/03）：非字符串承载（数值型）与判定域
    逃逸面（Unicode 数字/超长串）=整批原子 422。"""
    project_id, _task_id = await _project_with_result(client)
    # 形态畸形/数值承载/超长串（不可转换）=server 422（R 轮 G1-01：
    # int 逃逸转本闸）；域越界（可转换但>上限）归 core 终闸 501。
    for case, expected in (
        ({"options": {"sheet": "profile", "h_scale": 2000}}, 422),
        ({"options": {"sheet": "profile", "h_scale": "②"}}, 422),
        ({"options": {"sheet": "profile", "h_scale": "9" * 5000}}, 422),
    ):
        resp = await client.post(
            "/api/exports/dxf",
            json={"project_id": project_id, "condition_key": "design", **case},
        )
        assert resp.status_code == expected, (case, resp.status_code)
        assert "h_scale" in resp.json()["detail"]


@pytest.mark.anyio
async def test_batch_mixed_unit_item_not_inherit_sheet_e2e_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """R 轮（A2-G1-04 端到端）：批级 sheet+unit 项混装——unit 项不继承批级
    sheet（互斥归一层压制），任务 done 零 failures，双产物各自落位。"""
    import asyncio

    project_id, _task_id = await _project_with_result(client)
    resp = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {
                "sheet": "profile",
                "items": [  # 混装：厂级项（继承 sheet）+unit 项（不继承）
                    {"kind": "dxf", "condition_key": "design"},
                    {"kind": "dxf", "condition_key": "design", "unit_id": "municipal_cass"},
                ],
            },
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    task_id = resp.json()["task_id"]
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"  # 混装批无必败项（R 轮修复前 unit 项必入 failures）
    assert not body.get("failures"), body.get("failures")
    files = sorted(
        p.name for p in test_settings.exports_dir.glob("*.dxf")
        if "design" in p.name
    )
    assert len(files) == 2  # 纵断（-profile-）+单单元（municipal_cass）各一
    assert sum("-dxf-profile-" in f for f in files) == 1
    assert sum("municipal_cass" in f for f in files) == 1
