"""losses 镜像测试：水头损失公式（非负/单调性质 + 注册表求值通道）。

输入:  waterprint.elevation.losses 公开符号
输出:  损失语义断言（数值 golden 归 docs/norms 手算对照）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.elevation.losses")
friction_loss = getattr(_mod, "friction_loss", None)

pytestmark = pytest.mark.skipif(
    friction_loss is None,
    reason="实现未就绪：waterprint.elevation.losses（M2）",
)


def _geom(diameter: float = 0.5, length: float = 100.0):
    return {"diameter": diameter, "length": length}


def test_loss_is_nonnegative() -> None:
    """R3：损失恒非负。"""
    assert friction_loss(_geom(), 0.2) >= 0.0


def test_loss_monotone_in_flow() -> None:
    """R4：沿程损失随流量单调不减。"""
    low = friction_loss(_geom(), 0.1)
    high = friction_loss(_geom(), 0.5)
    assert high >= low


def test_loss_monotone_against_diameter() -> None:
    """R4：同流量下管径增大损失不增。"""
    small = friction_loss(_geom(diameter=0.3), 0.2)
    large = friction_loss(_geom(diameter=0.8), 0.2)
    assert large <= small
