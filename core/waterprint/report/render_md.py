"""ReportAST → Markdown 渲染器（两段式管线第二段——标准库拼装，零依赖）。

路径:   waterprint/report/render_md.py
职责:   章节树渲染为 Markdown 说明书：NumberLine →「{label}：{value}
        {unit}〔{formula_id}〕」；NarrativeSlot → 撰稿回填或占位；末尾
        自动生成「溯源索引」表（数字 → 公式 ID → 首现位置）。确定性输出
        （无时钟／无随机——同 AST 双渲染字节级相同）。
输入:   ReportAST+narrative_fills（本包 build 的 AST 类型——无外部依赖）。
输出:   Markdown 全文字符串（agent 工具 #21/server 报告端点/golden 快照
        消费）。
禁区:   禁 import server／fastmcp／waterprint_agent 与内核任何层（渲染器
        只消费本包 AST 类型，连 contracts 都不需要）；禁引 Markdown 三方
        库（标准库字符串拼装——KaTeX 渲染在前端，md 生产面零三方）。
参照:   v2 设计书 D5②（F1 起步——AST→渲染器两段式，docx 为未来升级位）／
        D5④（数值〔公式ID〕形态＋溯源索引＋审计附件 A 衔接）；B6 移植
        core（import 路径重写零逻辑改动）+B6 计算说明批数学块/附录扩面
        （LaTeX 串自 AST 内 FormulaCatalog 取——渲染器仍零内核依赖，
        $$…$$ 数学块供前端 remark-math/KaTeX 消费）。
"""

from __future__ import annotations

from collections.abc import Mapping

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

__all__ = ["render_markdown"]

# 叙述槽标记（HTML 注释形态——Markdown 原生合法；供 verify_report 抽取
# 叙述区与 AI 撰稿回填两侧共用）
_NARRATIVE_OPEN = "<!-- narrative:{slot_id} -->"
_NARRATIVE_CLOSE = "<!-- /narrative -->"

# 叙述槽缺省占位（管线约定文案——自身零数字，validate_narrative 可过）
_NARRATIVE_PLACEHOLDER = "（本段由撰写管线生成——见管线说明）"


def _fmt(value: float) -> str:
    """数值渲染：str(float) 最短往返表示（与 serialize round(x,10) 值
    逐字节一致——verify_report 等值断言的前提）。"""
    return str(float(value))


def _cell(value: str) -> str:
    """表格单元格转义：竖线转义＋换行压空格（Markdown 表行完整性）。"""
    return value.replace("|", "\\|").replace("\n", " ")


def _render_table(block: TableBlock) -> str:
    """TableBlock → 标题加粗行＋Markdown 管道表。"""
    lines = [f"**{block.title}**", ""]
    lines.append("| " + " | ".join(_cell(h) for h in block.headers) + " |")
    lines.append("| " + " | ".join("---" for _ in block.headers) + " |")
    for row in block.rows:
        lines.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return "\n".join(lines)


def _render_number_line(block: NumberLine) -> str:
    """NumberLine →「- {label}：{value} {unit}〔{formula_id}〕」。

    单位空串＝无量纲或未知量纲（省略单位段）；公式 ID 空串＝无 trace
    对应（省略锚点段——禁伪造锚定）。
    """
    unit_part = f" {block.unit}" if block.unit else ""
    anchor_part = f"〔{block.formula_id}〕" if block.formula_id else ""
    return f"- {block.label}：{_fmt(block.value)}{unit_part}{anchor_part}"


def _render_narrative(
    block: NarrativeSlot, fills: Mapping[str, str] | None
) -> str:
    """NarrativeSlot → 撰写要点引言＋标记包裹的回填文本（或缺省占位）。"""
    body = fills[block.slot_id] if fills and block.slot_id in fills else (
        _NARRATIVE_PLACEHOLDER
    )
    return "\n".join(
        [
            f"> 撰写要点：{block.hint}",
            "",
            _NARRATIVE_OPEN.format(slot_id=block.slot_id),
            body,
            _NARRATIVE_CLOSE,
        ]
    )


def _render_figure(block: FigureRef) -> str:
    """FigureRef → 附图段落（非列表行——图名与摘要串不经数值行检查面）。"""
    return f"附图：{block.caption}（{block.name}）"


def _formula_sources(ast: ReportAST) -> dict[str, FormulaSource]:
    """AST 内 FormulaCatalog 全集 → formula_id → 溯源条目（首目录优先）。

    数学块首现渲染的数据源：LaTeX/条文号自 build 装配的目录块取——渲染
    器零 registry 依赖（呈现数据随 AST 流入，两层职责不破）。
    """
    sources: dict[str, FormulaSource] = {}
    for chapter in ast:
        for block in chapter.blocks:
            if isinstance(block, FormulaCatalog):
                for row in block.rows:
                    sources.setdefault(row.formula_id, row)
    return sources


