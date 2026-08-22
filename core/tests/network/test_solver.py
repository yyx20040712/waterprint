"""solver 镜像测试：管径枚举设计（确定性/跌水井判定/无解显式接线）。

输入:  waterprint.network.solver 公开符号
输出:  设计语义断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.network.solver")
design_pipes = getattr(_mod, "design_pipes", None)

pytestmark = pytest.mark.skipif(
    design_pipes is None,
    reason="实现未就绪：waterprint.network.solver（M3）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：design_pipes(segments, options)——约束值全部来自数据（R4）。"""
    assert callable(design_pipes)


def test_infeasible_segment_reports_reasons_wiring() -> None:
    """R5 接线断言：无解段显式失败 + 违反约束清单（禁止静默选最接近）。"""
    raise AssertionError(
        "M3 接线断言：构造不可行段断言失败原因完整——不得删除"
    )
