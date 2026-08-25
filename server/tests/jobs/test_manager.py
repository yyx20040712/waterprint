"""jobs manager 镜像测试：任务状态机、优先级队列、取消语义。

输入:  waterprint_server.jobs.manager 公开符号
输出:  调度契约断言（§12.2/§17.1）
"""

from __future__ import annotations

import asyncio
import importlib
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.jobs.manager")
Manager = getattr(_mod, "Manager")
TaskRequest = getattr(_mod, "TaskRequest")

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
