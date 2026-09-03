"""池体/渠道/水面几何图元生成：单体构筑物的盒体/拉伸/水面包络。

输入:  单元结果（几何字段 ID：池长/宽/有效水深/超高/渠道断面…）+ assumptions
输出:  单体的图元+变换列表（供 scene.build_scene 装配）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/geometry/test_pools.py）
#
# 【公开接口】
#   pool_primitives(unit_result, assumptions) -> tuple[Node, ...]
#   channel_primitives(unit_result, assumptions) -> tuple[Node, ...]
#   water_surface_node(unit_result, assumptions) -> Node
#
# 【行为规格】
#   R1 尺寸字段只按 field_id 取（如 pool_length/pool_width/
#      water_depth/freeboard）；几何层零业务公式——池体尺寸是计算
#      结果，不在此重新计算（纯投影铁律）。
#   R2 超高/壁厚/板厚类构造尺寸来自 assumptions（带出处），标注于
#      节点 source_assumption_keys（三维上可查假设来源）。
#   R3 水面语义：water_surface 独立图元（半透明材质由前端按 semantic
#      渲染）；水位 = 池底 + 水深，这一加法是几何投影允许的唯一运算。
#   R4 并联池组：n_active 池按 manifest 工况语义排布（列间距来自
#      assumptions）；检修工况 n-1 池时场景图标注缺失池位置（警示渲染）。
#   R5 多格池（AAO 厌氧/缺氧/好氧分格）：分格尺寸来自结果字段，
#      隔墙图元 semantic=partition。
#
# 【测试要求】图元尺寸与结果字段一致、水面高程=底+深、
#   n_active 排布与检修标注、假设键标注完整。
#
# 【参照】重写计划 §10.5/§14.1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from waterprint.contracts.drawing_projection import (
    PROJECTION_TABLE,
    UnitProjection,
)
from waterprint.contracts.result_schema import UnitResultSnapshot
from waterprint.registry.assumptions import assumption

__all__ = ["InvalidGeometryError", "Node", "Primitive", "channel_primitives",
           "pool_primitives", "water_surface_node"]

_FREEBOARD_KEY = "safety.superheight"
_SPACING_KEY = "geometry.pool.spacing"


class InvalidGeometryError(Exception):
    """池体图元生成非法（对照表缺行/槽位键缺）——GR-11 族。"""


@dataclass(frozen=True)
@final
class Primitive:
    """图元声明（不可变）：kind + 规范单位 m 裸值 dims + 语义标签。

    类型定义于本文件（图元域类型——scene.py 正门再导出；internals 同向
    消费，杜绝 scene↔pools↔internals 环）。
    """

    kind: str  # box/cylinder/plane/water_surface/extrusion
    dims: Mapping[str, float]
    semantic: str  # pool_wall/water_surface/aerator/paddle/media/pipe…

    def __post_init__(self) -> None:
        """dims 只读快照（T3A-01 同款）。"""
        object.__setattr__(self, "dims", dict(self.dims))


@dataclass(frozen=True)
@final
class Node:
    """场景节点（不可变）：图元 + 语义 + 局部变换 + 实例数 + 假设来源键。"""

    node_id: str
    primitive: Primitive
    semantic: str
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)
    children: tuple[Node, ...] = ()
    instance_count: int = 1
    source_assumption_keys: tuple[str, ...] = ()


def _projection(unit_id: str) -> UnitProjection:
    """对照表行取数（13 单元外=领域异常——表覆盖与单元发现同步冻结）。"""
    projection = PROJECTION_TABLE.get(unit_id)
    if projection is None:
        raise InvalidGeometryError(
            f"单元 {unit_id!r} 不在 UF-32 对照表（三维取数前提——"
            "非市政 13 单元的表行随对应批次扩展）"
        )
    return projection


def pool_primitives(
    unit_result: UnitResultSnapshot, assumptions: Mapping[str, float]
) -> tuple[Node, ...]:
    """单体池体图元（R1 纯投影：尺寸只按对照表 primitive_dims 槽位取）。

    box 槽（length/width/depth）→池壁盒体；cylinder 槽（diameter/depth）
    →圆柱池体；两者皆缺→空组（AAO 等容积法单元 v1 无池体图元——显式
    注记归报告）。R3 水位=池底+水深唯一允许运算归 water_surface_node。
    """
    projection = _projection(unit_result.unit_id)
    dims = unit_result.dims
    nodes: list[Node] = []
    length_key = projection.primitive_dims.get("length")
    width_key = projection.primitive_dims.get("width")
    depth_key = projection.primitive_dims.get("depth")
    diameter_key = projection.primitive_dims.get("diameter")
    uid = unit_result.unit_id
    if length_key and width_key and depth_key:
        nodes.append(
            Node(
                node_id=f"{uid}::pool_wall",
                primitive=Primitive(
                    "box",
                    {"length": float(dims[length_key]),
                     "width": float(dims[width_key]),
                     "depth": float(dims[depth_key])},
                    "pool_wall",
                ),
                semantic="pool_wall",
                source_assumption_keys=(_FREEBOARD_KEY,),
            )
        )
    if diameter_key and depth_key:
        nodes.append(
            Node(
                node_id=f"{uid}::pool_cylinder",
                primitive=Primitive(
                    "cylinder",
                    {"diameter": float(dims[diameter_key]),
                     "depth": float(dims[depth_key])},
                    "pool_wall",
                ),
                semantic="pool_wall",
                source_assumption_keys=(_FREEBOARD_KEY,),
            )
        )
    return tuple(nodes)


def channel_primitives(
    unit_result: UnitResultSnapshot, assumptions: Mapping[str, float]
) -> tuple[Node, ...]:
    """渠道图元（extrusion 拉伸体：v1 按表 depth 槽声明，无槽=显式空组）。"""
    projection = _projection(unit_result.unit_id)
    dims = unit_result.dims
    depth_key = projection.primitive_dims.get("depth")
    if depth_key is None:
        return ()  # 表无渠道槽=非渠道单元（显式空组）
    return (
        Node(
            node_id=f"{unit_result.unit_id}::channel",
            primitive=Primitive("extrusion",
                                {"depth": float(dims[depth_key])}, "channel"),
            semantic="channel",
        ),
    )


def water_surface_node(
    unit_result: UnitResultSnapshot, assumptions: Mapping[str, float]
) -> Node:
    """水面图元（R3：水位=池底+水深——几何投影唯一允许的加法运算）。

    池底基准=0.0（模型局部坐标；全厂地面标高经 elevation 总线数据由
    app 装配传入——R4 全局装配归消费方）；水深经对照表
    section_keys.water_depth 取（缺键=0 水面占位，语义同 profile INFO）。
    足迹键（L5R A-S1）：水面几何=池面投影——box 池取 length/width 同源
    键、cylinder 池取 diameter 双向外接方（v1 渲染面近似：方角超出圆壁
    ≈0.207d——相邻池排布跨界复核归后续圆形水面图元批），前端消费
    length/width 渲染池面（缺键=1×1 兜底方块=接线即显性缺陷）。
    """
    projection = _projection(unit_result.unit_id)
    dims = unit_result.dims
    depth_key = projection.section_keys.get("water_depth")
    water_depth = float(dims[depth_key]) if depth_key else 0.0
    freeboard = assumption(_FREEBOARD_KEY, assumptions)
    length_key = projection.primitive_dims.get("length")
    width_key = projection.primitive_dims.get("width")
    diameter_key = projection.primitive_dims.get("diameter")
    if length_key and width_key:
        footprint = {"length": float(dims[length_key]),
                     "width": float(dims[width_key])}
    elif diameter_key:
        span = float(dims[diameter_key])
        footprint = {"length": span, "width": span}
    else:
        footprint = {}
    return Node(
        node_id=f"{unit_result.unit_id}::water_surface",
        primitive=Primitive(
            "water_surface",
            {"level": water_depth, "freeboard": freeboard, **footprint},
            "water_surface",
        ),
        semantic="water_surface",
        position=(0.0, 0.0, water_depth),
        source_assumption_keys=(_FREEBOARD_KEY,),
    )
