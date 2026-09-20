"""test_demo_rules——演示版规则解析面：三话术+变体路由+规模抽取（零沙箱纯函数）。

输入:  parse_with_rules 纯函数（话术字符串）
输出:  DemoIntent 断言（seed/scale_m3_d/name/parse_source——B4-4a 验收三话术基准）
"""

from __future__ import annotations

import math

from waterprint_agent.demo import DemoIntent, parse_with_rules

# 演示三话术（规划档 §三验收基准——勿改口径）
UTTERANCE_AAO = "设计一座日处理 3 万吨的市政污水处理厂，AAO 工艺"
UTTERANCE_MINE = "矿井水处理厂，日处理量 1 万吨"
UTTERANCE_LEVEL_A = "市政污水厂 5 万吨每天，出水要一级 A"


def _assert_scale(value: float, expected_m3_d: float) -> None:
    assert isinstance(value, float)
    assert math.isclose(value, expected_m3_d, rel_tol=1e-12)


def test_rules_three_demo_utterances() -> None:
    """三话术基准：市政 AAO/矿井/市政一级 A 的 seed 与规模抽取。"""
    aao = parse_with_rules(UTTERANCE_AAO)
    assert aao.seed == "municipal_34760"
    assert aao.parse_source == "rules"
    assert aao.scale_m3_d is not None
    _assert_scale(aao.scale_m3_d, 30000.0)

    mine = parse_with_rules(UTTERANCE_MINE)
    assert mine.seed == "mine_43836"
    assert mine.scale_m3_d is not None
    _assert_scale(mine.scale_m3_d, 10000.0)

    level_a = parse_with_rules(UTTERANCE_LEVEL_A)
    assert level_a.seed == "municipal_34760"
    assert level_a.scale_m3_d is not None
    _assert_scale(level_a.scale_m3_d, 50000.0)


def test_rules_scale_variants() -> None:
    """规模表述变体：万吨前置/每天 N 万吨/小数万吨/未提及规模。"""
    pre = parse_with_rules("3万吨市政污水厂")
    assert pre.scale_m3_d is not None
    _assert_scale(pre.scale_m3_d, 30000.0)

    daily_first = parse_with_rules("每天 1.5 万吨市政污水处理")
    assert daily_first.scale_m3_d is not None
    _assert_scale(daily_first.scale_m3_d, 15000.0)

    no_scale = parse_with_rules("市政污水处理厂 AAO 工艺")
    assert no_scale.scale_m3_d is None  # 未提及规模→种子原规模（零 patch）
    assert no_scale.seed == "municipal_34760"


def test_rules_seed_routing() -> None:
    """种子路由：矿井/中水回用/回流回路关键词与市政缺省。"""
    assert parse_with_rules("矿井水 2 万吨").seed == "mine_43836"
    assert parse_with_rules("煤矿矿井水处理").seed == "mine_43836"
    assert parse_with_rules("市政污水 2 万吨，中水回用").seed == "municipal_recycle_34760"
    assert parse_with_rules("市政污水 2 万吨，再生利用").seed == "municipal_recycle_34760"
    assert parse_with_rules("市政污水 2 万吨，回流回路").seed == "municipal_loop_34760"
    assert parse_with_rules("某污水处理厂").seed == "municipal_34760"  # 缺省市政


def test_rules_intent_shape() -> None:
    """DemoIntent 形态：冻结数据类+项目名生成+parse_note 非空。"""
    intent = parse_with_rules(UTTERANCE_AAO)
    assert isinstance(intent, DemoIntent)
    assert intent.name.startswith("演示-")
    assert intent.parse_note
    assert intent.utterance == UTTERANCE_AAO
