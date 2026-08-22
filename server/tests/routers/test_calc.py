"""calc 路由镜像测试：任务端点（幂等、stale 标志、取消、分页）。

输入:  waterprint_server.routers.calc 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.routers.calc")
router = getattr(_mod, "router", None)

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.calc（服务层 M2）",
    ),
]


def test_router_exposes_six_endpoints_wiring() -> None:
    """端点集 == 规格六件（run/enumerate/tasks/cancel/solutions/apply）。"""
    raise AssertionError(
        "M2 接线断言：端点路径与规格一致；solutions 分页默认 200——不得删除"
    )


def test_duplicate_submit_is_idempotent_wiring() -> None:
    """R1 接线断言：同 (design_hash, condition) 重复提交返回同一 task_id。"""
    raise AssertionError(
        "M2 接线断言：两次相同 run 提交，task_id 相同且进程池只占一次——不得删除"
    )
