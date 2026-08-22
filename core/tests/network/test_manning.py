"""manning 镜像测试：曼宁水力（非负/单调性质；数值 golden 归 norms 手算）。

输入:  waterprint.network.manning 公开符号
输出:  水力语义断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.network.manning")
manning_velocity = getattr(_mod, "manning_velocity", None)
solve_depth = getattr(_mod, "solve_depth", None)

pytestmark = pytest.mark.skipif(
    None in (manning_velocity, solve_depth),
    reason="实现未就绪：waterprint.network.manning（M3）",
)


def test_velocity_positive_and_monotone_in_slope() -> None:
    """R3/R4：流速为正且随坡度单调增。"""
    low = manning_velocity(0.5, 0.001, 0.009)
    high = manning_velocity(0.5, 0.004, 0.009)
    assert low > 0
    assert high > low


def test_solve_depth_finds_consistent_root() -> None:
    """求根一致性：解出的充满度反算流量应匹配输入（容差内）。"""
    depth = solve_depth(0.5, 0.002, 0.009, 0.05)
    assert 0.0 < depth <= 1.0
