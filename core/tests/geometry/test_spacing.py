"""spacing 镜像测试：间距校核裁判（AABB 净距/阈值限定对/未计算降级/确定性）。

输入:  waterprint.geometry.spacing 公开符号
输出:  校核契约断言（L4b 简报 §二冻结签名——AABB 口径与 webapp
       measureToNearest 同源所见即所得；OBB 精确净距挂账）
"""

from __future__ import annotations

import math

import pytest

from waterprint.geometry.spacing import (
    SpacingThreshold,
    spacing_report,
)


def _threshold(
    min_clearance_m: float,
    severity: str = "WARN",
    unit_kinds: frozenset[str] | None = None,
) -> SpacingThreshold:
    """阈值条目速构（unit_kinds=None=全对通用；frozenset=限定对成员集）。"""
    return SpacingThreshold(
        unit_kinds=unit_kinds, min_clearance_m=min_clearance_m, severity=severity
    )


def test_axis_aligned_pair_gap_and_boundary_pass() -> None:
    """轴向对齐净距=中心距-半轴和；clearance==threshold 恰过界（>= 合格）。"""
    placements = {"a": (0.0, 0.0, 0.0), "b": (20.0, 0.0, 0.0)}
    footprints = {"a": (10.0, 6.0), "b": (10.0, 6.0)}
    report = spacing_report(placements, footprints, [_threshold(10.0)])
    # gapX = 20 - 5 - 5 = 10（Y 向重叠 clamp 0 不参与——单轴分离）
    assert report.violations == ()  # 恰等=合格（>= 语义——clearance==threshold）
    assert report.uncalculated == ()
    over = spacing_report(placements, footprints, [_threshold(10.0 + 0.1)])
    assert len(over.violations) == 1
    row = over.violations[0]
    assert (row.a, row.b) == ("a", "b")
    assert row.clearance_m == pytest.approx(10.0)
    assert row.threshold_m == pytest.approx(10.1)
    assert row.severity == "WARN"


def test_rotation_widens_projected_half_extents() -> None:
    """旋转 90°：AABB 半轴对调（hx=hy 互换）——同摆位净距随旋转收紧。"""
    placements = {"a": (0.0, 0.0, 90.0), "b": (0.0, 20.0, 0.0)}
    footprints = {"a": (10.0, 4.0), "b": (4.0, 4.0)}
    report = spacing_report(placements, footprints, [_threshold(1.0)])
    # a 旋 90°：hx=4/2=2、hy=10/2=5；b：hx=hy=2
    # gapY = 20 - 5 - 2 = 13（X 向重叠 clamp 0）
    assert report.violations == ()
    tight = spacing_report(placements, footprints, [_threshold(13.0 + 0.5)])
    assert tight.violations[0].clearance_m == pytest.approx(13.0)


def test_arbitrary_angle_matches_webapp_formula() -> None:
    """任意角：净距=webapp halfExtents 口径逐值（hypot(max(gapX,0),max(gapY,0))）。"""
    rotation_deg = 30.0
    placements = {"a": (0.0, 0.0, rotation_deg), "b": (17.0, 9.0, 0.0)}
    footprints = {"a": (12.0, 5.0), "b": (6.0, 6.0)}
    rad = math.radians(rotation_deg)
    cos, sin = abs(math.cos(rad)), abs(math.sin(rad))
    ax, ay = (12.0 * cos + 5.0 * sin) / 2, (12.0 * sin + 5.0 * cos) / 2
    bx, by = 3.0, 3.0
    expected = math.hypot(
        max(abs(17.0) - ax - bx, 0.0), max(abs(9.0) - ay - by, 0.0)
    )
    report = spacing_report(placements, footprints, [_threshold(0.0)])
    assert report.violations == ()  # 阈值 0 恒合格（clearance >= 0）
    probe = spacing_report(placements, footprints, [_threshold(expected + 0.01)])
    assert probe.violations[0].clearance_m == pytest.approx(expected)


def test_overlap_clamps_to_zero() -> None:
    """两轴皆重叠：净距 clamp 0（重叠=零净距非负值）。"""
    placements = {"a": (0.0, 0.0, 0.0), "b": (1.0, 1.0, 0.0)}
    footprints = {"a": (10.0, 10.0), "b": (10.0, 10.0)}
    report = spacing_report(placements, footprints, [_threshold(6.0, "ERROR")])
    assert len(report.violations) == 1
    assert report.violations[0].clearance_m == 0.0
    assert report.violations[0].severity == "ERROR"


