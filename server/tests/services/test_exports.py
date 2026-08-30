"""exports 服务镜像测试：stale 守门、确定性命名、批量转任务。

输入:  waterprint_server.services.exports 公开符号
输出:  服务契约断言
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.exports")
create_export = getattr(_mod, "create_export")
list_exports = getattr(_mod, "list_exports")

calculation_mod = importlib.import_module("waterprint_server.services.calculation")
projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = [
    pytest.mark.skipif(
        None in (create_export, list_exports),
        reason="实现未就绪：waterprint_server.services.exports（服务层 M2/M3）",
    ),
    pytest.mark.anyio,
]


async def _project_with_result(ctx) -> str:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（最近结果集就绪——导出消费前提）。"""
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


async def test_export_filename_is_deterministic_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R4 接线断言：同输入两次导出产物同名（无时钟进文件名，幂等覆盖）。"""
    project_id = await _project_with_result(service_ctx)
    first = await create_export(service_ctx, project_id, "calcbook")
    second = await create_export(service_ctx, project_id, "calcbook")
    assert first.path == second.path  # 同名同输入即同文件（禁当前时钟）
    assert first.task_id is None and second.task_id is None  # 单产物即时生成
    metas = list_exports(service_ctx, project_id)
    assert len(metas) == 1  # 幂等重导出覆盖（注册表不重复登记）


async def test_forced_export_of_stale_result_is_labeled_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：force 导出旧结果的产物名/元数据显式标注旧三元组。"""
    project_id = await _project_with_result(service_ctx)
    result_digest = service_ctx.manager.status(
        service_ctx.manager.task_ids_for_project(project_id)[-1]
    ).result["design_hash"]
    project = projects_mod.read_project(service_ctx, project_id)
    edited = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"assumption_overrides": {"safety.superheight": 0.3}}
            )
        }
    )
    projects_mod.save_project(service_ctx, project_id, edited)  # 输入版本漂移
    with pytest.raises(_mod.StaleExportError, match=result_digest[:6]):  # 未 force：409 附摘要（AU-6/R1-4②）
        await create_export(service_ctx, project_id, "calcbook")
    forced = await create_export(service_ctx, project_id, "calcbook", force=True)
    assert forced.stale_labeled is True  # 产物/元数据显式标注（永不冒充）
    metas = list_exports(service_ctx, project_id)
    assert metas and metas[-1].stale_labeled is True
    assert metas[-1].design_digest == result_digest  # 标注的是旧三元组
    assert metas[-1].design_digest != projects_mod.design_digest(
        projects_mod.read_project(service_ctx, project_id).design
    )  # 与当前 design 不同（冒充防线）


async def test_traversal_components_rejected_no_escape_writing(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """AU-1/R1-1 接线断言：文件名分量穿越=422 族且 exports_dir/上层零新增落盘。

    浅穿越（a/../../evil）+深穿越（b/../../../../../deep）与批量 items[*].kind
    穿越（kind 含路径段）——目录快照（exports_dir+其上层全树）前后对比锁定
    "越界即拒于落盘之前"（§18 路径安全；exports.py 规格 R3 白名单字符集）。
    """
    import os

    project_id = await _project_with_result(service_ctx)
    exports_dir = service_ctx.exports_dir
    sandbox = exports_dir.parent.parent  # pytest tmp 根（深穿越上限 containment 窗）
    before_files = {str(p.relative_to(sandbox)) for p in sandbox.rglob("*")}
    before_listing = sorted(os.listdir(exports_dir))
    shallow = "a/../../evil"  # 浅穿越：逃出 exports_dir 一层
    deep = "b/" + "../" * 10 + "deep"  # 深穿越：多级上溯
    for evil_condition in (shallow, deep):
        with pytest.raises(_mod.InvalidExportRequestError, match="文件名分量"):
            await create_export(service_ctx, project_id, "calcbook", evil_condition)
    with pytest.raises(_mod.InvalidExportRequestError):  # 批量 items kind 穿越（kind 白名单）
        await create_export(
            service_ctx,
            project_id,
            "calcbook",
            "ok",
            {"items": [{"kind": "calcbook/../../evil", "condition_key": ""}]},
        )
    assert sorted(os.listdir(exports_dir)) == before_listing  # exports_dir 零新增
    assert {str(p.relative_to(sandbox)) for p in sandbox.rglob("*")} == before_files  # 全树零逃逸


async def test_export_corrupt_result_file_raises_404_face_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """FE1 M4：结果文件损坏=ExportSourceNotFoundError（404 面——deserialize 裸 500 归一）。"""
    from pathlib import Path

    project_id = await _project_with_result(service_ctx)
    status = service_ctx.manager.status(
        service_ctx.manager.task_ids_for_project(project_id)[-1]
    )
    Path(str(status.result["result_file"])).write_bytes(b"\xff\xfe{not json")  # type: ignore[index]
    with pytest.raises(_mod.ExportSourceNotFoundError, match="先重算"):
        await create_export(service_ctx, project_id, "calcbook")


async def test_batch_export_names_carry_unit_component_wiring(
    service_ctx, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """S2 D6 接线断言：批量导出文件名含 unit 分量+payload items 逐项透传。

    命名收口：_deterministic_name(unit_id=options.unit_id) 恒传（去
    len(items)<=1 条件——FE9 R1 挂账「命名面随 worker 面同批收口」）；
    items 每项 unit_id（批级共享=options.unit_id）+condition_key（item
    自有）——exports→worker IPC 契约面（submit 侦听断言）。
    """
    project_id = await _project_with_result(service_ctx)
    captured: list[object] = []
    original_submit = service_ctx.manager.submit

    async def _spy_submit(request, *, idempotency_key=None):  # type: ignore[no-untyped-def]
        captured.append(request)
        return await original_submit(request, idempotency_key=idempotency_key)

    monkeypatch.setattr(service_ctx.manager, "submit", _spy_submit)
    handle = await create_export(
        service_ctx,
        project_id,
        "dxf",
        "ok",
        {
            "unit_id": "municipal_cass",
            "items": [
                {"kind": "dxf", "condition_key": "design"},
                {"kind": "dxf", "condition_key": "avg"},
            ],
        },
    )
    assert handle.task_id is not None  # 批量转任务（R3：items>1 即转 export_batch）
    assert "-dxf-municipal_cass-design-" in handle.path  # 批量名含 unit 分量（命名收口）
    items = captured[0].payload["items"]
    assert [item["unit_id"] for item in items] == [  # 批级共享=options.unit_id
        "municipal_cass",
        "municipal_cass",
    ]
    assert [item["condition_key"] for item in items] == ["design", "avg"]  # item 自有