def _render_math_block(source: FormulaSource) -> list[str]:
    """公式首现展示块：「$$LaTeX$$」＋条文中号行（B6——KaTeX 消费面）。"""
    norm_ref = source.norm_ref.replace("|", "\\|")
    return [
        "$$",
        source.latex,
        "$$",
        "",
        f"（公式 {source.formula_id}——条文出处：{norm_ref}）",
    ]


def _render_catalog(block: FormulaCatalog) -> str:
    """FormulaCatalog → 公式溯源全表（附录章主体——四列管道表）。"""
    return _render_table(
        TableBlock(
            title="公式溯源全表（项目公式全集）",
            headers=("公式 ID", "LaTeX", "条文号", "符号释义"),
            rows=tuple(
                (
                    row.formula_id,
                    row.latex,
                    row.norm_ref,
                    row.symbols_note,
                )
                for row in block.rows
            ),
        )
    )


def _trace_index(ast: ReportAST) -> str:
    """溯源索引表：锚定数字 → 公式 ID（首现位置，AST 序确定性收集）。"""
    entries: dict[str, dict[str, str]] = {}

    def _collect(line: NumberLine, location: str) -> None:
        if not line.formula_id:
            return
        key = _fmt(line.value)
        entry = entries.setdefault(
            key, {"formulas": "", "location": location}
        )
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
    rows = tuple(
        (value, info["formulas"], info["location"])
        for value, info in entries.items()
    )
    lines = [
        "## 附录 溯源索引（数字 → 公式 ID）",
        "",
        "锚定数字与计算迹（trace）同公式输出逐项相等；公式表达式／符号／"
        "输入快照详见附件 A 审计报告与「附录 公式溯源」全表。",
        "",
        _render_table(
            TableBlock(
                title="数字溯源",
                headers=("数字", "公式 ID", "首现位置"),
                rows=rows,
            )
        ),
        "",
    ]
    return "\n".join(lines)


def render_markdown(
    ast: ReportAST, *, narrative_fills: Mapping[str, str] | None = None
) -> str:
    """渲染正门：AST → Markdown 全文（纯函数——确定性输出）。

    narrative_fills：N3 叙述槽回填（slot_id → 文本）；缺省槽渲染占位
    文案。AI 回填文本应在渲染后经 verify_report／validate_narrative
    守卫（检出数字即拒并重写该段——守卫不在渲染器内做，职责分离）。
    B6 数学块：NumberLine 首现公式处渲染「$$LaTeX$$」展示块+条文中号
    （数据自 AST 内 FormulaCatalog 取——目录外公式不渲染块，附录亦
    无此行；呈现面一致性非错误面）。
    """
    formulas = _formula_sources(ast)
    emitted: set[str] = set()
    parts: list[str] = [
        "# 污水处理厂设计说明书",
        "",
        "> 本说明书由 WaterPrint 设计说明书管线生成：计算章（第 2／4／6 章）"
        "数值全部由程序自计算迹锚定回填，不经撰写环节；叙述章（第 3／5 章）"
        "由撰写管线承接程序已注入的结论撰写，正文禁新增数字（后检守卫）。",
        "",
    ]
    chapter_no = 0
    for chapter in ast:
        if chapter.numbered:
            chapter_no += 1
            parts.append(f"## 第 {chapter_no} 章 {chapter.title}")
        else:
            parts.append(f"## 附录 {chapter.title}")
        parts.append("")
        for section_no, block in enumerate(chapter.blocks, start=1):
            if isinstance(block, Section):
                parts.append(f"### {chapter_no}.{section_no} {block.title}")
                parts.append("")
                for inner in block.blocks:
                    parts.extend(
                        _render_block(inner, narrative_fills, formulas, emitted)
                    )
            else:
                parts.extend(
                    _render_block(block, narrative_fills, formulas, emitted)
                )
        parts.append("")
    parts.append(_trace_index(ast))
    return "\n".join(parts)


def _render_block(
    block: object,
    fills: Mapping[str, str] | None,
    formulas: Mapping[str, FormulaSource],
    emitted: set[str],
) -> list[str]:
    """单块渲染分发（块间以空行分隔）。

    NumberLine 携首现数学块：公式 ID 在目录且未渲染过 → 展示块+条文中号
    前置（每公式恰一次——dedup 经 emitted 集合）。
    """
    if isinstance(block, TableBlock):
        text = _render_table(block)
    elif isinstance(block, NumberLine):
        lines: list[str] = []
        if (
            block.formula_id
            and block.formula_id in formulas
            and block.formula_id not in emitted
        ):
            emitted.add(block.formula_id)
            lines.extend(_render_math_block(formulas[block.formula_id]))
            lines.append("")
        lines.append(_render_number_line(block))
        return [*lines, ""]
    elif isinstance(block, NarrativeSlot):
        text = _render_narrative(block, fills)
    elif isinstance(block, FigureRef):
        text = _render_figure(block)
    elif isinstance(block, NoteLine):
        text = block.text
    elif isinstance(block, FormulaCatalog):
        text = _render_catalog(block)
    else:
        raise TypeError(f"未知块类型：{type(block).__name__}")
    return [text, ""]
