"""edge_parsing 薄壳镜像：导入冒烟+公开面在场+注入语义冒烟（B3-c 批 2c）。

行为主体（双胞胎绑定件恒等/消息形态/消费面）由 tests/graph/
test_executor_assembly.py 与 tests/app/test_app_assembly.py 既有镜像
承担——本件满足镜像规则最小义务并钉 error 注入语义（批 3a not_found
先例同型的内核契约）。
"""

from __future__ import annotations

import pytest

from waterprint.contracts.edge_parsing import edges_from, endpoint_from
from waterprint.contracts.ports import Edge, PortRef


class _CarrierError(Exception):
    """注入载体桩（error 参数语义冒烟用——不消费真实领域异常类）。"""


def test_public_face() -> None:
    """公开面在场：两公开名可寻址且可调用。"""
    assert callable(endpoint_from) and callable(edges_from)


def test_error_injection() -> None:
    """error 注入语义：拒绝载体=注入类本体（消息内核单源构造）。"""
    with pytest.raises(_CarrierError, match="须为对象"):
        endpoint_from(None, "src", 0, error=_CarrierError)
    with pytest.raises(_CarrierError, match="须为布尔"):
        edges_from([{"recycle": 1}], error=_CarrierError)


def test_happy_path() -> None:
    """正常路径冒烟：raw 映射 → PortRef/Edge（recycle 缺省 False）。"""
    ref = endpoint_from({"unit_id": "a", "port_id": "p"}, "src", 0, error=_CarrierError)
    assert isinstance(ref, PortRef) and (ref.unit_id, ref.port_id) == ("a", "p")
    (edge,) = edges_from(
        [{"src": {"unit_id": "a", "port_id": "p"},
          "dst": {"unit_id": "b", "port_id": "q"}}],
        error=_CarrierError,
    )
    assert isinstance(edge, Edge) and edge.recycle is False
