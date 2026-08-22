"""diagnose 镜像测试：无解诊断（最小冲突集、失败计数、建议有据）。

输入:  waterprint.solution.diagnose 公开符号 + 布尔通过矩阵
输出:  诊断语义断言（"不是只会说无解"）
"""

from __future__ import annotations

import importlib

import pytest

pd = pytest.importorskip("pandas")

_mod = importlib.import_module("waterprint.solution.diagnose")
diagnose_infeasibility = getattr(_mod, "diagnose_infeasibility", None)

pytestmark = [
    pytest.mark.skipif(
        diagnose_infeasibility is None,
        reason="实现未就绪：waterprint.solution.diagnose（M1）",
    ),
]


def _matrix() -> "pd.DataFrame":
    """三方案 × 三约束：A∩B 联合无解（各自单独都有解）。"""
    return pd.DataFrame(
        {
            "c_len_max": [True, True, False],
            "c_len_min": [False, True, True],
            "c_velocity": [True, True, True],
        }
    )


def test_minimal_conflict_set_identified() -> None:
    """R1：最小冲突集恰为联合无解的两条（c_len_max + c_len_min）。"""
    constraints = {
        "c_len_max": {"key": "c_len_max", "source": "kb"},
        "c_len_min": {"key": "c_len_min", "source": "kb"},
        "c_velocity": {"key": "c_velocity", "source": "kb"},
    }
    report = diagnose_infeasibility(_matrix(), constraints, grid=None)
    conflict_keys = {frozenset(conflict) for conflict in report.minimal_conflicts}
    assert frozenset({"c_len_max", "c_len_min"}) in conflict_keys


def test_fail_counts_complete() -> None:
    """R1：每约束失败计数完整（矩阵列求和口径）。"""
    constraints = {name: {"key": name, "source": "kb"} for name in _matrix().columns}
    report = diagnose_infeasibility(_matrix(), constraints, grid=None)
    assert report.fail_counts["c_len_max"] == 1
    assert report.fail_counts["c_len_min"] == 1
    assert report.fail_counts["c_velocity"] == 0


def test_suggestions_reference_evidence() -> None:
    """R2：建议必须引用依据（冲突约束/失败计数），拒绝空话。"""
    constraints = {name: {"key": name, "source": "kb"} for name in _matrix().columns}
    report = diagnose_infeasibility(_matrix(), constraints, grid=None)
    assert report.suggestions
    for suggestion in report.suggestions:
        text = str(suggestion)
        assert any(key in text for key in ("c_len_max", "c_len_min", "c_velocity"))
