"""boundary 镜像测试：用地红线越界校核（OBB 四角内含/射线法/确定性）。

输入:  waterprint.geometry.boundary 公开符号
输出:  校核契约断言（SPC2 简报 §2.2——四角全在内含边上=合规、任一角
       严格在外=违规；射线法奇偶+边上容差 1e-9=内+顶点序无关+凹多边形；
       boundary 空/len<3=零违规零报错；message 形态「unit X 有 N 个
       角点超出红线」；全序确定性=unit_id sorted）
"""

from __future__ import annotations

import math

from waterprint.geometry.boundary import BoundaryRule, boundary_violations

_RULE = BoundaryRule(severity="ERROR")

_SQUARE = ((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0))

# L 形凹多边形：覆盖 x∈[0,100]×y∈[0,60] ∪ x∈[0,60]×y∈[60,100]
# （凹口=东北象限 x∈(60,100]×y∈(60,100]）
_L_SHAPE = (
    (0.0, 0.0),
    (100.0, 0.0),
    (100.0, 60.0),
    (60.0, 60.0),
    (60.0, 100.0),
    (0.0, 100.0),
)


def test_all_corners_inside_compliant() -> None:
    """四角全内：合规零违规（severity 透传面不触发）。"""
    placements = {"a": (50.0, 50.0, 30.0)}
    footprints = {"a": (10.0, 6.0)}
    assert boundary_violations(placements, footprints, _SQUARE, _RULE) == ()


def test_corner_exactly_on_edge_is_inside() -> None:
    """贴边=内：OBB 角点恰落红线上（容差 1e-9）——不计违规。

    45° 旋转方形底角 y=5√2-5√2=0 恰在底边（IEEE754 残差 ~1e-16 <
    容差 1e-9——两段式判定先行边上归内）。
    """
    center_y = 5.0 * math.sqrt(2.0)
    placements = {"a": (50.0, center_y, 45.0)}
    footprints = {"a": (10.0, 10.0)}
    assert boundary_violations(placements, footprints, _SQUARE, _RULE) == ()


def test_any_corner_outside_violates_with_message() -> None:
    """任一角严格在外=违规：unit_id/severity/message 三字段，N=外角数。"""
    placements = {"a": (50.0, 4.0, 0.0)}
    footprints = {"a": (10.0, 10.0)}  # 角 y=-1（2 角外）与 y=9（2 角内）
    rows = boundary_violations(placements, footprints, _SQUARE, _RULE)
    assert len(rows) == 1
    row = rows[0]
    assert row.unit_id == "a"
    assert row.severity == "ERROR"
    assert row.message == "unit a 有 2 个角点超出红线"


def test_rotated_corner_outside_counts() -> None:
    """旋转 OBB 单角出界：45° 方形底角越底边 0.5 m——恰 1 角。"""
    center_y = 5.0 * math.sqrt(2.0) - 0.5
    placements = {"a": (50.0, center_y, 45.0)}
    footprints = {"a": (10.0, 10.0)}
    rows = boundary_violations(placements, footprints, _SQUARE, _RULE)
    assert len(rows) == 1
    assert rows[0].message == "unit a 有 1 个角点超出红线"


def test_concave_polygon_notch_is_outside() -> None:
    """凹多边形：凹口内（东北象限）=外；同一红线 L 形主体内=合规。"""
    placements = {
        "notch": (80.0, 80.0, 0.0),  # 凹口中心——四角全在凹口内=外
        "body": (30.0, 30.0, 0.0),  # L 主体内=合规
    }
    footprints = {"notch": (10.0, 10.0), "body": (10.0, 10.0)}
    rows = boundary_violations(placements, footprints, _L_SHAPE, _RULE)
    assert [row.unit_id for row in rows] == ["notch"]
    assert rows[0].message == "unit notch 有 4 个角点超出红线"


def test_empty_or_short_boundary_zero_violations() -> None:
    """boundary 空/len<3 防御：零违规零报错（未划界不校核）。"""
    placements = {"a": (500.0, 500.0, 0.0)}
    footprints = {"a": (10.0, 10.0)}
    assert boundary_violations(placements, footprints, (), _RULE) == ()
    short = ((0.0, 0.0), (1.0, 1.0))
    assert boundary_violations(placements, footprints, short, _RULE) == ()


def test_vertex_order_reversal_irrelevant() -> None:
    """顶点序顺/逆无关：红线逆转后判定逐字同。"""
    placements = {"a": (50.0, 4.0, 0.0), "b": (50.0, 50.0, 0.0)}
    footprints = {"a": (10.0, 10.0), "b": (10.0, 10.0)}
    forward = boundary_violations(placements, footprints, _SQUARE, _RULE)
    reversed_square = tuple(reversed(_SQUARE))
    backward = boundary_violations(placements, footprints, reversed_square, _RULE)
    assert forward == backward
    assert [row.unit_id for row in forward] == ["a"]


def test_deterministic_full_order_and_double_run() -> None:
    """全序确定性：多违规行按 unit_id sorted；双跑全等（纯函数零加料）。"""
    placements = {
        "z9": (150.0, 150.0, 0.0),
        "a1": (5.0, 5.0, 0.0),
        "m5": (-2.0, 50.0, 0.0),
    }
    footprints = dict.fromkeys(placements, (10.0, 10.0))
    rows = boundary_violations(placements, footprints, _SQUARE, _RULE)
    # a1 角点贴边（0/10 恰在红线上）=内不列；m5/z9 全外
    assert [row.unit_id for row in rows] == ["m5", "z9"]
    assert rows[0].message == "unit m5 有 2 个角点超出红线"
    assert rows[1].message == "unit z9 有 4 个角点超出红线"
    again = boundary_violations(placements, footprints, _SQUARE, _RULE)
    assert again == rows


def test_footprint_none_or_missing_skipped() -> None:
    """footprint None/缺键=未计算不入校核（spacing R2 同构——无 OBB 角可判）。"""
    placements = {"a": (500.0, 500.0, 0.0), "b": (500.0, 500.0, 0.0)}
    assert boundary_violations(placements, {"a": None}, _SQUARE, _RULE) == ()
    assert boundary_violations(placements, {}, _SQUARE, _RULE) == ()
