"""report 包正门（设计说明书管线，两段式 AST→渲染；B6 批自 agent 移植 core）。

路径:   waterprint/report/
职责:   build（七章节 AST 装配——NumberLine 绑定数字+单位+公式 ID）→
        render_md（Markdown 渲染＋溯源索引）；anchors（N3 叙述章数字
        守卫）；checks（verify_report 数值锚定断言件——集成批 e2e 面）。
输入:   无（纯再导出聚合面——消费包内五子模块公开名）。
输出:   说明书管线公开接口十五名（agent MCP 工具 #21 与 server 服务面
        消费——B6 起 report 居 core，agent 改 import 本包）。
禁区:   包内禁 import server／fastmcp／waterprint_agent（L4 消费位只向
        下：waterprint.app 正门+waterprint.contracts.*+registry 只读
        ——ADR-020/022 分层契约沿承，B6 移植改写 core 视角）。
"""

from waterprint.report.anchors import NarrativeViolation, validate_narrative
from waterprint.report.build import (
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
from waterprint.report.checks import CheckReport, verify_report
from waterprint.report.render_md import render_markdown

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
