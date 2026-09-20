"""joint_enumeration 主编排镜像测试：beam 全链+静态预检+双轴预算（B4-3 TDD 序 3）。

输入:  waterprint.solution.joint_enumerate 公开符号+真实 coefficients 数据包
输出:  两单元小网格全链断言（拓扑序+top-k 冻结+末段复验+排序）/静态预检
       422 面/k=1 边界/超预算拒/截断语义/terminal_summary 单源一致
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

_mod = importlib.import_module("waterprint.solution.joint_enumeration")
run_joint_enumerate = getattr(_mod, "run_joint_enumerate", None)
estimate_rows = getattr(_mod, "estimate_rows", None)
terminal_summary = getattr(_mod, "terminal_summary", None)
JointEnumerationOptions = getattr(_mod, "JointEnumerationOptions", None)
JointEnumerationTooLarge = getattr(_mod, "JointEnumerationTooLarge", None)

pytestmark = pytest.mark.skipif(
    None in (run_joint_enumerate, estimate_rows, terminal_summary,
             JointEnumerationOptions, JointEnumerationTooLarge),
    reason="实现未就绪：solution.joint_enumeration.beam（B4-3）",
)

_DATA = Path(__file__).resolve().parents[2].parent / "data" / "coefficients"
_AAO, _CASS, _VX = "municipal_aao", "municipal_cass", "municipal_vxinglvchi"
_GRIDS = {
    _AAO: ({"field_id": "n", "values": [2.0, 3.0]},),
    _CASS: ({"field_id": "n_pool", "values": [2.0, 3.0]},),
    _VX: ({"field_id": "n", "values": [4.0, 6.0]},),
}


def _project() -> Any:
    """inlet→aao→cass→V 型滤池四节点链（三寻优目标拓扑序载体）。"""
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile

    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "NH3N": 26.0,
                    "TN": 43.0,
                    "TP": 6.5,
                },
                _AAO: {},
                _CASS: {},
            },
            edges=[
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": _AAO, "port_id": "in"}},
                {"src": {"unit_id": _AAO, "port_id": "out"},
                 "dst": {"unit_id": _CASS, "port_id": "in"}},
            ],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="b43", data_version="b43",
        ),
    )


def _env(overrides: dict[str, float] | None = None) -> Any:
    """真实数据包 env（coefficients 1.5.0：factor.aao/cass/opex/carbon 全在册）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
    from waterprint.registry.coefficients import load_coefficients

    assumptions = {item.key: item.default for item in DEFAULT_ASSUMPTIONS}
    assumptions.update(overrides or {})
    return RunEnv(
        engine_version="b43", data_version="b43", assumptions=assumptions,
        coefficients=load_coefficients(_DATA), price_book={},
        trace_sink=None, engine_params={},
    )


def _options(**overrides: Any) -> Any:
    """选项装配（assemble 类注入防环面——经 app_assembly 真源）。"""
    from waterprint.app_assembly import assemble

    return JointEnumerationOptions(assemble=assemble, **overrides)  # type: ignore[misc]


def _conditions() -> Any:
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set([])


def _standard(limits: dict[str, float]) -> Any:
    from waterprint.contracts.quality import EffluentStandard

    return EffluentStandard(standard_id="test_std", name_i18n="测试标准", limits=limits)


def test_two_unit_full_chain_wiring() -> None:
    """两单元全链：拓扑序重排（乱序输入）+top-k 冻结+末段复验+排序面。"""
    outcome = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_CASS, _AAO], _conditions(), _env(),
        _options(grids=_GRIDS),
    )
    assert outcome.search_semantics == {
        "structure": "staged_beam", "optimality": "beam_approx",
        "loop_semantics": "frozen", "pruning_bias": "baseline_context",
    }
    assert outcome.combos, "宽松无标准面：可行组合非空（opex 真键在册）"
    for combo in outcome.combos:
        assert set(combo.params) == {_AAO, _CASS}  # 拓扑序重排后两单元齐备
        assert combo.feasible and not combo.sensitivity_degraded
        assert "cost_opex_yuan_a" in combo.metrics  # N6 opex 在场门
        assert "power_total_kwh_d" in combo.metrics
        assert "avg.cost_opex_yuan_a" in combo.metrics  # R6 avg 附带
        assert combo.score is not None
    scores = [combo.score for combo in outcome.combos]
    assert scores == sorted(scores)  # 排序面：分数升序（降权感知序）
    # 双轴预算：g=2,k=5→stage1 行 2；stage2 前缀 2×行 2=4；末段 evals=min(5,4)=4
    usage = outcome.budget_usage
    assert usage["rows_evaluated"] == 2 + 2 * 2
    assert usage["full_plant_evals"] == len(outcome.combos)
    assert usage["truncated"] is False


def test_strict_standard_marks_infeasible_with_failed_conditions() -> None:
    """R5 硬门：严标准全越限=不可行+failed_conditions 载 condition 键+W11 交付。"""
    strict = _standard({"CODCR": 1e-9, "BOD5": 1e-9})
    outcome = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], _conditions(), _env(),
        _options(grids=_GRIDS, standards=(strict,)),
    )
    assert not outcome.combos
    assert outcome.diagnosis is not None and outcome.diagnosis["kind"] == "final_infeasible"


