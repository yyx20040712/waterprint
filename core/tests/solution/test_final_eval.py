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
    assert guards.weights == {"opex": 0.25, "energy": 0.3, "carbon": 0.2, "capex": 0.25}
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


# ══ 批2b capex 第四真键域（test_capex_keys_draft 转正——[HUMAN-LOCK]
#     2026-09-26 用户「全部追认」授权落地 b2b 呈批件）══

from pathlib import Path  # noqa: E402 （域内追加——parents 路径解析用）

_registry_mod = importlib.import_module("waterprint.registry.assumptions")
DEFAULT_ASSUMPTIONS = getattr(_registry_mod, "DEFAULT_ASSUMPTIONS", None)
capex_kit_of = getattr(_mod, "capex_kit_of", None)
capex_grand_total = getattr(_mod, "capex_grand_total", None)
design_baseline_metrics = metrics_of  # 头部已取符号（草稿名对齐——b2b 域用例直名引用）

# 转正路径 core/tests/solution → parents[3]=仓库根（草稿期 .workflow 同深度口径）
_REPO_DATA = Path(__file__).resolve().parents[3] / "data"
_K_OPEX = "solution.joint.objective_weight_opex"
_K_ENERGY = "solution.joint.objective_weight_energy"
_K_CARBON = "solution.joint.objective_weight_carbon"
_K_CAPEX = "solution.joint.objective_weight_capex"


def _defaults() -> dict[str, float]:
    return {item.key: item.default for item in DEFAULT_ASSUMPTIONS}  # type: ignore[misc]


def test_registry_four_objective_keys() -> None:
    """四键全在场+初值 .25/.30/.20/.25（成本面 opex+capex=0.5 守恒）。"""
    defaults = _defaults()
    assert defaults[_K_CAPEX] == pytest.approx(0.25)  # 新键在场（批2b 前缺=红）
    assert defaults[_K_OPEX] == pytest.approx(0.25)  # 旧值 0.5 → 0.25（红先证锚）
    assert defaults[_K_ENERGY] == pytest.approx(0.30)
    assert defaults[_K_CARBON] == pytest.approx(0.20)
    assert sum(defaults[key] for key in (_K_OPEX, _K_ENERGY, _K_CARBON, _K_CAPEX)) == (
        pytest.approx(1.0)
    )


def test_joint_guards_weights_four_keys() -> None:
    """guards.weights 四键（三键断言面扩四——锁定件 test_final_eval:107 同步呈批）。"""
    guards = joint_guards(_defaults())  # type: ignore[misc]
    assert guards.weights == {
        "opex": pytest.approx(0.25), "energy": pytest.approx(0.30),
        "carbon": pytest.approx(0.20), "capex": pytest.approx(0.25),
    }


def test_capex_kit_none_semantics() -> None:
    """缺席语义：capex_kit_of(None)→None（core 直调向后兼容——kit 缺席键恒缺）。"""
    assert capex_kit_of(None) is None  # type: ignore[misc]


def test_capex_kit_loads_from_data_dir() -> None:
    """装载面：真数据包装配束三件（book 版本+费率+映射规则非空）。"""
    kit = capex_kit_of(_REPO_DATA)  # type: ignore[misc]
    assert kit is not None
    assert kit.book.data_version  # 单价包版本非空
    assert kit.fees  # 费率规则非空（field_mapping fee_rules=7 条）
    assert kit.mapping.rules  # 映射规则非空


def test_capex_grand_total_deterministic_positive() -> None:
    """确定性+正值：基线全厂结果集双跑同值（可复算——R3 确定性口径）。"""
    from waterprint.app_assembly import assemble
    from waterprint.solution.joint_enumeration import execute_graph

    from tests.solution.test_beam import _conditions, _env, _project

    env = completed_env(_env())  # type: ignore[misc]  loop.* 引擎参数补齐（beam 内部同款口径）
    project = _project()
    conditions = _conditions()
    plant = execute_graph(
        project.design, assemble(project, env).units, conditions, env,
    )
    kit = capex_kit_of(_REPO_DATA)  # type: ignore[misc]
    first = capex_grand_total(kit, plant, "design")  # type: ignore[misc]
    second = capex_grand_total(kit, plant, "design")  # type: ignore[misc]
    assert first == second and first > 0.0


def test_design_baseline_metrics_merges_capex_when_kit_present() -> None:
    """基线并键：plant+kit 在场→cost_capex_yuan 入基线；缺席→三键照旧。"""
    from waterprint.app_assembly import assemble
    from waterprint.solution.joint_enumeration import execute_graph
    from waterprint.solution.joint_enumeration.final_eval import merged_summary

    from tests.solution.test_beam import _conditions, _env, _project

    env = completed_env(_env())  # type: ignore[misc]  loop.* 引擎参数补齐（beam 内部同款口径）
    project = _project()
    conditions = _conditions()
    assembled = assemble(project, env)
    plant = execute_graph(project.design, assembled.units, conditions, env)
    summary = merged_summary(plant, assembled.edges, env)

    plain = design_baseline_metrics(summary, conditions)  # type: ignore[misc]
    assert set(plain) == {"opex", "energy", "carbon"}  # 向后兼容：缺席三键
    merged = design_baseline_metrics(  # type: ignore[misc]
        summary, conditions, plant=plant, capex_kit=capex_kit_of(_REPO_DATA),  # type: ignore[misc]
    )
    assert set(merged) == {"opex", "energy", "carbon", "capex"}
    assert merged["capex"] > 0.0  # 基线概算正值（金样链全单元映射在册）


def test_score_redistribution_when_capex_absent() -> None:
    """N6 重分配：capex 缺席→三键权重归一 .25/.30/.20→(.25,.30,.20)/.75。"""
    from waterprint.solution.joint_enumeration.ranking import plant_objective

    weights = {"opex": 0.25, "energy": 0.30, "carbon": 0.20, "capex": 0.25}
    values = [{"opex": 1.0, "energy": 2.0, "carbon": 3.0}]  # capex 缺席
    baseline = {"opex": 1.0, "energy": 1.0, "carbon": 1.0, "capex": 1.0}
    (score,) = plant_objective(values, baseline, weights)
    expected = (0.25 * 1.0 + 0.30 * 2.0 + 0.20 * 3.0) / 0.75
    assert score == pytest.approx(expected)  # 权重重排裁决本意（非回归）
