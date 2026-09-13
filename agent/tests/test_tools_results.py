"""test_tools_results——结果组 #11~#16：摘要/诊断/单单元/迹切片/概算/布置。

输入:  tmp_path 沙箱（模块级单例——一次 wp_run_calc 供六工具复读）
输出:  stale 门/压缩形态/概算真值锚（m3_deferred）/布置聚合断言
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.tools import calc, projects, results

_M3_ANCHOR = Path(__file__).resolve().parents[2] / (
    "core/tests/golden/golden_data/municipal_34760/expected_summary.json"
)


@pytest.fixture(scope="module")
def sandbox() -> Path:
    """模块级沙箱：建项+算一次（六工具复读同一结果集）。"""
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="wp-results-")) / "sb"
    patch = pytest.MonkeyPatch()
    patch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    created = asyncio.run(projects.wp_create_project(name="结果组", seed="municipal_34760"))
    outcome = asyncio.run(calc.wp_run_calc(created["project_id"]))
    assert "error" not in outcome, outcome
    yield root
    patch.undo()
    context.reset_context()


@pytest.fixture(scope="module")
def pid(sandbox: Path) -> str:
    """模块级 project_id（沙箱内唯一项目文件——剥 .wp.json 后缀）。"""
    files = list((sandbox / "projects").glob("*.wp.json"))
    assert len(files) == 1
    return files[0].name.removesuffix(".wp.json")


def test_result_summary_compressed_form(sandbox: Path, pid: str) -> None:
    """#11：达标判定+逐单元一行+闭合偏差（≤1.5k token 口径的压缩面）。"""
    data = asyncio.run(results.wp_get_result_summary(pid))
    assert "error" not in data, data
    assert data["design_digest"] == data["design_digest"]
    eff = data["effluent_design"]
    assert eff and all({"indicator", "value", "limit", "margin", "compliant"} <= set(e) for e in eff)
    assert isinstance(data["compliant"], bool)
    assert len(data["units"]) == 19  # golden 19 节点（含 inlet 与泥线）
    assert all("unit_id" in u and "warnings" in u and "dims" in u for u in data["units"])
    assert data["mass_closure"] is not None


def test_result_summary_requires_calc(sandbox: Path) -> None:
    """#11 错误面：未算项目→提示先 wp_run_calc 的错误 dict。"""
    created = asyncio.run(projects.wp_create_project(name="未算", seed="blank"))
    data = asyncio.run(results.wp_get_result_summary(created["project_id"]))
    assert "error" in data and "wp_run_calc" in data["hint"]


def test_result_summary_stale_gate(sandbox: Path, pid: str) -> None:
    """stale 门：改参后旧结果→提示重算的错误 dict（result_schema R4）。"""
    changed = asyncio.run(
        projects.wp_update_params(
            pid, patches=[{"unit_id": "municipal_chenshachi", "key": "n", "value": 3.0}]
        )
    )
    assert changed["accepted_count"] == 1
    data = asyncio.run(results.wp_get_result_summary(pid))
    assert "error" in data and "重算" in data["error"]
    # 复原（n=2=golden 缺省）+重算——后续用例（概算 golden 锚）依赖原设计。
    asyncio.run(
        projects.wp_update_params(
            pid, patches=[{"unit_id": "municipal_chenshachi", "key": "n", "value": 2.0}]
        )
    )
    redo = asyncio.run(calc.wp_run_calc(pid))
    assert "error" not in redo


def test_diagnostics_three_sources(sandbox: Path, pid: str) -> None:
    """#12：warnings 六键清单+convergence/mass_balance/effluent 三源。"""
    data = asyncio.run(results.wp_get_diagnostics(pid))
    assert "error" not in data, data
    assert data["diagnostics_available"] is True
    assert data["convergence"] == []  # municipal_34760 无回路（直线型）
    assert data["mass_balance"] and data["effluent"]
    for warning in data["warnings"]:
        assert {"unit_id", "severity", "source", "message"} <= set(warning)
    assert isinstance(data["warning_counts"], dict)
    assert isinstance(data["loop_params"], dict)


def test_unit_detail_full_slice(sandbox: Path, pid: str) -> None:
    """#13：单单元全量切片（design 缺省+工况显式+未知面错误）。"""
    data = asyncio.run(results.wp_get_unit_detail(pid, "inlet"))
    assert "error" not in data, data
    assert data["condition_key"] == "design"
    assert "inlet.out.q_avg_daily" in data["outflows"]
    explicit = asyncio.run(
        results.wp_get_unit_detail(pid, "inlet", condition_key="avg")
    )
    assert explicit["condition_key"] == "avg"
    missing_unit = asyncio.run(results.wp_get_unit_detail(pid, "ghost_unit"))
    assert "error" in missing_unit
    missing_cond = asyncio.run(
        results.wp_get_unit_detail(pid, "inlet", condition_key="nope")
    )
    assert "error" in missing_cond


def test_trace_excerpt_filters(sandbox: Path, pid: str) -> None:
    """#14：迹切片——单元/公式过滤+limit 截断。"""
    data = asyncio.run(results.wp_get_trace_excerpt(pid, unit_id="municipal_aao"))
    assert "error" not in data, data
    assert data["returned"] <= data["total_matched"] > 0
    assert all(n["unit_id"] == "municipal_aao" for n in data["nodes"])
    limited = asyncio.run(
        results.wp_get_trace_excerpt(pid, unit_id="municipal_aao", limit=3)
    )
    assert limited["returned"] == 3
    formula = data["nodes"][0]["formula_id"]
    by_formula = asyncio.run(results.wp_get_trace_excerpt(pid, formula_id=formula))
    assert by_formula["nodes"] and all(
        n["formula_id"] == formula for n in by_formula["nodes"]
    )


def test_estimate_summary_matches_golden_m3(sandbox: Path, pid: str) -> None:
    """#15：概算摘要——grand_total 与 golden m3_deferred 真值（1e-12 双容差）。"""
    data = asyncio.run(results.wp_get_estimate_summary(pid))
    assert "error" not in data, data
    expected = json.loads(_M3_ANCHOR.read_text(encoding="utf-8"))["m3_deferred"]
    anchor = expected["estimate_total"]
    assert data["grand_total"] == pytest.approx(
        anchor["value"], rel=anchor["rel"], abs=anchor["abs"]
    )
    levels = data["levels"]
    assert levels["grand_total"] == data["grand_total"]
    assert levels["subtotal"] < levels["grand_total"]
    assert isinstance(data["indicators"], list) and data["checked"] in (True, False)


def test_layout_summary_aggregates(sandbox: Path, pid: str) -> None:
    """#16：elevation/scene 聚合——纵断站位+提升泵站+场景节点（K8 压缩面）。"""
    data = asyncio.run(results.wp_get_layout_summary(pid))
    assert "error" not in data, data
    assert data["condition_key"] == "design"
    assert len(data["stations"]) == 18  # 纵断站位=19 节点去 inlet（进水无池体）
    assert all({"unit_id", "water_level", "crest_elev"} <= set(s) for s in data["stations"])
    assert isinstance(data["pump_stations"], list)
    assert data["scene"]["node_count"] > 0
    assert data["datum_note"]
    explicit = asyncio.run(
        results.wp_get_layout_summary(pid, condition_key="avg")
    )
    assert explicit["condition_key"] == "avg"


def test_estimate_bad_condition_is_error(sandbox: Path, pid: str) -> None:
    """#15 错误面：未知工况→错误 dict（estimate_summary_flow 领域异常收编）。"""
    data = asyncio.run(results.wp_get_estimate_summary(pid, condition_key="nope"))
    assert "error" in data
