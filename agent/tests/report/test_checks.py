"""verify_report 数值锚定断言件测试（集成批 D8③ 消费面——TDD 先红）。"""

from __future__ import annotations

from pathlib import Path

from waterprint.app import load_project
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    TraceNode,
    UnitResultSnapshot,
)

from waterprint_agent.report.build import build_report_ast
from waterprint_agent.report.checks import CheckReport, verify_report
from waterprint_agent.report.render_md import render_markdown

# 断言下限常量（合成例统计面 / golden 实测锚定面 243）
_MIN_ANCHORS = 1
_MIN_LINES = 2
_MIN_GOLDEN_ANCHORS = 200


def _mini_plant() -> PlantResult:
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


def _rendered(golden_project_path: Path, *, fills: dict[str, str] | None = None) -> str:
    project = load_project(golden_project_path)
    ast = build_report_ast(project, _mini_plant())
    return render_markdown(ast, narrative_fills=fills)


class TestCleanPass:
    """干净文档——CheckReport.ok 为真且统计非零。"""

    def test_mini_report_passes(self, golden_project_path: Path) -> None:
        report = verify_report(_rendered(golden_project_path), _mini_plant())
        assert isinstance(report, CheckReport)
        assert report.ok, report.failures
        assert report.anchors_checked >= _MIN_ANCHORS
        assert report.lines_checked >= _MIN_LINES

    def test_clean_narrative_fill_passes(self, golden_project_path: Path) -> None:
        md = _rendered(
            golden_project_path,
            fills={
                "process_selection": "程序注入结论表明主线工艺成立，论证从略。",
                "layout_narrative": "布置遵循流程顺畅与近远期结合原则。",
            },
        )
        assert verify_report(md, _mini_plant()).ok


class TestAnchorTamper:
    """锚点篡改——逐面拒绝。"""

    def test_value_tamper_detected(self, golden_project_path: Path) -> None:
        md = _rendered(golden_project_path)
        assert "〔UF-F1〕" in md
        tampered = md.replace("5.0〔UF-F1〕", "5.5〔UF-F1〕", 1)
        if tampered == md:  # 形态兜底：不带单位的锚定行
            tampered = md.replace("：5.0 ", "：5.5 ", 1)
        report = verify_report(tampered, _mini_plant())
        assert not report.ok
        assert any("UF-F1" in failure for failure in report.failures)

    def test_unknown_formula_detected(self, golden_project_path: Path) -> None:
        md = _rendered(golden_project_path)
        tampered = md.replace("〔UF-F1〕", "〔GHOST-F9〕", 1)
        report = verify_report(tampered, _mini_plant())
        assert not report.ok
        assert any("GHOST-F9" in failure for failure in report.failures)

    def test_unanchored_bogus_value_detected(self, golden_project_path: Path) -> None:
        """未锚定数值行：值必须落在 serialize 值域内（伪造即拒）。"""
        md = _rendered(golden_project_path)
        tampered = md.replace("- 长宽比：2.5", "- 长宽比：9.9", 1) if "- 长宽比：2.5" in md else md
        if tampered == md:
            # 合成例中 dims d_ratio=0.25 无锚——伪造其值
            tampered = md.replace("0.25", "0.99", 1)
        report = verify_report(tampered, _mini_plant())
        assert not report.ok


