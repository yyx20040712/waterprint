"""间距校核裁判：摆放+足迹+阈值 → 违规/未计算报告（纯函数，OBB 精确净距）。

输入:  placements（unit_id→(x,y,rotation_deg) 米/度）+footprints（unit_id→
       (w,h) 米，None=未计算不入对）+thresholds（结构化阈值——DSL 解析归
       server 装配面，core 零 DSL）
输出:  SpacingReport（violations 按 (min(a,b),max(a,b)) 字典序+uncalculated
       sorted——确定性全序，双跑全等）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（L4b 简报 §二冻结签名 2026-09-03；SPC2 简报 §2.1 OBB 扩
# 2026-09-05；镜像测试 tests/geometry/test_spacing.py）
#
# 【公开接口】
#   spacing_report(placements, footprints, thresholds) -> SpacingReport
#   SpacingThreshold(unit_kinds, min_clearance_m, severity)
#       —— unit_kinds: frozenset[str] | None：None=全对通用；frozenset=
#       限定对成员集（装配面以本项目 unit_id 集传入——kb unit_kinds 经
#       server design.nodes kind 解析后的成员集；空 frozenset=恒不命中）；
#       core 对成员串零语义假设（不透明 id，kind 映射不进 core——三参
#       冻结签名零偏移）
#   SpacingViolation(a, b, clearance_m, threshold_m, severity)——对内
#       a<b（sorted 序）；clearance_m=越限对净距（重叠/相交/包含=0）
#   SpacingReport(violations, uncalculated)
#
# 【行为规格】
#   R1 OBB 精确净距（SPC2 §2.1，替换 L4b AABB 投影口径）：净距=两旋转
#       矩形（OBB）真形间距——{A4 顶点×B4 边，B4 顶点×A4 边}32 对点-线段
#       距取 min（分离凸体最近特征对必为顶点-边）；**归零判定先行**：边对
#       相交（线段相交测试——十字穿插无顶点内含时点-边距恒>0）或一方全含
#       （任一顶点在对内）→ clearance=0.0；线段零长退化为点-点距（零宽
#       足迹防面）；旋转 0° 恒等旧 AABB 式（回归锚——单轴分离/对角斜距
#       两形态，test_rotation_zero_identity 显式断言）。webapp siteGeometry
#       measureToNearest 同式镜像（所见即所得——SPC2 笔④同步）。
#   R2 未计算降级（预裁 4）：footprint None（或缺键——防御面同 None）=
#       该单元不入对+入 uncalculated（sorted）；其余单元照常成对校核
#       ——编辑器部分可用语义。
#   R3 阈值适用（预裁 2/6）：threshold.unit_kinds is None=全对通用；
#       frozenset=双方 unit_id 均须 ∈ 集合才判。违规定义=净距 <
#       min_clearance_m（>= 语义——恰等合格）；同对多阈值逐条成行。
#   R4 确定性：violations 全序键 (min(a,b), max(a,b), threshold_m,
#       severity)；uncalculated sorted——同输入双跑全等（纯函数零加料）。
#   R5 纯投影铁律：本模块零 IO/零 DSL 解析/零 kind 映射——工程阈值
#       数值真源在 kb 数据面（server 装配透传），core 不另立数值权威。
#
# 【测试要求】旋转 0° AABB 恒等锚/黄金角 30/45/90° 解析值（容差 1e-9）/
#   归零族（边对相交/全含）/零宽退化/轴向净距/重叠 0/未计算降级/限定对/
#   全对通用/多阈值全序/字典序/空输入（test_spacing.py）。
#
# 【参照】SPC2 简报 §2.1（点-边枚举+归零判定先行终裁）；webapp
#   siteplan/lib/siteGeometry.ts（OBB 同式镜像）；scene.py 模块形态先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final

__all__ = ["SpacingReport", "SpacingThreshold", "SpacingViolation", "spacing_report"]

_Point = tuple[float, float]


@dataclass(frozen=True)
@final
class SpacingThreshold:
    """阈值条目（结构化三字段——kb expression 解析产物，core 零 DSL）。"""

    unit_kinds: frozenset[str] | None  # None=全对通用；frozenset=限定对成员集
    min_clearance_m: float
    severity: str


@dataclass(frozen=True)
@final
class SpacingViolation:
    """违规行（对内 a<b；clearance_m=净距，重叠/相交/包含=0）。"""

    a: str
    b: str
    clearance_m: float
    threshold_m: float
    severity: str


@dataclass(frozen=True)
@final
class SpacingReport:
    """校核报告（violations 全序+uncalculated sorted——R4）。"""

    violations: tuple[SpacingViolation, ...]
    uncalculated: tuple[str, ...]


def _obb_corners(
    position: tuple[float, float, float], footprint: tuple[float, float]
) -> tuple[_Point, ...]:
    """摆位+足迹 → OBB 四角（局部 (±w/2,±h/2) 旋转平移；序=逆时针环）。"""
    center_x, center_y, rotation_deg = position
    width, height = footprint
    rad = math.radians(rotation_deg)
    cos, sin = math.cos(rad), math.sin(rad)
    half_w, half_h = width / 2, height / 2
    return tuple(
        (center_x + lx * cos - ly * sin, center_y + lx * sin + ly * cos)
        for lx, ly in (
            (-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h),
        )
    )


def _edges(corners: tuple[_Point, ...]) -> tuple[tuple[_Point, _Point], ...]:
    """闭合环棱序列（末角→首角补齐——顶点序即权威，消费方补闭合段）。"""
    count = len(corners)
    return tuple(
        (corners[index], corners[(index + 1) % count]) for index in range(count)
    )


def _point_segment_distance(
    point: _Point, start: _Point, end: _Point
) -> float:
    """点-线段距（投影参数 clamp [0,1]；零长线段退化点-点距）。"""
    px, py = point
    (x1, y1), (x2, y2) = start, end
    dx, dy = x2 - x1, y2 - y1
    span_sq = dx * dx + dy * dy
    if span_sq == 0.0:
        return math.hypot(px - x1, py - y1)
    param = ((px - x1) * dx + (py - y1) * dy) / span_sq
    param = 0.0 if param < 0.0 else (1.0 if param > 1.0 else param)
    return math.hypot(px - (x1 + param * dx), py - (y1 + param * dy))


def _cross(origin: _Point, first: _Point, second: _Point) -> float:
    """三点叉积 z 分量（方向判定原语——相交/内含共用）。"""
    return (first[0] - origin[0]) * (second[1] - origin[1]) - (
        first[1] - origin[1]
    ) * (second[0] - origin[0])


def _segments_intersect(
    first: tuple[_Point, _Point], second: tuple[_Point, _Point]
) -> bool:
    """两线段相交判定（CLRS 四方向+共线落段三态；恰触=相交→归零）。"""
    (p1, p2), (p3, p4) = first, second

    def _between(edge: tuple[_Point, _Point], probe: _Point) -> bool:
        (ex1, ey1), (ex2, ey2) = edge
        return min(ex1, ex2) <= probe[0] <= max(ex1, ex2) and (
            min(ey1, ey2) <= probe[1] <= max(ey1, ey2)
        )

    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    if ((d1 > 0.0 and d2 < 0.0) or (d1 < 0.0 and d2 > 0.0)) and (
        (d3 > 0.0 and d4 < 0.0) or (d3 < 0.0 and d4 > 0.0)
    ):
        return True
    return (
        (d1 == 0.0 and _between(second, p1))
        or (d2 == 0.0 and _between(second, p2))
        or (d3 == 0.0 and _between(first, p3))
        or (d4 == 0.0 and _between(first, p4))
    )


def _point_in_box(point: _Point, corners: tuple[_Point, ...]) -> bool:
    """点在凸四边形内（含边上——叉积同号；共线棱=0 恒一致，R1 全含判定）。"""
    signs: list[bool] = []
    for (x1, y1), (x2, y2) in _edges(corners):
        turn = (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)
        if turn > 0.0:
            signs.append(True)
        elif turn < 0.0:
            signs.append(False)
    return not (True in signs and False in signs)


def _touching_or_overlapping(
    corners_a: tuple[_Point, ...], corners_b: tuple[_Point, ...]
) -> bool:
    """归零判定先行（R1）：边对相交或任一顶点在对内（全含/部分搭接）。"""
    if any(
        _segments_intersect(edge_a, edge_b)
        for edge_a in _edges(corners_a)
        for edge_b in _edges(corners_b)
    ):
        return True
    return any(_point_in_box(point, corners_b) for point in corners_a) or any(
        _point_in_box(point, corners_a) for point in corners_b
    )


def _clearance(
    position_a: tuple[float, float, float], footprint_a: tuple[float, float],
    position_b: tuple[float, float, float], footprint_b: tuple[float, float],
) -> float:
    """两 OBB 精确净距（R1）：相交/全含→0.0；否则 32 对点-线段距取 min。"""
    corners_a = _obb_corners(position_a, footprint_a)
    corners_b = _obb_corners(position_b, footprint_b)
    if _touching_or_overlapping(corners_a, corners_b):
        return 0.0
    return min(
        _point_segment_distance(point, edge[0], edge[1])
        for corners, other in ((corners_a, corners_b), (corners_b, corners_a))
        for point in corners
        for edge in _edges(other)
    )


def _applies_to_pair(threshold: SpacingThreshold, a: str, b: str) -> bool:
    """阈值适用判定：None=全对；frozenset=双方均须成员（R3——空集恒不中）。"""
    return threshold.unit_kinds is None or (
        a in threshold.unit_kinds and b in threshold.unit_kinds
    )


def spacing_report(
    placements: Mapping[str, tuple[float, float, float]],
    footprints: Mapping[str, tuple[float, float] | None],
    thresholds: Sequence[SpacingThreshold],
) -> SpacingReport:
    """间距校核正门（纯函数——同输入同报告，R4 确定性）。

    未计算单元（footprint None/缺键）不入对、入 uncalculated（R2）；
    成对单元按全部适用阈值逐条判越限（净距 < min_clearance_m，R3）。
    """
    uncalculated = tuple(
        sorted(unit_id for unit_id in placements if footprints.get(unit_id) is None)
    )
    usable = sorted(
        unit_id for unit_id in placements if footprints.get(unit_id) is not None
    )
    violations: list[SpacingViolation] = []
    for index, a in enumerate(usable):
        footprint_a = footprints[a]
        assert footprint_a is not None  # usable 过滤后必非 None（类型收窄）
        for b in usable[index + 1:]:
            footprint_b = footprints[b]
            assert footprint_b is not None
            clearance = _clearance(placements[a], footprint_a, placements[b], footprint_b)
            violations.extend(
                SpacingViolation(
                    a=a, b=b, clearance_m=clearance,
                    threshold_m=threshold.min_clearance_m, severity=threshold.severity,
                )
                for threshold in thresholds
                if clearance < threshold.min_clearance_m
                and _applies_to_pair(threshold, a, b)
            )
    violations.sort(key=lambda v: (min(v.a, v.b), max(v.a, v.b), v.threshold_m, v.severity))
    return SpacingReport(violations=tuple(violations), uncalculated=uncalculated)
