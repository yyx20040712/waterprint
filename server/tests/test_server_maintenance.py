"""服务端维护面镜像测试（WP4 外审整改#6）：任务 TTL 清扫/cap 驱逐、PUT
深度闸、项目锁过期、settings 新字段 fail-fast、WATERPRINT_PORT 边界。

输入:  waterprint_server jobs.manager / services.projects / settings 公开符号
输出:  维护行为契约断言（四修红先绿后）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（WP4 服务端小修攒批 2026-09-02）
#
# 【覆盖面】
#   - TTL 清扫（修1）：伪造终态+旧时间戳→sweep_expired→_tasks/_idem/
#     registry 档/cancel 标记/calc 结果/enum 行文件全灭+新鲜终态存活；
#   - cap 驱逐（修1）：_tasks 超上限驱最旧终态（finished_at 升序）；
#   - PUT 深度闸（修3）：view.layout 深炸弹→422+域面 InvalidProjectPayload
#     Error（修复前=pydantic 序列化守卫 ValueError 兜底面+≤99 层静默落盘
#     ——parse_project 的 layout=dict[str,Any] 透传无深度闸）；
#   - 锁过期（修4）：mtime 年龄>lock_expiry_s=陈旧残留→放行；新鲜锁
#     409 旧语义保持；stat 不可得=保守锁面（旧语义）；
#   - K-5（R2-C 修1·2026-09-02）：TOCTOU 竞态注入——过期判定后校验前
#     （Path.read_bytes 第二次快照钩子注入点）新持有者重建锁（新内容+
#     新 mtime）→409 fail-closed 新持有者锁存活；持有者心跳 touch（同
#     内容+新 mtime）→409 活性铁证；心跳原语 refresh_lock_mtime（touch
#     已存锁 mtime；缺锁 False 零创建——server 零写入方不变）；
#   - settings：task_retention_s/task_sweep_interval_s/task_registry_cap/
#     lock_expiry_s 默认合法+0/-1 构造拒（fail-fast 入列）+E1 冻结真值
#     精确锚（R2-C 测试债——字面真值非比较表）；
#   - WP1 债：WATERPRINT_PORT env 0/65536 出 TCP 值域→ValidationError。
# 【替身口径】直构 _TaskRecord 终态（manager 内部面——noqa SLF001 同
#   tests/jobs/test_manager.py 先例；不经调度=清扫判定单变量）。
# 【参照】WP4 简报；外审整改#6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic import ValidationError

_manager_mod = importlib.import_module("waterprint_server.jobs.manager")
_projects_mod = importlib.import_module("waterprint_server.services.projects")
_io_mod = importlib.import_module("waterprint.project.io")
InvalidProjectError = getattr(_io_mod, "InvalidProjectError")
_settings_mod = importlib.import_module("waterprint_server.settings")
Settings = getattr(_settings_mod, "Settings")
TaskRequest = getattr(_manager_mod, "TaskRequest")

pytestmark = [
    pytest.mark.skipif(
        None in (Settings, TaskRequest),
        reason="实现未就绪：waterprint_server 维护面（服务层）",
    ),
]

_WP4_FIELDS = (
    "task_retention_s",
    "task_sweep_interval_s",
    "task_registry_cap",
    "lock_expiry_s",
)


def _terminal_record(task_id: str, finished_at: float) -> object:  # type: ignore[no-any-return]
    """伪造终态记录（done+完成时间戳——TTL/cap 判定输入，不经调度）。"""
    return _manager_mod._TaskRecord(  # noqa: SLF001  # 内部面直构（test_manager.py 先例）
        task_id=task_id,
        request=TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p1"}),
        state="done",
        finished_at=finished_at,
    )


@pytest.mark.anyio
async def test_ttl_sweep_removes_expired_terminal_task_wiring(tmp_path: Path) -> None:
    """修1 接线断言：过期终态淘汰=内存双表+四类落盘面全灭；新鲜终态存活。"""
    registry_dir = tmp_path / "tasks" / "registry"
    cancel_dir = tmp_path / "tasks" / "cancel"
    artifacts_dir = tmp_path / "tasks"
    executor = ThreadPoolExecutor(max_workers=1)
    manager = _manager_mod.Manager(
        executor,
        cancel_dir=cancel_dir,
        loop=asyncio.get_running_loop(),
        max_concurrent=1,
        registry_dir=registry_dir,
        artifacts_dir=artifacts_dir,
        task_retention_s=1,
        task_registry_cap=10 * 10,  # cap 充裕：本用例 retention 单变量
    )
    try:
        registry_dir.mkdir(parents=True, exist_ok=True)
        cancel_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        manager._tasks["t-old"] = _terminal_record("t-old", time.time() - 2)  # noqa: SLF001
        manager._tasks["t-fresh"] = _terminal_record("t-fresh", time.time())  # noqa: SLF001
        manager._idem["k-old"] = "t-old"  # noqa: SLF001
        manager._idem["k-fresh"] = "t-fresh"  # noqa: SLF001
        (registry_dir / "t-old.json").write_bytes(b"{}")
        (cancel_dir / "t-old.cancel").write_text("cancelled", encoding="utf-8")
        (artifacts_dir / "calc-t-old.json").write_bytes(b"{}")
        (artifacts_dir / "enum-t-old.feather").write_bytes(b"arrow")
        (registry_dir / "t-fresh.json").write_bytes(b"{}")  # 新鲜终态文件面
        evicted = manager.sweep_expired()
        assert evicted == 1
        assert "t-old" not in manager._tasks  # noqa: SLF001
        assert "t-fresh" in manager._tasks  # noqa: SLF001
        assert "k-old" not in manager._idem and "k-fresh" in manager._idem  # noqa: SLF001
        assert not (registry_dir / "t-old.json").exists()  # registry 档灭
        assert not (cancel_dir / "t-old.cancel").exists()  # cancel 标记灭
        assert not (artifacts_dir / "calc-t-old.json").exists()  # calc 结果灭
        assert not (artifacts_dir / "enum-t-old.feather").exists()  # enum 行文件灭
        assert (registry_dir / "t-fresh.json").is_file()  # 新鲜终态不动
    finally:
        executor.shutdown(wait=True)


@pytest.mark.anyio
async def test_sweep_cap_evicts_oldest_terminal_wiring(tmp_path: Path) -> None:
    """修1 接线断言：_tasks 超 cap 驱逐最旧终态（finished_at 升序最前者）。"""
    executor = ThreadPoolExecutor(max_workers=1)
    manager = _manager_mod.Manager(
        executor,
        cancel_dir=tmp_path / "cancel",
        loop=asyncio.get_running_loop(),
        max_concurrent=1,
        task_retention_s=10**6,  # 保留窗极大：本用例 cap 单变量
        task_registry_cap=2,
    )
    try:
        now = time.time()
        for task_id, age in (("t-a", 30), ("t-b", 20), ("t-c", 10)):
            manager._tasks[task_id] = _terminal_record(task_id, now - age)  # noqa: SLF001
        assert manager.sweep_expired() == 1
        assert set(manager._tasks) == {"t-b", "t-c"}  # noqa: SLF001  # 最旧 t-a 被驱
    finally:
        executor.shutdown(wait=True)


@pytest.mark.anyio
async def test_put_depth_bomb_returns_422_not_500_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """修3 接线断言：PUT view.layout 深炸弹→422 且域面=深度闸（非偶然面）。

    修复前：parse_project 透传（ViewState.layout=dict[str,Any]）→落盘期
    pydantic 序列化器 100 层守卫炸 ValueError「Circular reference」（422
    出自 ValueError 兜底映射非深度闸；≤99 层深结构更被静默落盘 200）。
    修复后：服务面 _check_depth 前置（max_json_depth 与 create 同限）。
    """
    created = await client.post("/api/projects", json={})
    project_id = created.json()["project_id"]
    body = (await client.get(f"/api/projects/{project_id}")).json()
    bomb: dict[str, object] = {"leaf": 0}
    for _ in range(2 * 10**2):  # 深度 200+ >> max_json_depth=100
        bomb = {"n": bomb}
    body["view"]["layout"] = bomb
    response = await client.put(f"/api/projects/{project_id}", json=body)
    assert response.status_code == 422  # 深度闸 422（非 500）
    assert response.json()["error_type"] == "InvalidProjectPayloadError"  # 域面非兜底


@pytest.mark.anyio
async def test_expired_lock_allows_save_wiring(service_ctx, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """修4 接线断言：锁 mtime 年龄>lock_expiry_s=陈旧残留→视为无锁放行。"""
    outcome = _projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_id = outcome.project_id
    project = _projects_mod.read_project(service_ctx, project_id)  # 锁前置读取
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("stale-holder", encoding="utf-8")
    expired = time.time() - (service_ctx.settings.lock_expiry_s + 1)
    os.utime(lock, (expired, expired))  # 显式旧 mtime（跨文件系统精度无关）
    result = _projects_mod.save_project(service_ctx, project_id, project)
    assert result.design_changed is False  # 同内容保存走通全链（放行铁证）
    assert not lock.exists()  # 陈旧锁清除=「视为无锁」落地形态（后续读写不再受阻）


@pytest.mark.anyio
async def test_fresh_lock_still_blocks_409_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """修4 接线断言：新鲜锁（mtime 未过窗）409——旧语义保持零漂移。"""
    created = await client.post("/api/projects", json={})
    project_id = created.json()["project_id"]
    body = (await client.get(f"/api/projects/{project_id}")).json()
    lock = test_settings.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("active-holder", encoding="utf-8")
    response = await client.put(f"/api/projects/{project_id}", json=body)
    assert response.status_code == 409
    assert response.json()["error_type"] == "ProjectLockedError"


@pytest.mark.anyio
async def test_stale_lock_swap_in_window_blocks_save_wiring(
    service_ctx, cass_payload, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """K-5+M8-A/W1 竞态注入：判定后摘下前新持有者重建锁→409 fail-closed。

    注入口=Path.rename 钩子（M8-A 原子摘下机制——摘下前注入换锁，rename
    把新持有者文件摘走→摘下件快照≠首快照→回滚+409，新持有者锁存活；
    修复前旧码 unlink 直落=新持有者锁被误删+双写者放行——红相即本缺陷）。
    时间推进=os.utime 回拨 mtime（真文件系统面，非全局 time.time patch）。
    """
    outcome = _projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_id = outcome.project_id
    project = _projects_mod.read_project(service_ctx, project_id)
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("holder-a|111|t0", encoding="utf-8")
    expired = time.time() - (service_ctx.settings.lock_expiry_s + 1)
    os.utime(lock, (expired, expired))
    original_rename = Path.rename

    def _swap_before_rename(self: Path, target: Path) -> Path:  # type: ignore[no-untyped-def]
        if self == lock:  # K-5 窗口注入：判定后摘下前新持有者换锁
            lock.write_text("holder-b|222|t1", encoding="utf-8")
            os.utime(lock, None)  # 新内容+新 mtime（重建锁全量替换）
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", _swap_before_rename)
    with pytest.raises(_projects_mod.ProjectLockedError):
        _projects_mod.save_project(service_ctx, project_id, project)
    assert lock.read_text(encoding="utf-8") == "holder-b|222|t1"  # 新持有者锁存活


@pytest.mark.anyio
async def test_stale_lock_new_holder_after_claim_survives_wiring(
    service_ctx, cass_payload, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """M8-A/W1 铁证：摘下后新持有者获锁→新锁存活+保存 fail-closed 拒。

    W1（K-01 本体残余）收口面：R2C 版二次快照→unlink 微窗内新锁会被
    误删（旧码删锁后读面无锁放行=双会话并行缺陷）；M8-A 原子摘下后
    微窗内锁已离原径，新锁不可能被误删——保存流随后 core.load_project
    读面见新锁即拒（InvalidProjectError fail-closed，新持有者赢）。
    """
    outcome = _projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_id = outcome.project_id
    project = _projects_mod.read_project(service_ctx, project_id)
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("holder-a|111|t0", encoding="utf-8")
    expired = time.time() - (service_ctx.settings.lock_expiry_s + 1)
    os.utime(lock, (expired, expired))
    original_rename = Path.rename

    def _create_after_rename(self: Path, target: Path) -> Path:  # type: ignore[no-untyped-def]
        moved = original_rename(self, target)
        if self == lock:  # W1 微窗注入：摘下后 unlink 前新持有者获锁
            lock.write_text("holder-b|222|t1", encoding="utf-8")
            os.utime(lock, None)
        return moved

    monkeypatch.setattr(Path, "rename", _create_after_rename)
    with pytest.raises(InvalidProjectError, match="锁定"):  # 读面 fail-closed
        _projects_mod.save_project(service_ctx, project_id, project)
    assert lock.read_text(encoding="utf-8") == "holder-b|222|t1"  # W1 铁证：新锁零误删


@pytest.mark.anyio
async def test_heartbeat_touch_in_window_blocks_save_wiring(
    service_ctx, cass_payload, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """K-5+M8-A 心跳语义：判定后摘下前持有者 touch mtime（内容不变）→409。

    长保存/长编辑会话的持有者周期心跳刷新 mtime——判定窗口内任何触碰
    =持有者活性铁证，陈旧清除拒绝（fail-closed）；注入口=Path.rename
    钩子（摘下前 touch——摘下件快照 mtime≠首快照→回滚+409，锁存活）。
    """
    outcome = _projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_id = outcome.project_id
    project = _projects_mod.read_project(service_ctx, project_id)
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    lock.write_text("holder-a|111|t0", encoding="utf-8")
    expired = time.time() - (service_ctx.settings.lock_expiry_s + 1)
    os.utime(lock, (expired, expired))
    touched = time.time()  # 心跳戳（区别于判定快照的旧 mtime）
    original_rename = Path.rename

    def _touch_before_rename(self: Path, target: Path) -> Path:  # type: ignore[no-untyped-def]
        if self == lock:  # 窗口注入：心跳 touch（内容不变仅 mtime）
            os.utime(lock, (touched, touched))
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", _touch_before_rename)
    with pytest.raises(_projects_mod.ProjectLockedError):
        _projects_mod.save_project(service_ctx, project_id, project)
    assert lock.read_text(encoding="utf-8") == "holder-a|111|t0"  # 原持有者锁存活


@pytest.mark.anyio
async def test_refresh_lock_mtime_heartbeat_helper_wiring(
    service_ctx, cass_payload  # type: ignore[no-untyped-def]
) -> None:
    """K-5 心跳原语：refresh_lock_mtime touch 已存锁 mtime 至当前；缺锁不创建。"""
    outcome = _projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_id = outcome.project_id
    lock = service_ctx.projects_dir / f"{project_id}.wp.lock"
    assert _projects_mod.refresh_lock_mtime(service_ctx, project_id) is False  # 缺锁=False
    assert not lock.exists()  # 零创建（server 零写入方铁律不变）
    lock.write_text("holder-a|111|t0", encoding="utf-8")
    stale = time.time() - service_ctx.settings.lock_expiry_s
    os.utime(lock, (stale, stale))
    assert _projects_mod.refresh_lock_mtime(service_ctx, project_id) is True
    # 刷新至当前（远新于陈旧戳——半窗余量防时钟源毫秒级偏差误报）
    assert lock.stat().st_mtime > stale + (service_ctx.settings.lock_expiry_s / 2)
    assert lock.stat().st_mtime <= time.time() + 1  # 且贴近当前时刻（非未来戳）


def test_wp4_settings_defaults_valid_wiring() -> None:
    """修1/修4 接线断言：新字段默认合法+E1 冻结真值精确锚（R2-C 测试债）。"""
    defaults = Settings()
    expected = {
        "task_retention_s": 100000,
        "task_sweep_interval_s": 100,
        "task_registry_cap": 1000,
        "lock_expiry_s": 10000,
    }
    for field, value in expected.items():
        assert getattr(defaults, field) == value  # E1 冻结全集（字面真值锚非比较表）


@pytest.mark.parametrize("field", _WP4_FIELDS)
@pytest.mark.parametrize("bad", [0, -1])
def test_wp4_settings_reject_nonpositive_wiring(field: str, bad: int) -> None:
    """修1/修4 接线断言：R2 fail-fast——0/-1 构造即 ValidationError（不静默）。"""
    assert getattr(Settings(**{field: 1}), field) == 1  # 合法下限过（1=白名单值）
    with pytest.raises(ValidationError):
        Settings(**{field: bad})


@pytest.mark.parametrize("bad_port", ["0", "65536"])
def test_waterprint_port_env_boundary_rejected_wiring(
    monkeypatch: pytest.MonkeyPatch, bad_port: str
) -> None:
    """WP1 挂账补测：WATERPRINT_PORT env 0/65536 出 TCP 值域→ValidationError。"""
    monkeypatch.setenv("WATERPRINT_PORT", bad_port)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
