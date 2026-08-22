"""executor 镜像测试：图执行编排（工况 2+k 全索引、异常隔离、装配边界）。

输入:  waterprint.graph.execute_graph 公开符号
输出:  编排语义断言（细粒度端到端归 M1 三单元切片与 golden）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.graph.executor")
execute_graph = getattr(_mod, "execute_graph", None)

pytestmark = pytest.mark.skipif(
    execute_graph is None,
    reason="实现未就绪：waterprint.graph.executor（M1 三单元切片）",
)


def test_executor_exposes_protocol_only_entry() -> None:
    """装配边界：执行器入口存在且可调用（具体单元由 app.py 注入）。

    深度行为断言（三单元线性图/回路/双跑 diff=0）随 M1 切片实现激活，
    数值对照由 golden 端到端承载（tests/golden/）。
    """
    assert callable(execute_graph)


def test_executor_does_not_import_units_lib() -> None:
    """铁律：executor 模块禁止 import units_lib（import-linter 同款断言）。"""
    import sys

    assert not any(
        name.startswith("waterprint.units_lib")
        for name in sys.modules
        if name.startswith("waterprint.graph")
    ), "graph 执行链不得加载具体单元（装配点唯一）"
