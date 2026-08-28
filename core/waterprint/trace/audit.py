"""公式溯源审计报告（HTML）：迹树 → 可打印的逐条溯源文档。

输入:  TraceTree + PlantResult
输出:  单文件 HTML（自包含样式，可离线打印，M4 交付物）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M4 实现，AUDIT 批裁决 2026-08-28；镜像测试 tests/trace/
#   test_audit.py）
#
# 【公开接口】
#   render_audit_html(trace: TraceTree, result: PlantResult,
#                     out: Path) -> Path
#   class InvalidAuditError(Exception)（GR-11 族：未知公式反查/空条文号）
#   class InvalidAuditPathError(Exception)（输出路径越界——R5）
#
# 【行为规格】
#   R1 报告结构（M4 验收"任一数字可回溯到条文与输入"）：
#      按工况分章 → 单元分节 → 公式逐条（公式 ID/表达式/符号定义/
#      输入值/输出值/条文号出处）；汇总指标表列值与来源字段 ID；
#      expression/符号定义经 registry by_id 只读查询面反查（与
#      collector norm_ref_of 同源——迹是事实，registry 是释义）。
#   R2 HTML 转义一切用户可控文本（单元名/项目名——§18 注入面；
#      React 默认转义是前端，这里是内核导出物同样守规矩）。
#   R3 自包含：内联 CSS、零外部 URL/字体/脚本（离线可开；
#      出站请求零依赖原则 §18）。
#   R4 确定性输出：同迹树同 HTML 字节（时间取 result.repro 三元组
#      而非当前时钟）；汇总表键排序、迹按到达序、LF 落盘。
#   R5 路径安全：输出限制在配置目录（同 dxf_writer R4 口径——
#      绝对路径 + 拒 '..' 分量，越界抛领域异常）。
#   R6 打印版（M4a ⑤）：@media print——表头跨页重复（thead→
#      table-header-group）/工况分章分页断点（首章除外 :not(:first-
#      of-type)——标题页与首章同页）/行与单元节不跨页截断；"隐藏交互
#      元素"结构性不适用（R3 自包含=零脚本零链接零交互面，无可藏——
#      注记非缺陷）；内联 CSS 自包含原则 R3 保持不变。
#
# 【数值纪律】本文件不在魔法数字白名单——代码 AST 零数值字面量；
#   CSS 视觉常量（字号/边距/颜色）以字符串形态内联于 _CSS 常量，
#   AST 门禁面外（str 常量非 int/float），纯展示值零工程含义——
#   豁免口径同 drafting styles.py"带出处的声明式常量"记档。
#
# 【测试要求】结构完整性（每公式含条文号断言）、转义（恶意单元名）、
#   自包含（零 http/脚本）、确定性、路径越界拒绝。
#
# 【参照】重写计划 §7 M4 审计链路/§18；dxf_writer R4 路径口径
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import html
from pathlib import Path

from waterprint.contracts.result_schema import PlantResult, TraceNode
from waterprint.registry import formulas
from waterprint.trace.collector import TraceTree

__all__ = ["InvalidAuditError", "InvalidAuditPathError", "render_audit_html"]

# R3 内联样式（打印友好）：零外部 URL/字体/脚本——视觉常量字符串形态
# （数值纪律豁免口径见上），generic 字体族零出站依赖。
# 打印版（M4a ⑤/R6）：thead 表头跨页重复 + 工况分章分页断点（首章
# 豁免）+ tr/单元节不截断；交互元素面=零（R3 自包含——无可藏，注记）。
_CSS = """
body{font-family:sans-serif;color:#1f1f1f;background:#ffffff;
margin:2em;line-height:1.5}
h1{font-size:1.6em;border-bottom:2px solid #2c5f8a;padding-bottom:.3em}
h2{font-size:1.25em;border-left:5px solid #2c5f8a;padding-left:.5em;
margin-top:1.8em}
h3{font-size:1.05em;margin:1.2em 0 .5em}
table{border-collapse:collapse;width:100%;margin:.6em 0 1em;
font-size:.92em}
th,td{border:1px solid #b9c6d1;padding:.35em .6em;text-align:left;
vertical-align:top}
th{background:#eef3f7}
caption{caption-side:top;text-align:left;font-weight:bold;
padding:.3em 0}
section.unit{page-break-inside:avoid}
footer{margin-top:2em;font-size:.85em;color:#5a6a77;
border-top:1px solid #b9c6d1;padding-top:.5em}
@media print{
body{margin:0}
thead{display:table-header-group}
tr{page-break-inside:avoid}
section.condition:not(:first-of-type){page-break-before:always}
}
""".strip()


class InvalidAuditError(Exception):
    """审计报告渲染非法（未知公式反查/空条文号）——GR-11 族（M4）。"""


class InvalidAuditPathError(Exception):
    """输出路径越界（非绝对路径或含 '..' 分量）——R5（同 dxf_writer R4）。"""


def _validate_out(out: Path) -> None:
    """R5 路径安全（dxf_writer R4 同款口径）：拒相对路径与 '..' 分量。"""
    if not out.is_absolute():
        raise InvalidAuditPathError(
            f"输出路径须为绝对路径：{out!r}（拼接基准由调用方目录限定）"
        )
    for part in out.parts:
        if part == "..":
            raise InvalidAuditPathError(
                f"输出路径含越界分量 '..'：{out!r}（§18 路径安全——SERVER 教训）"
            )


def _number(value: float) -> str:
    """数值 → 确定性文本（repr 全精度往返稳定，R4 字节级组成件）。"""
    return repr(float(value))


def _spec_of(formula_id: str, cache: dict[str, formulas.FormulaSpec]
             ) -> formulas.FormulaSpec:
    """formula_id → FormulaSpec（expression/符号定义反查；R1 释义半）。

    未知公式/空条文号 = InvalidAuditError（审计链断链即失败，GR-09
    消息含 formula_id——M4 验收"任一数字可回溯条文"的结构性保证）。
    """
    if formula_id not in cache:
        try:
            cache[formula_id] = formulas.by_id(formula_id)
        except formulas.InvalidFormulaError as exc:
            raise InvalidAuditError(
                f"计算迹含未知公式：{formula_id!r}（expression/符号定义"
                "反查失败——审计链断链即失败）"
            ) from exc
    return cache[formula_id]


def _rows_for(nodes: list[TraceNode],
              cache: dict[str, formulas.FormulaSpec]) -> str:
    """单元节内公式逐条表体（R1：五要素审计链逐行可回溯）。"""
    esc = html.escape
    rows: list[str] = []
    for node in nodes:
        spec = _spec_of(node.formula_id, cache)
        if not node.norm_ref:
            raise InvalidAuditError(
                f"计算迹节点条文号为空：{node.formula_id!r}（单元 "
                f"{node.unit_id!r}——M4 验收'任一数字可回溯条文'拒绝无源数字）"
            )
        symbols = "<br>".join(
            f"{esc(symbol)}：{esc(meaning)}"
            for symbol, (_dim, meaning) in spec.symbols.items()
        )
        inputs = "<br>".join(
            f"{esc(key)} = {_number(value)}"
            for key, value in node.inputs.items()
        )
        rows.append(
            "<tr>"
            f"<td>{esc(node.formula_id)}</td>"
            f"<td>{esc(spec.expression)}<br><small>{symbols}</small></td>"
            f"<td>{inputs}</td>"
            f"<td>{_number(node.output)}</td>"
            f"<td>{esc(node.norm_ref)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _summary_table(result: PlantResult) -> str:
    """汇总指标表（R1：值 + 来源字段 ID；键排序=R4 确定性）。"""
    esc = html.escape
    rows: list[str] = []
    for condition_key in sorted(result.summary):
        for field_id in sorted(result.summary[condition_key]):
            rows.append(
                "<tr>"
                f"<td>{esc(condition_key)}</td>"
                f"<td>{esc(field_id)}</td>"
                f"<td>{_number(result.summary[condition_key][field_id])}</td>"
                "</tr>"
            )
    if not rows:
        return ""
    return (
        "<h2>汇总指标</h2><table><caption>汇总面值与来源字段</caption>"
        "<thead><tr><th>工况</th><th>来源字段 ID</th><th>值</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _chapters(trace: TraceTree) -> str:
    """工况分章 → 单元分节 → 公式逐条表（R1 主体；到达序=R4 确定性）。"""
    esc = html.escape
    grouped: dict[tuple[str, str], list[TraceNode]] = {}
    for node in trace:
        grouped.setdefault(
            (node.condition_key, node.unit_id), []
        ).append(node)
    cache: dict[str, formulas.FormulaSpec] = {}
    parts: list[str] = []
    for (condition_key, unit_id), nodes in grouped.items():
        parts.append(
            f"<section class=\"condition\"><h2>工况 {esc(condition_key)}</h2>"
            f"<section class=\"unit\"><h3>单元 {esc(unit_id)}</h3>"
            "<table><caption>公式逐条（输入快照 → 输出 → 条文出处）</caption>"
            "<thead><tr><th>公式 ID</th><th>表达式与符号定义</th>"
            "<th>输入值</th><th>输出值</th><th>条文出处</th></tr></thead>"
            f"<tbody>{_rows_for(nodes, cache)}</tbody></table></section>"
            "</section>"
        )
    return "".join(parts)


def render_audit_html(
    trace: TraceTree, result: PlantResult, out: Path
) -> Path:
    """审计报告渲染正门：迹树分组 → 转义拼接 → 确定性落盘（返回 out）。

    R4 确定性：文档头部时间面 = result.repro 三元组（design_hash/
    engine_version/data_version），全程零当前时钟调用——同迹树同结果
    双渲染字节相同；R5：越界路径先拒后写。
    """
    _validate_out(out)
    esc = html.escape
    repro = result.repro
    meta = "".join(
        f"<tr><th>{esc(label)}</th><td>{esc(value)}</td></tr>"
        for label, value in (
            ("design_hash", repro.design_hash),
            ("engine_version", repro.engine_version),
            ("data_version", repro.data_version),
        )
    )
    document = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<title>{esc('公式溯源审计报告')}</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"<h1>{esc('公式溯源审计报告')}</h1>\n"
        f"<table><caption>可复算三元组（R4：时间面取此，非时钟）</caption>"
        f"{meta}</table>\n"
        f"{_summary_table(result)}\n"
        f"{_chapters(trace)}\n"
        "<footer>WaterPrint 审计链路：任一输出数字可回溯公式 ID + 条文号"
        " + 输入快照（M4 验收）。</footer>\n"
        "</body>\n</html>\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document, encoding="utf-8", newline="\n")
    return out
