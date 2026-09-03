"""场景图 schema 与装配：图元/变换/语义标签的场景树（全厂 <100ms 的总入口）。

输入:  PlantResult（几何类字段 ID）+ assumptions（超高/壁厚等）
       + site_design（L5a site 级摆放——None/空 structures=回退 X 轴排布；
       L6 roads/corridors 条带+boundary 红线沿 site 级装配挂载）
输出:  SceneGraph（可序列化 JSON：图元声明 + 局部变换 + 实例数 + 语义标签）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/geometry/test_scene.py）
#
# 【公开接口】
#   class Primitive(不可变)：kind（box/cylinder/plane/water_surface/
#      extrusion）、dims（规范单位 m 裸值）、semantic（语义标签：
#      pool_wall/water_surface/aerator/paddle/media/pipe…）
#   class Node(不可变)：node_id、primitive、position/rotation/scale
#      （局部变换）、children、instance_count（InstancedMesh 依据）
#   build_scene(plant_result, assumptions, condition_key,
#               *, site_design=None) -> SceneGraph   # L5 site 级扩展
#   class SceneGraph：root + nodes + scene_version + condition_key
#
# 【行为规格】
#   R1 纯投影：场景图只由结果字段与假设生成，同结果同场景图（确定性、
#      可快照回归）；改参数 → 计算变 → 场景图自动变，不存在
#      "改了图忘改模型"（§10.2 关键约束）。
#   R2 图元组合优先（§12.6）：池壁=盒体、水面=半透明盒、渠道=拉伸体；
#      CSG 仅开口/穿孔场景（由 internals 显式声明 kind=opening），
#      禁止全模型布尔。
#   R3 千级重复构件必须 instance_count 表达（曝气头/填料：每类构件
#      一次 draw call 的数据前提）；数量来自 compute 结果（台数/个数
#      字段 ID），不在几何层重新推算。
#   R4 单位与坐标：场景单位 m、Y-up 或 Z-up 在 scene_version 声明
#      （前端渲染器读取，禁止两处各自假设）；地面标高来自 elevation
#      总线数据（经 app 装配传入）。
#   R5 性能预算：全厂场景图生成 <100ms（§18.1，pytest-benchmark 守卫）；
#      图元量级 ~ 每单元几百声明，纯 Python/初等算术完成。
#   R6 site 级总装（L5a）：site_design.structures 非空=已摆放单元按
#      placement 定位（position=(x, y, ground_elevation 或 0.0)、
#      rotation=(0, 0, radians(度))——度→弧度换算归 core 装配层，前端
#      零业务几何）；未摆放单元不进场景图（总装语义=只摆已放）；
#      structures 空/None=回退站序 X 轴占位排布（既有调用方零改动）；
#      boundary 非空=地面红线闭合折线图元（semantic="site_boundary"，
#      z=0 零高度；闭合段末点→首点由消费方补——顶点序即权威）。
#      水面/渠道图元接线收口（有池体且有 water_depth 键附水面；
#      渠道走既有 depth 槽）；roads/corridors 条带图元（L6 收编——
#      kind="strip"，分段四边形角点 core 预计算压平进 dims（每段环序
#      4 角点，消费端每 4 点组两三角——宽度消费归 core），semantic=
#      site_road / site_corridor:{kind}（开放 str 唯一可复原通道），
#      node_id=site::road[i] / site::corridor[i] 逐条平铺入 root；
#      挂载沿 boundary 先例（site_design 非 None 且列表非空即挂，不受
#      structures 空回退门影响）；span≤0 退化段跳过，全退化=整条
#      零节点（3D 无面积即无图元——诚实呈现不编造）。
#
# 【测试要求】确定性（同结果双跑同 JSON）、instance_count 汇总正确、
#   语义标签集合稳定、site 模式摆放/未摆放/红线断言、strip 角点/退化
#   段断言（L6）、性能基准（<100ms）。
#
# 【参照】重写计划 §10.5/§12.6/§16 A7/§18.1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import pairwise
from typing import Final, final

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.project_schema import (
    SiteDesign,
    SitePoint,
    StructurePlacement,
)
from waterprint.contracts.result_schema import PlantResult, UnitResultSnapshot
from waterprint.geometry.internals import internal_instances
from waterprint.geometry.pools import (
    Node,
    Primitive,
    channel_primitives,
    pool_primitives,
    water_surface_node,
)

__all__ = ["SCENE_VERSION", "Node", "Primitive", "SceneGraph", "build_scene"]

# 场景版本（R4：存储坐标约定 + 单位 m 在此声明——前端渲染器唯一读取口）。
# L5a 步进 -2：site 摆放+rotation 放行（语义变即步进，前端门同步）。
# L5R 轴标签勘正：存储坐标=Z-up（X 东 Y 北 Z 标高——DXF 出图/IFC/
# SitePoint 同族），-2 步进时的 "y-up" 标签系实现期误记（G1-01 根因），
# 首次推送前就地勘正——渲染层 projectScene 换轴至 three Y-up（消费约定
# 名不改版本号：R 轮不改线格式，仅正名）。
# L6 步进 -3：roads/corridors strip 图元收编（新 kind+新 semantic=
# 场景图语义变——「语义变即步进」先例）。
SCENE_VERSION: Final[str] = "waterprint-scene-3/z-up/m"
_INSTANCE_KINDS: Final[frozenset[str]] = frozenset({
    "aerator", "paddle", "media", "gate", "lamp", "module", "decant",
    "pump", "mech_cleaner", "pipe", "opening", "disk", "machine",  # disk=M3D1；machine=M3D2 脱水机
})
_UNIT_GAP: Final[float] = 1.0  # 单元排布模型间隙 m（占位——工程间距归 M5 布置）
_SITE_BOUNDARY_NODE_ID: Final[str] = "site::boundary"
_SITE_BOUNDARY_KIND: Final[str] = "polyline"
_SITE_BOUNDARY_SEMANTIC: Final[str] = "site_boundary"
_STRIP_KIND: Final[str] = "strip"  # 条带图元（L6：roads/corridors 分段四边形角点）
_SITE_ROAD_SEMANTIC: Final[str] = "site_road"
_SITE_CORRIDOR_SEMANTIC_PREFIX: Final[str] = "site_corridor:"  # + kind 拼接
_SITE_ROAD_NODE_ID_PREFIX: Final[str] = "site::road["  # + 下标 + "]"
_SITE_CORRIDOR_NODE_ID_PREFIX: Final[str] = "site::corridor["  # + 下标 + "]"


@dataclass(frozen=True)
@final
class SceneGraph:
    """场景图（不可变）：root + 节点表 + 版本/工况声明（R4）。"""

    root: tuple[str, ...]
    nodes: tuple[Node, ...]
    scene_version: str
    condition_key: str


def _unit_extent(nodes: tuple[Node, ...]) -> float:
    """单元 X 向占位长度（模型排布推位用——pool 图元长/径取大）。"""
    return max(
        (
            node.primitive.dims.get("length", 0.0)
            + node.primitive.dims.get("diameter", 0.0)
            for node in nodes
        ),
        default=_UNIT_GAP,
    )


def _ground_z(placement: StructurePlacement) -> float:
    """单元基准标高：ground_elevation None→0.0（池底基准 0.0 铁律不变）。"""
    return (
        placement.ground_elevation
        if placement.ground_elevation is not None
        else 0.0
    )


def _water_surface(
    snapshot: UnitResultSnapshot,
    assumptions: Mapping[str, float],
    pool_nodes: tuple[Node, ...],
) -> Node | None:
    """水面条件接线：有池体图元且有 water_depth 键（L5a 收口——缺键不占位）。"""
    if not pool_nodes:
        return None
    projection = PROJECTION_TABLE.get(snapshot.unit_id)
    depth_key = (
        projection.section_keys.get("water_depth") if projection else None
    )
    if depth_key is None or depth_key not in snapshot.dims:
        return None
    return water_surface_node(snapshot, assumptions)


def _boundary_node(site_design: SiteDesign) -> Node:
    """地面红线图元：闭合折线顶点序压平进 dims（x0/y0/x1/y1…，z=0）。

    Primitive.dims 是 str→float 映射——压平编码是 Mapping 形态下的最小
    载体（L5a 简报「复用现有 Primitive 形态」实现裁量路线）；闭合段
    （末点→首点）不在顶点序内，消费方按 schema 口径补（顶点序即权威）。
    """
    dims: dict[str, float] = {}
    for index, point in enumerate(site_design.boundary):
        dims[f"x{index}"] = point.x
        dims[f"y{index}"] = point.y
    return Node(
        node_id=_SITE_BOUNDARY_NODE_ID,
        primitive=Primitive(_SITE_BOUNDARY_KIND, dims, _SITE_BOUNDARY_SEMANTIC),
        semantic=_SITE_BOUNDARY_SEMANTIC,
    )


def _strip_node(
    node_id: str,
    centerline: Sequence[SitePoint],
    width_m: float,
    semantic: str,
) -> Node | None:
    """条带图元（L6）：分段四边形角点压平进 dims（每段环序 4 角点）。

    每段法向 n=((y0−y1)/span,(x1−x0)/span)（2D 出图 _route_projection
    同款公式，core 侧重写不 import drafting——出图层不可被几何层反向
    依赖）；角点=中心线端点±(width_m/2)·n，环序 (p0+n·h, p1+n·h,
    p1−n·h, p0−n·h)（第 k 段=索引 4k..4k+3，消费端每 4 点组两三角）
    ——宽度消费归 core，前端零业务几何纪律。span≤0 退化段跳过（该段
    4 角点不产出——2D 先例同款）；全退化（有效段数 0）返回 None=整条
    不产出节点（空族语义同构零节点——3D 无面积即无图元，诚实呈现）。
    """
    half = width_m / 2
    dims: dict[str, float] = {}
    corner = 0
    for first, second in pairwise(centerline):
        span = math.hypot(second.x - first.x, second.y - first.y)
        if span <= 0:
            continue
        normal_x = (first.y - second.y) / span
        normal_y = (second.x - first.x) / span
        corners = (
            (first.x + normal_x * half, first.y + normal_y * half),
            (second.x + normal_x * half, second.y + normal_y * half),
            (second.x - normal_x * half, second.y - normal_y * half),
            (first.x - normal_x * half, first.y - normal_y * half),
        )
        for x, y in corners:
            dims[f"x{corner}"] = x
            dims[f"y{corner}"] = y
            corner += 1
    if not dims:
        return None
    return Node(
        node_id=node_id,
        primitive=Primitive(_STRIP_KIND, dims, semantic),
        semantic=semantic,
    )


def _route_nodes(site_design: SiteDesign) -> tuple[Node, ...]:
    """roads/corridors 条带装配（L6）：逐条 strip 节点平铺（全退化跳过）。

    挂载沿 boundary 先例（site_design 非 None 且列表非空即挂，不受
    structures 空回退门影响）；road 恒 site_road，corridor=
    "site_corridor:"+kind；node_id=前缀+列表下标（i 从 0）逐条平铺，
    不设聚合节点。"""
    routes: list[Node] = []
    for index, road in enumerate(site_design.roads):
        route = _strip_node(
            f"{_SITE_ROAD_NODE_ID_PREFIX}{index}]",
            road.centerline,
            road.width_m,
            _SITE_ROAD_SEMANTIC,
        )
        if route is not None:
            routes.append(route)
    for index, corridor in enumerate(site_design.corridors):
        route = _strip_node(
            f"{_SITE_CORRIDOR_NODE_ID_PREFIX}{index}]",
            corridor.centerline,
            corridor.width_m,
            f"{_SITE_CORRIDOR_SEMANTIC_PREFIX}{corridor.kind}",
        )
        if route is not None:
            routes.append(route)
    return tuple(routes)


def _site_overlay(site_design: SiteDesign) -> tuple[Node, ...]:
    """site 级覆盖图元：roads/corridors 条带（L6）+boundary 红线（L5a）。

    装配顺序沿 2D 出图 parts=[*structures, *roads, *corridors, boundary]
    先例（routes 前、boundary 殿后）；boundary 非空即挂（既有先例），
    roads/corridors 列表非空即挂、空列表=零节点不占位。"""
    overlay = list(_route_nodes(site_design))
    if site_design.boundary:
        overlay.append(_boundary_node(site_design))
    return tuple(overlay)


def build_scene(
    plant_result: PlantResult,
    assumptions: Mapping[str, float],
    condition_key: str,
    *,
    site_design: SiteDesign | None = None,
) -> SceneGraph:
    """全厂场景图装配正门（R1 纯投影：同结果同场景图，<100ms 预算 R5）。

    摆放双模（R6）：site_design.structures 非空=已摆放单元按 placement
    定位（度→弧度换算在本装配层），未摆放单元不进场景图；structures 空/
    None=回退站序 X 轴排布（既有调用方零改动）。台数类经对照表
    instance_counts→InstanceGroup（R3 千级构件一次 draw call 数据前提）。
    roads/corridors（L6）：site_design 非 None 且列表非空即挂 strip 条带
    图元（沿 boundary 先例，不受 structures 空回退门影响）。
    """
    if condition_key not in plant_result.conditions:
        raise KeyError(
            f"工况 {condition_key!r} 不在结果（合法 "
            f"{sorted(plant_result.conditions)}——scene 按工况索引，R4）"
        )
    snapshots = plant_result.conditions[condition_key]
    placements = site_design.structures if site_design is not None else {}
    site_mode = bool(placements)
    nodes: list[Node] = []
    root: list[str] = []
    cursor_x = 0.0
    for unit_id, snapshot in snapshots.items():
        if unit_id == "inlet":
            continue
        placement = placements.get(unit_id)
        if site_mode and placement is None:
            continue  # 未摆放单元不进场景图（总装语义=只摆已放——诚实呈现）
        pool_nodes = pool_primitives(snapshot, assumptions)
        unit_nodes: list[Node] = [
            *pool_nodes,
            *channel_primitives(snapshot, assumptions),
        ]
        surface = _water_surface(snapshot, assumptions, pool_nodes)
        if surface is not None:
            unit_nodes.append(surface)
        located = (
            _place_unit(unit_nodes, placement)
            if placement is not None
            else _shift(tuple(unit_nodes), cursor_x)
        )
        nodes.extend(located)
        root.extend(node.node_id for node in located)
        for group in internal_instances(snapshot, assumptions):
            origin = group.placements.get("origin", (0.0, 0.0))
            assert isinstance(origin, tuple)
            origin_x = float(origin[0])
            origin_y = float(origin[1]) if len(origin) > 1 else 0.0
            if placement is not None:
                position = (
                    placement.x + origin_x,
                    placement.y + origin_y,
                    _ground_z(placement),
                )
                rotation = (0.0, 0.0, math.radians(placement.rotation))
            else:
                position = (origin_x + cursor_x, origin_y, 0.0)
                rotation = (0.0, 0.0, 0.0)
            nodes.append(
                Node(
                    node_id=f"{unit_id}::{group.semantic}",
                    primitive=group.prototype,
                    semantic=group.semantic,
                    position=position,
                    rotation=rotation,
                    instance_count=group.count,
                )
            )
        cursor_x += _unit_extent(pool_nodes) + _UNIT_GAP
    if site_design is not None:
        for route in _site_overlay(site_design):
            nodes.append(route)
            root.append(route.node_id)
    return SceneGraph(
        root=tuple(root), nodes=tuple(nodes),
        scene_version=SCENE_VERSION, condition_key=condition_key,
    )


def _place_unit(nodes: list[Node], placement: StructurePlacement) -> tuple[Node, ...]:
    """单元摆放：局部系整体平移 (x, y, 标高) + 绕 Z 旋转（度→弧度装配层）。

    局部 XY 偏移不随旋转变换——v1 单元内局部 XY 恒 0（水面仅 z 分量、
    内部构件 origin 恒 (0,0)），加法形式与旋转矩阵形式退化等价；单元内
    出现非零局部 XY 时升级为旋转矩阵（挂账注记归报告）。
    """
    base = (placement.x, placement.y, _ground_z(placement))
    rz = math.radians(placement.rotation)
    return tuple(
        replace(
            node,
            position=(
                base[0] + node.position[0],
                base[1] + node.position[1],
                base[2] + node.position[2],
            ),
            rotation=(node.rotation[0], node.rotation[1], node.rotation[2] + rz),
        )
        for node in nodes
    )


def _shift(nodes: tuple[Node, ...], cursor_x: float) -> tuple[Node, ...]:
    """池体节点沿 X 平移（dataclasses.replace 保不可变语义）。"""
    return tuple(
        replace(
            node,
            position=(node.position[0] + cursor_x, node.position[1], node.position[2]),
        )
        for node in nodes
    )
