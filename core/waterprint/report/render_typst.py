"""Typst 渲染器：ReportAST → Typst 源（A4/页眉页脚/表格/数学——B6 PDF 路）。

路径:   waterprint/report/render_typst.py
职责:   章节树渲染为 Typst 排版源（PDF 计算书编译输入）：A4 页面+
        页眉〔{项目名}·计算书〕+页脚页码 numbering+Times New Roman/SimSun
        字体声明+TableBlock→Typst table（字符串单元格零标记解释）+
        NumberLine 行（首现公式展示块=Typst display math）+NarrativeSlot/
        NoteLine/FigureRef+公式溯源附录（公式列=Typst math）+溯源索引。
        确定性输出（无时钟/无随机——同 AST 双渲染字节级相同，render_md
        同纪律）。内容文本一律经字符串字面量通道（#"…" 形）——零标记
        解释（符号释义/标题多下划线面实测：标记上下文 _ 配对会误强调）。
输入:   ReportAST+标题/页眉项目名（本包 build 的 AST 类型+registry
        by_id 只读——公式 Typst math 经 formula_printers 单源打印机）。
输出:   Typst 源字符串（server exports report_pdf 编排消费→typst CLI
        编译 PDF；golden 快照=Typst 源字节对账面）。
禁区:   禁 import server／fastmcp／waterprint_agent 与内核 L3/L2/L1
        （只许包内 blocks/formula_printers+registry 只读——build.py 同边域）；
        禁 IO——纯函数；禁时钟/随机（确定性纪律）。
引擎中立申报（任务书 §二.⑥ DoD）：本件=「AST→排版源」渲染器接口的
        Typst 实现；Tectonic（LaTeX 编译器）=同接口另一实现（复用
        formula_printers 的 LaTeX 串——KaTeX/数学块同源），换引擎=换
        渲染器不动 AST（AST 与渲染源严格两层，Typst 排版语义零入 AST）。
确定性边界：Typst **源**字节确定（对账面）；PDF 二进制含引擎时间戳
        =引擎行为，不入字节对账面（简报明示）。
参照:   render_md.py（对位渲染器+首现数学块/溯源索引纪律同源）；
        .workflow/b6-20261009/ 前置#1 冒烟实录（typst 0.15.1——
        A4/页眉页脚/table/CJK/数学块全过）。
"""

from __future__ import annotations

from waterprint.registry import by_id
from waterprint.report.blocks import (
    FigureRef,
    FormulaCatalog,
    FormulaSource,
    NarrativeSlot,
    NoteLine,
    NumberLine,
    ReportAST,
    Section,
    TableBlock,
)
from waterprint.report.formula_printers import typst_of_expression

__all__ = ["render_typst"]

# 叙述槽标记（Typst 注释形态——md 侧 HTML 注释同位协议；溯源用非渲染）
_NARRATIVE_OPEN = "// narrative:{slot_id}"
_NARRATIVE_CLOSE = "// /narrative"

# 叙述槽缺省占位（render_md 同款管线约定文案——自身零数字）
_NARRATIVE_PLACEHOLDER = "（本段由撰写管线生成——见管线说明）"

# 文档导语（render_md 头部引言同文——两渲染器同源）
_INTRO_NOTE = (
    "本说明书由 WaterPrint 设计说明书管线生成：计算章（第 2／4／6 章）"
    "数值全部由程序自计算迹锚定回填，不经撰写环节；叙述章（第 3／5 章）"
    "由撰写管线承接程序已注入的结论撰写，正文禁新增数字（后检守卫）。"
)

_DEFAULT_TITLE = "污水处理厂设计说明书"
_DEFAULT_PROJECT_LABEL = "污水处理厂"


def _esc(text: str) -> str:
    """内容文本 → Typst 代码模式字符串字面量（仅 \\ 与 \" 转义+换行压空格）。

    字符串字面量在 Typst 中零标记解释（_ * # $ [ ] 皆字面）——一切内容
    文本经此通道免标记注入（#"…" 形消费；符号释义/标题多下划线面实测：
    标记上下文 _ 配对会误强调）。
    """
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _text(text: str) -> str:
    """内容文本 → 字符串表达式行（#"…" 形——markup 中插入字符串字面量）。"""
    return f'#"{_esc(text)}"'


