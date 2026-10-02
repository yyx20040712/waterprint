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
                # inlet-m3d 批 2026-10-02 随行 v4（L4a v3 先例同形态）：载荷=
                # 当前版新建态——回滚重写面版本头零漂移（v3 字面经读时迁移
                # 回写=字节变）。q_avg_daily=m³/d 参数面直用。
                "format_version": "4.0",
                "design": {
                    "nodes": {
                        "inlet": {
                            "kind": "municipal_input",
                            "q_avg_daily": 34760.7,
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
                    "format_version": "4.0",
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


# ── 批3b face④/builtin 带 422 与软提示面（b3a §二 A/E 组+§七追认）───────


async def test_apply_rejects_out_of_range_param_422(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """批3b face④ E2E：cass t_draw=2.0 越带 [1.0,1.5]→InvalidSolutionRefError
    （=路由 422 源——AUD2 C-4 整批拒语义；D-5 执法接线实证）。"""
    project_id = await _created(service_ctx)
    with pytest.raises(_mod.InvalidSolutionRefError, match="越带"):
        await apply_solution(
            service_ctx,
            project_id,
            {"unit_id": "municipal_cass", "params": {"t_draw": 2.0}},
        )


async def test_apply_rejects_absurd_inlet_flow_422(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """批3b A-1 E2E（inlet-m3d 批 2026-10-02 换轴 m³/d 面）：q_avg_daily=
    6000000.0（600 万 m³/d）超 518.4 万 m³/d 顶格类硬界→422 拒（进水
    物理域检之前提交面早拒）。audit AUD-B3 病例值 34760.7 统一后=常规
    量级改走接受面（core test_params_guard 同款换轴锚）。"""
    project_id = await _created(service_ctx)
    with pytest.raises(_mod.InvalidSolutionRefError, match="硬界"):
        await apply_solution(
            service_ctx,
            project_id,
            {"unit_id": "inlet", "params": {"q_avg_daily": 6000000.0}},
        )


async def test_apply_warn_band_not_blocking_only_logged(  # type: ignore[no-untyped-def]
    service_ctx, monkeypatch
) -> None:
    """批3b A-2：提示带不阻塞（E2E-1 fail-fast——硬错早拒、软提示不拦）
    +服务侧日志记一条（verdict.warn→_LOGGER.warning，exports.py 先例面）。"""
    from types import SimpleNamespace

    recorded: list[dict] = []

    class _SpyLogger:
        def warning(self, event: str, **kw: object) -> None:
            recorded.append({"event": event, **kw})

    async def quiet_trigger(*args, **kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(task_id="t-warn-face")

    monkeypatch.setattr(_mod, "_LOGGER", _SpyLogger())
    monkeypatch.setattr(_mod, "submit_calculation", quiet_trigger)
    project_id = await _created(service_ctx)
    outcome = await apply_solution(
        service_ctx,
        project_id,
        # 120 万 m³/d 提示带（inlet-m3d 批换轴——m³/d 输入面直用）
        {"unit_id": "inlet", "params": {"q_avg_daily": 1200000.0}},
    )
    assert outcome.project_id == project_id  # 不阻塞：应用成功
    assert outcome.recalc_task_id == "t-warn-face"
    assert any("超大型厂" in str(r.get("warn", "")) for r in recorded)  # 日志恰记


async def test_idempotency_key_derived_from_migrated_design_hash(  # type: ignore[no-untyped-def]
    service_ctx, monkeypatch
) -> None:
    """UF-62⑥ 幂等键派生面锚（conv-golden 批 2026-10-02）：键 digest=
    read_project **迁移态** design_hash——v3 存量档读时迁移 v4 后取哈希，
    与档内 stored content_hash（旧版占位）异源恒不受扰。

    既有覆盖（routers/test_calc duplicate submit→同 task_id+派发恰 1）
    只锚幂等行为面，不锚键派生面——本用例补缺面（禁重复锚）：golden
    migrations v3_0_to_4_0_input.json 造 projects 存量档（v3.0 字节原样
    落盘），submit_calculation 两次同 task_id（同键命中）+键全文==
    calc:{project_id}:{design_hash(read_project.design)}:{sorted conditions
    join}（manager._idem 内部面观测——test_server_maintenance noqa SLF001
    先例）。sorted 面：conditions 乱序传入（municipal_aao 在前），键内
    'conveyance_peishuiqu|municipal_aao' 字典序归一（回炉轮 1 R5：虚构
    id conveyance_aao 改档内真实单元 id——两 id 取自单元注册表在册名）。
    """
    import json as _json
    from pathlib import Path

    from waterprint import app as core_app

    import waterprint_server.jobs.manager as manager_mod

    def quick_done(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
        return {"state": "done", "project_id": payload.get("project_id", "")}

    monkeypatch.setattr(manager_mod, "run_task", quick_done)
    sample = (
        Path(__file__).resolve().parents[3]
        / "core" / "tests" / "golden" / "golden_data" / "migrations"
        / "v3_0_to_4_0_input.json"
    )  # 仓库根定位（server/tests/services→根=parents[3]）
    project_id = "legacy-v3-idempotency-probe"
    (service_ctx.projects_dir / f"{project_id}.wp.json").write_text(
        sample.read_text(encoding="utf-8"), encoding="utf-8"
    )  # v3 存量档字节原样（读时迁移面承接）
    conditions = ["municipal_aao", "conveyance_peishuiqu"]  # 乱序传入（字典序归一在键内）
    first = await submit_calculation(service_ctx, project_id, conditions)
    second = await submit_calculation(service_ctx, project_id, conditions)
    assert first.task_id == second.task_id  # 同键命中（不重复入队）
    migrated = projects_mod.read_project(service_ctx, project_id)
    assert migrated.format_version == "4.0"  # 读路径迁移到达态（键哈希基）
    digest = core_app.design_hash(migrated.design)
    stored = _json.loads(sample.read_text(encoding="utf-8"))["metadata"][
        "content_hash"
    ]
    assert digest != stored  # 异源恒等面：键取迁移态哈希非档内旧版占位
    expected_key = (
        f"calc:{project_id}:{digest}:{'|'.join(sorted(conditions))}"
    )
    assert service_ctx.manager._idem[expected_key] == first.task_id  # noqa: SLF001  # 内部面观测（先例注记在 docstring）
    for _ in range(100):  # 收尾（替身终态迁移）
        if task_status(service_ctx, first.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.05)
