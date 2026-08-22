"""topo 镜像测试：拓扑分层 + SCC 划分（回路一等公民第一步）。

输入:  waterprint.graph.topo 公开符号（+ contracts.ports 边类型）
输出:  分层/回路组/误连环异常/确定性断言
"""

from __future__ import annotations

import importlib

import pytest

_ports = importlib.import_module("waterprint.contracts.ports")
Edge = getattr(_ports, "Edge", None)
PortRef = getattr(_ports, "PortRef", None)
InvalidConnection = getattr(_ports, "InvalidConnection", None)

_mod = importlib.import_module("waterprint.graph.topo")
topological_layers = getattr(_mod, "topological_layers", None)
strongly_connected_components = getattr(_mod, "strongly_connected_components", None)
split_graph = getattr(_mod, "split_graph", None)

pytestmark = pytest.mark.skipif(
    None in (Edge, PortRef, InvalidConnection, topological_layers,
             strongly_connected_components, split_graph),
    reason="实现未就绪：waterprint.graph.topo 公开符号缺失（M1）",
)


def _edge(src: str, dst: str, recycle: bool = False):
    return Edge(src=PortRef(src, "out"), dst=PortRef(dst, "in"), recycle=recycle)


def test_linear_dag_layers() -> None:
    """线性链 a→b→c 分三层且序确定。"""
    layers = topological_layers(["a", "b", "c"], [_edge("a", "b"), _edge("b", "c")])
    assert [list(layer) for layer in layers] == [["a"], ["b"], ["c"]]


def test_recycle_cycle_becomes_scc_not_exception() -> None:
    """R1：recycle 环 → SCC 组（不抛异常——旧病灶根除）。"""
    sccs = strongly_connected_components(
        ["a", "b", "c"],
        [_edge("a", "b"), _edge("b", "c"), _edge("c", "a", recycle=True)],
    )
    merged = sorted(sum((list(g) for g in sccs), []))
    assert merged == ["a", "b", "c"]
    assert any(set(g) == {"a", "b", "c"} for g in sccs)


def test_plain_cycle_raises_with_path() -> None:
    """R1：非 recycle 误连环 → InvalidConnection（消息含节点路径）。"""
    with pytest.raises(InvalidConnection, match="a.*b.*a|b.*a.*b"):
        topological_layers(
            ["a", "b"], [_edge("a", "b"), _edge("b", "a", recycle=False)]
        )


def test_layering_is_deterministic_under_input_shuffle() -> None:
    """R3：同层按 unit_id 字典序——节点输入乱序不影响分层。"""
    edges = [_edge("a", "c"), _edge("b", "c")]
    first = topological_layers(["c", "b", "a"], edges)
    second = topological_layers(["a", "b", "c"], edges)
    assert [list(x) for x in first] == [list(x) for x in second] == [["a", "b"], ["c"]]


def test_split_graph_returns_both_parts() -> None:
    """总入口：一次调用同时得到分层与回路组。"""
    layers, loop_groups = split_graph(
        ["in", "a", "b"],
        [_edge("in", "a"), _edge("a", "b"), _edge("b", "a", recycle=True)],
    )
    assert loop_groups, "recycle 环必须被识别为回路组"
    assert all(node in ("a", "b") for g in loop_groups for node in g)