def _fmt(value: float) -> str:
    """数值渲染（render_md._fmt 同源：str(float) 最短往返表示）。"""
    return str(float(value))


def _formula_sources(ast: ReportAST) -> dict[str, FormulaSource]:
    """AST 内 FormulaCatalog 全集 → formula_id → 溯源条目（render_md 同源）。"""
    sources: dict[str, FormulaSource] = {}
    for chapter in ast:
        for block in chapter.blocks:
            if isinstance(block, FormulaCatalog):
                for row in block.rows:
                    sources.setdefault(row.formula_id, row)
    return sources


def _typst_table(block: TableBlock) -> list[str]:
    """TableBlock → 加粗标题行+#table（columns 计数+table.header 首行）。"""
    header = ", ".join(f'"{_esc(h)}"' for h in block.headers)
    cells = [f"  table.header({header}),"]
    cells.extend(f'  "{_esc(cell)}",' for row in block.rows for cell in row)
    return [
        f'#strong("{_esc(block.title)}")',
        "",
        "#table(",
        f"  columns: {len(block.headers)},",
        *cells,
        ")",
    ]


def _math_lines(source: FormulaSource, math: str) -> list[str]:
    """公式展示块：Typst display math+条文中号行（md $$ 块对位）。"""
    return [
        f"$ {math} $",
        "",
        _text(f"（公式 {source.formula_id}——条文出处：{source.norm_ref}）"),
    ]


def _catalog_table(block: FormulaCatalog, math_of: dict[str, str]) -> list[str]:
    """公式溯源附录表：公式列=Typst math 单元格（§二.⑥ to_typst_math 输出面）。"""
    headers = ("公式 ID", "公式", "条文号", "符号释义")
    header = ", ".join(f'"{_esc(h)}"' for h in headers)
    lines = [
        '#strong("公式溯源全表（项目公式全集）")',
        "",
        "#table(",
        f"  columns: {len(headers)},",
        f"  table.header({header}),",
    ]
    for row in block.rows:
        lines.append(f'  "{_esc(row.formula_id)}",')
        lines.append(f"  [$ {math_of.get(row.formula_id, '')} $],")
        lines.append(f'  "{_esc(row.norm_ref)}",')
        lines.append(f'  "{_esc(row.symbols_note)}",')
    lines.append(")")
    return lines


def _trace_index(ast: ReportAST) -> list[str]:
    """溯源索引表（数字 → 公式 ID——render_md 同源收集序与文案）。"""
    entries: dict[str, dict[str, str]] = {}

    def _collect(line: NumberLine, location: str) -> None:
        if not line.formula_id:
            return
        key = _fmt(line.value)
        entry = entries.setdefault(key, {"formulas": "", "location": location})
        if line.formula_id not in entry["formulas"].split("、"):
            entry["formulas"] = (
                f"{entry['formulas']}、{line.formula_id}"
                if entry["formulas"]
                else line.formula_id
            )

    chapter_no = 0
    for chapter in ast:
        if not chapter.numbered:
            continue
        chapter_no += 1
        chapter_location = f"第 {chapter_no} 章"
        for section_no, block in enumerate(chapter.blocks, start=1):
            if isinstance(block, Section):
                location = f"{chapter_location} {chapter_no}.{section_no}"
                for inner in block.blocks:
                    if isinstance(inner, NumberLine):
                        _collect(inner, location)
            elif isinstance(block, NumberLine):
                _collect(block, chapter_location)
    table = TableBlock(
        title="数字溯源",
        headers=("数字", "公式 ID", "首现位置"),
        rows=tuple(
            (value, info["formulas"], info["location"])
            for value, info in entries.items()
        ),
    )
    return [
        '= #("附录 溯源索引（数字 → 公式 ID）")',
        "",
        _text(
            "锚定数字与计算迹（trace）同公式输出逐项相等；公式表达式／符号／"
            "输入快照详见「附录 公式溯源」全表。"
        ),
        "",
        *_typst_table(table),
    ]


