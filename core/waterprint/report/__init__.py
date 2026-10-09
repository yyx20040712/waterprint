"""report 包正门（设计说明书管线，两段式 AST→渲染；B6 批自 agent 移植 core）。

路径:   waterprint/report/
职责:   build（章节 AST 装配——NumberLine 绑定数字+单位+公式 ID+附录
        公式溯源）→render_md（Markdown 渲染＋首现数学块＋溯源索引）＋
        render_typst（Typst 排版源渲染——B6 PDF 路，引擎中立渲染器面）；
        anchors（N3 叙述章数字守卫）；checks（verify_report 数值锚定
        断言件——集成批 e2e 面）；formula_printers（公式双打印机——
        LaTeX/Typst math 双态，引擎中立单源）。
输入:   无（纯再导出聚合面——消费包内七子模块公开名）。
输出:   说明书管线公开接口二十六名（agent MCP 工具 #21 与 server 服务面
        消费——B6 起 report 居 core，agent 改 import 本包；跨包只走正门）。
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
    FormulaCatalog,
    FormulaSource,
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
from waterprint.report.formula_printers import (
    LatexPrinter,
    TypstMathPrinter,
    latex_of_expression,
    to_latex,
    to_typst_math,
    typst_of_expression,
)
from waterprint.report.render_md import render_markdown
from waterprint.report.render_typst import render_typst

__all__ = [
    "Chapter",
    "CheckReport",
    "EstimateRowLike",
    "EstimateSheetLike",
    "FigureRef",
    "FormulaCatalog",
    "FormulaSource",
    "InvalidReportError",
    "LatexPrinter",
    "NarrativeSlot",
    "NarrativeViolation",
    "NoteLine",
    "NumberLine",
    "ReportAST",
    "Section",
    "TableBlock",
    "TypstMathPrinter",
    "build_report_ast",
    "latex_of_expression",
    "render_markdown",
    "render_typst",
    "to_latex",
    "to_typst_math",
    "typst_of_expression",
    "validate_narrative",
    "verify_report",
]
