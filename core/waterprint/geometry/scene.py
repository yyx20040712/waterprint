"""场景图 schema 与装配：图元/变换/语义标签的场景树（全厂 <100ms 的总入口）。

输入:  PlantResult（几何类字段 ID）+ assumptions（超高/壁厚等）
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
#   build_scene(plant_result, assumptions, condition_key) -> SceneGraph
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
#
# 【测试要求】确定性（同结果双跑同 JSON）、instance_count 汇总正确、
#   语义标签集合稳定、性能基准（<100ms）。
#
# 【参照】重写计划 §10.5/§12.6/§16 A7/§18.1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Final, final

from waterprint.contracts.result_schema import PlantResult
from waterprint.geometry.internals import internal_instances
from waterprint.geometry.pools import Node, Primitive, pool_primitives

__all__ = ["SCENE_VERSION", "Node", "Primitive", "SceneGraph", "build_scene"]

# 场景版本（R4：坐标约定 Y-up + 单位 m 在此声明——前端渲染器唯一读取口）。
SCENE_VERSION: Final[str] = "waterprint-scene-1/y-up/m"
_INSTANCE_KINDS: Final[frozenset[str]] = frozenset({
    "aerator", "paddle", "media", "gate", "lamp", "module", "decant",
    "pump", "mech_cleaner", "pipe", "opening", "disk", "machine",  # disk=M3D1；machine=M3D2 脱水机
})
_UNIT_GAP: Final[float] = 1.0  # 单元排布模型间隙 m（占位——工程间距归 M5 布置）


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


def build_scene(
    plant_result: PlantResult,
    assumptions: Mapping[str, float],
    condition_key: str,
) -> SceneGraph:
    """全厂场景图装配正门（R1 纯投影：同结果同场景图，<100ms 预算 R5）。

    站序=executor 拓扑执行序；沿 X 轴按池体占位长顺序排布（缺槽单元以
    间隙占位）；台数类经对照表 instance_counts→InstanceGroup（节点
    instance_count 汇总——R3 千级构件一次 draw call 的数据前提）。
    """
    if condition_key not in plant_result.conditions:
        raise KeyError(
            f"工况 {condition_key!r} 不在结果（合法 "
            f"{sorted(plant_result.conditions)}——scene 按工况索引，R4）"
        )
    snapshots = plant_result.conditions[condition_key]
    nodes: list[Node] = []
    root: list[str] = []
    cursor_x = 0.0
    for unit_id, snapshot in snapshots.items():
        if unit_id == "inlet":
            continue
        pool_nodes = _shift(pool_primitives(snapshot, assumptions), cursor_x)
        nodes.extend(pool_nodes)
        root.extend(node.node_id for node in pool_nodes)
        for group in internal_instances(snapshot, assumptions):
            origin = group.placements.get("origin", (0.0, 0.0))
            assert isinstance(origin, tuple)
            origin_x = float(origin[0]) + cursor_x
            origin_y = float(origin[1]) if len(origin) > 1 else 0.0
            nodes.append(
                Node(
                    node_id=f"{unit_id}::{group.semantic}",
                    primitive=group.prototype,
                    semantic=group.semantic,
                    position=(origin_x, origin_y, 0.0),
                    instance_count=group.count,
                )
            )
        cursor_x += _unit_extent(pool_nodes) + _UNIT_GAP
    return SceneGraph(
        root=tuple(root), nodes=tuple(nodes),
        scene_version=SCENE_VERSION, condition_key=condition_key,
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
