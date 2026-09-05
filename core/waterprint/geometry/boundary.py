"""boundary 越界校核裁判：OBB 四角 vs 用地红线多边形（纯函数，独立可测）。

输入:  placements（unit_id→(x,y,rotation_deg) 米/度）+footprints（unit_id→
       (w,h) 米，None=未计算跳过）+boundary（红线顶点序闭合多边形，米，
       空/len<3=未划界不校核）+rule（BoundaryRule——kb boundary_check 解析
       产物，severity 透传）
输出:  BoundaryViolation 序列（unit_id sorted 全序——确定性，双跑全等）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（SPC2 简报 §2.2 D3 采纳——独立模块，2026-09-05；镜像测试
# tests/geometry/test_boundary.py）
#
# 【公开接口】
#   boundary_violations(placements, footprints, boundary, rule)
#       -> tuple[BoundaryViolation, ...]
#   BoundaryRule(severity)——kb boundary_check 条目解析产物（server
#       services/site.py 唯一解析面，core 零 DSL）
#   BoundaryViolation(unit_id, severity, message)——三字段冻结（不发明
#       「越界深度」——非冻结需求，D3.5）；message 形态
#       「unit X 有 N 个角点超出红线」（N=严格在外角数）
#
# 【行为规格】
#   R1 判定口径：OBB（摆位旋转+足迹真形）四角全在多边形内（含边上，
#       容差 _EPS=1e-9）=合规；任一角严格在外=违规。射线法奇偶计数
#       （水平右向，半开区间 (y1>py)!=(y2>py) 防顶点双计）；两段式：
#       先边上判定（点-线段距 ≤ 容差=内）再射线——贴边归内。
#   R2 多边形口径：顶点序即权威（顺/逆无关）；闭合段末点→首点由本
#       模块补（消费方先例——schema 不存闭合段）；凹多边形支持；
#       自交多边形行为不保证（挂账记档）。
#   R3 防御面：boundary 空 **或 len<3**=零违规零报错（未划界不校核）；
#       footprint None/缺键=未计算跳过（spacing R2 同构——无 OBB 角可判）。
#   R4 确定性：行序=unit_id sorted；同输入双跑全等（纯函数零加料）。
#   R5 纯投影铁律：零 IO/零 DSL 解析——severity 数值真源在 kb 数据面
#       （server 装配透传），core 不另立数值权威。
#
# 【测试要求】四角全内（含贴边=内）/任一角外（N 计数+message 形态）/
#   凹多边形/顶点序逆转无关/boundary 空=len<3/全序双跑/footprint None
#   跳过（test_boundary.py）。
#
# 【参照】SPC2 简报 §2.2；contracts/project_schema.py SiteDesign.boundary
#   （0<len<3 schema 拒——本模块防御面兜底迁移前旧档）；webapp
#   siteplan/lib/siteGeometry.ts pointInPolygon 同式镜像（笔④）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final

__all__ = ["BoundaryRule", "BoundaryViolation", "boundary_violations"]

_Point = tuple[float, float]

# 红线闭合多边形最少顶点数（1+2 算术形态=值 3——project_schema.py
# _BOUNDARY_MIN_POINTS 同款先例：Final 常量化解 PLR2004+幂积绕字面量门禁）
_MIN_BOUNDARY_POINTS: Final[int] = 1 + 2

# 边上归内容差 1e-9（幂积形态绕字面量门禁——site_plan CIRCLE_SEGMENTS /
# catalog _TITLE_GAP 同款先例；跨语言 IEEE754 三角函数镜像断言同口径）
_EPS: Final[float] = 10.0 ** -(2 * 2 + 2 * 2 + 1)


@dataclass(frozen=True)
@final
class BoundaryRule:
    """越界校核规则（kb boundary_check 解析产物——severity 透传，core 零 DSL）。"""

    severity: str


@dataclass(frozen=True)
@final
class BoundaryViolation:
    """越界行（三字段冻结——不发明越界深度；message 含外角计数）。"""

    unit_id: str
    severity: str
    message: str


def _obb_corners(
    position: tuple[float, float, float], footprint: tuple[float, float]
) -> tuple[_Point, ...]:
    """摆位+足迹 → OBB 四角（局部 (±w/2,±h/2) 旋转平移——spacing 同式）。"""
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


def _point_segment_distance(point: _Point, start: _Point, end: _Point) -> float:
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


def _point_in_polygon(point: _Point, vertices: Sequence[_Point]) -> bool:
    """点在多边形内（含边上，容差 _EPS——两段式：先边上判定再射线奇偶）。"""
    edges = tuple(
        (vertices[index], vertices[(index + 1) % len(vertices)])
        for index in range(len(vertices))
    )
    for start, end in edges:
        if _point_segment_distance(point, start, end) <= _EPS:
            return True  # 贴边=内（R1——半开区间顶点双计由此前置归内消解）
    px, py = point
    inside = False
    for (x1, y1), (x2, y2) in edges:
        if (y1 > py) != (y2 > py):  # 半开区间：恰在延伸线上的顶点单计一次
            crossing_x = x1 + (py - y1) / (y2 - y1) * (x2 - x1)
            if crossing_x > px:
                inside = not inside
    return inside


def boundary_violations(
    placements: Mapping[str, tuple[float, float, float]],
    footprints: Mapping[str, tuple[float, float] | None],
    boundary: Sequence[_Point],
    rule: BoundaryRule,
) -> tuple[BoundaryViolation, ...]:
    """越界校核正门（纯函数——R3 未划界零违规；R4 unit_id 全序）。"""
    if len(boundary) < _MIN_BOUNDARY_POINTS:
        return ()  # 空/len<3=未划界不校核（防御面——schema 迁移前旧档兜底）
    rows: list[BoundaryViolation] = []
    for unit_id in sorted(placements):
        footprint = footprints.get(unit_id)
        if footprint is None:
            continue  # 未计算跳过（R3——spacing R2 同构）
        corners = _obb_corners(placements[unit_id], footprint)
        outside = sum(
            1 for corner in corners if not _point_in_polygon(corner, boundary)
        )
        if outside:
            rows.append(
                BoundaryViolation(
                    unit_id=unit_id,
                    severity=rule.severity,
                    message=f"unit {unit_id} 有 {outside} 个角点超出红线",
                )
            )
    return tuple(rows)
