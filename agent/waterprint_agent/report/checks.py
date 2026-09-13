"""verify_report 数值锚定断言件（D8③——集成批 e2e 消费面）。

路径:   waterprint_agent/report/checks.py
职责:   渲染文本 → CheckReport：①全部〔公式ID〕可在 plant.trace 查到；
        ②锚定数值与该公式 trace 输出逐项相等（round(x,10) 同口径）；
        ③未锚定数值行的值必落 serialize 值域（dims／outflows／
        outqualities／summary／trace 输出全集）；④叙述区（渲染标记
        抽取）validate_narrative 零违例；⑤表格数值面（门一 FIX-1
        收口）：管道表行数值进断言——带锚表值同面②、plant 数据源表
        （见 _PLANT_TABLE_TITLES）无锚表值同面③。纯函数、零 IO。
禁区:   禁 import server／fastmcp／core L1-L3（只许 waterprint.contracts.*）。
参照:   v2 设计书 D8③（说明书断言——仅 municipal_34760 口径）；任务书
        预裁决「数值锚定断言件」；门一审查 C2（表格数值盲区）FIX-1。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import final

from waterprint.contracts.result_schema import PlantResult

from waterprint_agent.report.anchors import validate_narrative

__all__ = ["CheckReport", "verify_report"]

# 叙述区标记抽取（render_md._NARRATIVE_OPEN/CLOSE 同形——文本协议）
_NARRATIVE_ZONE = re.compile(
    r"<!-- narrative:(?P<slot_id>[^>]+) -->\n(?P<body>.*?)<!-- /narrative -->",
    re.DOTALL,
)

# 锚点对：行内〔公式ID〕（〔〕为全角括号——渲染形态契约）
_ANCHOR = re.compile(r"〔([^〕]+)〕")

# 数值词法（半角，含科学计数法；前置词字符排斥——单位记号 m3/s 的 3
# 不算数值）：「数字前不得是字母／数字／下划线／点」确保取到的是值本身
# 而非单位内数字。
_NUMBER_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
)

# 数值行形态：列表行 + 全角冒号（NumberLine 渲染形态契约）
_VALUE_LINE = re.compile(r"^- .+：")

# 表标题行（render_md._render_table 的「**{title}**」形态——表上下文锚）
_TITLE_LINE = re.compile(r"^\*\*(.+?)\*\*$")

# 表内纯数值单元格：可选负号+数值词法（整个单元格即一个值，可选锚后缀
# ——「GB 50014-2021」类混排文本与十六进制摘要天然不入面）
_PLAIN_NUMBER = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
_ANCHORED_CELL = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)〔([^〕]+)〕")

# plant 数据源表标题注册面（门一 FIX-1/C2 值域面·表的适用域声明）：
# 仅这些表的数值单元格源于 plant.serialize 值域（进水/出水水质=快照
# outqualities、设计流量=inlet outflows、数字溯源=锚定值回显）。其余
# 表（达标校核限值/裕度、水力闭合、概算、布置块等）数值来自诊断/
# 单价包/标准等外部数据源——serialize 值域不是其真值锚，显式豁免并
# 记档（标题串与 build.py TableBlock.title 逐字对齐；design=DESIGN_KEY）。
_PLANT_TABLE_TITLES: frozenset[str] = frozenset({
    "设计流量",
    "进水水质（design 工况，mg/L）",
    "出水水质（design 工况，mg/L）",
    "数字溯源",
})


@dataclass(frozen=True)
@final
class CheckReport:
    """断言件结论：ok＋失败明细＋统计面（供 e2e 断言与报告呈现）。

    table_cells_checked：表格数值面受检单元格数（面⑤——覆盖边界显式
    呈现：外部数据源表不计入，见 _PLANT_TABLE_TITLES 注记）。
    """

    ok: bool
    failures: tuple[str, ...]
    anchors_checked: int
    lines_checked: int
    narrative_zones: int
    table_cells_checked: int = 0


def _serialize_universe(plant: PlantResult) -> set[float]:
    """serialize 值域全集：结果总线全部数值叶（round(x,10) 定点口径）。"""
    universe: set[float] = set()
    for units in plant.conditions.values():
        for snapshot in units.values():
            universe.update(round(v, 10) for v in snapshot.dims.values())
            universe.update(round(v, 10) for v in snapshot.outflows.values())
            universe.update(round(v, 10) for v in snapshot.outqualities.values())
    for fields in plant.summary.values():
        universe.update(round(v, 10) for v in fields.values())
    universe.update(round(node.output, 10) for node in plant.trace)
    return universe


def _last_number(segment: str) -> float | None:
    """段内最末数值词法（锚点前的值提取——排斥单位内数字）。"""
    matches = _NUMBER_TOKEN.findall(segment)
    if not matches:
        return None
    return float(matches[-1])


def _table_cells(line: str) -> list[str]:
    """管道表行 → 单元格列表（首尾空段剔除；单元格不去内空格只 strip）。"""
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _check_table_row(  # noqa: PLR0913, PLR0917  # 断言面参数（表行上下文+两投影容器——verify 内单调用位）
    line: str,
    line_no: int,
    title: str,
    formula_ids: set[str],
    outputs_by_formula: dict[str, set[float]],
    universe: set[float],
    failures: list[str],
) -> int:
    """面⑤：单表行数值断言——锚定表值同面②、注册表无锚值同面③。

    返回本行受检单元格数（锚定单元格恒受检；无锚值仅注册表受检——
    外部数据源表显式豁免，覆盖边界见 _PLANT_TABLE_TITLES）。"""
    checked = 0
    for cell in _table_cells(line):
        anchored = _ANCHORED_CELL.fullmatch(cell)
        if anchored is not None:
            value_text, formula_id = anchored.group(1), anchored.group(2)
            checked += 1
            if formula_id not in formula_ids:
                failures.append(
                    f"第 {line_no} 行：表内锚点公式 ID {formula_id!r} 不在"
                    " plant.trace（锚点存在性面①·表）"
                )
                continue
            value = float(value_text)
            if round(value, 10) not in outputs_by_formula.get(formula_id, ()):
                failures.append(
                    f"第 {line_no} 行：表内锚定值 {value!r} 与公式 {formula_id!r}"
                    " 的 trace 输出不等（锚定等值面②·表）"
                )
            continue
        if title not in _PLANT_TABLE_TITLES:
            continue
        plain = _PLAIN_NUMBER.fullmatch(cell)
        if plain is None:
            continue
        checked += 1
        value = float(plain.group(1))
        if round(value, 10) not in universe:
            failures.append(
                f"第 {line_no} 行：表内未锚定数值 {value!r} 不在 serialize 值域"
                "（值域面③·表——数据源表 {_PLANT_TABLE_TITLES & {title}}）"
            )
    return checked


def _check_value_line(  # noqa: PLR0913  # 断言面参数（值线上下文+投影容器——_check_table_row 对称）
    line: str,
    line_no: int,
    formula_ids: set[str],
    *,
    outputs_by_formula: dict[str, set[float]],
    universe: set[float],
    failures: list[str],
) -> tuple[int, int]:
    """面①②③的值线投影：返回（anchors_checked, lines_checked）增量。"""
    anchors_checked = 0
    anchors = list(_ANCHOR.finditer(line))
    if anchors:
        for match in anchors:
            formula_id = match.group(1)
            anchors_checked += 1
            if formula_id not in formula_ids:
                failures.append(
                    f"第 {line_no} 行：公式 ID {formula_id!r} 不在 plant.trace"
                    "（锚点存在性面①）"
                )
                continue
            value = _last_number(line[: match.start()])
            if value is None:
                failures.append(
                    f"第 {line_no} 行：锚点 {formula_id!r} 前无数值（形态面）"
                )
                continue
            if round(value, 10) not in outputs_by_formula.get(formula_id, ()):
                failures.append(
                    f"第 {line_no} 行：锚定值 {value!r} 与公式 {formula_id!r} "
                    "的 trace 输出不等（锚定等值面②）"
                )
        return anchors_checked, 1
    value = _last_number(line)
    if value is None:
        return 0, 0
    if round(value, 10) not in universe:
        failures.append(
            f"第 {line_no} 行：未锚定数值 {value!r} 不在 serialize 值域"
            "（值域面③）"
        )
    return 0, 1


def verify_report(markdown_text: str, plant: PlantResult) -> CheckReport:
    """渲染文本数值锚定断言：五检查面全部通过 → ok=True。

    面①锚点存在性／②锚定等值（D8③ 逐项）；③未锚定值行落 serialize
    值域（伪造值拒收）；④叙述区零数字违例（N3 后检）；⑤表格数值面
    （门一 FIX-1——带锚表值①②同径、plant 数据源表无锚值③同径，
    外部数据源表显式豁免记档）。
    """
    failures: list[str] = []
    anchors_checked = 0
    lines_checked = 0
    table_cells_checked = 0

    formula_ids = {node.formula_id for node in plant.trace}
    outputs_by_formula: dict[str, set[float]] = {}
    for node in plant.trace:
        outputs_by_formula.setdefault(node.formula_id, set()).add(
            round(node.output, 10)
        )
    universe = _serialize_universe(plant)

    current_title = ""
    for line_no, line in enumerate(markdown_text.split("\n"), start=1):
        title_match = _TITLE_LINE.match(line)
        if title_match is not None:
            current_title = title_match.group(1)
        elif line.startswith("|"):
            table_cells_checked += _check_table_row(
                line, line_no, current_title, formula_ids,
                outputs_by_formula, universe, failures,
            )
        elif _VALUE_LINE.match(line):
            gained_anchors, gained_lines = _check_value_line(
                line, line_no, formula_ids,
                outputs_by_formula=outputs_by_formula, universe=universe,
                failures=failures,
            )
            anchors_checked += gained_anchors
            lines_checked += gained_lines

    narrative_zones = 0
    for zone in _NARRATIVE_ZONE.finditer(markdown_text):
        narrative_zones += 1
        body = zone.group("body")
        for violation in validate_narrative(body):
            failures.append(
                f"叙述槽 {zone.group('slot_id')!r} 检出数字（规则 "
                f"{violation.rule!r}，节选「{violation.excerpt}」）——叙述面④"
            )

    return CheckReport(
        ok=not failures,
        failures=tuple(failures),
        anchors_checked=anchors_checked,
        lines_checked=lines_checked,
        narrative_zones=narrative_zones,
        table_cells_checked=table_cells_checked,
    )