def test_footprint_none_excluded_and_uncalculated_sorted() -> None:
    """footprint None=该单元不入对+uncalculated sorted（未计算降级面）。"""
    placements = {"c": (0.0, 0.0, 0.0), "a": (100.0, 0.0, 0.0), "b": (0.0, 0.0, 0.0)}
    footprints = {"c": (4.0, 4.0), "a": None, "b": (4.0, 4.0)}
    report = spacing_report(placements, footprints, [_threshold(0.0)])
    assert report.uncalculated == ("a",)  # sorted
    # 仅 (b,c) 成对（a 不入对）；阈值 0 → 零违规
    assert report.violations == ()
    close = spacing_report(placements, footprints, [_threshold(6.0)])
    assert [(v.a, v.b) for v in close.violations] == [("b", "c")]


def test_placement_missing_footprint_key_is_uncalculated() -> None:
    """placements 键缺于 footprints=防御面同 None（未计算，非崩）。"""
    placements = {"a": (0.0, 0.0, 0.0), "b": (50.0, 0.0, 0.0)}
    report = spacing_report(placements, {"b": (4.0, 4.0)}, [_threshold(0.0)])
    assert report.uncalculated == ("a",)
    assert report.violations == ()


def test_scoped_threshold_applies_only_to_member_pairs() -> None:
    """限定对：frozenset 成员双方命中才判（非成员对/半成员对均不判）。"""
    placements = {
        "nongsuo": (0.0, 0.0, 0.0),
        "xiaohua": (1.0, 0.0, 0.0),
        "cass": (1.0, 1.0, 0.0),
    }
    footprints = dict.fromkeys(placements, (4.0, 4.0))
    scoped = spacing_report(
        placements,
        footprints,
        [_threshold(10.0, "ERROR", frozenset({"nongsuo", "xiaohua"}))],
    )
    assert [(v.a, v.b, v.severity) for v in scoped.violations] == [
        ("nongsuo", "xiaohua", "ERROR")
    ]
    # 阈值空集=frozenset() 恒不命中（kb 限定对解析空集语义）；None=全对通用
    empty_scope = spacing_report(
        placements, footprints, [_threshold(0.5, "ERROR", frozenset())]
    )
    assert empty_scope.violations == ()
    universal = spacing_report(placements, footprints, [_threshold(0.5)])
    assert len(universal.violations) == 3  # 三对全判（重叠 0 < 0.5）


def test_multiple_thresholds_same_pair_rows_sorted_deterministic() -> None:
    """同对多阈值：逐阈值成行；(min,max) 字典序+阈值/severity 全序确定。"""
    placements = {"a": (0.0, 0.0, 0.0), "b": (2.0, 0.0, 0.0), "c": (60.0, 0.0, 0.0)}
    footprints = {"a": (4.0, 4.0), "b": (4.0, 4.0), "c": (4.0, 4.0)}
    thresholds = [
        _threshold(8.0, "WARN"),
        _threshold(4.0, "ERROR"),
        _threshold(8.0, "ERROR"),
    ]
    report = spacing_report(placements, footprints, thresholds)
    # (a,b) 重叠 0 违反全部三阈值；(a,c)/(b,c) 净距 56 合格
    rows = [(v.a, v.b, v.threshold_m, v.severity) for v in report.violations]
    assert rows == [("a", "b", 4.0, "ERROR"), ("a", "b", 8.0, "ERROR"), ("a", "b", 8.0, "WARN")]
    again = spacing_report(placements, footprints, thresholds)
    assert again == report  # 双跑全等（冻结 dataclass 值相等）


def test_violation_pair_ordering_lexicographic() -> None:
    """violations 按 (min(a,b), max(a,b)) 字典序——对内无序输入归一。"""
    placements = {"z2": (0.0, 0.0, 0.0), "m1": (1.0, 0.0, 0.0), "a9": (2.0, 0.0, 0.0)}
    footprints = dict.fromkeys(placements, (4.0, 4.0))
    report = spacing_report(placements, footprints, [_threshold(1.0)])
    pairs = [(v.a, v.b) for v in report.violations]
    assert pairs == [("a9", "m1"), ("a9", "z2"), ("m1", "z2")]


def test_empty_inputs_return_empty_report() -> None:
    """空摆放/空阈值=空报告（未放置项目零违规零未计算）。"""
    assert spacing_report({}, {}, [_threshold(6.0)]) == spacing_report({}, {}, [])
    report = spacing_report({"a": (0.0, 0.0, 0.0)}, {"a": (4.0, 4.0)}, [])
    assert report.violations == () and report.uncalculated == ()
