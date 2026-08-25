"""enumeration 服务镜像测试：单单元守护、分页白名单、arrow 重载。

输入:  waterprint_server.services.enumeration 公开符号
输出:  服务契约断言（ADR-005 的服务侧强制）
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.enumeration")
submit_enumeration = getattr(_mod, "submit_enumeration")
fetch_solutions = getattr(_mod, "fetch_solutions")
fetch_diagnosis = getattr(_mod, "fetch_diagnosis")

projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = [
    pytest.mark.skipif(
        None in (submit_enumeration, fetch_solutions),
        reason="实现未就绪：waterprint_server.services.enumeration（服务层 M2）",
    ),
    pytest.mark.anyio,
]


async def _cass_project(ctx) -> str:  # type: ignore[no-untyped-def]
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
    return outcome.project_id


async def _await_terminal(ctx, task_id: str) -> None:  # type: ignore[no-untyped-def]
    for _ in range(200):
        if ctx.manager.status(task_id).state in {"done", "failed", "cancelled"}:
            return
        await asyncio.sleep(0.1)
    raise TimeoutError(task_id)


async def test_multi_unit_request_rejected_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：多 unit_id 请求 422（防语义滑坡成全厂枚举）。"""
    project_id = await _cass_project(service_ctx)
    with pytest.raises(_mod.MultiUnitEnumerationError, match="单单元"):
        await submit_enumeration(service_ctx, project_id, ["unit_a", "unit_b"])
    with pytest.raises(_mod.MultiUnitEnumerationError):  # 空集同拒（恰一语义）
        await submit_enumeration(service_ctx, project_id, [])


async def test_infeasible_enumeration_is_done_not_failed_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R4 接线断言：无解枚举任务终态 done + feasible_count=0（非 failed）。"""
    project_id = await _cass_project(service_ctx)
    handle = await submit_enumeration(
        service_ctx,
        project_id,
        ["municipal_cass"],
        {
            "constraints": [
                {"key": "impossible", "expression": "ns_act > 100", "source": "ui:test"}
            ]
        },
    )
    await _await_terminal(service_ctx, handle.task_id)
    status = service_ctx.manager.status(handle.task_id)
    assert status.state == "done"  # 无解=合法终态（非 failed，R4）
    assert status.result is not None
    assert status.result["feasible_count"] == 0
    diagnosis = fetch_diagnosis(service_ctx, handle.task_id)  # 诊断交付面
    assert diagnosis["minimal_conflicts"]  # 最小冲突集非空
    # 可行枚举对照：正常任务无诊断（DiagnosisNotAvailableError）
    ok_handle = await submit_enumeration(service_ctx, project_id, ["municipal_cass"])
    await _await_terminal(service_ctx, ok_handle.task_id)
    assert service_ctx.manager.status(ok_handle.task_id).state == "done"
    page = fetch_solutions(service_ctx, ok_handle.task_id, 1, 2, "margin_min")
    assert page.size == 2 and len(page.rows) <= 2 and page.total >= 1  # 分页+重载
    with pytest.raises(_mod.InvalidPageParameterError):  # 排序白名单外 422 面
        fetch_solutions(service_ctx, ok_handle.task_id, 1, 2, "not_a_field")
