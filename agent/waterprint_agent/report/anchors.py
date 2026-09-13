"""N3 叙述章数字守卫：validate_narrative 正则族检出（AI 段禁数字后检）。

路径:   waterprint_agent/report/anchors.py
职责:   叙述文本数字形态族检出——阿拉伯（半角／全角）、小数、百分比、
        中文数字、量纲紧邻；纯序号「第X章／X.X 节」标题形态显式豁免
        （豁免规则可测）。零外部依赖（纯函数，标准库 re）。
禁区:   禁 import server／fastmcp／core L1-L3；禁写入任何文件——本模块
        只做文本判定，不做 IO（管线纯函数纪律）。
参照:   v2 设计书 D5③（N3 分段混合——叙述章正文禁新增任何数字：提示词
        约束+正则后检，检出即拒并重写该段）；K4（中文数字／百分比变体
        完备性属缓解非根除——宁误报不漏报的严格姿态）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import final

__all__ = ["NarrativeViolation", "validate_narrative"]

# 数字字符族（半角+全角——AI 变体逃逸面封堵）
_DIGITS = r"[0-9０-９]"
# 中文数字族（一至九／零两十百千万亿——复合形态如「二十」按连续段命中）
_ZH_NUMERALS = r"[零一二两三四五六七八九十百千万亿]"

# 规则名族（封闭集——测试对照的契约面）
RULE_ARABIC = "arabic"
RULE_DECIMAL = "decimal"
RULE_PERCENT = "percent"
RULE_CHINESE_NUMERAL = "chinese_numeral"
RULE_UNIT_ADJACENT = "unit_adjacent"

# 量纲单位族（长在前防短前缀吞并；上标写法 m³/m² 与规范写法 m3/m2 并收）
_UNIT_TOKENS = (
    "m³/d",
    "m³/h",
    "m³/s",
    "m²/s",
    "mg/L",
    "g/m³",
    "g/m3",
    "kg/d",
    "t/d",
    "m/s",
    "km/h",
    "ppm",
    "NTU",
    "degC",
    "kW",
    "MW",
    "m³",
    "m²",
    "m3",
    "m2",
    "kg",
    "mm",
    "cm",
    "km",
    "mL",
    "mg",
    "μg",
    "min",
    "‰",
    "℃",
    "°C",
    "L",
    "m",
    "d",
    "h",
    "s",
    "W",
)

# 检出器族（rule → 编译正则）——小数／百分比／量纲为阿拉伯的特化形态，
# 重叠命中各自独立报告（多规则并存是刻意的冗余信号面）。
_DETECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        RULE_DECIMAL,
        re.compile(rf"{_DIGITS}+[.．]{_DIGITS}+"),
    ),
    (
        RULE_PERCENT,
        re.compile(rf"{_DIGITS}+(?:[.．]{_DIGITS}+)?[%％]"),
    ),
    (
        RULE_UNIT_ADJACENT,
        re.compile(
            rf"{_DIGITS}+(?:[.．]{_DIGITS}+)?\s*(?:{'|'.join(_UNIT_TOKENS)})"
            r"(?![A-Za-z0-9])"
        ),
    ),
    (
        RULE_ARABIC,
        re.compile(rf"{_DIGITS}+"),
    ),
    (
        RULE_CHINESE_NUMERAL,
        re.compile(rf"{_ZH_NUMERALS}+"),
    ),
)

# 豁免族（纯序号标题形态——显式白名单，可测边界）
#   ①「第X章／节／条／款／篇／部分」——X 为中文数字或阿拉伯数字（含全角）
#   ②「X.Y〔.Z…〕 节」——层级序号后接「节」字（工程文档目录引用惯例）
_EXEMPT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        rf"第\s*(?:{_ZH_NUMERALS}+|{_DIGITS}+|\d+)\s*[章节条款篇部]"
    ),
    re.compile(r"\d+(?:\.\d+)*\s*[节章条]"),
)

# 节选窗半径（excerpt 上下文——命中片段前后各取固定窗，便于人工定位）
_EXCERPT_RADIUS = 8


@dataclass(frozen=True)
@final
class NarrativeViolation:
    """单条叙述数字违例：offset（原文位置）+ excerpt（命中上下文）+ rule。"""

    offset: int
    excerpt: str
    rule: str


def _exempt_spans(text: str) -> list[tuple[int, int]]:
    """豁免序号形态的原文区间集。"""
    return [
        (match.start(), match.end())
        for pattern in _EXEMPT_PATTERNS
        for match in pattern.finditer(text)
    ]


def _is_exempt(span: tuple[int, int], exemptions: list[tuple[int, int]]) -> bool:
    """命中区间完整落于某豁免区间内 → 豁免（半跨不豁免——边界从严）。"""
    start, end = span
    return any(begin <= start and end <= finish for begin, finish in exemptions)


def _excerpt(text: str, start: int, end: int) -> str:
    """命中上下文节选（固定窗半径，含命中片段本身）。"""
    window_begin = max(start - _EXCERPT_RADIUS, 0)
    window_end = min(end + _EXCERPT_RADIUS, len(text))
    return text[window_begin:window_end]


def validate_narrative(text: str) -> list[NarrativeViolation]:
    """叙述文本数字后检：检出全部违例（按 offset 升序），干净文本返回空表。

    严格姿态（K4 缓解策略）：中文数字按字符族整体检出——「一体化」「千万」
    类普通词会误报，宁误报不漏报，由 AI 改写规避；豁免仅覆盖显式序号形态。
    """
    exemptions = _exempt_spans(text)
    hits: list[NarrativeViolation] = []
    for rule, pattern in _DETECTORS:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if _is_exempt(span, exemptions):
                continue
            hits.append(
                NarrativeViolation(
                    offset=match.start(),
                    excerpt=_excerpt(text, span[0], span[1]),
                    rule=rule,
                )
            )
    hits.sort(key=lambda violation: violation.offset)
    return hits
