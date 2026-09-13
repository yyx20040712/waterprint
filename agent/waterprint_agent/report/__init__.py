"""report 包正门（AI1 战役轨道丙——设计说明书管线，两段式 AST→渲染）。

路径:   waterprint_agent/report/
职责:   build（七章节 AST 装配——NumberLine 绑定数字+单位+公式 ID）→
        render_md（Markdown 渲染＋溯源索引）；anchors（N3 叙述章数字
        守卫）；checks（verify_report 数值锚定断言件——集成批 e2e 面）。
禁区:   包内禁 import server／fastmcp／core L1-L3（只许 waterprint.app
        正门与 waterprint.contracts.*——ADR-020/022 分层契约）。
"""

from waterprint_agent.report.anchors import NarrativeViolation, validate_narrative
from waterprint_agent.report.build import (
    Chapter,
    EstimateRowLike,
    EstimateSheetLike,
    FigureRef,
    InvalidReportError,
    NarrativeSlot,
    NoteLine,
    NumberLine,
    ReportAST,
    Section,
    TableBlock,
    build_report_ast,
)
from waterprint_agent.report.checks import CheckReport, verify_report
from waterprint_agent.report.render_md import render_markdown

__all__ = [
    "Chapter",
    "CheckReport",
    "EstimateRowLike",
    "EstimateSheetLike",
    "FigureRef",
    "InvalidReportError",
    "NarrativeSlot",
    "NarrativeViolation",
    "NoteLine",
    "NumberLine",
    "ReportAST",
    "Section",
    "TableBlock",
    "build_report_ast",
    "render_markdown",
    "validate_narrative",
    "verify_report",
]
