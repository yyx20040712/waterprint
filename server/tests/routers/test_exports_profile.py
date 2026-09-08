"""PROFILE2 纵断导出 server 接线测试（2026-09-08）：sheet 通道透传+命名互异+批量拒。

输入:  client wiring 夹具+_project_with_result（test_exports 同源辅助——
       辅助函数经 import 复用非复制）
输出:  sheet=profile 经既有 dxf 端点（零新端点 openapi 恒 27）导出流
       断言+批量面诚实拒绝断言（PROFILE2 PD3/PD8）。
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
async def test_profile_sheet_batch_rejected_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """PROFILE2：批量面 sheet 选项诚实拒绝 422（worker 通道未透传——M5 先例）。"""
    project_id, _task_id = await _project_with_result(client)
    resp = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {
                "sheet": "profile",
                "items": [  # 多项=批量转任务路径（R2）——sheet 拒于转任务前
                    {"kind": "dxf", "condition_key": "design"},
                    {"kind": "dxf", "condition_key": "design", "unit_id": "municipal_cass"},
                ],
            },
        },
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "sheet" in resp.json()["detail"] and "批量" in resp.json()["detail"]



@pytest.mark.anyio
async def test_item_level_sheet_not_silently_ignored_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R 轮 P2A2-1 回归：item 级 sheet 并入提取——批量面诚实拒（禁静默吞错）。

    顶层无 sheet+item 内携带 sheet=profile（与 unit_id 同层）——原实现
    静默按普通 dxf 产出；R 轮并入提取后批量面统一拒（item 覆盖批级沿
    unit_id 同语义，批量面 worker 无通道整体拒）。
    """
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
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "sheet" in resp.json()["detail"]
