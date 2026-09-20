"""final_eval 镜像测试：末段全厂真值评估面（W9/W10/W12/N6 直面断言）。

输入:  waterprint.solution.joint_enumeration.final_eval 公开符号
输出:  硬门/真键映射/护栏取值/环境补齐契约断言（beam 全链外的一面直测）
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

_mod = importlib.import_module("waterprint.solution.joint_enumeration.final_eval")
compliance_of = getattr(_mod, "compliance_of", None)
metrics_of = getattr(_mod, "design_baseline_metrics", None)
terminal_summary = getattr(_mod, "terminal_summary", None)
joint_guards = getattr(_mod, "joint_guards", None)
completed_env = getattr(_mod, "completed_env", None)

pytestmark = pytest.mark.skipif(
    None in (compliance_of, metrics_of, terminal_summary, joint_guards, completed_env),
    reason="实现未就绪：joint_enumeration.final_eval（B4-3）",
)


def _standard(limits: dict[str, float]) -> Any:
    from waterprint.contracts.quality import EffluentStandard

    return EffluentStandard(standard_id="s", name_i18n="测试", limits=limits)


def _conditions() -> Any:
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set(["municipal_aao"])


def test_compliance_baseline_breach_is_infeasible() -> None:
    """R5：baseline（design/avg）越限=不可行；sensitivity 越限=可行+载荷。"""
    keys = ("design", "avg", "design_offline_municipal_aao")
    summary = {
        keys[0]: {"CODCR": 60.0},
        keys[1]: {"CODCR": 50.0},
        keys[2]: {"CODCR": 40.0},
    }
    std = (_standard({"CODCR": 50.0}),)
    baseline = frozenset(keys[:2])
    feasible, failed = compliance_of(summary, std, baseline)  # type: ignore[misc]
    assert feasible is False  # design 60>50 越限
    assert any(item.startswith("design:") for item in failed)
    summary[keys[0]] = {"CODCR": 25.0}  # baseline 全过（25/50≤30）
    summary[keys[1]] = {"CODCR": 25.0}
    std = (_standard({"CODCR": 30.0}),)
    feasible, failed = compliance_of(summary, std, baseline)  # type: ignore[misc]
    assert feasible is True  # W10：sensitivity 失守不剔除
    assert failed == ("design_offline_municipal_aao:s:CODCR",)


def test_compliance_missing_indicator_not_judged() -> None:
    """summary 缺指标=有则录无则略（不判越限——_effluent_of 同口径）。"""
    feasible, failed = compliance_of(  # type: ignore[misc]
        {"design": {"BOD5": 5.0}}, (_standard({"CODCR": 1.0}),),
        frozenset({"design"}),
    )
    assert feasible is True and failed == ()


def test_design_baseline_metrics_alias_mapping() -> None:
    """W12 真键映射：opex/energy/carbon 别名 ← summary 真键三联。"""
    from waterprint.contracts.condition import ConditionSet

    conditions = _conditions()
    summary = {
        "design": {
            "cost_opex_yuan_a": 100.0,
            "power_total_kwh_d": 50.0,
            "carbon_intensity_kgco2e_m3": 2.0,
        },
        "avg": {"cost_opex_yuan_a": 999.0},
    }
    baseline = metrics_of(summary, conditions)  # type: ignore[misc]
    assert baseline == {"opex": 100.0, "energy": 50.0, "carbon": 2.0}
    assert ConditionSet.key(conditions.baseline[0]) == "design"


def test_terminal_summary_empty_legal() -> None:
    """terminal 无水质键→空映射合法（矿井线 BOD5 缺同口径）。"""
    class _Snap:
        unit_id = "terminal"
        outqualities = {}  # noqa: RUF012

    class _Plant:
        conditions = {"design": {"terminal": _Snap()}}  # noqa: RUF012

    assert terminal_summary(_Plant(), ()) == {"design": {}}  # type: ignore[misc]


def test_joint_guards_defaults_and_overrides() -> None:
    """R4：护栏全量经 assumption() 取值（覆盖优先——W7/W8 键面）。"""
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    assumptions = {item.key: item.default for item in DEFAULT_ASSUMPTIONS}
    guards = joint_guards(assumptions)  # type: ignore[misc]
    assert guards.beam_width == 5.0 and guards.max_units == 6.0
    assert guards.max_rows == 500000.0 and guards.max_evals == 25.0
    assert guards.weights == {"opex": 0.5, "energy": 0.3, "carbon": 0.2}
    assert guards.all_outer is False  # validation_conditions=0=「all」
    assumptions["solution.joint.validation_conditions"] = 1.0
    assumptions["solution.joint.beam_width"] = 3.0
    guards = joint_guards(assumptions)  # type: ignore[misc]
    assert guards.all_outer is True and guards.beam_width == 3.0


def test_completed_env_fills_loop_keys() -> None:
    """engine_params loop.* 补齐（app._completed_env 同语义——UF-08 同源）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    assumptions = {item.key: item.default for item in DEFAULT_ASSUMPTIONS}
    env = RunEnv(
        engine_version="t", data_version="t", assumptions=assumptions,
        coefficients=_Lib(), price_book={}, trace_sink=None, engine_params={},
    )
    filled = completed_env(env)  # type: ignore[misc]
    assert set(filled.engine_params) >= {
        "loop.tolerance", "loop.max_iterations", "loop.damping"
    }
    assert completed_env(filled) is filled  # type: ignore[misc] 已齐=恒等返回


class _Lib:
    """系数视图占位（结构满足 CoefficientsView）。"""

    data_version = "t"

    def get(self, key: str) -> None:
        return None

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return ()

    def require_keys(self, keys: Any) -> None:
        return None
