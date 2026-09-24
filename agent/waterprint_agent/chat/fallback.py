"""关键词直译回退（B4-4a 规划档 §三蓝图沿承——降级模式执行计划）。

输入:  自然语言话术
输出:  FallbackPlan（种子/名称/报告意愿/注记）或 None（非设计域）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/fallback.py
#   职责：LLM 不可用时的单轮降级——话术→种子模板映射（建项+计算+
#       可选双报告的执行计划）；非设计域=None 显式拒绝。
#   禁区：禁数值改参（降级模式用模板原样参数——规模差异如实注记，
#       精确改参留给 LLM 模式）；禁模糊匹配延伸（关键词表封闭集）。
#
# 【行为规格】
#   R1 域判：话术含设计域词（污水/矿井/水厂/处理）才入计划，否则 None。
#   R2 种子：矿井→mine_43836；回流/再生→municipal_recycle_34760；
#      回路→municipal_loop_34760；其余市政→municipal_34760。
#   R3 意图：报告词（报告/说明书）→wants_report；计算恒真（降级链
#      固定建项+计算）；一级 A 等出水词→note 记录（模板标准档为准）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["FallbackPlan", "parse"]

_DOMAIN_WORDS = ("污水", "矿井", "水厂", "处理")
_REPORT_WORDS = ("报告", "说明书")
_STANDARD_WORDS = ("一级A", "一级 A", "一级a")
_SCALE_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*万吨")


@dataclass(frozen=True)
class FallbackPlan:
    """降级执行计划（模板原样——零参数改写）。"""

    seed: str
    name: str
    wants_report: bool
    note: str


def _pick_seed(text: str) -> str:
    """种子映射（R2——封闭关键词表，矿井>回流>回路>市政缺省）。"""
    if "矿井" in text:
        return "mine_43836"
    if "回流" in text or "再生" in text:
        return "municipal_recycle_34760"
    if "回路" in text:
        return "municipal_loop_34760"
    return "municipal_34760"


def parse(text: str) -> FallbackPlan | None:
    """话术→计划（非设计域=None——R1）。"""
    if not any(word in text for word in _DOMAIN_WORDS):
        return None
    seed = _pick_seed(text)
    notes: list[str] = []
    for word in _STANDARD_WORDS:
        if word in text:
            notes.append(
                f"出水要求「{word.strip()}」已记录，以模板标准档为准（精确改标准档请配置 AI 接口）"
            )
            break
    scale_match = _SCALE_PATTERN.search(text)
    name = f"对话回退-{scale_match.group()}" if scale_match else "对话回退项目"
    return FallbackPlan(
        seed=seed,
        name=name,
        wants_report=any(word in text for word in _REPORT_WORDS),
        note="；".join(notes),
    )
