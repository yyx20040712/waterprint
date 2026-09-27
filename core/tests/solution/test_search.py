"""search 镜像测试（批6g 新增件——beam 拆件主题段；[HUMAN-LOCK] 随批预授权①）。

覆盖：行估计公式（k=1 边界+几何级数）+拓扑序重排/环拒/重复拒（Kahn 私面
直证）+产出 schema 形状+beam 再导出恒等（拆件公开面不变性）。
落位目标：core/tests/solution/test_search.py（镜像规则闭合）。
"""
from __future__ import annotations

import pytest

_search = pytest.importorskip(
    "waterprint.solution.joint_enumeration.search",
    reason="实现未就绪：批6g search 件（beam 拆件）",
)
estimate_rows = _search.estimate_rows
_ordered_targets = _search._ordered_targets  # noqa: SLF001  # 私面直证（镜像件义务）


def test_estimate_rows_k1_boundary_is_linear() -> None:
    """k=1 边界：g·N·W（N1 边界式——几何级数退化为线性；g=最大档）。"""
    assert estimate_rows([4, 6, 8], 1.0, 3) == 72.0


def test_estimate_rows_geometric_series() -> None:
    """k>1：g·(k^N−1)/(k−1)·W_s（首例 g=4/k=3/N=3/W=2）。"""
    assert estimate_rows([4, 4, 4], 3.0, 2) == 4.0 * (27 - 1) / 2 * 2


class _Edge:
    """assembled.edges 最小形状（src/dst.unit_id 消费面）。"""

    def __init__(self, src: str, dst: str) -> None:
        from types import SimpleNamespace

        self.src = SimpleNamespace(unit_id=src)
        self.dst = SimpleNamespace(unit_id=dst)


class _Assembled:
    """AssembledView 最小形状（units 键集+edges 拓扑）。"""

    def __init__(self, units: tuple[str, ...], edges: tuple[_Edge, ...]) -> None:
        from types import SimpleNamespace

        self.units = {unit: SimpleNamespace() for unit in units}
        self.edges = edges


class _Design:
    """DesignState 最小形状（nodes 键集）。"""

    def __init__(self, nodes: tuple[str, ...]) -> None:
        self.nodes: dict[str, dict[str, float]] = {node: {} for node in nodes}


_A, _B, _C = "unit_a", "unit_b", "unit_c"


def test_ordered_targets_reorders_by_topology() -> None:
    """乱序输入→Kahn 拓扑序（A→B→C 链上 C,B,A 输入重排为 A,B,C）。"""
    assembled = _Assembled(
        (_A, _B, _C), (_Edge(_A, _B), _Edge(_B, _C)))
    assert _ordered_targets([_C, _B, _A], assembled, _Design((_A, _B, _C))) == (_A, _B, _C)


def test_ordered_targets_rejects_cycle() -> None:
    """子图有环=拓扑序前提失败（InvalidJointEnumerationError）。"""
    from waterprint.solution.joint_enumeration import InvalidJointEnumerationError

    assembled = _Assembled(
        (_A, _B), (_Edge(_A, _B), _Edge(_B, _A)))
    with pytest.raises(InvalidJointEnumerationError, match="有环"):
        _ordered_targets([_A, _B], assembled, _Design((_A, _B)))


def test_ordered_targets_rejects_duplicates_and_unknown() -> None:
    """重复 unit_id（GR-14）/不在装配图=启动期拒。"""
    from waterprint.solution.joint_enumeration import InvalidJointEnumerationError

    assembled = _Assembled((_A,), ())
    with pytest.raises(InvalidJointEnumerationError, match="重复"):
        _ordered_targets([_A, _A], assembled, _Design((_A,)))
    with pytest.raises(InvalidJointEnumerationError, match="不在装配图"):
        _ordered_targets([_A, _B], assembled, _Design((_A, _B)))


def test_joint_outcome_schema_and_too_large_semantics() -> None:
    """产出四字段不可变+超限异常承载 422 语义（GridTooLarge 先例名）。"""
    from waterprint.solution.joint_enumeration.search import (
        JointEnumerationTooLarge,
        JointOutcome,
    )

    assert issubclass(JointEnumerationTooLarge, Exception)
    outcome = JointOutcome(
        search_semantics={}, combos=(), diagnosis=None, budget_usage={})
    assert (outcome.search_semantics, outcome.combos,
            outcome.diagnosis, outcome.budget_usage) == ({}, (), None, {})


def test_beam_reexport_identity() -> None:
    """批6g 拆件公开面不变性：beam 再导出=定义面恒等（同对象）。"""
    from waterprint.solution.joint_enumeration import beam

    assert beam.JointOutcome is _search.JointOutcome
    assert beam.JointEnumerationTooLarge is _search.JointEnumerationTooLarge
    assert beam.estimate_rows is _search.estimate_rows
    # _JointSearch 私名再导出经 getattr 取（mypy attr-defined 面零特赦）
    assert getattr(beam, "_JointSearch") is getattr(_search, "_JointSearch")
