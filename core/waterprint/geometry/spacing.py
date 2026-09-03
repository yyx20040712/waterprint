"""间距校核裁判：摆放+足迹+阈值 → 违规/未计算报告（纯函数，AABB 口径）。

输入:  placements（unit_id→(x,y,rotation_deg) 米/度）+footprints（unit_id→
       (w,h) 米，None=未计算不入对）+thresholds（结构化阈值——DSL 解析归
       server 装配面，core 零 DSL）
输出:  SpacingReport（violations 按 (min(a,b),max(a,b)) 字典序+uncalculated
       sorted——确定性全序，双跑全等）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（L4b 简报 §二冻结签名 2026-09-03；镜像测试 tests/geometry/test_spacing.py）
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
#       a<b（sorted 序）；clearance_m=越限对净距（重叠 clamp 0）
#   SpacingReport(violations, uncalculated)
#
# 【行为规格】
#   R1 AABB 净距口径（总控预裁 5）：旋转矩形的轴对齐投影半轴
#       hx=(w·|cosθ|+h·|sinθ|)/2、hy=(w·|sinθ|+h·|cosθ|)/2——与 webapp
#       lib/projectSite.ts measureToNearest/halfExtents 同口径（编辑器
#       测距与 server 校核所见即所得）；净距=hypot(max(gapX,0),max(gapY,0))
#       ，两轴皆重叠=clamp 0；OBB 精确净距挂账（简报 §六）。
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
# 【测试要求】轴向净距/旋转半轴/重叠 0/未计算降级/限定对/全对通用/
#   多阈值全序/字典序/空输入九面（test_spacing.py）。
#
# 【参照】L4 简报 §一 L4b/§二/§三预裁 4~6；webapp projectSite.ts:440-479
#   （AABB 口径同源）；scene.py 模块形态先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final

__all__ = ["SpacingReport", "SpacingThreshold", "SpacingViolation", "spacing_report"]


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
    """违规行（对内 a<b；clearance_m=净距，重叠=0）。"""

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


def _half_extents(
    width: float, height: float, rotation_deg: float
) -> tuple[float, float]:
    """旋转矩形轴对齐投影半轴（webapp halfExtents 同式——R1 所见即所得）。"""
    rad = math.radians(rotation_deg)
    cos = abs(math.cos(rad))
    sin = abs(math.sin(rad))
    return (width * cos + height * sin) / 2, (width * sin + height * cos) / 2


def _clearance(
    position_a: tuple[float, float, float], footprint_a: tuple[float, float],
    position_b: tuple[float, float, float], footprint_b: tuple[float, float],
) -> float:
    """两 AABB 边到边净距：单轴分离取分离轴距，两轴皆重叠 clamp 0（R1）。"""
    ax, ay = _half_extents(footprint_a[0], footprint_a[1], position_a[2])
    bx, by = _half_extents(footprint_b[0], footprint_b[1], position_b[2])
    gap_x = abs(position_b[0] - position_a[0]) - ax - bx
    gap_y = abs(position_b[1] - position_a[1]) - ay - by
    return math.hypot(max(gap_x, 0.0), max(gap_y, 0.0))


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
