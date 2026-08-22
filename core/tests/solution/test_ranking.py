"""ranking 镜像测试：排序与截断（确定性全序、截断显式、成本列缺失拒绝）。

输入:  waterprint.solution.ranking 公开符号 + 内存 FilterResult/DataFrame
输出:  排序语义断言
"""

from __future__ import annotations

import importlib

import pytest

pd = pytest.importorskip("pandas")

_mod = importlib.import_module("waterprint.solution.ranking")
rank = getattr(_mod, "rank", None)
RankingKey = getattr(_mod, "RankingKey", None)

pytestmark = [
    pytest.mark.skipif(
        None in (rank, RankingKey),
        reason="实现未就绪：waterprint.solution.ranking（M1）",
    ),
]


def _result(feasible: list[int]) -> object:
    class _Stub:
        pass

    stub = _Stub()
    stub.feasible = feasible
    return stub


def test_sorting_is_deterministic_with_ties() -> None:
    """R1：tie_break 稳定全序——乱序输入两次排序结果逐行一致。"""
    df = pd.DataFrame({"margin_min": [0.1, 0.3, 0.1], "row_id": [2, 1, 3]})
    key = RankingKey(sort_by="margin_min", ascending=False, tie_break=["row_id"])
    first = rank(_result([0, 1, 2]), df, key, limit=10)
    second = rank(_result([2, 1, 0]), df.iloc[::-1].reset_index(drop=True), key, limit=10)
    assert first.rows["row_id"].tolist() == second.rows["row_id"].tolist()


def test_truncation_is_explicit() -> None:
    """R3：截断必须标注 truncated 与 total_feasible（前端"还有 N 条"依据）。"""
    df = pd.DataFrame({"margin_min": [0.5, 0.4, 0.3], "row_id": [1, 2, 3]})
    key = RankingKey(sort_by="margin_min", ascending=False, tie_break=["row_id"])
    result = rank(_result([0, 1, 2]), df, key, limit=2)
    assert result.truncated is True
    assert result.total_feasible == 3
    assert len(result.rows) == 2


def test_missing_cost_column_raises() -> None:
    """R2：成本排序键缺成本列 → 领域异常（禁止静默回退裕度排序）。"""
    df = pd.DataFrame({"margin_min": [0.5], "row_id": [1]})
    key = RankingKey(sort_by="cost", ascending=True, tie_break=["row_id"])
    with pytest.raises(Exception, match=".+"):
        rank(_result([0]), df, key, limit=10)