class TestTableTamper:
    """表格数值盲区收口（门一 FIX-1/C2）——管道表行数值进断言面。

    ①表内锚定值〔公式ID〕→trace 等值；②plant 数据源表的无锚数值→
    serialize 值域全集（与值线同面）。合成锚定表注入验证 ①两面，进水
    水质/出水水质表（registered 数据源表）验证 ②幽灵值面。
    """

    _ANCHORED_TABLE = (
        "\n**合成锚定表**\n\n| 值 | 备注 |\n| --- | --- |\n"
        "| 5.0〔UF-F1〕 | 通过 |\n"
    )

    def test_table_anchored_value_tamper_detected(
        self, golden_project_path: Path
    ) -> None:
        """红证①：表内锚定值篡改（5.0→5.5 同公式 ID）必红。"""
        md = _rendered(golden_project_path) + self._ANCHORED_TABLE
        assert "| 5.0〔UF-F1〕 |" in md
        tampered = md.replace("| 5.0〔UF-F1〕 |", "| 5.5〔UF-F1〕 |", 1)
        report = verify_report(tampered, _mini_plant())
        assert not report.ok
        assert any("UF-F1" in failure and "表" in failure for failure in report.failures)

    def test_table_anchored_unknown_formula_detected(
        self, golden_project_path: Path
    ) -> None:
        """红证①附：表内锚点引未知公式 ID 必红。"""
        md = _rendered(golden_project_path) + self._ANCHORED_TABLE
        tampered = md.replace("〔UF-F1〕 |", "〔GHOST-F9〕 |", 1)
        report = verify_report(tampered, _mini_plant())
        assert not report.ok
        assert any("GHOST-F9" in failure for failure in report.failures)

    def test_table_ghost_value_detected(self, golden_project_path: Path) -> None:
        """红证②：plant 数据源表（出水水质）幽灵值必红（值域面·表）。"""
        md = _rendered(golden_project_path)
        assert "| BOD5 | 12.0 |" in md  # u_fake 出水水质表（design 档）
        tampered = md.replace("| BOD5 | 12.0 |", "| BOD5 | 99.5 |", 1)
        report = verify_report(tampered, _mini_plant())
        assert not report.ok
        assert any("serialize 值域" in failure and "表" in failure
                   for failure in report.failures)

    def test_table_anchor_matches_trace_passes(self, golden_project_path: Path) -> None:
        """干净面：锚定表值与 trace 等值→ok（含 table_cells_checked 统计）。"""
        md = _rendered(golden_project_path) + self._ANCHORED_TABLE
        report = verify_report(md, _mini_plant())
        assert report.ok, report.failures
        assert report.table_cells_checked >= 2  # 锚定表值+出水水质表数值面

    def test_golden_influent_quality_table_tamper_detected(
        self, golden_project_path: Path, golden_plant: PlantResult
    ) -> None:
        """golden 真源面：第 2 章进水水质表（评审示例盲区）篡改必红。"""
        project = load_project(golden_project_path)
        md = render_markdown(build_report_ast(project, golden_plant))
        row = next(
            line for line in md.splitlines() if line.startswith("| BOD5 |")
        )
        tampered = md.replace(row, "| BOD5 | 999.9 |", 1)
        report = verify_report(tampered, golden_plant)
        assert not report.ok
        assert any("serialize 值域" in failure for failure in report.failures)


class TestNarrativeGuard:
    """叙述段数字——validate_narrative 零违例面接入。"""

    def test_narrative_digit_detected(self, golden_project_path: Path) -> None:
        md = _rendered(
            golden_project_path,
            fills={"process_selection": "本方案共 3 组并列运行。"},
        )
        report = verify_report(md, _mini_plant())
        assert not report.ok
        assert any("narrative" in failure or "数字" in failure for failure in report.failures)

    def test_narrative_chinese_numeral_detected(
        self, golden_project_path: Path
    ) -> None:
        md = _rendered(
            golden_project_path,
            fills={"layout_narrative": "厂区共分三个台块布置。"},
        )
        report = verify_report(md, _mini_plant())
        assert not report.ok

    def test_narrative_ordinal_exemption_passes(
        self, golden_project_path: Path
    ) -> None:
        """序号豁免在叙述守卫同样生效。"""
        md = _rendered(
            golden_project_path,
            fills={"process_selection": "结论与第 4 章设计依据吻合。"},
        )
        assert verify_report(md, _mini_plant()).ok


class TestGoldenVerify:
    """golden municipal_34760 全量断言（skipif 数据缺失）。"""

    def test_golden_report_verifies(
        self, golden_project_path: Path, golden_plant: PlantResult
    ) -> None:
        project = load_project(golden_project_path)
        ast = build_report_ast(project, golden_plant)
        md = render_markdown(ast)
        report = verify_report(md, golden_plant)
        assert report.ok, report.failures[:5]
        assert report.anchors_checked >= _MIN_GOLDEN_ANCHORS