def _render_block(
    block: object,
    formulas: dict[str, FormulaSource],
    math_of: dict[str, str],
    emitted: set[str],
) -> list[str]:
    """单块渲染分发（块间空行分隔——首现公式展示块前置，render_md 同纪律）。"""
    if isinstance(block, TableBlock):
        return [*_typst_table(block), ""]
    if isinstance(block, NumberLine):
        lines: list[str] = []
        if (
            block.formula_id
            and block.formula_id in formulas
            and block.formula_id not in emitted
        ):
            emitted.add(block.formula_id)
            lines.extend(
                _math_lines(formulas[block.formula_id], math_of[block.formula_id])
            )
            lines.append("")
        unit_part = f" {block.unit}" if block.unit else ""
        anchor_part = f"〔{block.formula_id}〕" if block.formula_id else ""
        body = f"{block.label}：{_fmt(block.value)}{unit_part}{anchor_part}"
        lines.append(f"- {_text(body)}")  # 列表标记在外，字符串字面量在内
        return [*lines, ""]
    if isinstance(block, NarrativeSlot):
        return [
            f'#quote("{_esc(f"撰写要点：{block.hint}")}")',
            "",
            _NARRATIVE_OPEN.format(slot_id=block.slot_id),
            "",
            _text(_NARRATIVE_PLACEHOLDER),
            "",
            _NARRATIVE_CLOSE,
            "",
        ]
    if isinstance(block, FigureRef):
        return [_text(f"附图：{block.caption}（{block.name}）"), ""]
    if isinstance(block, NoteLine):
        return [_text(block.text), ""]
    if isinstance(block, FormulaCatalog):
        return [*_catalog_table(block, math_of), ""]
    raise TypeError(f"未知块类型：{type(block).__name__}")


def render_typst(
    ast: ReportAST,
    *,
    title: str = _DEFAULT_TITLE,
    project_label: str = _DEFAULT_PROJECT_LABEL,
) -> str:
    """渲染正门：AST → Typst 源（纯函数——确定性输出，双渲染字节相同）。

    title=文档主标题；project_label=页眉项目名（server 侧传 view.name
    回落 project_id）。首现数学块/附录公式列经 formula_printers Typst
    打印机单源（公式源=sympy 树单源——引擎中立；registry by_id 只读，
    trace 公式按构造必在登记表）。
    """
    formulas = _formula_sources(ast)
    math_of: dict[str, str] = {}
    for formula_id in sorted(formulas):
        spec = by_id(formula_id)
        math_of[formula_id] = typst_of_expression(spec.expression, spec.symbols)
    emitted: set[str] = set()
    parts: list[str] = [
        "#set page(",
        '  paper: "a4",',
        "  margin: (x: 2cm, y: 2.5cm),",
        '  numbering: "1",',
        "  header: [",
        "    #set text(size: 9pt)",
        "    #h(1fr)",
        f'    {_text(f"{project_label} · 计算书")}',
        "  ],",
        ")",
        '#set text(font: ("Times New Roman", "SimSun"), lang: "zh", '
        'region: "cn", size: 10pt)',
        "#set par(justify: true)",
        "",
        f'= {_text(title)}',
        "",
        f'#quote("{_esc(_INTRO_NOTE)}")',
        "",
    ]
    chapter_no = 0
    for chapter in ast:
        if chapter.numbered:
            chapter_no += 1
            parts.append(f'= {_text(f"第 {chapter_no} 章 {chapter.title}")}')
        else:
            parts.append(f'= {_text(f"附录 {chapter.title}")}')
        parts.append("")
        for section_no, block in enumerate(chapter.blocks, start=1):
            if isinstance(block, Section):
                parts.append(
                    f'== {_text(f"{chapter_no}.{section_no} {block.title}")}'
                )
                parts.append("")
                for inner in block.blocks:
                    parts.extend(_render_block(inner, formulas, math_of, emitted))
            else:
                parts.extend(_render_block(block, formulas, math_of, emitted))
        parts.append("")
    parts.extend(_trace_index(ast))
    return "\n".join(parts) + "\n"
