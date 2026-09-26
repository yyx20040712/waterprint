"""relax 镜像测试（批5 新增件——[HUMAN-LOCK] 草案转正）。

覆盖：名义/真实放宽区分（AUD-P2）+预算拒 skip 事由（AUD-W7 前半）+
末空级诊断三支（timeout 维度/预算拒/无域可放——beam._final_infeasible_
diagnosis 纯函数直证）。
落位目标：core/tests/solution/test_relax.py（三连锁同批闭合）。
"""
from __future__ import annotations

import pytest

_relax = pytest.importorskip(
    "waterprint.solution.joint_enumeration.relax",
    reason="实现未就绪：批5 relax 件（beam 拆件）",
)
relaxed_grids = _relax.relaxed_grids
retry_joint = _relax.retry_joint

_RANGE_GRID = {
    "municipal_aao": ({"field_id": "n", "range": {"min": 2.0, "max": 4.0},
                       "step": 1.0},),
}
_DISCRETE_GRID = {"municipal_aao": ({"field_id": "n", "values": [2.0, 3.0]},)}


def test_discrete_specs_are_nominal_relaxation_skipped() -> None:
    """AUD-P2：离散档原样=名义放宽——不进重试面（空集诚实跳过）。"""
    assert relaxed_grids(_DISCRETE_GRID, 2.0) == {}


def test_range_specs_widen_both_sides() -> None:
    """真实域扩：range 两侧各扩 (f−1)/2×域宽（f=2 → 域宽翻倍）。"""
    widened = relaxed_grids(_RANGE_GRID, 2.0)
    assert widened["municipal_aao"][0]["range"] == {"min": 1.0, "max": 5.0}


def test_partial_widening_keeps_only_changed_units() -> None:
    """混合网格：仅收录实际变化的单元（离散档单元不进 widened）。"""
    mixed = {**_RANGE_GRID, **_DISCRETE_GRID}
    # 键同名会覆盖——用两单元键构造
    mixed = {
        "municipal_aao": _RANGE_GRID["municipal_aao"],
        "municipal_cass": _DISCRETE_GRID["municipal_aao"],
    }
    widened = relaxed_grids(mixed, 2.0)
    assert set(widened) == {"municipal_aao"}


class _BudgetSkipSearch:
    """预算拒 stub：within_budget 恒 False（retry_joint 消费面最小形状）。"""

    class guards:  # noqa: N801  # stub 形状注记
        relax_factor = 2.0

    targets = ("municipal_aao",)
    assembled = None

    class env:  # noqa: N801  # stub 形状注记（grid_of overrides 面）
        assumptions = {}

    def within_budget(self, grids: object) -> bool:
        """预算拒分支（不抛——事由分叉）。"""
        return False


def test_retry_budget_skip_returns_reason_not_raise() -> None:
    """AUD-W7 前半：放宽后超预算=skip_reason='budget'（静默 None 是旧病）。"""
    from waterprint.solution.joint_enumeration import JointEnumerationOptions

    options = JointEnumerationOptions(grids=_RANGE_GRID)
    outcome = retry_joint(_BudgetSkipSearch(), options, {})
    assert outcome.skip_reason == "budget"
    assert outcome.outcome is None


def test_final_infeasible_diagnosis_three_branches() -> None:
    """AUD-W7 后半：timeout 维度/预算拒注记/无域可放三支分叉。"""
    from waterprint.solution.joint_enumeration.beam import (  # noqa: SLF001  # 私面直证（镜像件义务）
        _final_infeasible_diagnosis,
    )

    timeout = _final_infeasible_diagnosis(True, None)
    assert timeout["timeout_truncated"] is True
    assert "timeout 截断" in timeout["note"]

    budget = _final_infeasible_diagnosis(False, "budget")
    assert budget["timeout_truncated"] is False
    assert "超" in budget["note"] and "max_total_rows" in budget["note"]

    no_domain = _final_infeasible_diagnosis(False, None)
    assert no_domain["relaxed"] is False
    assert "无可放宽 range 域" in no_domain["note"]
