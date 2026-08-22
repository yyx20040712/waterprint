"""性能基准：万级方案枚举 <5s（§18.1；M1 起接线，CI 手动触发）。

输入:  示范单元万级网格
输出:  pytest-benchmark 计时
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.solution.enumerate")
enumerate_solutions = getattr(_mod, "enumerate_solutions", None)

pytestmark = [
    pytest.mark.skipif(
        enumerate_solutions is None,
        reason="实现未就绪：waterprint.solution.enumerate（M1）",
    ),
]

BUDGET_SECONDS = 5.0  # §18.1：万级枚举（单单元，向量化唯一实现前提）


def test_enumerate_10k_benchmark(benchmark) -> None:
    """万级枚举在预算内（逐方案标量循环的退化实现必然超时——防双轨守卫）。"""
    raise AssertionError(
        "M1 接线：万级网格 benchmark——不得删除（向量化守卫）"
    )
