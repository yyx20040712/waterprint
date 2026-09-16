"""validate_narrative 数字形态族测试（N3 叙述章守卫——TDD 先红）。

覆盖形态族：阿拉伯（半角/全角）/小数/百分比（半角/全角）/中文数字/
量纲紧邻/序号豁免（显式可测）；以及违例字段（offset/excerpt/rule）与
多违例排序契约。
"""

from __future__ import annotations

import pytest

from waterprint_agent.report.anchors import validate_narrative

# 多命中排序断言的下限（三处独立形态：阿拉伯/百分比/量纲紧邻）
_MIN_MULTI_HITS = 3


def _rules(text: str) -> list[str]:
    """便捷投影：违例规则名列表（按 offset 序）。"""
    return [v.rule for v in validate_narrative(text)]


class TestCleanText:
    """干净叙述文本——零违例。"""

    def test_pure_chinese_narrative_passes(self) -> None:
        assert validate_narrative("本方案采用厌氧缺氧好氧工艺，出水稳定达标。") == []

    def test_empty_text_passes(self) -> None:
        assert validate_narrative("") == []

    def test_ordinal_exemption_chapter_zh(self) -> None:
        """豁免形态：第X章（中文数字）——纯序号标题形态。"""
        assert validate_narrative("详见第四章设计依据的说明。") == []

    def test_ordinal_exemption_chapter_arabic(self) -> None:
        """豁免形态：第X章（阿拉伯数字）。"""
        assert validate_narrative("按第 4 章执行。") == []

    def test_ordinal_exemption_section_numbering(self) -> None:
        """豁免形态：X.X 节（层级序号标题形态）。"""
        assert validate_narrative("对照 3.2 节的比选结论展开。") == []

    def test_ordinal_exemption_section_deep_numbering(self) -> None:
        """豁免形态：X.Y.Z 节（三层序号）。"""
        assert validate_narrative("见 4.2.1 节计算过程。") == []


class TestDigitForms:
    """数字形态族——逐形态检出。"""

    def test_arabic_integer_detected(self) -> None:
        text = "全厂共 34760 吨每日处理。"
        violations = validate_narrative(text)
        assert "arabic" in [v.rule for v in violations]

    def test_arabic_fullwidth_detected(self) -> None:
        """全角数字 ０-９ 同族检出（AI 变体逃逸面封堵）。"""
        assert "arabic" in _rules("规模为３４７６０吨。")

    def test_decimal_detected(self) -> None:
        assert "decimal" in _rules("回流比约 2.5 倍。")

    def test_percent_halfwidth_detected(self) -> None:
        assert "percent" in _rules("去除率达到 92%。")

    def test_percent_fullwidth_detected(self) -> None:
        assert "percent" in _rules("去除率达到 ９２.５％。")

    def test_percent_decimal_detected(self) -> None:
        assert "percent" in _rules("裕度约 12.5%（充裕）。")

    def test_chinese_numeral_detected(self) -> None:
        assert "chinese_numeral" in _rules("全厂共三组并列运行。")

    def test_chinese_numeral_compound_detected(self) -> None:
        """复合中文数字（二十、十五）同族检出。"""
        assert "chinese_numeral" in _rules("池深约二十米上下。")

    def test_unit_adjacent_detected(self) -> None:
        """量纲紧邻形态：数字后紧贴工程单位——独立规则名。"""
        assert "unit_adjacent" in _rules("池容约 12000 m3 上下。")

    def test_unit_adjacent_superscript_detected(self) -> None:
        """上标单位变体 m³/d——量纲紧邻同族。"""
        assert "unit_adjacent" in _rules("设计规模 34760 m³/d。")

    def test_unit_adjacent_with_concentration(self) -> None:
        assert "unit_adjacent" in _rules("进水浓度约 400mg/L。")


class TestExemptionBoundary:
    """豁免边界——豁免只覆盖纯序号形态，其余数字照常检出。"""

    def test_bare_number_not_exempted(self) -> None:
        """非序号语境的阿拉伯数字不豁免。"""
        assert "arabic" in _rules("共设 3 座初沉池。")

    def test_chapter_word_without_ordinal_prefix_keeps_digits(self) -> None:
        """「章」字前无「第」且无序号形态——普通数字照常检出。"""
        assert "arabic" in _rules("详见 GB 50014 相关章节。")

    def test_exemption_does_not_mask_following_digits(self) -> None:
        """同一句内：豁免序号 + 非豁免数字并存——后者仍检出。"""
        text = "见第 4 章，全厂共 3 座提升泵房。"
        assert "arabic" in _rules(text)

    def test_decimal_section_numbering_still_exempts_only_section(self) -> None:
        """X.X 节豁免不吞并句内其它数字（「22 天」照常检出）。"""
        text = "按 3.2 节结论，泥龄取 22 天。"
        rules = _rules(text)
        assert rules == ["arabic"]  # 序号 3.2 豁免，唯「22」命中


class TestViolationContract:
    """违例对象字段契约：offset／excerpt／rule。"""

    def test_offset_points_to_digit(self) -> None:
        text = "本段说明共 34760 吨。"
        violations = validate_narrative(text)
        arabic = next(v for v in violations if v.rule == "arabic")
        assert text[arabic.offset : arabic.offset + len("34760")] == "34760"

    def test_excerpt_contains_hit(self) -> None:
        text = "本段说明共 34760 吨。"
        violations = validate_narrative(text)
        assert violations
        for violation in violations:
            assert "34760" in violation.excerpt
            assert violation.excerpt  # 非空

    def test_multiple_violations_sorted_by_offset(self) -> None:
        text = "共 3 座池，去除率 92%，池深 6 m。"
        violations = validate_narrative(text)
        offsets = [v.offset for v in violations]
        assert offsets == sorted(offsets)
        assert len(violations) >= _MIN_MULTI_HITS  # 至少三处独立命中

    def test_all_rules_in_documented_family(self) -> None:
        """规则名族封闭：arabic/decimal/percent/chinese_numeral/unit_adjacent。"""
        text = "3 座，3.5 倍，92%，三组，6 m3。"
        rules = set(_rules(text))
        assert rules <= {
            "arabic",
            "decimal",
            "percent",
            "chinese_numeral",
            "unit_adjacent",
        }
        assert rules == {
            "arabic",
            "decimal",
            "percent",
            "chinese_numeral",
            "unit_adjacent",
        }


class TestPlaceholderCompat:
    """管线占位文本自身必须零违例（渲染默认占位即守卫通过）。"""

    def test_default_placeholder_is_clean(self) -> None:
        assert validate_narrative("（本段由撰写管线生成——见管线说明）") == []


@pytest.mark.parametrize(
    ("text", "expected_rule"),
    [
        ("设 2 组。", "arabic"),
        ("约 0.6 的系数。", "decimal"),
        ("达 98%。", "percent"),
        ("达９８％。", "percent"),
        ("第五十章附录。", None),  # 豁免
        ("见 5.3 节。", None),  # 豁免
        ("高 12 m。", "unit_adjacent"),
        ("泥龄二十二天。", "chinese_numeral"),
    ],
)
def test_parametrized_forms(text: str, expected_rule: str | None) -> None:
    """参数化对照：形态族逐一红绿。"""
    rules = _rules(text)
    if expected_rule is None:
        assert rules == []
    else:
        assert expected_rule in rules
