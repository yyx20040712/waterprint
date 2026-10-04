"""jobs 测试面公共夹具（HH1/1A7 批 2026-10-04）。

背景：worker._PROGRESS_QUEUE 是模块级全局（Manager.start 注入、
进程池 initializer 注入同队列——两条通路同一队列）；Manager.shutdown
关闭队列但不回收该全局（生产单 Manager 生命周期=进程级无恙；测试每
测试起停 Manager=全局残留已关闭队列）。后跑的直调 run_task(payload,
None, None) 落到全局兜底面即踩「mp.Queue is closed」（exp-hygiene
2026-09-30 P7 在册组合子集 3 红——序敏感存量缺陷）。

隔离口径（1A7 预裁决 ①测试基建 per-test 隔离优先）：每测试前清 None、
测试后还原先值——jobs 面任何测试不再继承前序测试的队列残留；需要进度
通路的测试经自身 Manager.start()/显式 sink 装配（service_ctx/client
夹具每测试新建 Manager 重写全局——隔离零干扰）。test_worker.py 模块级
残留植入件为本隔离的持续防御锚（隔离移除即复红）。
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator

import pytest

_worker_mod = importlib.import_module("waterprint_server.jobs.worker")


@pytest.fixture(autouse=True)
def _isolated_worker_progress_queue() -> Iterator[None]:
    """per-test 隔离：worker._PROGRESS_QUEUE 前清 None（残留切断）后还原。"""
    prior = _worker_mod._PROGRESS_QUEUE  # noqa: SLF001  # 快照（注入口全局）
    _worker_mod._PROGRESS_QUEUE = None  # noqa: SLF001  # 前清（隔离继承残留）
    try:
        yield
    finally:
        _worker_mod._PROGRESS_QUEUE = prior  # noqa: SLF001  # 还原（基线动态零漂移）
