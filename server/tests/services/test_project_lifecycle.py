"""project_lifecycle 服务镜像测试：复制（副本名递增/同 digest/无名源）、
重命名（view.name 轻通道 design_changed=False）、删除（404/锁/在途三守卫）。

输入:  waterprint_server.services.project_lifecycle 公开符号
输出:  服务契约断言
"""

from __future__ import annotations

import importlib
from typing import cast

import pytest

from waterprint_server.jobs.manager import Manager
from waterprint_server.services import ServiceContext

_mod = importlib.import_module("waterprint_server.services.project_lifecycle")
copy_project = getattr(_mod, "copy_project")
rename_project = getattr(_mod, "rename_project")
delete_project = getattr(_mod, "delete_project")
ProjectBusyError = getattr(_mod, "ProjectBusyError")

_projects = importlib.import_module("waterprint_server.services.projects")
create_project = getattr(_projects, "create_project")
read_project = getattr(_projects, "read_project")
InvalidProjectPayloadError = getattr(_projects, "InvalidProjectPayloadError")
ProjectLockedError = getattr(_projects, "ProjectLockedError")
ProjectNotFoundError = getattr(_projects, "ProjectNotFoundError")

# skipif 不挂（PL-N-04 R2）：实现件与本测试同批落库——import 即保证；
# 骨架期休眠制式（AGENTS §6）适用于实现后置批，本件无该窗口。
pytestmark = [pytest.mark.anyio]


async def _created(ctx, name: str | None):  # type: ignore[no-untyped-def]
    """创建命名（name=None=未命名）项目并返回 (id, content_hash)。"""
    outcome = create_project(ctx, {"name": name} if name else {})
    return outcome.project_id, outcome.content_hash


# ── C1 复制 ───────────────────────────────────────────────────────


async def test_copy_design_unchanged_and_name_increment_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C1 接线断言：design 零动同 digest+副本名占用面递增（(副本)/(副本2)）。"""
    source_id, digest = await _created(service_ctx, "原型")
    copy1 = copy_project(service_ctx, source_id)
    copy2 = copy_project(service_ctx, source_id)
    assert copy1.project_id not in {source_id, copy2.project_id}
    assert copy1.content_hash == digest == copy2.content_hash  # design 不动
    assert copy1.design_changed is True  # 新项目落盘=创建语义
    assert read_project(service_ctx, copy1.project_id).view.name == "原型 (副本)"
    assert read_project(service_ctx, copy2.project_id).view.name == "原型 (副本2)"


async def test_copy_unnamed_source_keeps_unnamed_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C1 接线断言：源无名→副本无名（空串语义沿 P0-1——FE 回退 id）。"""
    source_id, _ = await _created(service_ctx, None)
    copied = copy_project(service_ctx, source_id)
    assert read_project(service_ctx, copied.project_id).view.name == ""


