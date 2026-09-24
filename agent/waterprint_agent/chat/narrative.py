"""轨道丙扩展：决策纪要→工艺选择叙述草稿（纯文案零计算）。

输入:  会话决策纪要四键列表（sessions.read_decisions 投影）
输出:  process_selection 叙述槽建议文本（经 wp_export_report 的
       narrative_fills 入口人工采用——verify 门零动）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 3 2026-09-24）
#   路径：agent/waterprint_agent/chat/narrative.py
#   职责：对话决策纪要模板化组装为设计说明书 process_selection 章
#       叙述建议（终裁 §五：环内函数非工具；承接章=process_selection
#       ——七章节唯一工艺叙事槽，审 W6 处置）。
#   禁区：禁数值计算/编造数字（纯文案；草稿若含数字由叙述槽守卫
#       validate_narrative 在导出面拒——宁误报不漏报，人工改写后采用）；
#       禁直写报告文件（产物仅文本，落盘决策归 wp_export_report）。
#
# 【行为规格】
#   R1 组装：逐决策「主题：结论（依据：理由）」句列+首尾引导语；
#      无决策=占位说明文本（诚实空态不编造）。
#   R2 确定性：同输入同文本（模板纯函数）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

__all__ = ["draft_process_selection"]

_HEADER = "工艺选择与主要设计决策如下（本段为对话决策纪要草稿，采用前请核改）："
_EMPTY = "（本会话暂无决策纪要——在对话中明确「记录决策」后重新生成。）"


def draft_process_selection(decisions: list[dict[str, Any]]) -> str:
    """决策纪要→process_selection 叙述草稿（R1/R2——纯模板零计算）。"""
    if not decisions:
        return _EMPTY
    lines = [_HEADER]
    for item in decisions:
        topic = str(item.get("topic") or "未主题决策")
        conclusion = str(item.get("conclusion") or "").strip()
        rationale = str(item.get("rationale") or "").strip()
        sentence = f"{topic}：{conclusion}。" if conclusion else f"{topic}：（结论未记录）。"
        if rationale:
            sentence = sentence[:-1] + f"（依据：{rationale}）。"
        lines.append(sentence)
    return "\n".join(lines)
