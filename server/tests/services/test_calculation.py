"""calculation 服务镜像测试：幂等提交、快照绑定、方案应用原子性。

输入:  waterprint_server.services.calculation 公开符号
输出:  服务契约断言（§17.1 事件矩阵的服务侧执行）
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import threading

import pytest

_mod = importlib.import_module("waterprint_server.services.calculation")
submit_calculation = getattr(_mod, "submit_calculation")
apply_solution = getattr(_mod, "apply_solution")
task_status = getattr(_mod, "task_status")

projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = [
    pytest.mark.skipif(
        None in (submit_calculation, apply_solution),
        reason="实现未就绪：waterprint_server.services.calculation（服务层 M2）",
    ),
    pytest.mark.anyio,
]


def _file_digest(path) -> str:  # type: ignore[no-untyped-def]
    """项目文件字节哈希（回滚断言面——半写=字节漂移）。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def _created(ctx) -> str:  # type: ignore[no-untyped-def]
    outcome = projects_mod.create_project(
        ctx,
        {
            "project": {
                "format_version": "2.0",
                "design": {
                    "nodes": {
                        "inlet": {
                            "kind": "municipal_input",
                            "q_avg_daily": 34760.7 / 86400,
                            "kz": 1.4,
                            "CODCR": 400.0,
                            "BOD5": 200.0,
                            "SS": 250.0,
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
                    "format_version": "2.0",
                    "content_hash": "0",
                    "engine_version": "0",
                    "data_version": "0",
                },
            }
        },
    )
    return outcome.project_id


async def test_running_task_result_marked_stale_on_edit_wiring(service_ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：任务运行期间编辑 → 完成结果 stale=True（禁止静默覆盖）。"""
    import waterprint_server.jobs.manager as manager_mod

    release = threading.Event()

    def slow_task(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        release.wait(timeout=10)  # 运行窗口内完成编辑
        return {"state": "done", "project_id": payload.get("project_id", "")}

    monkeypatch.setattr(manager_mod, "run_task", slow_task)
    project_id = await _created(service_ctx)
    handle = await submit_calculation(service_ctx, project_id, [])
    await asyncio.sleep(0.2)  # 进入 running
    project = projects_mod.read_project(service_ctx, project_id)
    edited = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"assumption_overrides": {"safety.superheight": 0.3}}
            )
        }
    )
    projects_mod.save_project(service_ctx, project_id, edited)  # 运行期间编辑
    release.set()
    for _ in range(100):
        status = task_status(service_ctx, handle.task_id)
        if status.state in {"done", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.05)
    assert status.state == "done"
    assert status.stale is True  # 快照 vs 当前（UF-37：完成时对比=提示性标记）


async def test_failed_task_error_code_wired_wiring(service_ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """R1-2（AU-2）行为断言：failed 任务携 LoopDivergence 名→error_code==422。

    worker 侧领域异常（类不可直连导入——D7 forbidden）按 error_type 名经
    DOMAIN_ERROR_CODES 注入表回填结构化 error_code（响应体语义字段）。
    """
    from fastapi import status as http_status

    import waterprint_server.jobs.manager as manager_mod
    from waterprint_server.main import DOMAIN_ERROR_CODES

    class LoopDivergence(Exception):  # noqa: N818  # 与 core 同名异常（名义表按名映射的前提）
        """测试替身：worker 侧回路发散诊断名。"""

    def divergent_task(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        raise LoopDivergence("回路发散：迭代超上限（测试注入）")

    monkeypatch.setattr(manager_mod, "run_task", divergent_task)
    # 注入表（生产由 main lifespan 注入；service_ctx 直测面手动同款注入）
    object.__setattr__(
        service_ctx, "domain_error_codes", dict(DOMAIN_ERROR_CODES)
    )
    project_id = await _created(service_ctx)
    handle = await submit_calculation(service_ctx, project_id, [])
    for _ in range(100):
        final = task_status(service_ctx, handle.task_id)
        if final.state in {"done", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.05)
    assert final.state == "failed"
    assert final.error_type == "LoopDivergence"  # 诊断名回传（worker→manager 面）
    assert final.error_code == http_status.HTTP_422_UNPROCESSABLE_CONTENT  # 名义表接线
    assert final.error_code == DOMAIN_ERROR_CODES["LoopDivergence"]  # 与映射表一致


async def test_apply_solution_rolls_back_on_failure_wiring(service_ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：应用方案中途失败 → design/hash 回滚（无半写）。"""
    project_id = await _created(service_ctx)
    path = service_ctx.projects_dir / f"{project_id}.wp.json"
    before = _file_digest(path)

    def broken_trigger(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("注入的触发器失败（测试构造中途失败）")

    monkeypatch.setattr(_mod, "submit_calculation", broken_trigger)
    with pytest.raises(RuntimeError, match="已回滚"):
        await apply_solution(
            service_ctx, project_id, {"unit_id": "inlet", "params": {"kz": 1.5}}
        )
    assert _file_digest(path) == before  # 项目文件字节未变（无半写）
    outcome = projects_mod.validate_project(service_ctx, project_id)
    assert outcome.valid  # 回滚后装载面完好
