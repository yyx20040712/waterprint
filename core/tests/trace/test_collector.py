"""collector 镜像测试：计算迹收集（零遗漏/确定性/失败传播）。

输入:  waterprint.trace.collector 公开符号
输出:  采集契约断言（审计链路的数据半）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.trace.collector")
TraceCollector = getattr(_mod, "TraceCollector", None)
collect = getattr(_mod, "collect", None)

pytestmark = pytest.mark.skipif(
    None in (TraceCollector, collect),
    reason="实现未就绪：waterprint.trace.collector（M1）",
)


def test_collector_records_every_application_wiring() -> None:
    """R1 接线断言：迹节点数 == apply 调用数（零遗漏）。"""
    raise AssertionError(
        "M1 接线断言：N 次 apply 断言迹树恰有 N 节点——不得删除"
    )


def test_trace_deterministic_wiring() -> None:
    """R2 接线断言：同执行同迹序（序列化字节相同）。"""
    raise AssertionError(
        "M1 接线断言：同一执行序列双采迹比较序列化字节——不得删除"
    )
