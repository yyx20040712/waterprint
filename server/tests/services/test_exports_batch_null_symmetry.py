"""批量导出 items condition_key 三态对称测试（HH7/1A7 批 2026-10-04）。

输入:  waterprint_server.services.exports.create_export（批量转任务面）
       + exports_support._batch_items_payload 产物（payload/meta 边车/命名）
输出:  显式 null == 缺省 == 空串三态同口径断言（产物命名/meta 归一一致）

【拆件注记】本件自 test_exports.py 拆出（1A7 批 HH7 首落 test_exports.py
后 533>500 顶 §2 行数预算墙——test_app_validation_mass_balance.py 预算
墙拆分先例同款；测试内容零变纯搬迁）。
"""

from __future__ import annotations

import asyncio
import importlib
import json

import pytest

_mod = importlib.import_module("waterprint_server.services.exports")
projects_mod = importlib.import_module("waterprint_server.services.projects")
calculation_mod = importlib.import_module("waterprint_server.services.calculation")
create_export = getattr(_mod, "create_export")

pytestmark = [
    pytest.mark.skipif(
        create_export is None,
        reason="实现未就绪：waterprint_server.services.exports（服务层）",
    ),
    pytest.mark.anyio,
]


async def _project_with_result(ctx) -> str:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（最近结果集就绪——导出消费前提；
    test_exports.py 同款前置束搬迁）。"""
    outcome = projects_mod.create_project(
        ctx,
        {
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
        },
    )
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(ctx, project_id, [])
    for _ in range(200):
        if ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert ctx.manager.status(handle.task_id).state == "done"
    return project_id


async def _spy_captured_submit(service_ctx, monkeypatch):  # type: ignore[no-untyped-def]
    """submit 侦听替身（test_exports.py 先例形态——原样透传真提交）。"""
    captured: list[object] = []
    original_submit = service_ctx.manager.submit

    async def _spy_submit(request, *, idempotency_key=None):  # type: ignore[no-untyped-def]
        captured.append(request)
        return await original_submit(request, idempotency_key=idempotency_key)

    monkeypatch.setattr(service_ctx.manager, "submit", _spy_submit)
    return captured


async def test_batch_items_condition_key_null_states_symmetry_wiring(
    service_ctx, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """HH7（1A7 批）：items condition_key 显式 null == 缺省 == 空串三态同口径。

    旧句 str(item.get("condition_key", "")) 对显式 null 物化 "None"
    （payload/meta 边车/确定性命名三分量一致携带——worker 侧 ""→None
    对偶口径失配，项级错配失败）；or-归一与单产物口径逐字同构后三态
    皆归一 ""（命名分量走 fallback、meta condition_key 空、worker 收 None）。"""
    project_id = await _project_with_result(service_ctx)
    captured = await _spy_captured_submit(service_ctx, monkeypatch)
    handle = await create_export(
        service_ctx,
        project_id,
        "dxf",
        "ok",
        {
            "unit_id": "municipal_cass",
            "items": [
                {"kind": "dxf", "condition_key": None},  # 显式 null
                {"kind": "dxf"},  # 键缺席
                {"kind": "dxf", "condition_key": ""},  # 空串
            ],
        },
    )
    assert handle.task_id is not None  # 批量转任务（items>1）
    items = captured[0].payload["items"]  # type: ignore[attr-defined]
    assert [item["condition_key"] for item in items] == ["", "", ""]
    # 命名三态一致（null 物化 "None" 曾致分量分叉——同名回归锚）
    out_names = [item["out_name"] for item in items]
    assert out_names[0] == out_names[1] == out_names[2], out_names
    # meta 边车三态同形（dxf 边车 JSON condition_key 归一空串）
    for item in items:
        meta = json.loads(item["sidecars"]["dxf"])
        assert meta["condition_key"] == ""
