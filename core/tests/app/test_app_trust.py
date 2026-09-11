"""app_trust 域镜像测试：run_full_calc 诊断产出/回路采集/闭合与裕度投影（ADR-012）。

夹具复用先例=tests.app.test_app_export（from tests.app.test_app import）；
回路图夹具复用 tests.graph.test_executor（_ProducerStub/_PassStub/_env——
机制行为锁定夹具跨件消费，tests 层私有共享先例同款）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.app.test_app import _env as _linear_env
from tests.app.test_app import _project
from tests.graph.test_executor import (
    _conditions,
    _design,
    _edge,
    _env,
    _PassStub,
    _ProducerStub,
)
from waterprint.app import run_full_calc
from waterprint.app_trust import DiagCollector
from waterprint.graph.executor import execute_graph
from waterprint.graph.nodes import builtin_unit
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
from waterprint.registry.effluent import load_effluent_standards

_REPO_DATA = Path(__file__).resolve().parents[3] / "data"
_LOOP_DEFAULTS = {
    item.key: item.default for item in DEFAULT_ASSUMPTIONS
    if item.key.startswith("loop.")
}


def _loop_design() -> object:
    """回路图（SCC 环：producer+pass1+pass2+rj）——test_executor 同款形状。"""
    return _design(
        nodes={
            "src": {"kind": "municipal_input", "q_avg_daily": 0.4023229167, "kz": 1.4},
            "producer": {},
            "pass1": {},
            "pass2": {},
            "rj": {"kind": "recycle_junction"},
        },
        edges=[
            _edge("src", "out", "producer", "in"),
            _edge("producer", "sludge_out", "pass1", "in"),
            _edge("pass1", "out", "pass2", "in"),
            _edge("pass2", "sup", "rj", "in", recycle=True),
            _edge("rj", "out", "producer", "in_r"),
        ],
    )


def _loop_units() -> dict[str, object]:
    """回路图单元表（src/rj=builtin + 三 stub——每用例新实例防可变串扰）。"""
    return {
        "src": builtin_unit(
            "municipal_input", {"q_avg_daily": 0.4023229167, "kz": 1.4}
        ),
        "producer": _ProducerStub(),
        "pass1": _PassStub(),
        "pass2": _PassStub(),
        "rj": builtin_unit("recycle_junction", {}),
    }


def test_diagnostics_on_linear_chain() -> None:
    """三单元链诊断：无回路 convergence 空+线性链闭合 0+空标准 effluent 空。"""
    bundle = run_full_calc(_project(), _conditions(), _linear_env())  # type: ignore[misc]
    diagnostics = bundle.diagnostics
    assert diagnostics.convergence == ()
    assert diagnostics.effluent == ()
    assert set(diagnostics.loop_params) == set(_LOOP_DEFAULTS)
    assert diagnostics.loop_params["loop.tolerance"] == _LOOP_DEFAULTS["loop.tolerance"]
    assert diagnostics.repro == bundle.repro
    for closure in diagnostics.mass_balance:
        water = next(line for line in closure.lines if line.fluid == "WATER")
        assert water.q_sources_total > 0.0
        # 直通链（格栅/沉砂不减量）：源汇恒等 → 厂级闭合差 0
        assert water.closure_rel == 0.0
        for item in closure.unit_imbalances:
            assert item.delta_rel == 0.0


def test_design_vs_avg_flow_case_fields() -> None:
    """工况取值口径（R1）：design 线取 q_design（×kz）、avg 线取 q_avg_daily。"""
    bundle = run_full_calc(_project(), _conditions(), _linear_env())  # type: ignore[misc]
    by_key = {item.condition_key: item for item in bundle.diagnostics.mass_balance}
    design = next(line for line in by_key["design"].lines if line.fluid == "WATER")
    avg = next(line for line in by_key["avg"].lines if line.fluid == "WATER")
    assert design.q_sources_total / avg.q_sources_total == pytest.approx(1.4)  # kz=1.4 直录


def test_effluent_margins_with_standards() -> None:
    """裕度投影：真源标准注入→summary 指标有则录；margin=(限值−值)/限值 手算对照。"""
    standards = load_effluent_standards(
        _REPO_DATA / "constraint_kb" / "constraints.json"
    )
    bundle = run_full_calc(
        _project(), _conditions(), _linear_env(), standards=standards  # type: ignore[misc]
    )
    entries = {
        (item.condition_key, item.standard_id, item.indicator): item
        for item in bundle.diagnostics.effluent
    }
    level_a = standards[0]
    design_value = bundle.plant.summary["design"]
    for indicator in ("BOD5", "CODCR", "SS"):
        entry = entries[("design", "gb18918.level_a", indicator)]
        value, limit = design_value[indicator], level_a.limits[indicator]
        assert entry.value == value and entry.limit == limit
        assert entry.margin == (limit - value) / limit
    # inlet 仅三指标（NH3N/TN/TP 缺）→有则录无则略（R5）
    assert ("design", "gb18918.level_a", "TP") not in entries


def test_loop_stats_collected_via_execute_graph() -> None:
    """回路统计采集：diag_sink 在场→每工况每回路组一条；收敛语义（残差<容差）。"""
    collector = DiagCollector()
    execute_graph(
        _loop_design(), _loop_units(), _conditions(),
        _env(), diag_sink=collector,  # type: ignore[arg-type]
    )
    assert collector.loops, "回路图必产回路统计"
    for stats in collector.loops:
        assert stats.iterations >= 1
        assert stats.final_residual < _LOOP_DEFAULTS["loop.tolerance"]
        assert set(stats.loop_nodes) >= {"producer", "rj"}
    assert {stats.condition_key for stats in collector.loops} == {"design", "avg"}


def test_diag_sink_none_keeps_behavior() -> None:
    """diag_sink 缺省（None）行为不变：四参正门照常产出（ADR-012 D3 回归锚）。"""
    plant = execute_graph(
        _loop_design(), _loop_units(), _conditions(), _env(),  # type: ignore[arg-type]
    )
    assert "design" in plant.conditions and "avg" in plant.conditions
