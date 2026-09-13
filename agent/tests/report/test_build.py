"""build_report_ast 七章节装配测试（TDD 先红）。

两轨：合成最小 PlantResult（零外部数据依赖——CI 恒跑）+ golden
municipal_34760（一次性 result.json——缺失 skip）。
"""

from __future__ import annotations

import pytest
from waterprint.app import load_project
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    TraceNode,
    UnitResultSnapshot,
)
from waterprint.contracts.trust import DiagnosticsReport

from waterprint_agent.report.build import (
    Chapter,
    NarrativeSlot,
    NumberLine,
    ReportAST,
    build_report_ast,
)

# golden municipal_34760 实测下限（dims 总量 325、锚定量 243——主尺寸扩面
# 只增不减的钳制值，见 expected_summary.json design_dims 覆盖面）
_CHAPTER_COUNT = 7
_MIN_GOLDEN_DIM_LINES = 240
_MIN_GOLDEN_ANCHORED = 230
# 合成例锚定值（UF-F1 输出）
_ANCHOR_VALUE = 5.0


def _all_number_lines(ast: ReportAST) -> list[NumberLine]:
    """全树收集 NumberLine（含 Section 嵌套——第 4 章逐单元小节）。"""
    collected: list[NumberLine] = []
    stack = [block for chapter in ast for block in chapter.blocks]
    while stack:
        block = stack.pop(0)
        if isinstance(block, NumberLine):
            collected.append(block)
        elif hasattr(block, "blocks"):
            stack.extend(block.blocks)  # type: ignore[attr-defined]
    return collected


def _mini_plant() -> PlantResult:
    """合成最小结果：单单元单公式（锚定链最小闭环）。"""
    snapshot = UnitResultSnapshot(
        unit_id="u_fake",
        outflows={"u_fake.out.q": 0.5},
        outqualities={"u_fake.out.BOD5": 12.0},
        dims={"d_len": 5.0, "d_ratio": 0.25},
        warnings=(),
        formula_ids=("UF-F1",),
    )
    return PlantResult(
        conditions={"design": {"u_fake": snapshot}},
        summary={"design": {"BOD5": 12.0}},
        trace=(
            TraceNode(
                formula_id="UF-F1",
                inputs={"x": 2.5},
                output=5.0,
                norm_ref="GB 合成 §1",
                unit_id="u_fake",
                condition_key="design",
            ),
        ),
        repro=ReproTriple(
            design_hash="hash", engine_version="eng", data_version="dat"
        ),
    )


class TestSevenChapters:
    """七章节结构契约。"""

    def test_mini_build_has_seven_chapters_in_order(
        self, golden_project_path: object
    ) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast = build_report_ast(project, _mini_plant())
        assert isinstance(ast, tuple)
        ids = [chapter.id for chapter in ast]
        assert ids == [
            "design_basis",
            "flow_quality",
            "process_selection",
            "unit_calc",
            "layout",
            "estimate",
            "drawings",
        ]
        titles = [chapter.title for chapter in ast]
        assert titles[0] == "设计依据"
        assert titles[3] == "构筑物逐单元计算"

    def test_every_chapter_has_blocks(
        self, golden_project_path: object
    ) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast = build_report_ast(project, _mini_plant())
        for chapter in ast:
            assert chapter.blocks, f"章 {chapter.id} 空块非法"


class TestNumberLineAnchoring:
    """NumberLine 数字+单位+公式 ID 绑定。"""

    def test_mini_dims_anchored_to_trace(self, golden_project_path: object) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast = build_report_ast(project, _mini_plant())
        lines = _all_number_lines(ast)
        assert "d_len" in {line.label for line in lines}
        assert any(line.formula_id == "UF-F1" for line in lines)
        # 锚定值必与 trace 输出相等（同一公式）
        hit = next(line for line in lines if line.formula_id == "UF-F1")
        assert hit.value == pytest.approx(_ANCHOR_VALUE)
        # 合成例 u_fake 无 manifest 声明面 → 未知量纲回落空单位（不猜量纲）
        assert hit.unit == ""

    def test_untraceable_dim_rendered_without_fake_anchor(
        self, golden_project_path: object
    ) -> None:
        """无 trace 对应的 dims 值（d_ratio=0.25）禁止伪造锚点。"""
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast = build_report_ast(project, _mini_plant())
        lines = _all_number_lines(ast)
        ratio = next(line for line in lines if line.label == "d_ratio")
        assert ratio.formula_id == ""


class TestNarrativeSlots:
    """N3 叙述章槽位。"""

    def test_ch3_ch5_have_narrative_slots(
        self, golden_project_path: object
    ) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast: ReportAST = build_report_ast(project, _mini_plant())
        slots = [
            block
            for chapter in ast
            for block in chapter.blocks
            if isinstance(block, NarrativeSlot)
        ]
        slot_ids = {slot.slot_id for slot in slots}
        assert "process_selection" in slot_ids
        assert "layout_narrative" in slot_ids


class TestOptionalInputs:
    """diagnostics／estimate／layout 可缺省（集成批接线）。"""

    def test_defaults_are_none_friendly(self, golden_project_path: object) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast = build_report_ast(project, _mini_plant())  # 三参全缺省
        assert len(ast) == _CHAPTER_COUNT


class TestGoldenBuild:
    """golden municipal_34760 实数据装配（skipif 数据缺失）。"""

    def test_golden_chapter4_anchor_coverage(
        self, golden_project_path: object, golden_plant: PlantResult
    ) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        ast = build_report_ast(project, golden_plant)
        chapter4 = ast[3]
        assert isinstance(chapter4, Chapter)
        # 收集全部 NumberLine（含 Section 嵌套）
        stack = list(chapter4.blocks)
        lines: list[NumberLine] = []
        while stack:
            block = stack.pop()
            if isinstance(block, NumberLine):
                lines.append(block)
            elif hasattr(block, "blocks"):
                stack.extend(block.blocks)  # type: ignore[attr-defined]
        assert len(lines) >= _MIN_GOLDEN_DIM_LINES  # 325 项 dims 的主体
        anchored = [line for line in lines if line.formula_id]
        assert len(anchored) >= _MIN_GOLDEN_ANCHORED  # 243/325 实测锚定面
        # 锚定公式 ID 全部可在 plant.trace 查到
        trace_ids = {node.formula_id for node in golden_plant.trace}
        assert {line.formula_id for line in anchored} <= trace_ids
        # 锚定值与该公式 trace 输出逐项相等
        outputs_by_formula: dict[str, set[float]] = {}
        for node in golden_plant.trace:
            outputs_by_formula.setdefault(node.formula_id, set()).add(
                round(node.output, 10)
            )
        for line in anchored:
            assert round(line.value, 10) in outputs_by_formula[line.formula_id]

    def test_golden_diagnostics_feed_ch2_ch5(
        self, golden_project_path: object, golden_plant: PlantResult
    ) -> None:
        project = load_project(golden_project_path)  # type: ignore[arg-type]
        diag = DiagnosticsReport(
            convergence=(),
            loop_params={},
            mass_balance=(),
            effluent=(),
            repro=golden_plant.repro,
        )
        ast = build_report_ast(project, golden_plant, diagnostics=diag)
        assert len(ast) == _CHAPTER_COUNT  # 空诊断也合法
