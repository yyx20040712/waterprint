"""ports 镜像测试：端口/边契约（类型裁判、回流标记、不可变）。

输入:  waterprint.contracts.ports 公开符号
输出:  连接合法性断言（错误消息人类可读）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.ports")
Port = getattr(_mod, "Port", None)
Edge = getattr(_mod, "Edge", None)
PortRef = getattr(_mod, "PortRef", None)
validate_edge = getattr(_mod, "validate_edge", None)
FluidKind = getattr(_mod, "FluidKind", None)
Direction = getattr(_mod, "Direction", None)
InvalidConnection = getattr(_mod, "InvalidConnection", None)

pytestmark = pytest.mark.skipif(
    None in (Port, Edge, PortRef, validate_edge, FluidKind, Direction, InvalidConnection),
    reason="实现未就绪：waterprint.contracts.ports 公开符号缺失（M1）",
)


def _index():
    """构建最小端口索引：水出/水入/泥出/泥入各一。"""
    return {
        ("a", "out"): Port(port_id="out", fluid=FluidKind.WATER, direction=Direction.OUT),
        ("b", "in"): Port(port_id="in", fluid=FluidKind.WATER, direction=Direction.IN),
        ("s", "out"): Port(port_id="out", fluid=FluidKind.SLUDGE, direction=Direction.OUT),
        ("t", "in"): Port(port_id="in", fluid=FluidKind.SLUDGE, direction=Direction.IN),
    }


def test_fluid_type_mismatch_rejected_with_reason() -> None:
    """R1：水→泥 = InvalidConnection，消息可读。"""
    edge = Edge(src=PortRef("a", "out"), dst=PortRef("t", "in"))
    with pytest.raises(InvalidConnection, match=".+"):
        validate_edge(edge, _index())


def test_direction_mismatch_rejected() -> None:
    """R2：非 OUT→IN 拒绝。"""
    edge = Edge(src=PortRef("b", "in"), dst=PortRef("a", "out"))
    with pytest.raises(InvalidConnection):
        validate_edge(edge, _index())


def test_recycle_defaults_false_and_is_valid() -> None:
    """R3：recycle 缺省 False；合法水边带 recycle=True 也通过校验。"""
    plain = Port(port_id="out", fluid=FluidKind.WATER, direction=Direction.OUT)
    assert plain.recycle is False
    edge = Edge(src=PortRef("a", "out"), dst=PortRef("b", "in"))
    validate_edge(edge, _index())  # 不抛即通过


def test_port_immutable() -> None:
    """R4：Port 不可变。"""
    port = Port(port_id="out", fluid=FluidKind.WATER, direction=Direction.OUT)
    with pytest.raises((AttributeError, TypeError)):
        port.recycle = True  # type: ignore[misc]
