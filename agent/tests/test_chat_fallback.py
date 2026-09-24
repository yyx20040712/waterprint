"""test_chat_fallback——关键词直译回退：话术→计划（B4-4a 蓝图沿承）。

输入:  自然语言话术
输出:  FallbackPlan（seed/名称/报告意愿）或 None（不支持域）
"""

from __future__ import annotations

from waterprint_agent.chat.fallback import parse


def test_municipal_catchphrase() -> None:
    """三话术①：市政+AAO→municipal_34760 种子。"""
    plan = parse("设计一座日处理 3 万吨的市政污水处理厂，AAO 工艺")
    assert plan is not None
    assert plan.seed == "municipal_34760"
    assert plan.wants_report is False


def test_mine_catchphrase() -> None:
    """三话术②：矿井→mine_43836 种子。"""
    plan = parse("矿井水处理厂，日处理量 1 万吨")
    assert plan is not None
    assert plan.seed == "mine_43836"


def test_grade_a_catchphrase() -> None:
    """三话术③：一级 A 出水要求→市政种子+标准注记（模板标准档为准）。"""
    plan = parse("市政污水厂 5 万吨每天，出水要一级A")
    assert plan is not None
    assert plan.seed == "municipal_34760"
    assert "一级A" in plan.note


def test_recycle_seed_variant() -> None:
    """回流/再生变体→municipal_recycle_34760。"""
    plan = parse("市政污水厂带回流再生的，3 万吨")
    assert plan is not None
    assert plan.seed == "municipal_recycle_34760"


def test_unsupported_returns_none() -> None:
    """非设计域话术→None（降级模式显式拒绝而非瞎猜）。"""
    assert parse("你好") is None
    assert parse("今天天气怎么样") is None
