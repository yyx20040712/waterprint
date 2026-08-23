"""condition 镜像测试：工况语义（ADR-007：flow 全局 2 档 × 逐单元敏感性）。

输入:  waterprint.contracts.condition 公开符号
输出:  2+k 条数/键确定性/语义字段断言（两版矛盾表述的终结测试）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.condition")
FlowCase = getattr(_mod, "FlowCase", None)
build_condition_set = getattr(_mod, "build_condition_set", None)

pytestmark = pytest.mark.skipif(
    None in (FlowCase, build_condition_set),
    reason="实现未就绪：waterprint.contracts.condition（M1）",
)


def test_baseline_is_exactly_two_flow_cases() -> None:
    """R1：空受检集合 = 基线 design/avg 两档（不是 1 档也不是 4 档）。"""
    condition_set = build_condition_set([])
    assert len(condition_set.baseline) == 2
    assert {c.flow_case for c in condition_set.baseline} == {
        FlowCase.DESIGN,
        FlowCase.AVG,
    }


@pytest.mark.parametrize("k", [1, 2, 5])
def test_total_runs_are_linear_two_plus_k(k: int) -> None:
    """R1（§16 A3 终结）：运行次数 = 2 + k，禁止 2^n 组合。"""
    condition_set = build_condition_set([f"unit_{i}" for i in range(k)])
    assert len(list(condition_set.iter_all())) == 2 + k


def test_sensitivity_conditions_isolate_one_unit() -> None:
    """敏感性工况：每条恰好只有一个 offline 单元（其余全池）。"""
    condition_set = build_condition_set(["aao", "sedimentation"])
    for condition in condition_set.sensitivity:
        assert condition.offline_unit in {"aao", "sedimentation"}
    assert len({c.offline_unit for c in condition_set.sensitivity}) == 2


def test_condition_keys_unique_and_deterministic() -> None:
    """R2：键唯一且确定（结果索引/缓存键/SSE 通道的稳定性前提）。"""
    units = ["aao", "thickener"]
    condition_set = build_condition_set(units)
    keys = [type(condition_set).key(c) for c in condition_set.iter_all()]
    assert len(keys) == len(set(keys))
    again = [type(condition_set).key(c) for c in build_condition_set(units).iter_all()]
    assert keys == again
