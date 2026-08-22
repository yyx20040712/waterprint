"""constraints 镜像测试：布尔约束过滤（pass_matrix 完整性/UI 覆盖/DSL 拒绝）。

输入:  waterprint.solution.constraints 公开符号 + 内存 DataFrame
输出:  过滤语义断言（无解诊断的输入保证）
"""

from __future__ import annotations

import importlib

import pytest

pd = pytest.importorskip("pandas")

_mod = importlib.import_module("waterprint.solution.constraints")
apply_constraints = getattr(_mod, "apply_constraints", None)
Constraint = getattr(_mod, "Constraint", None)

pytestmark = [
    pytest.mark.skipif(
        None in (apply_constraints, Constraint),
        reason="实现未就绪：waterprint.solution.constraints（M1）",
    ),
]


def _df() -> "pd.DataFrame":
    return pd.DataFrame({"pool_length": [8.0, 12.0, 20.0], "id": [0, 1, 2]})


def test_feasible_subset_and_pass_matrix() -> None:
    """R2：可行子集与逐约束通过矩阵同时产出（全 False 也要有矩阵）。"""
    constraint = Constraint(
        key="kb.demo.len_max", expression="pool_length <= 15", source="kb.demo"
    )
    result = apply_constraints(_df(), [constraint])
    assert list(result.feasible) == [0, 1]
    assert len(result.pass_matrix) == 3


def test_all_false_matrix_survives_for_diagnosis() -> None:
    """R2：无解时矩阵完整（诊断依赖——禁止只返回空集丢信息）。"""
    impossible = Constraint(
        key="kb.demo.impossible", expression="pool_length > 999", source="kb.demo"
    )
    result = apply_constraints(_df(), [impossible])
    assert list(result.feasible) == []
    assert result.pass_matrix["pool_length > 999"].tolist() == [False, False, False]


def test_unknown_field_in_expression_rejected() -> None:
    """R1：DSL 白名单——未知字段表达式拒绝（安全与可序列化）。"""
    bad = Constraint(
        key="kb.demo.bad", expression="no_such_field <= 1", source="kb.demo"
    )
    with pytest.raises(Exception, match=".+"):
        apply_constraints(_df(), [bad])
