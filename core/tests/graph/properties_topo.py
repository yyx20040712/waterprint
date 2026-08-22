"""topo 性质测试：随机 DAG 分层的拓扑不变性。

输入:  hypothesis 随机前向边 DAG（保证无环）
输出:  每条边低层→高层、SCC 全为单点、确定性三条性质
"""

from __future__ import annotations

import importlib

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

_ports = importlib.import_module("waterprint.contracts.ports")
Edge = getattr(_ports, "Edge", None)
PortRef = getattr(_ports, "PortRef", None)

_mod = importlib.import_module("waterprint.graph.topo")
topological_layers = getattr(_mod, "topological_layers", None)
strongly_connected_components = getattr(_mod, "strongly_connected_components", None)

pytestmark = [
    pytest.mark.skipif(
        None in (Edge, PortRef, topological_layers, strongly_connected_components),
        reason="实现未就绪：waterprint.graph.topo（M1）",
    ),
]

node_ids = st.sampled_from([f"n{i}" for i in range(8)])
forward_dags = st.lists(
    st.tuples(st.integers(0, 6), st.integers(1, 7)),
    unique=True,
).filter(lambda pairs: all(i < j for (i, j) in pairs))


def _edge(i: int, j: int):
    return Edge(src=PortRef(f"n{i}", "out"), dst=PortRef(f"n{j}", "in"))


@given(pairs=forward_dags)
def test_every_edge_points_to_higher_layer(pairs: list[tuple[int, int]]) -> None:
    """性质：分层后每条边都从低层指向高层（拓扑序定义）。"""
    nodes = sorted({f"n{i}" for pair in pairs for i in pair} or ["n0"])
    edges = [_edge(i, j) for (i, j) in pairs]
    layers = topological_layers(nodes, edges)
    level = {node: idx for idx, layer in enumerate(layers) for node in layer}
    for edge in edges:
        assert level[edge.src.unit_id] < level[edge.dst.unit_id]


@given(pairs=forward_dags)
def test_forward_dag_has_no_multi_node_scc(pairs: list[tuple[int, int]]) -> None:
    """性质：纯前向边（无 recycle 环）的 SCC 全为单点。"""
    nodes = sorted({f"n{i}" for pair in pairs for i in pair} or ["n0"])
    edges = [_edge(i, j) for (i, j) in pairs]
    sccs = strongly_connected_components(nodes, edges)
    assert all(len(group) == 1 for group in sccs)