async def test_copy_missing_project_raises_404_family(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C1 守卫：源不存在→ProjectNotFoundError（404 面）。"""
    with pytest.raises(ProjectNotFoundError):
        copy_project(service_ctx, "absent-project")


async def test_copy_name_two_digit_index_stays_within_limit(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """PL-N-01 R2 闭合：两位序数（(副本10)）逐候选动态截断——全长恒 ≤100。

    占满 (副本)~(副本9) 后下一候选=两位序数：后缀更长即基名再让一位，
    任意序数不越限（原静态预算制两位序数 101 越限缺陷实证修复）。
    """
    long_name = "长" * 95
    source_id, _ = await _created(service_ctx, long_name)
    # 占用 (副本)~(副本9)：首候选=95+5=100 恰满；两位序数候选=94+6=100
    for index in range(1, 10):
        suffix = " (副本)" if index == 1 else f" (副本{index})"
        create_project(service_ctx, {"name": f"{long_name[:100 - len(suffix)]}{suffix}"})
    outcome = copy_project(service_ctx, source_id)
    final = read_project(service_ctx, outcome.project_id).view.name
    assert final.endswith("(副本10)")
    assert len(final) <= 100
    assert final not in {"长" * 95 + f" (副本{i})" for i in range(1, 10)}


async def test_copy_fresh_lock_raises_409_family(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C1 守卫：新鲜锁→ProjectLockedError（core 读锁拒绝以 400 错族——守卫前置归 409 正族）。"""
    source_id, _ = await _created(service_ctx, "锁拷")
    lock = service_ctx.projects_dir / f"{source_id}.wp.lock"
    lock.write_text("host|pid|ts", encoding="utf-8")
    try:
        with pytest.raises(ProjectLockedError):
            copy_project(service_ctx, source_id)
    finally:
        lock.unlink(missing_ok=True)


# ── C2 重命名 ─────────────────────────────────────────────────────


async def test_rename_light_channel_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C2 接线断言：strip 落盘+design_changed=False+digest 恒等（view 态不入哈希）。"""
    project_id, digest = await _created(service_ctx, "旧名")
    outcome = rename_project(service_ctx, project_id, "  新名  ")
    assert outcome.design_changed is False
    assert outcome.content_hash == digest
    assert read_project(service_ctx, project_id).view.name == "新名"


async def test_rename_rejects_blank_and_overlong_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C2 守卫：空白名（重命名至未命名无意义）与超长名→422 面。"""
    project_id, _ = await _created(service_ctx, "名")
    with pytest.raises(InvalidProjectPayloadError):
        rename_project(service_ctx, project_id, "   ")
    with pytest.raises(InvalidProjectPayloadError):
        rename_project(service_ctx, project_id, "长" * 101)


async def test_rename_missing_project_raises_404_family(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C2 守卫：目标不存在→ProjectNotFoundError。"""
    with pytest.raises(ProjectNotFoundError):
        rename_project(service_ctx, "absent-project", "新名")


async def test_rename_bad_name_precedes_missing_project(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """PL-N-06 R2 口径锁：名称校验 422 先于存在性 404（FastAPI body 层序一致）。"""
    with pytest.raises(InvalidProjectPayloadError):
        rename_project(service_ctx, "absent-project", "   ")


async def test_rename_fresh_lock_raises_409_family(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C2 守卫：新鲜锁（save_project 复用面）→ProjectLockedError，名未落盘。"""
    project_id, _ = await _created(service_ctx, "锁名")
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("host|pid|ts", encoding="utf-8")
    try:
        with pytest.raises(ProjectLockedError):
            rename_project(service_ctx, project_id, "锁后名")
    finally:
        lock.unlink(missing_ok=True)
    # 回读断言在锁清除后（core 读锁对锁存在恒拒——断言先行即误伤）
    assert read_project(service_ctx, project_id).view.name == "锁名"


# ── C3 删除 ───────────────────────────────────────────────────────


class _StateView:
    """status() 桩视角（本面仅读 .state——守卫判据单源）。"""

    def __init__(self, state: str) -> None:
        self.state = state


class _StubManager:
    """在途任务桩（task_ids_for_project+status 两面——确定性守卫测试）。"""

    def __init__(self, states: dict[str, str]) -> None:
        self._states = states

    def task_ids_for_project(self, project_id: str) -> tuple[str, ...]:
        return tuple(self._states)

    def status(self, task_id: str) -> _StateView:  # type: ignore[override]
        return _StateView(self._states[task_id])


async def test_delete_removes_file_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C3 接线断言：删除后文件除却（read 404）+project_id 回显。"""
    project_id, _ = await _created(service_ctx, "待删")
    outcome = delete_project(service_ctx, project_id)
    assert outcome.project_id == project_id
    with pytest.raises(ProjectNotFoundError):
        read_project(service_ctx, project_id)


async def test_delete_missing_project_raises_404_family(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C3 守卫①：不存在→ProjectNotFoundError。"""
    with pytest.raises(ProjectNotFoundError):
        delete_project(service_ctx, "absent-project")


async def test_delete_busy_guard_blocks_and_done_allows(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C3 守卫③：在途（queued/running）→ProjectBusyError 文件保留；终态放行。"""
    busy_id, _ = await _created(service_ctx, "在途项目")
    busy_ctx = ServiceContext(
        settings=service_ctx.settings,
        manager=cast(Manager, _StubManager({"t-running": "running"})),
    )
    with pytest.raises(ProjectBusyError):
        delete_project(busy_ctx, busy_id)
    assert read_project(busy_ctx, busy_id).view.name == "在途项目"  # 未删
    done_ctx = ServiceContext(
        settings=service_ctx.settings,
        manager=cast(Manager, _StubManager({"t-done": "done"})),
    )
    delete_project(done_ctx, busy_id)  # 终态记录不阻
    with pytest.raises(ProjectNotFoundError):
        read_project(done_ctx, busy_id)


async def test_delete_fresh_lock_raises_409_family(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """C3 守卫②：新鲜锁→ProjectLockedError（陈旧清除放行面归 save 锁族测试）。"""
    project_id, _ = await _created(service_ctx, "锁删")
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("host|pid|ts", encoding="utf-8")
    try:
        with pytest.raises(ProjectLockedError):
            delete_project(service_ctx, project_id)
    finally:
        lock.unlink(missing_ok=True)
