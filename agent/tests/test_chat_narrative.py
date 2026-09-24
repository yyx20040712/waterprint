"""轨道丙 narrative 草稿测试（B4-4b 子批 3）：决策纪要→叙述建议文本。

输入:  决策四键列表（或空）
输出:  模板组装断言（确定性/空态诚实/依据句拼接）
"""

from __future__ import annotations

from waterprint_agent.chat.narrative import draft_process_selection

_DECISIONS = [
    {"topic": "工艺路线", "conclusion": "AAO", "rationale": "脱氮需求", "turn": 2},
    {"topic": "污泥处理", "conclusion": "机械脱水", "rationale": "", "turn": 3},
]


def test_draft_assembles_sentences() -> None:
    """逐决策句列：主题：结论（依据：理由）拼接+引导语首行。"""
    text = draft_process_selection(_DECISIONS)
    assert text.startswith("工艺选择与主要设计决策如下")
    assert "工艺路线：AAO（依据：脱氮需求）。" in text
    assert "污泥处理：机械脱水。" in text


def test_draft_deterministic() -> None:
    """R2 确定性：同输入同文本。"""
    assert draft_process_selection(_DECISIONS) == draft_process_selection(_DECISIONS)


def test_draft_empty_honest() -> None:
    """空态：占位说明（不编造决策）。"""
    assert "暂无决策纪要" in draft_process_selection([])
