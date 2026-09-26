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


# ══ 批2a 约束带裕度域（test_margins_draft 转正——[HUMAN-LOCK]
#     2026-09-26 用户「全部追认」授权落地 b2a 呈批件）══

from math import isnan  # noqa: E402 （域内追加——NaN 断言用）

band_margin_column = getattr(_mod, "band_margin_column", None)
band_of = getattr(_mod, "band_of", None)


def _frame(rows: list[dict[str, float]]) -> "pd.DataFrame":
    return pd.DataFrame(rows)


# ── band_of：带形解析（DSL 家园面）────────────────────────────────


def test_band_of_two_sided_same_field() -> None:
    """双侧同字段带（>= 与 <= 各一）→ (field, low, high)；子句序无关。"""
    assert band_of("v >= 7.0 and v <= 10.0") == ("v", 7.0, 10.0)  # type: ignore[misc]
    assert band_of("v <= 10.0 and v >= 7.0") == ("v", 7.0, 10.0)  # type: ignore[misc]


def test_band_of_strict_ops_accepted() -> None:
    """严格不等号同构带（>/<）——带缘测度零，距离公式同形。"""
    assert band_of("v > 7.0 and v < 10.0") == ("v", 7.0, 10.0)  # type: ignore[misc]


def test_band_of_non_band_shapes_return_none() -> None:
    """单侧/∈ 档列表/跨字段/单子句/同向双子句 → None（无带宽概念）。"""
    assert band_of("v <= 13.0") is None  # type: ignore[misc]
    assert band_of("n ∈ [2.0, 4.0]") is None  # type: ignore[misc]
    assert band_of("x >= 1.0 and y <= 2.0") is None  # type: ignore[misc]
    assert band_of("v >= 1.0 and v >= 5.0") is None  # type: ignore[misc]


def test_band_of_degenerate_band_returns_none() -> None:
    """退化带（low>=high）→ None 不产出裕度（门一 W1 回炉处置：与过滤面
    行为对称——恒不可行带由 apply_constraints 自然产出空集，low==high 单点
    带可行域不受误杀；裕度面不引入任务级行为回归）。"""
    assert band_of("v >= 5.0 and v <= 3.0") is None  # type: ignore[misc]
    assert band_of("v >= 5.0 and v <= 5.0") is None  # type: ignore[misc]  单点带：无带宽概念


# ── band_margin_column：归一距离列─────────────────────────────────


def test_band_margin_in_band_values() -> None:
    """带 [7,10]：带缘=0、带中心=0.5、偏侧=距近缘比例（R1 归一距离）。"""
    frame = _frame([{"v": 7.0}, {"v": 8.5}, {"v": 9.25}, {"v": 10.0}])
    column = band_margin_column(frame, [Constraint(key="kb.test",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert column.name == "margin_min"
    assert column.iloc[0] == pytest.approx(0.0)
    assert column.iloc[1] == pytest.approx(0.5)
    assert column.iloc[2] == pytest.approx(0.25)  # min(2.25, 0.75)/3
    assert column.iloc[3] == pytest.approx(0.0)


def test_band_margin_out_of_band_negative() -> None:
    """越带行为负（随后被约束过滤剔除——数学一致不留消费面）。"""
    frame = _frame([{"v": 11.0}, {"v": 5.0}])
    column = band_margin_column(frame, [Constraint(key="kb.test",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert column.iloc[0] == pytest.approx(-1.0 / 3.0)  # min(4, -1)/3
    assert column.iloc[1] == pytest.approx(-2.0 / 3.0)  # min(-2, 5)/3


def test_band_margin_multiple_bands_take_tightest() -> None:
    """多带适用 → 行级取最紧（min——最紧指标优先，与旧 margin_* 语义同口径）。"""
    frame = _frame([
        {"v": 8.5, "p": 0.3},   # 带1=0.5 带2=0.5 → 0.5
        {"v": 8.5, "p": 0.22},  # 带1=0.5 带2=0.1 → 0.1（带2 更紧）
        {"v": 7.1, "p": 0.3},   # 带1≈0.033 带2=0.5 → 0.033
    ])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.band_v", expression="v >= 7.0 and v <= 10.0", source="kb:test"),
        Constraint(key="kb.band_p", expression="p >= 0.2 and p <= 0.4", source="kb:test"),
    ])
    assert column.iloc[0] == pytest.approx(0.5)
    assert column.iloc[1] == pytest.approx(0.1)
    assert column.iloc[2] == pytest.approx(0.1 / 3.0)


def test_band_margin_non_band_constraints_excluded() -> None:
    """单侧/∈ 约束不产出裕度（无带宽概念——覆盖面随 kb 扩条渐进）。"""
    frame = _frame([{"v": 8.5}])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.one_sided", expression="v <= 13.0", source="kb:test"),
        Constraint(key="kb.discrete", expression="n ∈ [2.0, 4.0]", source="kb:test"),
    ])
    assert isnan(column.iloc[0])


def test_band_margin_field_absent_from_frame_skipped() -> None:
    """带字段不在枚举行列=不适用（跳过；字段合法性由 apply_constraints 统一执法）。"""
    frame = _frame([{"v": 8.5}])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.band_p", expression="p >= 0.2 and p <= 0.4", source="kb:test"),
        Constraint(key="kb.band_v", expression="v >= 7.0 and v <= 10.0", source="kb:test"),
    ])
    assert column.iloc[0] == pytest.approx(0.5)  # 仅带 v 适用


def test_band_margin_empty_constraints_all_nan() -> None:
    """空约束集 → 全 NaN（「无裕度信息」诚实语义——旧行为兼容面）。"""
    frame = _frame([{"v": 8.5}, {"v": 9.0}])
    column = band_margin_column(frame, [])  # type: ignore[misc]
    assert all(isnan(value) for value in column)


def test_band_margin_nan_field_propagation() -> None:
    """域拒行（字段 NaN）：单带→NaN；他带有效→取有效（skipna 口径——
    双源可行判定仍由 nan_flag 承载，裕度列不重复判）。"""
    frame = _frame([
        {"v": float("nan"), "p": 0.3},
        {"v": 8.5, "p": float("nan")},
    ])
    column = band_margin_column(frame, [  # type: ignore[misc]
        Constraint(key="kb.band_v", expression="v >= 7.0 and v <= 10.0", source="kb:test"),
        Constraint(key="kb.band_p", expression="p >= 0.2 and p <= 0.4", source="kb:test"),
    ])
    assert column.iloc[0] == pytest.approx(0.5)  # v 带 NaN，p 带 0.5 有效
    assert column.iloc[1] == pytest.approx(0.5)  # v 带 0.5 有效，p 带 NaN
    only_v = band_margin_column(frame, [Constraint(key="kb.band_v",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert isnan(only_v.iloc[0])
    assert only_v.iloc[1] == pytest.approx(0.5)


def test_band_margin_index_follows_frame() -> None:
    """列索引随 frame（调用面 attach 对齐前提——run_enumeration concat 整帧）。"""
    frame = _frame([{"v": 7.0}, {"v": 8.5}, {"v": 9.5}])
    frame.index = pd.Index([10, 20, 30])
    column = band_margin_column(frame, [Constraint(key="kb.test",  # type: ignore[misc]
        expression="v >= 7.0 and v <= 10.0", source="kb:test")])
    assert list(column.index) == [10, 20, 30]
