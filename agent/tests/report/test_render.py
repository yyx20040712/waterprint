"""render_markdown 渲染测试（两段式管线第二段——TDD 先红）。"""

from __future__ import annotations

from pathlib import Path

from waterprint.app import load_project
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    TraceNode,
    UnitResultSnapshot,
)

from waterprint_agent.report.build import (
    Chapter,
    NarrativeSlot,
    NumberLine,
    ReportAST,
    TableBlock,
    build_report_ast,
)
from waterprint_agent.report.render_md import render_markdown


def _mini_plant() -> PlantResult:
    snapshot = UnitResultSnapshot(
        unit_id="u_fake",
        outflows={},
        outqualities={"u_fake.out.BOD5": 12.0},
        dims={"d_len": 5.0},
        warnings=(),
        formula_ids=("UF-F1",),
    )
    return PlantResult(
        conditions={"design": {"u_fake": snapshot}},
        summary={"design": {"BOD5": 12.0}},
        trace=(
            TraceNode(
                formula_id="UF-F1",
                inputs={},
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


def _mini_ast(golden_project_path: Path) -> ReportAST:
    project = load_project(golden_project_path)
    return build_report_ast(project, _mini_plant())


class TestNumberLineForm:
    """NumberLine →「{label}：{value} {unit}〔{formula_id}〕」形态。"""

    def test_anchored_line_form(self) -> None:
        line = NumberLine(
            label="好氧区容积", value=10823.1784546467, unit="m3", formula_id="AO-F1"
        )
        md = render_markdown((Chapter("c", "样章", (line,)),))
        assert "- 好氧区容积：10823.1784546467 m3〔AO-F1〕" in md

    def test_unanchored_line_omits_bracket(self) -> None:
        line = NumberLine(label="长宽比", value=2.5, unit="", formula_id="")
        md = render_markdown((Chapter("c", "样章", (line,)),))
        assert "- 长宽比：2.5" in md
        assert "〔" not in md.split("溯源索引")[0]


class TestNarrativeSlotRender:
    """NarrativeSlot → 占位/回填 + 叙述标记。"""

    def test_default_placeholder(self) -> None:
        slot = NarrativeSlot(slot_id="process_selection", hint="围绕已注入结论论证")
        md = render_markdown((Chapter("c", "样章", (slot,)),))
        assert "（本段由 AI 撰写——见管线说明）" in md
        assert "<!-- narrative:process_selection -->" in md
        assert "<!-- /narrative -->" in md

    def test_fill_from_mapping(self) -> None:
        slot = NarrativeSlot(slot_id="process_selection", hint="围绕已注入结论论证")
        md = render_markdown(
            (Chapter("c", "样章", (slot,)),),
            narrative_fills={"process_selection": "本方案以 AA 工艺为核心论证。"},
        )
        assert "本方案以 AA 工艺为核心论证。" in md
        assert "（本段由 AI 撰写——见管线说明）" not in md

    def test_extra_fill_ignored(self) -> None:
        slot = NarrativeSlot(slot_id="a", hint="h")
        md = render_markdown(
            (Chapter("c", "样章", (slot,)),), narrative_fills={"unknown": "无关"}
        )
        assert "无关" not in md


class TestTraceIndex:
    """末尾溯源索引：数字 → 公式 ID。"""

    def test_trace_index_appended(self, golden_project_path: Path) -> None:
        md = render_markdown(_mini_ast(golden_project_path))
        assert "溯源索引" in md
        appendix = md.split("溯源索引", 1)[1]
        assert "UF-F1" in appendix
        assert "5.0" in appendix

    def test_table_renders_pipe_rows(self) -> None:
        table = TableBlock(
            title="进水水质",
            headers=("指标", "进水值"),
            rows=(("BOD5", "200.0"),),
        )
        md = render_markdown((Chapter("c", "样章", (table,)),))
        assert "| 指标 | 进水值 |" in md
        assert "| BOD5 | 200.0 |" in md


class TestDeterminism:
    """同 AST 双渲染字节级相同（确定性纪律）。"""

    def test_double_render_identical(self, golden_project_path: Path) -> None:
        ast = _mini_ast(golden_project_path)
        assert render_markdown(ast) == render_markdown(ast)

    def test_chapter_headings_numbered(self, golden_project_path: Path) -> None:
        md = render_markdown(_mini_ast(golden_project_path))
        assert "## 第 1 章 设计依据" in md
        assert "## 第 7 章 附图" in md


class TestPlaceholderChapters:
    """estimate／layout 缺省 →「数据待接线」占位（可见于渲染面）。"""

    def test_estimate_layout_placeholders(self, golden_project_path: Path) -> None:
        md = render_markdown(_mini_ast(golden_project_path))
        assert "数据待接线" in md
