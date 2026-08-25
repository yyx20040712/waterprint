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
    with pytest.raises(_mod.StaleExportError, match="输入版本"):  # 未 force：409 面
        await create_export(service_ctx, project_id, "calcbook")
    forced = await create_export(service_ctx, project_id, "calcbook", force=True)
    assert forced.stale_labeled is True  # 产物/元数据显式标注（永不冒充）
    metas = list_exports(service_ctx, project_id)
    assert metas and metas[-1].stale_labeled is True
    assert metas[-1].design_digest == result_digest  # 标注的是旧三元组
    assert metas[-1].design_digest != projects_mod.design_digest(
        projects_mod.read_project(service_ctx, project_id).design
    )  # 与当前 design 不同（冒充防线）
