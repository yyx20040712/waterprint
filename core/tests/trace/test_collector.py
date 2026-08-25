"""collector 镜像测试：计算迹收集（零遗漏/确定性/失败传播）。

输入:  waterprint.trace.collector 公开符号
输出:  采集契约断言（审计链路的数据半）
"""

from __future__ import annotations

import importlib
import json

import pytest

from waterprint.contracts.trace_api import TraceNodeSpec

_mod = importlib.import_module("waterprint.trace.collector")
TraceCollector = getattr(_mod, "TraceCollector", None)
collect = getattr(_mod, "collect", None)

pytestmark = pytest.mark.skipif(
    None in (TraceCollector, collect),
    reason="实现未就绪：waterprint.trace.collector（M1）",
)


def _register_probe_formula(formula_id: str) -> None:
    """登记测试专用公式 a+b（DimKey 全 DIMENSIONLESS；幂等容忍重复登记）。"""
    from waterprint.contracts.quantity import DimKey
    from waterprint.registry.formulas import (
        FormulaSpec,
        InvalidFormulaError,
        by_id,
        register,
    )

    try:
        by_id(formula_id)
        return  # 已登记（同进程多测试共享注册表）
    except InvalidFormulaError:
        pass
    register(
        FormulaSpec(
            formula_id=formula_id,
            expression="a + b",
            symbols={
                "a": (DimKey.DIMENSIONLESS, "测试符号 a"),
                "b": (DimKey.DIMENSIONLESS, "测试符号 b"),
            },
            output_dim=DimKey.DIMENSIONLESS,
            norm_ref="测试条文 M1b-collector",
        )
    )


def _node(formula_id: str, a: float, b: float) -> TraceNodeSpec:
    """TraceNodeSpec 构造探针（spec 五字段全量）。"""
    return TraceNodeSpec(
        formula_id=formula_id,
        unit_id="m1b_probe_unit",
        condition_key="design",
        bindings={"a": a, "b": b},
        result=a + b,
    )


def _serialized(collector: TraceCollector) -> bytes:
    """迹树序列化（result_schema TraceNode 六字段口径，键排序确定性）。"""
    return json.dumps(
        [
            {
                "formula_id": node.formula_id,
                "inputs": dict(node.inputs),
                "output": node.output,
                "norm_ref": node.norm_ref,
                "unit_id": node.unit_id,
                "condition_key": node.condition_key,
            }
            for node in collector.tree()
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def test_collector_records_every_application_wiring() -> None:
    """R1 接线断言：迹节点数 == apply 调用数（零遗漏）。"""
    _register_probe_formula("M1B-PROBE-SUM")
    collector: TraceCollector = TraceCollector()
    for index in range(10):
        collector.record(_node("M1B-PROBE-SUM", float(index), 1.0))
    tree = collector.tree()
    assert len(tree) == 10  # N 次 apply 断言迹树恰有 N 节点——不得遗漏
    assert [node.inputs["a"] for node in tree] == [float(i) for i in range(10)]
    assert all(node.norm_ref == "测试条文 M1b-collector" for node in tree)
    assert all(node.unit_id == "m1b_probe_unit" for node in tree)


def test_trace_deterministic_wiring() -> None:
    """R2 接线断言：同执行同迹序（序列化字节相同）。"""
    _register_probe_formula("M1B-PROBE-SUM")

    def _sample() -> bytes:
        collector: TraceCollector = TraceCollector()
        collector.record(_node("M1B-PROBE-SUM", 1.0, 2.0))
        collector.record(_node("M1B-PROBE-SUM", 3.0, 4.0))
        return _serialized(collector)

    assert _sample() == _sample()  # 同一执行序列双采迹比较序列化字节
    assert b"M1B-PROBE-SUM" in _sample()
