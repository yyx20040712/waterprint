# -*- python -*-
"""管廊装配（C2-3d V5）：design.edges → 单元间高架方管图元。

输入:  design.edges 原始字典序列（server 透传）+单元中心/顶标高/
        X 向占位长（build_scene 装配期收集）
输出:  pipe_nodes()（pipe_water/pipe_sludge 两语义 box——架顶=全厂
        最高构筑物顶+净空防穿模；管端缩进至结构缘）

规格说明（C2-3d 批——briefs/task-C2-3d-plan.md §二 V5+呈裁①同批
  core 扩面授权+glm 三/四轮断头管收口）：
  - 纯装配零业务推导（§10.5/A7 同构——几何推导在 geometry 层=正位）；
  - 两色制（任一端 sludge_ 前缀→泥棕；双端水线→水蓝——画布
    streamColorOf 同语义；v1 判据=unit_id 线前缀命名约定[catalog
    在册全库一致]——registry 轻量判别源挂账）；recycle 拓环标记
    不区分线型（3D 统一实体管——虚线语义归 2D 画布面）；
  - 防御消费：畸形边/自环/inlet 端/未摆放端静默跳过（design 上游
    已验证——装配层纯投影零异常纪律）；单元对去重（端口级分流挂账）；
  - scene.py 段抽离（C2-3d R 段：500 行预算收限——boundary/internals
    同件先例）。
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Final

from waterprint.geometry.pools import Node, Primitive

# C2-3d 管廊装配常量：断面 0.8×0.8 m 方管+净空 1.2 m（glm 一轮 0.8→1.2：
# 圆池顶视觉贴管；架顶=全厂最高构筑物顶+净空——数据驱动防穿模；
# 中心距≤净空视为重合退化不产出）。
_PIPE_SECTION_M: Final[float] = 0.8
_PIPE_CLEARANCE_M: Final[float] = 1.2
_PIPE_SEMANTIC_WATER: Final[str] = "pipe_water"
_PIPE_SEMANTIC_SLUDGE: Final[str] = "pipe_sludge"
_PIPE_SLUDGE_PREFIX: Final[str] = "sludge_"  # 泥线判据=命名前缀（v1 口径——catalog 在册全库一致）
# 管端缩进上限比例（每端 ≤ 中心距×0.25——防过缩；魔法数门禁真源化）
_PIPE_INSET_MAX_FRAC: Final[float] = 0.25
def _edge_unit(edge: Mapping[str, Any], side: str) -> str | None:
    """design.edges 原始字典端点单元提取（防御读——畸形边静默跳过：
    design 上游已验证，装配层按纯投影零异常纪律消费）。"""
    ref = edge.get(side)
    if not isinstance(ref, Mapping):
        return None
    unit_id = ref.get("unit_id")
    return unit_id if isinstance(unit_id, str) else None


def pipe_nodes(
    edges: Sequence[Mapping[str, Any]],
    centers: Mapping[str, tuple[float, float]],
    tops: Mapping[str, float],
    extents: Mapping[str, float],
) -> tuple[Node, ...]:
    """单元间高架管廊装配（C2-3d）：design.edges → 两单元中心连线方管。

    - 架顶=全厂最高构筑物顶+净空（数据驱动防穿模——全场景统一标高
      管廊层语义）；两端单元均在场景才画（inlet 无实体/未摆放边不画
      ——总装诚实语义同构）；单元对去重（多端口对同一对=一管，端口
      级分流归后续批）；自环/中心重合退化跳过；
    - **管端缩进**（glm 三轮断头管/穿池顶收口）：管长=中心距-两端
      单元半占位长（clamp 至多 span/4 防过缩）——管止于结构缘不悬空
      突出；缩尽（≤断面）退化跳过；
    - 两色制（任一端 sludge_ 前缀→泥棕；双端水线→水蓝——画布
      streamColorOf 同语义；v1 判据=unit_id 线前缀命名约定[catalog
      在册全库一致]——registry 轻量判别源挂账）；recycle 拓扑标记
      不区分线型（3D 统一实体管——虚线语义归 2D 画布面）。
    """
    rack_z = max(tops.values(), default=0.0) + _PIPE_CLEARANCE_M
    seen: set[frozenset[str]] = set()
    pipes: list[Node] = []
    for edge in edges:
        src = _edge_unit(edge, "src")
        dst = _edge_unit(edge, "dst")
        if (
            src is None
            or dst is None
            or src == dst
            or src not in centers
            or dst not in centers
        ):
            continue
        pair = frozenset((src, dst))
        if pair in seen:
            continue
        seen.add(pair)
        ax, ay = centers[src]
        bx, by = centers[dst]
        span_full = math.hypot(bx - ax, by - ay)
        if span_full <= _PIPE_CLEARANCE_M:
            continue
        # 管端缩进：两端各让半占位（每端 clamp ≤ span/4——管止于结构缘）
        inset = min(
            extents.get(src, 0.0) / 2, span_full * _PIPE_INSET_MAX_FRAC
        ) + min(extents.get(dst, 0.0) / 2, span_full * _PIPE_INSET_MAX_FRAC)
        span = span_full - inset
        if span <= _PIPE_SECTION_M:
            continue
        # 缩进后中点沿原方向回移（管段中点=全段中点-内法向×(缩进差/2)
        # 对称缩进时中点不变；非对称缩进按端缩进差校正）
        shrink_src = min(extents.get(src, 0.0) / 2, span_full * _PIPE_INSET_MAX_FRAC)
        shrink_dst = min(extents.get(dst, 0.0) / 2, span_full * _PIPE_INSET_MAX_FRAC)
        offset = (shrink_src - shrink_dst) / 2
        unit_dx = (bx - ax) / span_full
        unit_dy = (by - ay) / span_full
        mid_x = (ax + bx) / 2 + unit_dx * offset
        mid_y = (ay + by) / 2 + unit_dy * offset
        semantic = (
            _PIPE_SEMANTIC_SLUDGE
            if src.startswith(_PIPE_SLUDGE_PREFIX)
            or dst.startswith(_PIPE_SLUDGE_PREFIX)
            else _PIPE_SEMANTIC_WATER
        )
        pipes.append(
            Node(
                node_id=f"pipe::{src}::{dst}",
                primitive=Primitive(
                    "box",
                    {"length": span, "width": _PIPE_SECTION_M,
                     "depth": _PIPE_SECTION_M},
                    semantic,
                ),
                semantic=semantic,
                position=(mid_x, mid_y, rack_z),
                rotation=(0.0, 0.0, math.atan2(by - ay, bx - ax)),
            )
        )
    return tuple(pipes)


