"""calculation 服务镜像测试：幂等提交、快照绑定、方案应用原子性。

输入:  waterprint_server.services.calculation 公开符号
输出:  服务契约断言（§17.1 事件矩阵的服务侧执行）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.calculation")
submit_calculation = getattr(_mod, "submit_calculation", None)
apply_solution = getattr(_mod, "apply_solution", None)

pytestmark = [
    pytest.mark.skipif(
        None in (submit_calculation, apply_solution),
        reason="实现未就绪：waterprint_server.services.calculation（服务层 M2）",
    ),
]


def test_running_task_result_marked_stale_on_edit_wiring() -> None:
    """R2 接线断言：任务运行期间编辑 → 完成结果 stale=True（禁止静默覆盖）。"""
    raise AssertionError(
        "M2 接线断言：提交任务→改 design→等待完成，TaskStatus.stale 为 True"
        "——不得删除（§17.1）"
    )


def test_apply_solution_rolls_back_on_failure_wiring() -> None:
    """R2 接线断言：应用方案中途失败 → design/hash 回滚（无半写）。"""
    raise AssertionError(
        "M2 接线断言：注入触发器使应用第二步失败，断言项目文件哈希未变——不得删除"
    )