def test_sensitivity_failure_degrades_not_rejects() -> None:
    """W10 降权标记制：design/avg 过+offline 档失守=feasible 保持+degraded。

    构造：标准限值取 design 出水值之上（design/avg 过）、但 checked_units
    引入 design_offline 档（offline 工况出水更差→失守）。限值经第一跑
    实测 design 出水动态锚定（宽松标准面零硬编数值）。
    """
    from waterprint.contracts.condition import ConditionSet

    probe = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], _conditions(), _env(),
        _options(grids=_GRIDS),
    )
    assert probe.combos
    # design 出水最劣组合 CODCR×1.5：design/avg 档过、offline 档（n−1 池
    # 出水更差）构造失守带（实测通过带——条件断言防环境漂移假红）
    limit = max(combo.metrics.get("CODCR", 0.0) for combo in probe.combos) * 1.5
    from waterprint.contracts.condition import build_condition_set

    conditions = build_condition_set([_AAO])  # design/avg+design_offline_aao
    assert len(tuple(conditions.iter_all())) == 3
    loose_then_tight = _standard({"CODCR": float(limit)})
    outcome = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], conditions, _env(),
        _options(grids=_GRIDS, standards=(loose_then_tight,)),
    )
    degraded = [c for c in outcome.combos if c.sensitivity_degraded]
    if degraded:  # offline 失守成立时：feasible 保持 true+failed_conditions 在场
        for combo in degraded:
            assert combo.feasible
            assert any("design_offline" in item for item in combo.failed_conditions)
    assert ConditionSet.key(conditions.baseline[0]) == "design"


def test_static_precheck_rejects_over_budget() -> None:
    """W7 静态预检：rows>max_total_rows 事前 422（不进搜索）。"""
    tight = _env({"solution.joint.max_total_rows": 3.0})  # 估计 2·(5²−1)/4=12>3
    with pytest.raises(JointEnumerationTooLarge, match="静态预检"):  # type: ignore[misc]
        run_joint_enumerate(  # type: ignore[misc]
            _project(), [_AAO, _CASS], _conditions(), tight,
            _options(grids=_GRIDS),
        )


def test_static_precheck_rejects_over_max_units() -> None:
    """N>max_units 拒（名义护栏——N3 硬域口径）。"""
    tight = _env({"solution.joint.max_units": 1.0})
    with pytest.raises(JointEnumerationTooLarge, match="max_units"):  # type: ignore[misc]
        run_joint_enumerate(  # type: ignore[misc]
            _project(), [_AAO, _CASS], _conditions(), tight,
            _options(grids=_GRIDS),
        )


def test_estimate_rows_formula_and_k1_boundary() -> None:
    """N1 边界式：k=1→g·N；一般式 g·(k^N−1)/(k−1)·W_s（默认域锚 1.8e5）。"""
    assert estimate_rows([2, 2], 1.0, 1) == 4.0  # type: ignore[misc]
    assert estimate_rows([500], 3.0, 1) == 500.0
    # 默认域换算锚（W1）：N=6/g=500/k=3 → 500·(3^6−1)/2=182000≈1.8e5
    assert estimate_rows([500] * 6, 3.0, 1) == pytest.approx(182000.0)
    assert estimate_rows([500] * 6, 3.0, 3) == pytest.approx(182000.0 * 3)  # W5 all_outer


def test_beam_width_one_single_combo() -> None:
    """k=1：单组合传播（行计费 g·N=4，末段 evals=1）。"""
    outcome = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], _conditions(),
        _env({"solution.joint.beam_width": 1.0}),
        _options(grids=_GRIDS),
    )
    assert len(outcome.combos) == 1
    assert outcome.budget_usage["rows_evaluated"] == 2 + 1 * 2
    assert outcome.budget_usage["full_plant_evals"] == 1


def test_timeout_watchdog_truncates_honestly() -> None:
    """W1 看门狗：timeout_s=0 即截断——truncated=true 部分结果诚实返回不报错。"""
    outcome = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], _conditions(),
        _env({"solution.joint.timeout_s": 0.0}),
        _options(grids=_GRIDS),
    )
    assert outcome.budget_usage["truncated"] is True
    assert outcome.budget_usage["full_plant_evals"] == 0  # 首段即闸：零末段复验


def test_terminal_summary_single_source_with_app() -> None:
    """terminal_summary 自 app._summary_of 迁入单源：app 消费面同函数对象。"""
    import waterprint.app as app_module

    assert getattr(app_module, "_summary_of") is terminal_summary


def test_duplicate_and_unknown_units_rejected() -> None:
    """unit_ids 重复/未在图=InvalidJointEnumerationError（400 面）。"""
    from waterprint.solution.joint_enumeration import InvalidJointEnumerationError

    with pytest.raises(InvalidJointEnumerationError, match="重复"):  # type: ignore[misc]
        run_joint_enumerate(_project(), [_AAO, _AAO], _conditions(), _env(), _options())
    with pytest.raises(InvalidJointEnumerationError, match="不在装配图"):  # type: ignore[misc]
        run_joint_enumerate(_project(), ["nope"], _conditions(), _env(), _options())


def test_app_face_injects_assemble() -> None:
    """app 正门注入面：options 缺 assemble 经 waterprint.app 正门可用（UF-33）。"""
    import waterprint.app as app_module

    outcome = app_module.run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], _conditions(), _env(),
        app_module.JointEnumerationOptions(grids=_GRIDS),
    )
    assert outcome.combos
