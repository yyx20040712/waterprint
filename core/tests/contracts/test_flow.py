"""flow 镜像测试：水量契约（q_design 派生消双轨、构造校验）。

输入:  waterprint.contracts.flow 公开符号
输出:  双轨消除/校验拒绝/换算断言
"""

from __future__ import annotations

import importlib

import pytest

_qty = importlib.import_module("waterprint.contracts.quantity")
Quantity = getattr(_qty, "Quantity", None)
_mod = importlib.import_module("waterprint.contracts.flow")
make_flow = getattr(_mod, "make_flow", None)
InvalidFlowError = getattr(_mod, "InvalidFlowError", None)

pytestmark = pytest.mark.skipif(
    None in (Quantity, make_flow, InvalidFlowError),
    reason="实现未就绪：waterprint.contracts.flow 公开符号缺失（M1）",
)


def _flow_m3s(q_avg: float, kz: float):
    return make_flow(Quantity(q_avg, "m3/s"), kz)


def test_q_design_is_derived_not_input() -> None:
    """R1：q_design 是派生属性 = q_avg_daily × kz（双轨架构级根除）。"""
    flow = _flow_m3s(0.5, 1.3)
    assert flow.q_design == pytest.approx(flow.q_avg_daily * 1.3)


def test_daily_unit_conversion_at_boundary() -> None:
    """R4：边界换算——34760 m3/d 构造后内部为 m3/s 规范单位。"""
    flow = make_flow(Quantity(34760.0, "m3/d"), 1.0)
    assert flow.q_avg_daily == pytest.approx(34760.0 / 86400.0)


def test_nonpositive_flow_rejected() -> None:
    """R2：q_avg_daily <= 0 拒绝。"""
    with pytest.raises(InvalidFlowError):
        _flow_m3s(0.0, 1.2)


def test_kz_below_one_rejected() -> None:
    """R2：kz < 1 拒绝（总变化系数数学下界）。"""
    with pytest.raises(InvalidFlowError):
        _flow_m3s(0.5, 0.9)


def test_flow_immutable() -> None:
    """不可变值对象：q_design/字段不可赋值。"""
    flow = _flow_m3s(0.5, 1.3)
    with pytest.raises((AttributeError, TypeError)):
        flow.q_avg_daily = 0.9  # type: ignore[misc]
