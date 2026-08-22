"""quantity 镜像测试：量纲/规范单位/边界换算（ADR-002 三层策略的边界层）。

输入:  waterprint.contracts.quantity 公开符号
输出:  规范单位表/换算/拒绝路径断言（实现合入后必须全绿）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.quantity")
Quantity = getattr(_mod, "Quantity", None)
CANONICAL_UNITS = getattr(_mod, "CANONICAL_UNITS", None)
DimKey = getattr(_mod, "DimKey", None)
InvalidUnitError = getattr(_mod, "InvalidUnitError", None)
parse = getattr(_mod, "parse", None)
attach = getattr(_mod, "attach", None)

pytestmark = pytest.mark.skipif(
    None in (Quantity, CANONICAL_UNITS, DimKey, InvalidUnitError, parse, attach),
    reason="实现未就绪：waterprint.contracts.quantity 公开符号缺失（M1）",
)


def test_canonical_units_core_three() -> None:
    """规范单位表必含计划明示三项：流量 m3/s、浓度 mg/L、长度 m（§12.1）。"""
    assert CANONICAL_UNITS[DimKey.FLOW] == "m3/s"
    assert CANONICAL_UNITS[DimKey.CONCENTRATION] == "mg/L"
    assert CANONICAL_UNITS[DimKey.LENGTH] == "m"


def test_parse_converts_daily_flow_to_canonical() -> None:
    """golden 口径：34760 m3/d（市政案例规模）换算为 m3/s。"""
    assert parse(34760.0, "m3/d", DimKey.FLOW) == pytest.approx(34760.0 / 86400.0)


def test_parse_rejects_dimension_mismatch() -> None:
    """量纲不匹配直接拒绝（期望流量却给浓度单位）。"""
    with pytest.raises(InvalidUnitError):
        parse(1.0, "mg/L", DimKey.FLOW)


def test_parse_rejects_unknown_unit() -> None:
    """未知单位字符串拒绝，无默认单位回退。"""
    with pytest.raises(InvalidUnitError):
        parse(1.0, "立方千米每纳秒", DimKey.FLOW)


def test_attach_yields_canonical_quantity() -> None:
    """出口包装：规范单位裸值 → Quantity（数值不变，单位=规范单位）。"""
    value = parse(5.0, "m3/d", DimKey.FLOW)
    quantity = attach(value, DimKey.FLOW)
    assert quantity.magnitude == pytest.approx(value)
    assert quantity.unit == CANONICAL_UNITS[DimKey.FLOW]
