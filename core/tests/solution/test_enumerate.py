"""enumerate 镜像测试：向量化批量计算（N=1 防双轨、非负性、工况标注）。

输入:  waterprint.solution.enumerate 公开符号 + 示范单元（M1 三单元实现后激活）
输出:  单实现双用断言（§3 保证 1 的测试母版）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.solution.enumerate")
enumerate_solutions = getattr(_mod, "enumerate_solutions", None)

pytestmark = pytest.mark.skipif(
    enumerate_solutions is None,
    reason="实现未就绪：waterprint.solution.enumerate（M1 三单元切片）",
)


def test_entrypoint_is_callable() -> None:
    """入口冻结：enumerate_solutions(grid, upstream, unit, env)（签名见规格头）。"""
    assert callable(enumerate_solutions)


def test_n1_grid_matches_single_point_compute() -> None:
    """R1 防双轨铁律：N=1 网格行结果 == 单点 compute 结果。

    需要示范单元（M1 粗格栅/细格栅/旋流沉砂池之一）；实现后必须
    在此接线并保持断言（放宽/删除 = 评审拒绝）。数值期望来自
    docs/norms 手算对照表。
    """
    raise AssertionError(
        "M1 接线断言：用示范单元连接 enumerate(N=1) 与 compute 单点，"
        "断言两者维度字段逐项相等——不得删除"
    )
