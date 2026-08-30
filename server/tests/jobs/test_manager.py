"""jobs manager 镜像测试：任务状态机、优先级队列、取消语义。

输入:  waterprint_server.jobs.manager 公开符号
输出:  调度契约断言（§12.2/§17.1）
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import json
import os
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.jobs.manager")
_worker_mod = importlib.import_module("waterprint_server.jobs.worker")
Manager = getattr(_mod, "Manager")
TaskRequest = getattr(_mod, "TaskRequest")
UnknownTaskError = getattr(_mod, "UnknownTaskError")

pytestmark = [
    pytest.mark.skipif(
        Manager is None,
        reason="实现未就绪：waterprint_server.jobs.manager（服务层 M2）",
    ),
    pytest.mark.anyio,
]

ORDER: list[str] = []
GATE = threading.Event()


def _fake_run_task(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
    """测试替身：受 gate 控制的慢任务（记录派发序；取消标记先行=cancelled）。"""
    ORDER.append(payload["kind"])
    GATE.wait()  # 占住并发位（优先序断言前提：后提交者在队列中等待）
    if cancel_token is not None and Path(cancel_token).exists():
        return {"state": "cancelled"}
    return {"state": "done", "value": payload["kind"]}


@pytest.fixture
async def manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """单并发 Manager（run_task 替身注入——派发序可观测）。"""
    monkeypatch.setattr(_mod, "run_task", _fake_run_task)
    executor = ThreadPoolExecutor(max_workers=1)
    instance = Manager(
        executor,
        cancel_dir=tmp_path / "cancel",
        loop=asyncio.get_running_loop(),
        max_concurrent=1,
    )
    instance.start()
    yield instance
    GATE.set()
    executor.shutdown(wait=True, cancel_futures=True)


async def test_priority_interactive_beats_batch_wiring(manager) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：交互计算优先于批量导出出队（防饿死 §17.1）。

    入队 [导出, 计算, 导出2]（导出先占运行位）→ 释放后计算先于导出2 执行。
    """
    ORDER.clear(), GATE.clear()
    first = await manager.submit(TaskRequest(kind="export_batch", payload={"kind": "export_batch", "project_id": "p"}))
    await manager.submit(TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p"}, priority=10))
    await manager.submit(TaskRequest(kind="export_batch", payload={"kind": "export_batch", "project_id": "p"}))
    assert manager.status(first.task_id).state == "running"
    for _ in range(100):  # 线程启动竞态：等首个导出占住运行位
        if len(ORDER) == 1:
            break
        await asyncio.sleep(0.05)
    assert ORDER == ["export_batch"]  # 运行位被首个导出占用（后两者排队）
    GATE.set()  # 释放：出队次序必须 calc（priority=10）先于 export_batch（同级 FIFO）
    for _ in range(100):
        if len(ORDER) >= 3:
            break
        await asyncio.sleep(0.05)
    assert ORDER == ["export_batch", "calc", "export_batch"]


async def test_cancel_running_task_discards_partial_wiring(manager, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R5 接线断言：取消后无半途结果落地。"""
    ORDER.clear(), GATE.clear()
    handle = await manager.submit(TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p"}))
    for _ in range(100):
        if manager.status(handle.task_id).state == "running":
            break
        await asyncio.sleep(0.05)
    assert manager.cancel(handle.task_id) is True  # running：协作令牌置位
    marker = tmp_path / "cancel" / f"{handle.task_id}.cancel"
    assert marker.is_file()  # 令牌=取消标记文件（跨进程共享值面）
    GATE.set()
    for _ in range(100):
        if manager.status(handle.task_id).state in {"done", "cancelled", "failed"}:
            break
        await asyncio.sleep(0.05)
    status = manager.status(handle.task_id)
    assert status.state == "cancelled"  # cancelled 而非 done（状态机单向 R1）
    assert status.result is None  # 半途结果丢弃（R5：取消后结果不落地）
    assert manager.cancel(handle.task_id) is False  # 终态不受取消影响（R3）


def _quick_done(payload, cancel_token=None, progress_queue=None):  # type: ignore[no-untyped-def]
    """测试替身：立即 done 的快任务（registry 落盘/恢复面载荷）。"""
    return {"state": "done", "value": payload["kind"]}


@contextlib.contextmanager
def _progress_queue_guard() -> Iterator[None]:
    """worker._PROGRESS_QUEUE 全局快照还原（test_spawn_smoke 全局卫生同款）。

    本文件 registry 用例的 Manager.start 会重写该全局，shutdown 会 close
    本用例队列——不还原则后跑的 test_worker 直调 run_task 踩已关闭队列。
    """
    prior = _worker_mod._PROGRESS_QUEUE  # noqa: SLF001  # 快照（注入口全局）
    try:
        yield
    finally:
        _worker_mod._PROGRESS_QUEUE = prior  # noqa: SLF001  # 还原（基线动态零漂移）


async def _drive_done_task(  # type: ignore[no-untyped-def]
    tmp_path, monkeypatch, registry
) -> str:
    """前置束：Manager A 跑 calc 至终态 done 落盘后优雅停机（重启语义前半）。"""
    monkeypatch.setattr(_mod, "run_task", _quick_done)
    executor = ThreadPoolExecutor(max_workers=1)
    instance = Manager(
        executor,
        cancel_dir=tmp_path / "cancel",
        loop=asyncio.get_running_loop(),
        max_concurrent=1,
        registry_dir=registry,
    )
    instance.start()
    handle = await instance.submit(
        TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p1"}),
        idempotency_key="k1",
    )
    instance.bind_snapshot(handle.task_id, "digest-abc")
    for _ in range(100):  # 线程派发竞态：轮询至终态（落盘前提）
        if instance.status(handle.task_id).state == "done":
            break
        await asyncio.sleep(0.05)
    await instance.shutdown(1.0)
    executor.shutdown(wait=True)
    return handle.task_id


async def test_terminal_registry_persists_and_restores_wiring(
    tmp_path, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """S2 D1/D2/D4/D5 接线断言：终态记录落盘+重启恢复可查+损坏/非终态跳过。

    恢复矩阵（重启语义=同 registry_dir 两 Manager 实例先后构造+start）：
    终态 done 落盘（_finish 原子写）→ 新实例 status 可查（审计字段独立
    回读逐项：state/result/snapshot_hash/project_id/task_ids_for_project）；
    损坏 JSON 跳过不阻断启动（fail-visible）；非终态记录不恢复（D1 无痕
    404）；幂等表不恢复（同 key 提交=新任务，D5）。
    """
    with _progress_queue_guard():
        registry = tmp_path / "tasks" / "registry"
        task_id = await _drive_done_task(tmp_path, monkeypatch, registry)
        record_file = registry / f"{task_id}.json"
        assert record_file.is_file()  # 终态迁移落盘（D1：_finish 原子写）
        raw = json.loads(record_file.read_bytes())  # 独立回读落盘面（质量门 5）
        assert raw["state"] == "done"
        assert raw["kind"] == "calc"
        assert raw["result"] == {"state": "done", "value": "calc"}
        assert raw["snapshot_hash"] == "digest-abc"
        assert raw["project_id"] == "p1"
        # R2 R5（DS-08）：六键回读断言（done 任务终值面——无进度上报路径下
        # progress/stage 保持迁移时刻值；error 族 None；stale False；condition_key None）。
        assert (raw["error"], raw["error_type"], raw["stale"]) == (None, None, False)
        assert (raw["progress"], raw["stage"], raw["condition_key"]) == (0.0, "queued", None)
        assert "subscribers" not in raw and "cancel_requested" not in raw  # 进程内字段排除（D4）
        (registry / "broken.json").write_bytes(b"{not json")  # 恢复矩阵夹具：损坏档
        (registry / "ghost.json").write_bytes(  # 非终态遗留档（D1 面不应存在——防御跳过）
            json.dumps(
                {
                    "task_id": "ghost",
                    "kind": "calc",
                    "payload": {"kind": "calc", "project_id": "p1"},
                    "state": "running",
                }
            ).encode("utf-8")
        )
        executor_b = ThreadPoolExecutor(max_workers=1)  # 重启语义：新实例同目录
        manager_b = Manager(
            executor_b,
            cancel_dir=tmp_path / "cancel",
            loop=asyncio.get_running_loop(),
            max_concurrent=1,
            registry_dir=registry,
        )
        manager_b.start()  # 扫描恢复（损坏跳过不炸启动——D2 fail-visible）
        restored = manager_b.status(task_id)
        assert restored.state == "done"  # 终态恢复供读（exports 最近结果集消费面）
        assert restored.kind == "calc"
        assert restored.result == {"state": "done", "value": "calc"}
        assert restored.project_id == "p1"
        # R2 R5（DS-08）：恢复面六键逐项（与落盘面同构——审计字段回读）。
        assert (restored.error, restored.error_type, restored.stale) == (None, None, False)
        assert (restored.progress, restored.stage, restored.condition_key) == (0.0, "queued", None)
        assert manager_b.snapshot(task_id) == "digest-abc"  # stale 判定面回读
        assert manager_b.task_ids_for_project("p1") == (task_id,)
        with pytest.raises(UnknownTaskError):  # 损坏跳过=不在注册表（404 面）
            manager_b.status("broken")
        with pytest.raises(UnknownTaskError):  # 非终态不恢复（D1：queued/running 无痕）
            manager_b.status("ghost")
        fresh = await manager_b.submit(  # D5：幂等表不恢复——同 key 新任务
        TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p1"}),
        idempotency_key="k1",
        )
        assert fresh.task_id != task_id
        await manager_b.shutdown(1.0)
        executor_b.shutdown(wait=True)


async def test_persist_oserror_does_not_stall_scheduling_wiring(
    tmp_path, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """R2 R1（DS-03）：落盘 OSError 不阻断调度——_finish 的 _pump 必达。

    落盘失败只损失重启恢复档（诚实降级），禁令调度停摆：首个任务仍终态
    done+第二个任务仍被出队执行。
    """
    with _progress_queue_guard():

        def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise OSError("disk full")

        monkeypatch.setattr(_mod, "run_task", _quick_done)
        monkeypatch.setattr(_mod.registry, "write_record", _boom)  # 落盘面炸
        executor = ThreadPoolExecutor(max_workers=1)
        instance = Manager(
            executor,
            cancel_dir=tmp_path / "cancel",
            loop=asyncio.get_running_loop(),
            max_concurrent=1,
            registry_dir=tmp_path / "tasks" / "registry",
        )
        instance.start()
        first = await instance.submit(
            TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p1"})
        )
        second = await instance.submit(
            TaskRequest(kind="calc", payload={"kind": "calc", "project_id": "p1"})
        )
        for _ in range(100):  # 停摆面=第二个任务永不出队：轮询超时即红
            if instance.status(second.task_id).state == "done":
                break
            await asyncio.sleep(0.05)
        assert instance.status(first.task_id).state == "done"  # 终态迁移不受落盘失败影响
        assert instance.status(second.task_id).state == "done"  # 调度不停摆（_pump 必达）
        await instance.shutdown(1.0)
        executor.shutdown(wait=True)


async def test_restore_order_follows_mtime_wiring(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R2 R2（DS-04）：恢复序按文件 mtime 升序（近似完成时刻序）。

    文件名序（taskaaa<taskzzz）与 mtime 序（zzz 先完成）相反的两记录：
    恢复后 task_ids_for_project 注册序=mtime 序——单并发下与注册序等价，
    多并发下比 uuid 字典序更贴「最近完成」业务语义（exports 最近结果集
    取最末 done=最近完成）。
    """
    registry = tmp_path / "tasks" / "registry"
    registry.mkdir(parents=True)

    def _put(task_id: str, mtime: float) -> None:
        document = {
            "task_id": task_id,
            "kind": "calc",
            "payload": {"kind": "calc", "task_id": task_id, "project_id": "p1"},
            "state": "done",
            "progress": 1.0,
            "stage": "serialize",
            "condition_key": None,
            "stale": False,
            "error": None,
            "error_type": None,
            "result": {"state": "done"},
            "snapshot_hash": None,
            "project_id": "p1",
        }
        entry = registry / f"{task_id}.json"
        entry.write_bytes(
            (json.dumps(document, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        )
        os.utime(entry, (mtime, mtime))  # 显式 mtime（跨文件系统精度无关）

    _put("taskzzz", 1000.0)  # 先完成（mtime 早）
    _put("taskaaa", 2000.0)  # 后完成（文件名字典序在前——序漂移夹具）
    with _progress_queue_guard():
        executor = ThreadPoolExecutor(max_workers=1)
        instance = Manager(
            executor,
            cancel_dir=tmp_path / "cancel",
            loop=asyncio.get_running_loop(),
            max_concurrent=1,
            registry_dir=registry,
        )
        instance.start()
        assert instance.task_ids_for_project("p1") == ("taskzzz", "taskaaa")  # mtime 升序
        await instance.shutdown(1.0)
        executor.shutdown(wait=True)
