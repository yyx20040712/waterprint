"""市政污水 golden 端到端（34,760 m³/d，一级 A；M2 验收）。

输入:  golden_data/municipal_34760/{input_project.json, expected_summary.json}
输出:  全流程与实跑期望值对照断言（5 工况终水逐项+design 档主尺寸+
       计算书导出+2+k 工况索引——GOLDEN 批激活，2026-08-26）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M2 验收 = 13 单元全线 + 汇流 + 高程 + 枚举诊断端到端出全套
# 计算书；期望值来源 docs/norms 手算对照与旧系统结果（差异逐条解释，
# 由领域专家签字后录入 golden_data——实现者不得自编）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (Path(__file__).parent / "golden_data" / "municipal_34760" / "expected_summary.json").is_file(),
        reason="golden 数据未整理（M0 §9.4：34,760 m³/d 案例由领域专家录入）",
    ),
]

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_TERMINAL = "municipal_bashi_jiliangcao"


def _calcbook_min_template_renders(
    plant: Any, expected: dict[str, Any], tmp_path: Path
) -> None:
    """④ 计算书导出面：最小模板 trace/summary 两族占位符各≥1，全展开零残留。

    executor summary={} 现状（D10 冲突记档）——summary 取值=本实跑 design 档
    终水六指标（真值经 replace 注入 summary 面，非编造数字）。
    """
    from openpyxl import Workbook, load_workbook

    from waterprint.app import export_artifact

    summary_view = {
        indicator: plant.conditions["design"][_TERMINAL].outqualities[
            f"{_TERMINAL}.out.{indicator}"
        ]
        for indicator in expected["effluent"]["design"]
    }
    book_plant = replace(plant, summary={"design": summary_view})
    template = tmp_path / "calcbook_tpl.xlsx"
    workbook = Workbook()
    workbook.active["A1"] = "{{trace[0].formula_id}}"
    workbook.active["B1"] = "BOD5={{summary.design.BOD5}}"
    workbook.save(template)
    payload = export_artifact(
        "calcbook", book_plant, template, tmp_path / "calcbook_out.xlsx"
    )
    assert payload  # 产出非空（渲染成功即无 InvalidTemplateError）
    sheet = load_workbook(tmp_path / "calcbook_out.xlsx").active
    assert sheet["A1"].value == plant.trace[0].formula_id  # trace 占位符→实跑迹真值
    assert sheet["B1"].value == f"BOD5={summary_view['BOD5']}"  # summary 占位符→实跑值
    assert "{{" not in f"{sheet['A1'].value}{sheet['B1'].value}"  # 零残留


def test_municipal_golden_end_to_end(golden_data_dir: Path, tmp_path: Path) -> None:
    """端到端：run_full_calc 5 工况终水逐项+主尺寸+计算书导出对照期望（双容差禁放宽）。

    占位实质化（GOLDEN 批总授权"占位实质化"先例，2026-08-26）：原占位
    raise 的语义全部承载——①正门跑 input_project（5 工况全）②逐工况逐项
    对照 expected（rel/abs 1e-12 双容差按 expected 内标注）③主尺寸逐项
    对照 ④计算书导出（最小模板占位符全展开）⑤工况集 2+k 索引断言
    （iter_all 键集恰等 5 预期）。
    """
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    case_dir = golden_data_dir / "municipal_34760"
    project = load_project(case_dir / "input_project.json")
    expected = json.loads(
        (case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )

    # ⑤ 工况集 2+k 索引（ADR-007：基线两档+每受检单元一条，键集恰等预期）
    conditions = build_condition_set(expected["checked_units"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == expected["condition_keys"]
    assert len(keys) == 2 + len(expected["checked_units"]) == 5

    # ① 正门实跑（env 口径=expected.generated 实录：server 正门版本串）
    lib = load_coefficients(_REPO_DATA)
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    plant = run_full_calc(project, conditions, env).plant
    assert set(plant.conditions) == set(keys)  # 全 5 工况各出整图结果
    assert plant.repro.design_hash == project.metadata.content_hash  # 结果绑定输入

    # ② 逐工况逐项终水对照（双容差按 expected 内标注——不放宽）
    # 键集钳制（GOLDEN R1-2）：expected 工况块恰等 5 工况键集，防删块静默绿
    assert set(expected["effluent"]) == set(keys)
    for condition_key, fields in expected["effluent"].items():
        snapshot = plant.conditions[condition_key][_TERMINAL]
        for indicator, item in fields.items():
            actual = snapshot.outqualities[f"{_TERMINAL}.out.{indicator}"]
            assert actual == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"终水 {condition_key}.{indicator}"

    # ③ design 档主尺寸逐项对照（每 unit 主控项，容差同上）
    # 单元覆盖钳制（GOLDEN R1-2）：design_dims 恰覆盖十二节点减 inlet
    assert set(expected["design_dims"]) == set(project.design.nodes) - {"inlet"}
    for unit_id, fields in expected["design_dims"].items():
        dims = plant.conditions["design"][unit_id].dims
        for field, item in fields.items():
            assert dims[field] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"主尺寸 {unit_id}.{field}"

    # M3 面不造假：概算总数/全厂总泥量缺席占位（字串标"M3 补录"，禁数值）
    for deferred_key, marker in expected["m3_deferred"].items():
        assert isinstance(marker, str) and "M3" in marker, deferred_key

    _calcbook_min_template_renders(plant, expected, tmp_path)
