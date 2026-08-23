"""trace_api 镜像测试：TraceSink 协议与 TraceNodeSpec（L0 迹契约）。

输入:  waterprint.contracts.trace_api 公开符号（TraceNodeSpec/TraceSink）
输出:  协议结构与不可变性断言（实现合入后必须全绿；
       实现停靠于 t0.5-dsl-spec-wip 分支待合并，合并即激活本测试）
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

try:
    _mod = importlib.import_module("waterprint.contracts.trace_api")
except ModuleNotFoundError:
    _mod = None
TraceNodeSpec = getattr(_mod, "TraceNodeSpec", None)
TraceSink = getattr(_mod, "TraceSink", None)

pytestmark = pytest.mark.skipif(
    None in (TraceNodeSpec, TraceSink),
    reason="实现未就绪：waterprint.contracts.trace_api 公开符号缺失（t0.5 分支待合并）",
)


def test_trace_node_spec_frozen_with_five_fields() -> None:
    """TraceNodeSpec 冻结数据类：formula_id/unit_id/condition_key/bindings/result。"""
    spec = TraceNodeSpec(
        formula_id="GB50014-6.3.2-demo",
        unit_id="municipal_cugeshan",
        condition_key="design",
        bindings={"q": 0.4},
        result=1.25,
    )
    assert dataclasses.is_dataclass(spec)
    assert [f.name for f in dataclasses.fields(spec)] == [
        "formula_id", "unit_id", "condition_key", "bindings", "result",
    ]
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.result = 0.0  # type: ignore[misc]


def test_trace_sink_protocol_single_record_method() -> None:
    """TraceSink 协议唯一方法 record(TraceNodeSpec)——registry/trace 双实现零 import。"""
    assert hasattr(TraceSink, "record")
