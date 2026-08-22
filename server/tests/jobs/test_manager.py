"""jobs manager 镜像测试：任务状态机、优先级队列、取消语义。

输入:  waterprint_server.jobs.manager 公开符号
输出:  调度契约断言（§12.2/§17.1）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.jobs.manager")
Manager = getattr(_mod, "Manager", None)

pytestmark = [
    pytest.mark.skipif(
        Manager is None,
        reason="实现未就绪：waterprint_server.jobs.manager（服务层 M2）",
    ),
]


def test_priority_interactive_beats_batch_wiring() -> None:
    """R2 接线断言：交互计算优先于批量导出出队（防饿死 §17.1）。"""
    raise AssertionError(
        "M2 接线断言：入队 [导出, 计算] 后计算先执行——不得删除"
    )


def test_cancel_running_task_discards_partial_wiring() -> None:
    """R5 接线断言：取消后无半途结果落地。"""
    raise AssertionError(
        "M2 接线断言：运行中取消 → cancelled 且产物目录无新文件——不得删除"
    )
