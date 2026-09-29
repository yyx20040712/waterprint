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
core_app = importlib.import_module("waterprint.app")  # UF-47 收口（批6l）：digest 真源经 app 再导出面

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


# ═══ P0-2（深链死锁修复 2026-09-11）：result unit_id/design_hash 扩源 ═══


# ═══ API-1 R2 回炉（2026-09-30）：拆分语义锁面 ═══


async def test_fetch_diagnosis_on_calc_task_kind_mismatch_wiring(
    service_ctx, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """R2 回炉（k1-N2/d1-W5）：共享前提 helper 两调用面——fetch_diagnosis
    对 kind=calc done 任务同样 TaskKindMismatchError（单源拆分双面覆盖）。

    主控指令面书「apply 路径」；实查调用图勘误：apply 端点走
    calc_service.apply_solution（请求体无 task_id，不查任务注册表），
    _require_done_enumeration 第二调用面=fetch_diagnosis（诊断负载
    随任务状态载荷交付——本函数为该 helper 在 fetch_solutions 外
    唯一调用点，实报已呈主控）。
    """
    import waterprint_server.jobs.manager as manager_mod
    from waterprint_server.jobs.manager import TaskRequest

    def fake_calc(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        return {"state": "done", "project_id": payload.get("project_id", "")}

    monkeypatch.setattr(manager_mod, "run_task", fake_calc)
    handle = await service_ctx.manager.submit(
        TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "api1"})
    )
    await _await_terminal(service_ctx, handle.task_id)
    status = service_ctx.manager.status(handle.task_id)
    assert status.kind == "calc" and status.state == "done"  # 场景实证
    with pytest.raises(_mod.TaskKindMismatchError, match="kind=enumerate"):
        fetch_diagnosis(service_ctx, handle.task_id)


async def test_result_none_done_message_split_from_unfinished_wiring(
    service_ctx, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """R2 回炉（k1-W1/d1-W1）：NotComplete 面文案分流——done 但 result
    未落地（§16 A6 句柄缺失）与真·未完成（state≠done）两消息可辨
    （分流前同为「只在 done 终态可取」，与自述状态 done 自相矛盾）。
    """
    import time

    import waterprint_server.jobs.manager as manager_mod
    from waterprint_server.jobs.manager import TaskRequest

    def bare_done(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        return None  # 终态 done 而 result 未落地（§16 A6 句柄缺面）

    monkeypatch.setattr(manager_mod, "run_task", bare_done)
    handle = await service_ctx.manager.submit(
        TaskRequest(kind="enumerate", payload={"kind": "enumerate"})
    )
    await _await_terminal(service_ctx, handle.task_id)
    status = service_ctx.manager.status(handle.task_id)
    assert status.state == "done" and status.result is None  # 场景实证
    with pytest.raises(_mod.TaskNotCompleteError, match="结果尚未落地"):
        fetch_solutions(service_ctx, handle.task_id, 1, 2, "margin_min")

    def slow_enum(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        time.sleep(1)  # 保持非终态窗口
        return {"state": "done"}

    monkeypatch.setattr(manager_mod, "run_task", slow_enum)
    running = await service_ctx.manager.submit(
        TaskRequest(kind="enumerate", payload={"kind": "enumerate"})
    )
    assert service_ctx.manager.status(running.task_id).state in {"queued", "running"}
    with pytest.raises(_mod.TaskNotCompleteError, match="只在 done 终态可取"):
        fetch_solutions(service_ctx, running.task_id, 1, 2, "margin_min")
    await _await_terminal(service_ctx, running.task_id)  # 收尾


async def test_result_carries_unit_id_and_design_hash_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """P0-2：枚举 result 载荷带 unit_id（FE 深链回填源）+design_hash（漂移
    闸③比对源——与当前项目 design digest 一致锚：core/服务双胞胎镜像面）。"""
    project_id = await _cass_project(service_ctx)
    handle = await submit_enumeration(service_ctx, project_id, ["municipal_cass"])
    await _await_terminal(service_ctx, handle.task_id)
    status = service_ctx.manager.status(handle.task_id)
    assert status.state == "done"
    assert status.result is not None
    assert status.result["unit_id"] == "municipal_cass"
    # design_hash=枚举时点 design 摘要（calc result 同键先例）；未改设计时
    # 与当前项目 digest 一致（UF-47 收口批6l：core.design_hash 单源）
    assert status.result["design_hash"] == core_app.design_hash(
        projects_mod.read_project(service_ctx, project_id).design
    )
    # SolutionPage 透传（分页消费方零额外查询可知表源单元）
    page = fetch_solutions(service_ctx, handle.task_id, 1, 2, "margin_min")
    assert page.unit_id == "municipal_cass"


@pytest.mark.anyio
async def test_result_carries_dim_fields_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """V2 GOV5 批尾：枚举 result 载荷带 dim_fields（计算派生输出量列族
    [{key,dim,label_zh}]——manifest.out_dims 声明面真源）。ADR-018 批
    顺带（2026-09-12）：CASS 补声明 31 条 out_dims——本断言面随真源
    翻案（原「未声明全 None」→「声明面中文名透传」）。"""
    project_id = await _cass_project(service_ctx)
    handle = await submit_enumeration(service_ctx, project_id, ["municipal_cass"])
    await _await_terminal(service_ctx, handle.task_id)
    status = service_ctx.manager.status(handle.task_id)
    assert status.state == "done"
    assert status.result is not None
    # CASS 已声明 out_dims（31 条——ADR-018 批顺带）：dim 列族中文名
    # 透传真源（v_plant=全厂池容锚）；未声明键才降级 None（兜底归 webapp）
    dim_fields = status.result["dim_fields"]
    assert isinstance(dim_fields, list) and dim_fields, "dim 列族非空"
    by_key = {item["key"]: item for item in dim_fields}
    assert by_key["v_plant"]["label_zh"] == "全厂池容"
    assert by_key["theta_c"]["label_zh"] == "污泥龄"
    assert all(item["key"] for item in dim_fields)
    # grid 轴列不重复入 dim_fields（两族互斥）
    grid_keys = {item["key"] for item in status.result["grid_fields"]}
    assert not (grid_keys & {item["key"] for item in dim_fields})
