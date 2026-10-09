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
from waterprint.report.build import (
    Chapter,
    NarrativeSlot,
    NumberLine,
    ReportAST,
    TableBlock,
    build_report_ast,
)
from waterprint.report.render_md import render_markdown


def _mini_plant() -> PlantResult:
    snapshot = UnitResultSnapshot(
        unit_id="u_fake",
        outflows={},
        outqualities={"u_fake.out.BOD5": 12.0},
        dims={"d_len": 5.0},
        warnings=(),
        formula_ids=("TS-F4",),
    )
    return PlantResult(
        conditions={"design": {"u_fake": snapshot}},
        summary={"design": {"BOD5": 12.0}},
        trace=(
            TraceNode(
                formula_id="TS-F4",
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
        assert "（本段由撰写管线生成——见管线说明）" in md
        assert "<!-- narrative:process_selection -->" in md
        assert "<!-- /narrative -->" in md

    def test_fill_from_mapping(self) -> None:
        slot = NarrativeSlot(slot_id="process_selection", hint="围绕已注入结论论证")
        md = render_markdown(
            (Chapter("c", "样章", (slot,)),),
            narrative_fills={"process_selection": "本方案以 AA 工艺为核心论证。"},
        )
        assert "本方案以 AA 工艺为核心论证。" in md
        assert "（本段由撰写管线生成——见管线说明）" not in md

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
        assert "TS-F4" in appendix
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
        assert "## 附录 公式溯源" in md  # B6：附录章不占章号


class TestMathBlocks:
    """B6 数学块：NumberLine 首现公式处「$$LaTeX$$」展示块+条文中号。"""

    def test_math_display_block_at_first_occurrence(
        self, golden_project_path: Path
    ) -> None:
        md = render_markdown(_mini_ast(golden_project_path))
        assert "$$" in md
        # 展示块配对：$$ 行计数为偶
        fences = [line for line in md.splitlines() if line.strip() == "$$"]
        assert len(fences) >= 2 and len(fences) % 2 == 0
        # 条文中号随展示块在场（norm_ref 来自 registry spec——非 trace 合成值）
        assert "（公式 TS-F4" in md

    def test_first_occurrence_dedup(self) -> None:
        from waterprint.report.blocks import FormulaCatalog, FormulaSource

        catalog = FormulaCatalog(
            rows=(
                FormulaSource(
                    formula_id="F-1", latex="a = b + c", norm_ref="合成 §1",
                    symbols_note="a：甲；b：乙",
                ),
            )
        )
        line1 = NumberLine(label="甲", value=1.0, unit="m", formula_id="F-1")
        line2 = NumberLine(label="乙", value=2.0, unit="m", formula_id="F-1")
        plain = NumberLine(label="丙", value=3.0, unit="", formula_id="")
        md = render_markdown(
            (Chapter("c", "样章", (line1, line2, plain, catalog)),)
        )
        assert md.count("（公式 F-1") == 1  # 首现去重：展示块恰一次
        assert md.count("$$") == 2  # 恰一对围栏（附录表内 LaTeX 不算块）

    def test_unknown_formula_gets_no_math_block(self) -> None:
        line = NumberLine(label="甲", value=1.0, unit="", formula_id="GHOST-F9")
        md = render_markdown((Chapter("c", "样章", (line,)),))
        assert "$$" not in md  # 目录外公式不渲染展示块（附录亦无此行）

    def test_appendix_pipe_latex_substituted_as_vert(self) -> None:
        """B6 笔5 主控裁定修正锚：含竖线 LaTeX 附录单元格=\\vert 替代形。

        \\| 表格转义在 LaTeX 数学域=‖ 双竖线（范数形）——绝对值渲染失真
        （HB-F11/HB-F13 两式实录）；\\vert 数学语义与 | 恒等。首现 $$ 展示
        块在表格外保持裸 | 原形（零转义面——KaTeX 直渲染正确）。
        """
        from waterprint.report.blocks import FormulaCatalog, FormulaSource

        catalog = FormulaCatalog(
            rows=(
                FormulaSource(
                    formula_id="P-1",
                    latex=r"x = \left|{a - b}\right|",
                    norm_ref="合成 §2",
                    symbols_note="a：甲；b：乙",
                ),
            )
        )
        line = NumberLine(label="甲", value=1.0, unit="", formula_id="P-1")
        md = render_markdown((Chapter("c", "样章", (line, catalog)),))
        row = next(t for t in md.splitlines() if t.startswith("| P-1 |"))
        assert r"\left\vert" in row and r"\right\vert" in row  # 附录替代形
        assert r"\left\|" not in row  # ‖ 失真形禁现
        block = next(
            t for t in md.splitlines() if t.startswith("x = \\left|")
        )
        assert block == r"x = \left|{a - b}\right|"  # 展示块裸 | 原形保持

    def test_appendix_table_rendered(self, golden_project_path: Path) -> None:
        md = render_markdown(_mini_ast(golden_project_path))
        assert "| 公式 ID | LaTeX | 条文号 | 符号释义 |" in md
        row = next(line for line in md.splitlines() if line.startswith("| TS-F4 |"))
        # B6 笔5 主控裁定修正：附录 LaTeX 列=行内数学定界（$...$——与
        # render_typst 附录 math 列同源同形；裸串形态退役，源码级溯源归
        # audit HTML 承载）
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        assert cells[1].startswith("$") and cells[1].endswith("$")
        assert r"\sqrt" in cells[1]  # TS-F4 实式含根式（LaTeX 打印机输出）
        assert "d_{pipe" in cells[1]  # 多词符号下标级联（LaTeX 形态契约）
        assert "单泵流量" in row  # 符号释义（symbols 中文含义）


class TestPlaceholderChapters:
    """estimate／layout 缺省 →「数据待接线」占位（可见于渲染面）。"""

    def test_estimate_layout_placeholders(self, golden_project_path: Path) -> None:
        md = render_markdown(_mini_ast(golden_project_path))
        assert "数据待接线" in md


class TestAppendixVertPrecise:
    """N5-d1（R1 采纳廉价件）：\\vert 盲替换改精确——\\left|/\\right|/裸 |
    三形各归其位；\\|（范数双竖线）→\\Vert 语义形（禁盲替换产行断裂
    畸变——未来 \\| 入库面防）。"""

    def test_left_right_delimiters(self) -> None:
        from waterprint.report.render_md import _appendix_math_cell

        assert (
            _appendix_math_cell(r"x = \left|{a - b}\right|")
            == r"$x = \left\vert{a - b}\right\vert$"
        )

    def test_bare_pipe(self) -> None:
        from waterprint.report.render_md import _appendix_math_cell

        assert _appendix_math_cell(r"|x|") == r"$\vert x \vert$"

    def test_double_pipe_norm_not_distorted(self) -> None:
        from waterprint.report.render_md import _appendix_math_cell

        assert _appendix_math_cell(r"\|x\|") == r"$\Vert x \Vert$"

    def test_three_forms_combined(self) -> None:
        from waterprint.report.render_md import _appendix_math_cell

        out = _appendix_math_cell(r"\left| a \right| + \|b\| + |c|")
        assert (
            out == r"$\left\vert a \right\vert + \Vert b \Vert + \vert c \vert$"
        )
        assert "|" not in out  # 替身后单元格零裸竖线（表格转义零触发）
