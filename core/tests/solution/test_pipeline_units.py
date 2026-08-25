"""solution 管线新增测试：护栏/声明面两向/DSL 白名单/排序全序稳定（M2-SOL D4）。

输入:  waterprint.solution 各模块公开符号（grid/constraints/ranking）
输出:  镜像测试之外的新增契约断言（新文件不入锁——M2 收口批统一处理）
"""

from __future__ import annotations

import importlib

import pytest

pd = pytest.importorskip("pandas")

_grid = importlib.import_module("waterprint.solution.grid")
build_grid = getattr(_grid, "build_grid", None)
GridTooLarge = getattr(_grid, "GridTooLarge", None)
InvalidGridError = getattr(_grid, "InvalidGridError", None)
_constraints = importlib.import_module("waterprint.solution.constraints")
apply_constraints = getattr(_constraints, "apply_constraints", None)
Constraint = getattr(_constraints, "Constraint", None)
InvalidConstraintError = getattr(_constraints, "InvalidConstraintError", None)
_ranking = importlib.import_module("waterprint.solution.ranking")
rank = getattr(_ranking, "rank", None)
RankingKey = getattr(_ranking, "RankingKey", None)
InvalidRankingError = getattr(_ranking, "InvalidRankingError", None)

pytestmark = pytest.mark.skipif(
    None in (build_grid, InvalidGridError, apply_constraints, Constraint,
             InvalidConstraintError, rank, RankingKey, InvalidRankingError),
    reason="实现未就绪：waterprint.solution（M2-SOL）",
)


def test_paramspec_grid_enumerated() -> None:
    """R3：ParamSpec 声明面——grid 档即值域（default 不注入）。"""
    from waterprint.contracts.manifest import ParamSpec

    spec = ParamSpec(
        field_id="pool_length", dim="DIMENSIONLESS", default=99.0, grid=(1.0, 2.0)
    )
    grid = build_grid([spec])  # type: ignore[misc]
    assert grid.total == 2
    assert grid.array["pool_length"].tolist() == [1.0, 2.0]  # default 99 不入网格


def test_paramspec_without_grid_rejected() -> None:
    """R3 负向：无 grid 的 ParamSpec（range 归约束层）→ 声明非法拒。"""
    from waterprint.contracts.manifest import ParamSpec

    spec = ParamSpec(field_id="pool_length", dim="DIMENSIONLESS", default=1.0)
    with pytest.raises(InvalidGridError, match="grid"):  # type: ignore[misc]
        build_grid([spec])  # type: ignore[misc]


def test_range_step_generation_inclusive() -> None:
    """R3：range+step 起止步长生成（闭区间含端点，GR-06；1 维 ≤4 档合护栏）。

    I-1 负向（R1 轮补）：非整除 step（余数过半）不得越上界——
    min=0/max=1.0/step=0.6 → [0.0, 0.6]，不得出现 1.2。
    """
    grid = build_grid(  # type: ignore[misc]
        [{"field_id": "b", "range": {"min": 0.5, "max": 2.0}, "step": 0.5}]
    )
    assert grid.total == 4
    assert grid.array["b"].tolist() == [0.5, 1.0, 1.5, 2.0]
    uneven = build_grid(  # type: ignore[misc]
        [{"field_id": "b", "range": {"min": 0.0, "max": 1.0}, "step": 0.6}]
    )
    assert uneven.array["b"].tolist() == [0.0, 0.6]  # 1.2 越上界档被钳制


def test_single_dim_over_base_rejected() -> None:
    """R1 护栏字面口径：1 维 5 档（5 > 4^1）→ 拒（六池单元单维枚举同此，
    追认点记档——多于一维即放行，如 CASS n_pool×t_cycle=15 ≤ 4^2）。"""
    with pytest.raises(GridTooLarge, match="4"):  # type: ignore[misc]
        build_grid([{"field_id": "n", "values": [2.0, 3.0, 4.0, 5.0, 6.0]}])  # type: ignore[misc]


def test_paramspec_form_guard_too_large() -> None:
    """R1 护栏（探针④证据同源）：ParamSpec 形 10 维 × 5 档=5^10 > 4^10 → 拒。"""
    from waterprint.contracts.manifest import ParamSpec

    specs = [
        ParamSpec(field_id=f"f{i}", dim="DIMENSIONLESS", default=1.0,
                  grid=(1.0, 2.0, 3.0, 4.0, 5.0))
        for i in range(10)
    ]
    with pytest.raises(GridTooLarge, match="护栏"):  # type: ignore[misc]
        build_grid(specs)  # type: ignore[misc]


def test_operator_whitelist_rejected() -> None:
    """R1 DSL 白名单：非法算符（==/+）与裸 Python 一律拒。"""
    df = pd.DataFrame({"pool_length": [8.0, 12.0]})
    for expression in ("pool_length == 8", "pool_length + 1 <= 12", "abs(pool_length) > 1"):
        bad = Constraint(key="kb.bad", expression=expression, source="kb")  # type: ignore[misc]
        with pytest.raises(InvalidConstraintError):  # type: ignore[misc]
            apply_constraints(df, [bad])  # type: ignore[misc]


def test_membership_and_conjunction_evaluation() -> None:
    """R1 DSL 正向：∈ 数档 + and 组合的向量化求值。"""
    df = pd.DataFrame({"pool_length": [8.0, 12.0, 20.0], "id": [1.0, 2.0, 3.0]})
    constraint = Constraint(  # type: ignore[misc]
        key="kb.demo.mix",
        expression="pool_length ∈ [8, 20] and id >= 2",
        source="kb.demo",
    )
    result = apply_constraints(df, [constraint])  # type: ignore[misc]
    assert list(result.feasible) == [2]  # 行0：id=1 不满足 id>=2；行1：12∉[8,20]
    matrix = result.pass_matrix[constraint.expression]
    assert matrix.tolist() == [False, False, True]


def _stub(feasible: list[int]) -> object:
    class _Stub:
        pass

    stub = _Stub()
    stub.feasible = feasible
    return stub


def test_ranking_tie_break_full_order_deterministic() -> None:
    """R1：同排序值经 tie_break 成全序——乱序输入两次排序逐行一致。"""
    df = pd.DataFrame(
        {"cost": [5.0, 5.0, 5.0, 5.0], "row_id": [4.0, 2.0, 1.0, 3.0]}
    )
    key = RankingKey(sort_by="cost", ascending=True, tie_break=["row_id"])  # type: ignore[misc]
    first = rank(_stub([0, 1, 2, 3]), df, key, limit=10)  # type: ignore[misc]
    second = rank(
        _stub([3, 1, 0, 2]), df.iloc[::-1].reset_index(drop=True), key, limit=10  # type: ignore[misc]
    )
    assert first.rows["row_id"].tolist() == [1.0, 2.0, 3.0, 4.0]  # 全序（非仅稳定）
    assert first.rows["row_id"].tolist() == second.rows["row_id"].tolist()


def test_ranking_missing_tie_break_column_rejected() -> None:
    """R1 负向：tie_break 引用缺失列 → 领域异常（禁静默忽略次序键）。"""
    df = pd.DataFrame({"cost": [5.0]})
    key = RankingKey(sort_by="cost", ascending=True, tie_break=["no_such_col"])  # type: ignore[misc]
    with pytest.raises(InvalidRankingError, match="no_such_col"):  # type: ignore[misc]
        rank(_stub([0]), df, key, limit=10)  # type: ignore[misc]
