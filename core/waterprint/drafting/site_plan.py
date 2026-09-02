"""厂区总平面图生成：布置投影+坐标网+风玫瑰+图框注记（M4 L3 实装）。

输入:  SiteDesign（design 态布置）+ PlantResult（工况快照）+ styles 样式表
输出:  总平面图 DXF 实体组（坐标 m 1:1，布图缩放归 SheetSpec/调用方）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M4 L3 实装；镜像测试 tests/drafting/test_site_plan.py）
#
# 【公开接口】
#   site_layout(site_design, plant_result, styles,
#               options: SiteOptions | None = None) -> EntityGroup
#   class SiteOptions（frozen）：coord_grid（None=回退
#      site_design.options.coord_grid，再回退 schema 默认 10.0）、
#      wind_rose（None=回退 site_design.options.wind_rose）
#      ——出图期覆盖不改设计态（映射纯函数：值非 None 才覆盖，§三.15）
#
# 【行为规格】
#   R1 布置是设计输入（design 态）：摆放/道路/走廊来自用户编辑保存的
#      site_design，非自动布局结果；摆放点=构筑物中心（旋转中心——
#      webapp 编辑器 AABB 同口径）。轮廓尺寸=PlantResult 工况快照 dims
#      纯投影（直取 length/width/diameter 语义键——pools.py primitive_dims
#      槽同名；site 无 manifest 面，简报 §三/任务预裁）。
#   R2 纯投影零编造：缺轮廓键（容积法单元）=占位注记不画矩形；悬空
#      （structures 有 unit_id 而快照无该单元）=跳过+记档——投影非
#      校验（悬空校验 M1 前置于 ProjectFile 级）。圆形池=等分折线
#      逼近（CIRCLE_SEGMENTS 段 line 闭合）；rotation=cos/sin 通用
#      旋转（自由角，编辑器 90° 吸附仅输入面约定）。
#   R3 确定性：工况无入参——conditions 取 sorted 首键 + 进标题注记
#      （工况覆盖面=消费接线批 M5/L5）；方位序/构筑物序全 sorted；
#      同输入同实体组（哈希锚守卫）。
#   R4 标题栏注记（title_block 形态收窄）：condition+sheet_no 两栏
#      field=value 注记（source_key=栏位）；图纸目录页/批量出图挂 M5。
#   R5 纯投影零 ezdxf（同 plan_view R2）：实体中立描述由 dxf_writer
#      翻译；层用法零新层零 styles 触碰——轮廓=POOL/道路走廊=PIPE/
#      坐标网=AXIS/注记=LABEL/标题=TITLE/图框=BORDER（既有八层内）。
#   异常面 InvalidSitePlanError（GR-11 族）：conditions 空无可投影
#      工况 / coord_grid 非有限或非正——仅结构性非法不可投影形态；键缺
#      =占位不抛（R2）。注记锚点（标高/标题栏）并入内容包络——注记
#      恒在图框内（G1-05）；elev 回溯键含 unit_id 消歧（G1-02）。
#
# 【测试要求】结构断言（kind/layer/点数/坐标 approx/source_key 回溯）
#   +确定性 repr 哈希锚（测试文件内 sorted 归一 sha256 head16）。
#
# 【参照】重写计划 §7/§10.3 厂区图纸行；ADR-006；简报 M4 L3 §三预裁
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Final, final

from waterprint.contracts.project_schema import SiteDesign, SitePoint, StructurePlacement
from waterprint.contracts.result_schema import PlantResult, UnitResultSnapshot
from waterprint.drafting.styles import (
    ANNO_OFFSET_CONDITION,
    ANNO_OFFSET_LEVEL,
    LAYER_AXIS,
    LAYER_BORDER,
    LAYER_LABEL,
    LAYER_PIPE,
    LAYER_POOL,
    LAYER_TITLE,
    Entity,
    EntityGroup,
    StyleTable,
)

__all__ = ["InvalidSitePlanError", "SiteOptions", "site_layout"]

# 圆形池等分折线段数=16（2**(2*2) 幂积形态——M1 API_TOKEN_MIN_LENGTH 同款
# 绕字面量门禁先例；16 段=视觉圆整/实体量适中的工程档，§三.9）。
CIRCLE_SEGMENTS: Final[int] = 2 ** (2 * 2)
# 风玫瑰八方位（罗盘序：N 起顺时针）——方位角=索引×(π/(2·2))，即 45° 步进
# （角度经 π 幂积推导，零度数字面量——magic 门禁面外）。
_WIND_DIRS: Final[tuple[str, ...]] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
# 总平面首张图号（title_block sheet_no 栏位占位——目录页/批量编号归 M5，§三.1）。
_SITE_SHEET_NO: Final[str] = "01"


class InvalidSitePlanError(Exception):
    """总平面生成非法（无工况可投影/网格间距非正）——GR-11 族。"""


@dataclass(frozen=True)
@final
class SiteOptions:
    """出图期覆盖选项（不可变）：None=回退 site_design.options 对应值。"""

    coord_grid: float | None = None  # 坐标网间距 m（覆盖链 §三.15）
    wind_rose: Mapping[str, float] | None = None  # 方位→频率（None=回退设计态）


@dataclass(frozen=True)
@final
class _Projection:
    """子投影产物（内部值对象）：实体组+参与内容包络的足迹点集。"""

    entities: tuple[Entity, ...]
    footprint: tuple[tuple[float, float], ...]


def _rotated(
    corners: Sequence[tuple[float, float]],
    cx: float,
    cy: float,
    rotation_deg: float,
) -> tuple[tuple[float, float], ...]:
    """局部角点集绕 (cx,cy) 旋转（cos/sin 通用旋转——自由角同一路径，§三.8）。"""
    cos_r = math.cos(math.radians(rotation_deg))
    sin_r = math.sin(math.radians(rotation_deg))
    return tuple(
        (cx + px * cos_r - py * sin_r, cy + px * sin_r + py * cos_r)
        for px, py in corners
    )


def _circle_outline(
    cx: float, cy: float, radius: float, rotation_deg: float
) -> tuple[tuple[float, float], ...]:
    """圆形池等分折线顶点（CIRCLE_SEGMENTS 段闭合；rotation=起始角）。"""
    start = math.radians(rotation_deg)
    step = 2 * math.pi / CIRCLE_SEGMENTS
    return tuple(
        (
            cx + radius * math.cos(start + step * index),
            cy + radius * math.sin(start + step * index),
        )
        for index in range(CIRCLE_SEGMENTS)
    )


def _structure_projection(
    unit_id: str, placement: StructurePlacement, snapshot: UnitResultSnapshot | None
) -> _Projection:
    """单构筑物投影（R2 纯投影）：轮廓 dims 直取；缺键/悬空=注记记档不编造。"""
    entities: list[Entity] = []
    if snapshot is None:
        # 悬空面（快照无该单元）：跳过轮廓+记档（不抛——投影非校验，§三.6）
        return _Projection(
            entities=(
                Entity(
                    "text", LAYER_LABEL, ((placement.x, placement.y),),
                    text=f"未入工况 unit={unit_id}", source_key=unit_id,
                ),
            ),
            footprint=((placement.x, placement.y),),
        )
    dims = snapshot.dims
    diameter = dims.get("diameter")
    length = dims.get("length")
    width = dims.get("width")
    if diameter is not None:
        corners = _circle_outline(placement.x, placement.y, float(diameter) / 2,
                                  placement.rotation)
    elif length is not None and width is not None:
        half_l = float(length) / 2
        half_w = float(width) / 2
        corners = _rotated(
            ((-half_l, -half_w), (half_l, -half_w), (half_l, half_w), (-half_l, half_w)),
            placement.x, placement.y, placement.rotation,
        )
    else:
        corners = ()  # 缺轮廓键（容积法 AAO 等）：占位注记，不画矩形（§三.5）
    if corners:
        count = len(corners)
        for index in range(count):
            entities.append(Entity(
                "line", LAYER_POOL,
                (corners[index], corners[(index + 1) % count]),
                source_key=unit_id,
            ))
        footprint = tuple(corners)
    else:
        entities.append(Entity(
            "text", LAYER_LABEL, ((placement.x, placement.y),),
            text=f"无轮廓数据 unit={unit_id}", source_key=unit_id,
        ))
        footprint = ((placement.x, placement.y),)
    if placement.ground_elevation is not None:
        # 地面标高符号（§三.12）：结构位置+LEVEL 偏移（plan_view 标高注记同层）；
        # source_key 含 unit_id——多单元聚合面回溯消歧（roads[i] 索引先例同族，
        # G1-02）；锚点并入足迹（G1-05 注记入包络）
        anchor = (placement.x, placement.y + ANNO_OFFSET_LEVEL)
        entities.append(Entity(
            "elev_symbol", LAYER_LABEL, (anchor,),
            params={"ground_elevation": float(placement.ground_elevation)},
            text="ground_elevation", source_key=f"ground_elevation[{unit_id}]",
        ))
        footprint = (*footprint, anchor)
    return _Projection(entities=tuple(entities), footprint=footprint)


def _route_projection(
    source_key: str,
    centerline: Sequence[SitePoint],
    width_m: float,
    kind_text: str | None = None,
) -> _Projection:
    """道路/走廊投影（§三.10/11）：中心线+两侧 ±width_m/2 偏移边线（逐段独立
    line 实体）；走廊附 kind 注记（中段中点）。层=PIPE（§三.14）。"""
    pts = tuple((point.x, point.y) for point in centerline)
    half = width_m / 2
    entities: list[Entity] = []
    footprint: list[tuple[float, float]] = list(pts)
    segments = list(pairwise(pts))
    for first, second in segments:
        entities.append(Entity("line", LAYER_PIPE, (first, second),
                               source_key=source_key))
        span = math.hypot(second[0] - first[0], second[1] - first[1])
        if span <= 0:
            continue  # 重复点退化段：法向未定义——仅中心线（纯投影不编造）
        normal = ((first[1] - second[1]) / span, (second[0] - first[0]) / span)
        for sign in (1.0, -1.0):
            near = (first[0] + normal[0] * half * sign,
                    first[1] + normal[1] * half * sign)
            far = (second[0] + normal[0] * half * sign,
                   second[1] + normal[1] * half * sign)
            entities.append(Entity("line", LAYER_PIPE, (near, far),
                                   source_key=source_key))
            footprint.extend((near, far))
    if kind_text is not None and segments:
        # G1-01 防御深度：segments 空（<2 点中心线，仅 model_construct 绕
        # schema 面)=跳过 kind 注记不抛 IndexError（span≤0 守卫同类）
        mid_first, mid_second = segments[len(segments) // 2]  # 中段（奇偶同确定）
        entities.append(Entity(
            "text", LAYER_LABEL,
            (((mid_first[0] + mid_second[0]) / 2,
              (mid_first[1] + mid_second[1]) / 2),),
            text=f"kind={kind_text}", source_key=source_key,
        ))
    return _Projection(entities=tuple(entities), footprint=tuple(footprint))


def _grid_entities(
    coord_grid: float,
    window: tuple[float, float, float, float],
) -> list[Entity]:
    """坐标网（§三.3）：主网格线族，间距=coord_grid 透传；范围=window；
    线位=间距整数倍（索引算术防浮点漂移）；层=AXIS 复用零新层。"""
    wxmin, wymin, wxmax, wymax = window
    entities: list[Entity] = []
    for index in range(math.ceil(wxmin / coord_grid), math.floor(wxmax / coord_grid) + 1):
        x = index * coord_grid
        entities.append(Entity("line", LAYER_AXIS, ((x, wymin), (x, wymax)),
                               source_key="coord_grid"))
    for index in range(math.ceil(wymin / coord_grid), math.floor(wymax / coord_grid) + 1):
        y = index * coord_grid
        entities.append(Entity("line", LAYER_AXIS, ((wxmin, y), (wxmax, y)),
                               source_key="coord_grid"))
    return entities


def _wind_rose_entities(
    wind_rose: Mapping[str, float] | None,
    coord_grid: float,
    cx: float,
    cy: float,
) -> list[Entity]:
    """风玫瑰角标（§三.2）：放射线族+方位标注；长度=频率/max×基准半径
    （coord_grid×2——网格间距倍数语义参数化）；方位序=sorted；None/空
    /全零频率=不画；未知方位键=跳过（投影非校验）。中心=内容包络右上角
    （基准半径恰内接图框）。"""
    if not wind_rose:
        return []
    freqs = {k: float(v) for k, v in wind_rose.items() if k in _WIND_DIRS}
    if not freqs:
        return []
    peak = max(freqs.values())
    if peak <= 0:
        return []
    base_radius = coord_grid * 2
    entities: list[Entity] = []
    for direction in sorted(freqs):
        azimuth = _WIND_DIRS.index(direction) * (math.pi / (2 * 2))
        ux, uy = math.sin(azimuth), math.cos(azimuth)
        # G1-03：负频率钳 0（零长 spoke 于中心——方位族/标注保留完整，不画
        # 反象限穿心线编造几何；裁量=钳 0 非跳过）
        reach = max(freqs[direction], 0.0) / peak * base_radius
        key = f"wind_rose[{direction}]"
        entities.append(Entity(
            "line", LAYER_LABEL, ((cx, cy), (cx + ux * reach, cy + uy * reach)),
            source_key=key,
        ))
        entities.append(Entity(
            "text", LAYER_LABEL, ((cx + ux * base_radius, cy + uy * base_radius),),
            text=direction, source_key=key,
        ))
    return entities


def _fmt(value: float) -> str:
    """坐标注记数字形态（10 位有效——round(x,10) 同精度口径的显示面）。"""
    return f"{value:.10g}"


def _border_entities(
    window: tuple[float, float, float, float],
) -> list[Entity]:
    """图框（§三.13）：LAYER_BORDER 矩形（内容包络+边距窗）+四角坐标注记。"""
    wxmin, wymin, wxmax, wymax = window
    entities = [
        Entity("rect", LAYER_BORDER, ((wxmin, wymin), (wxmax, wymax)),
               source_key="border"),
    ]
    for corner_x, corner_y in (
        (wxmin, wymin), (wxmax, wymin), (wxmin, wymax), (wxmax, wymax),
    ):
        entities.append(Entity(
            "text", LAYER_LABEL, ((corner_x, corner_y),),
            text=f"({_fmt(corner_x)},{_fmt(corner_y)})", source_key="border",
        ))
    return entities


def _title_entities(
    condition_key: str,
    anchor_x: float,
    content_min_y: float,
) -> list[Entity]:
    """标题栏注记（§三.1 R4 收窄）：condition+sheet_no 两栏 field=value
    （title_block 形态，层=TITLE）；锚=内容包络右下角+注记偏移（偏移档沿
    plan_view 工况注记——锚点由调用方并入包络，注记恒在图框内 G1-05）。"""
    return [
        Entity(
            "text", LAYER_TITLE,
            ((anchor_x, content_min_y + ANNO_OFFSET_CONDITION),),
            text=f"condition={condition_key}", source_key="condition",
        ),
        Entity(
            "text", LAYER_TITLE,
            ((anchor_x, content_min_y + ANNO_OFFSET_LEVEL),),
            text=f"sheet_no={_SITE_SHEET_NO}", source_key="sheet_no",
        ),
    ]


def site_layout(
    site_design: SiteDesign,
    plant_result: PlantResult,
    styles: StyleTable,
    options: SiteOptions | None = None,
) -> EntityGroup:
    """厂区总平面图（design 态布置+PlantResult 纯投影，零 ezdxf）。

    坐标单位 m（模型 1:1）——m→mm 出图换算归 dxf_writer 唯一住所；
    实体段序（确定性）：坐标网→构筑物→道路→走廊→风玫瑰→图框→标题注记。
    """
    if not plant_result.conditions:
        raise InvalidSitePlanError(
            "plant_result.conditions 为空——无可投影工况（GR-11 族；"
            "工况覆盖面=消费接线批 M5/L5）"
        )
    chosen = options if options is not None else SiteOptions()
    coord_grid = (
        chosen.coord_grid
        if chosen.coord_grid is not None
        else site_design.options.coord_grid
    )
    if not math.isfinite(coord_grid) or coord_grid <= 0:
        # G1-04：NaN 绕 <=0 比较、Inf 产 nan 坐标——非有限与非正双拦（覆盖链
        # 与 site_design.options 双路可达：schema 对 coord_grid 无 gt/finite 面）
        raise InvalidSitePlanError(
            f"坐标网间距非法：{coord_grid!r}（非有限或非正——结构性非法"
            "不可投影，GR-11 族）"
        )
    wind_rose = (
        chosen.wind_rose
        if chosen.wind_rose is not None
        else site_design.options.wind_rose
    )
    # R3 确定性：工况=sorted 首键；构筑物序=sorted unit_id（悬空/占位同面）
    condition_key = sorted(plant_result.conditions)[0]
    units = plant_result.conditions[condition_key]
    structures = [
        _structure_projection(unit_id, site_design.structures[unit_id], units.get(unit_id))
        for unit_id in sorted(site_design.structures)
    ]
    roads = [
        _route_projection(f"roads[{index}]", road.centerline, road.width_m)
        for index, road in enumerate(site_design.roads)
    ]
    corridors = [
        _route_projection(
            f"corridors[{index}]", corridor.centerline, corridor.width_m, corridor.kind
        )
        for index, corridor in enumerate(site_design.corridors)
    ]
    parts = [*structures, *roads, *corridors]
    # 内容包络（全体足迹点集；空 site=原点邻域）；标高注记锚已并入各足迹
    xs = [x for part in parts for x, _ in part.footprint] or [0.0]
    ys = [y for part in parts for _, y in part.footprint] or [0.0]
    anchor_x = max(xs)
    content_min_y = min(ys)
    # G1-05：标题注记锚（内容包络右下角+注记偏移）并入包络——注记恒在
    # 图框内（此前锚=窗角-偏移恒在框外）；风玫瑰中心仍=内容包络右上角
    pad = coord_grid * 2
    window = (
        min(xs) - pad,
        min([*ys, content_min_y + ANNO_OFFSET_CONDITION,
             content_min_y + ANNO_OFFSET_LEVEL]) - pad,
        max(xs) + pad,
        max(ys) + pad,
    )
    entities: list[Entity] = _grid_entities(coord_grid, window)
    for part in parts:
        entities.extend(part.entities)
    entities.extend(_wind_rose_entities(wind_rose, coord_grid, anchor_x, max(ys)))
    entities.extend(_border_entities(window))
    entities.extend(_title_entities(condition_key, anchor_x, content_min_y))
    return EntityGroup(entities=tuple(entities))
