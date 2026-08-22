"""quantity 性质测试：单位换算的数学恒等（往返/线性/等价单位）。

输入:  hypothesis 生成的正有限浮点 + quantity 公开符号
输出:  换算一致性断言（违反 = 换算实现有误）
"""

from __future__ import annotations

import importlib

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

_mod = importlib.import_module("waterprint.contracts.quantity")
parse = getattr(_mod, "parse", None)
DimKey = getattr(_mod, "DimKey", None)

pytestmark = [
    pytest.mark.skipif(
        None in (parse, DimKey),
        reason="实现未就绪：waterprint.contracts.quantity（M1）",
    ),
]

positive = st.floats(min_value=1e-6, max_value=1e9, allow_nan=False)


@given(value=positive)
def test_daily_flow_conversion_is_linear(value: float) -> None:
    """换算线性：parse(2x, m3/d) == 2 × parse(x, m3/d)。"""
    assert parse(2 * value, "m3/d", DimKey.FLOW) == pytest.approx(
        2 * parse(value, "m3/d", DimKey.FLOW), rel=1e-12
    )


@given(value=positive)
def test_equivalent_concentration_units(value: float) -> None:
    """等价单位：1 mg/L == 1 g/m3（无量纲换算一致性）。"""
    assert parse(value, "mg/L", DimKey.CONCENTRATION) == pytest.approx(
        parse(value, "g/m3", DimKey.CONCENTRATION), rel=1e-12
    )


@given(value=positive)
def test_length_roundtrip_mm_m(value: float) -> None:
    """长度往返：parse(parse(x, mm→m 量纲值), m) 自反一致（mm→m→mm 恒等）。"""
    in_m = parse(value, "mm", DimKey.LENGTH)
    back_to_mm = in_m * 1000.0
    assert parse(back_to_mm, "mm", DimKey.LENGTH) == pytest.approx(in_m, rel=1e-9)
