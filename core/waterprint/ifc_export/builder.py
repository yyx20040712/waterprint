"""IFC 模型装配与落盘：场景图池壳体 → IfcBuildingElementProxy 拉伸体（L5c 原型）。

输入:  SceneGraph（geometry 场景图）+ ifcopenshell（LGPL 独立 pip 依赖，C1）
输出:  build_ifc → ifcopenshell 模型；write_ifc → .ifc 文件（tmp+os.replace）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（L5c 原型启动 2026-09-03；镜像测试 tests/ifc_export/test_builder.py）
#
# 【公开接口】
#   build_ifc(scene_graph) -> object（ifcopenshell 模型——公开签名 object，
#      消费方零 ifcopenshell 类型耦合）
#   write_ifc(model, path) -> None（同目录 .tmp → os.replace 原子替换）
#
# 【行为规格】
#   R1 纯投影（§10.2 路线 C）：只消费 SceneGraph 字段，零独立状态；
#      定位是 BIM 互操作投影，非语义中枢。
#   R2 原型范围=池壳体级：semantic=pool_wall 的 box/cylinder 图元 →
#      IfcExtrudedAreaSolid（box→IfcRectangleProfileDef、cylinder→
#      IfcCircleProfileDef，半径=直径/2）；水面/内部构件/渠道/红线
#      不进模型（原型边界）；构筑物=IfcBuildingElementProxy 中性形态
#      ——禁 IfcWall 等建筑语义（未做建筑判定即冒用=语义污染）。
#   R3 确定性：GlobalId=uuid5(固定命名空间, 场景键) 派生（禁随机源）；
#      OwnerHistory CreationDate 与 FILE_NAME time_stamp 固定值定槽
#      （禁 datetime.now）——同 SceneGraph 双跑写出 bytes 恒等。
#   R4 最小集：IfcProject/Site/Building 骨架 + OwnerHistory/Units(SI)/
#      GeometricContext + IfcLocalPlacement 链（site→building→元素，
#      元素摆放=场景图节点变换即 structure 摆放）+ IfcRelAggregates；
#      空间包含 IfcRelContainedInSpatialStructure（L5R G1-02：元素挂
#      building——BIM 查看器按空间树发现元素的主通道，仅摆放链=孤儿）。
#   R5 落盘原子性（GR-38）：tmp+os.replace（project/io.py 同款先例）。
#
# 【测试要求】ifcopenshell 回读往返（层级/element 计数/box extrude 深度/
#   cylinder 半径）、site 摆放进元素 LocalPlacement、双跑 bytes 恒等。
#
# 【参照】重写计划 §10.2/§10.3/§11 R16；LGPL 评估 C1~C6（2026-09-02）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
import os
import uuid
from pathlib import Path
from typing import Final, Literal, cast

import ifcopenshell
import ifcopenshell.guid

from waterprint.geometry import Node, SceneGraph

__all__ = ["build_ifc", "write_ifc"]

_SCHEMA: Final[Literal["IFC4"]] = "IFC4"
_FILE_NAME: Final[str] = "WaterPrint"
_FILE_TIME_STAMP: Final[str] = "1970-01-01T00:00:00"  # 固定值定槽（R3——禁 datetime.now）
_OWNER_CREATION_DATE: Final[int] = 0  # 固定槽：IfcTimeStamp 纪元零点（R3 同源）
_SPACE_DIMENSION: Final[int] = 1 + 2  # 三维几何上下文（白名单操作数形态，1+2 先例）
_MODEL_PRECISION: Final[float] = 1 / ((10 ** 2) * (10 ** 2))  # 0.1mm（同形态）
_GUID_NAMESPACE: Final[uuid.UUID] = uuid.uuid5(uuid.NAMESPACE_DNS, "waterprint-ifc-export")
_POOL_SEMANTIC: Final[str] = "pool_wall"
_BOX_KIND: Final[str] = "box"
_CYLINDER_KIND: Final[str] = "cylinder"
_EXPORTED_KINDS: Final[frozenset[str]] = frozenset({_BOX_KIND, _CYLINDER_KIND})
_AREA_PROFILE: Final[str] = "AREA"
_BODY_ID: Final[str] = "Body"
_SWEPT_SOLID: Final[str] = "SweptSolid"
_PROJECT_NAME: Final[str] = "WaterPrint Plant"
_SITE_NAME: Final[str] = "Site"
_BUILDING_NAME: Final[str] = "Process Units"
_PERSON_ID: Final[str] = "waterprint-engine"
_ORG_ID: Final[str] = "WaterPrint"
_APP_ID: Final[str] = "waterprint-ifc-export"
_APP_FULL_NAME: Final[str] = "WaterPrint IFC export"
_APP_VERSION: Final[str] = "0.1.0"


def _guid(key: str) -> str:
    """确定性 GlobalId：uuid5(固定命名空间, key) → 22 位压缩（R3 禁随机源）。"""
    return ifcopenshell.guid.compress(str(uuid.uuid5(_GUID_NAMESPACE, key)))


def _axis3(
    model: ifcopenshell.file, coordinates: tuple[float, ...], rz: float
) -> ifcopenshell.entity_instance:
    """IfcAxis2Placement3D：位置 + 绕 Z 旋转（RefDirection=(cos rz, sin rz, 0)）。"""
    return model.create_entity(
        "IfcAxis2Placement3D",
        Location=model.create_entity(
            "IfcCartesianPoint", Coordinates=coordinates
        ),
        Axis=model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
        RefDirection=model.create_entity(
            "IfcDirection", DirectionRatios=(math.cos(rz), math.sin(rz), 0.0)
        ),
    )


def _owner_history(model: ifcopenshell.file) -> ifcopenshell.entity_instance:
    """OwnerHistory：CreationDate 固定槽（R3——双跑 bytes 恒等前提）。"""
    person = model.create_entity("IfcPerson", Identification=_PERSON_ID)
    org = model.create_entity("IfcOrganization", Identification=_ORG_ID)
    person_org = model.create_entity(
        "IfcPersonAndOrganization", ThePerson=person, TheOrganization=org
    )
    application = model.create_entity(
        "IfcApplication", ApplicationDeveloper=org, Version=_APP_VERSION,
        ApplicationFullName=_APP_FULL_NAME, ApplicationIdentifier=_APP_ID,
    )
    return model.create_entity(
        "IfcOwnerHistory", OwningUser=person_org,
        OwningApplication=application, State=None, ChangeAction=None,
        LastModifiedDate=None, LastModifyingUser=None,
        LastModifyingApplication=None, CreationDate=_OWNER_CREATION_DATE,
    )


def _units(model: ifcopenshell.file) -> ifcopenshell.entity_instance:
    """SI 单位制：长度/面积/体积/平面角（R4 最小集）。"""

    def si_unit(unit_type: str, name: str) -> ifcopenshell.entity_instance:
        return model.create_entity(
            "IfcSIUnit", Dimensions=None, UnitType=unit_type,
            Prefix=None, Name=name,
        )

    return model.create_entity(
        "IfcUnitAssignment",
        Units=[
            si_unit("LENGTHUNIT", "METRE"),
            si_unit("AREAUNIT", "SQUARE_METRE"),
            si_unit("VOLUMEUNIT", "CUBIC_METRE"),
            si_unit("PLANEANGLEUNIT", "RADIAN"),
        ],
    )


def _context(model: ifcopenshell.file) -> ifcopenshell.entity_instance:
    """几何上下文：三维 + 模型精度 + 世界坐标系（R4）。"""
    return model.create_entity(
        "IfcGeometricRepresentationContext", ContextIdentifier=None,
        CoordinateSpaceDimension=_SPACE_DIMENSION, Precision=_MODEL_PRECISION,
        WorldCoordinateSystem=_axis3(model, (0.0, 0.0, 0.0), 0.0),
        TrueNorth=None,
    )


def _skeleton(
    model: ifcopenshell.file,
    owner: ifcopenshell.entity_instance,
    context: ifcopenshell.entity_instance,
    units: ifcopenshell.entity_instance,
) -> tuple[ifcopenshell.entity_instance, ifcopenshell.entity_instance]:
    """项目骨架：Project/Site/Building + 两级 IfcRelAggregates（R4 最小集）。

    返回 (building, building 的 IfcLocalPlacement)——元素摆放链的父节点
    （R4 链式）与空间包含的挂接结构（L5R G1-02 containment 面）。
    """
    origin = _axis3(model, (0.0, 0.0, 0.0), 0.0)
    site_placement = model.create_entity(
        "IfcLocalPlacement", PlacementRelTo=None, RelativePlacement=origin
    )
    project = model.create_entity(
        "IfcProject", GlobalId=_guid("project"), OwnerHistory=owner,
        Name=_PROJECT_NAME, Description=None, ObjectType=None, LongName=None,
        Phase=None, RepresentationContexts=[context], UnitsInContext=units,
    )
    site = model.create_entity(
        "IfcSite", GlobalId=_guid("site"), OwnerHistory=owner,
        Name=_SITE_NAME, Description=None, ObjectType=None,
        ObjectPlacement=site_placement, Representation=None, LongName=None,
        CompositionType=None, RefLatitude=None, RefLongitude=None,
        RefElevation=None, LandTitleNumber=None, SiteAddress=None,
    )
    building_placement = model.create_entity(
        "IfcLocalPlacement", PlacementRelTo=site_placement,
        RelativePlacement=origin,
    )
    building = model.create_entity(
        "IfcBuilding", GlobalId=_guid("building"), OwnerHistory=owner,
        Name=_BUILDING_NAME, Description=None, ObjectType=None,
        ObjectPlacement=building_placement, Representation=None,
        LongName=None, CompositionType=None, ElevationOfRefHeight=None,
        ElevationOfTerrain=None, BuildingAddress=None,
    )
    model.create_entity(
        "IfcRelAggregates", GlobalId=_guid("aggregate:project:site"),
        OwnerHistory=owner, Name=None, Description=None,
        RelatingObject=project, RelatedObjects=[site],
    )
    model.create_entity(
        "IfcRelAggregates", GlobalId=_guid("aggregate:site:building"),
        OwnerHistory=owner, Name=None, Description=None,
        RelatingObject=site, RelatedObjects=[building],
    )
    return building, building_placement


def _profile(model: ifcopenshell.file, node: Node) -> ifcopenshell.entity_instance:
    """拉伸断面：box→矩形（length×width）/cylinder→圆（半径=直径/2）。"""
    dims = node.primitive.dims
    position = model.create_entity(
        "IfcAxis2Placement2D",
        Location=model.create_entity(
            "IfcCartesianPoint", Coordinates=(0.0, 0.0)
        ),
        RefDirection=None,
    )
    if node.primitive.kind == _CYLINDER_KIND:
        return model.create_entity(
            "IfcCircleProfileDef", ProfileType=_AREA_PROFILE,
            ProfileName=node.node_id, Position=position,
            Radius=dims["diameter"] / 2,
        )
    return model.create_entity(
        "IfcRectangleProfileDef", ProfileType=_AREA_PROFILE,
        ProfileName=node.node_id, Position=position,
        XDim=dims["length"], YDim=dims["width"],
    )


def build_ifc(scene_graph: SceneGraph) -> object:
    """场景图 → ifcopenshell 模型（R1 纯投影正门；IFC4 最小集 R4）。

    池壳体（pool_wall 的 box/cylinder）逐节点产出 IfcBuildingElementProxy
    拉伸体；摆放=场景图节点变换（site placement 已在装配层定位，此处
    直投 LocalPlacement——零二次几何推导）。
    """
    model = ifcopenshell.file(schema=_SCHEMA)
    owner = _owner_history(model)
    context = _context(model)
    building, building_placement = _skeleton(model, owner, context, _units(model))
    key_prefix = f"{scene_graph.scene_version}|{scene_graph.condition_key}"
    proxies: list[ifcopenshell.entity_instance] = []
    for node in scene_graph.nodes:
        if node.semantic != _POOL_SEMANTIC or (
            node.primitive.kind not in _EXPORTED_KINDS
        ):
            continue  # R2 原型边界：水面/内部构件/渠道/红线不含
        placement = model.create_entity(
            "IfcLocalPlacement", PlacementRelTo=building_placement,
            RelativePlacement=_axis3(model, node.position, node.rotation[2]),
        )
        solid = model.create_entity(
            "IfcExtrudedAreaSolid", SweptArea=_profile(model, node),
            Position=_axis3(model, (0.0, 0.0, 0.0), 0.0),
            ExtrudedDirection=model.create_entity(
                "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
            ),
            Depth=node.primitive.dims["depth"],
        )
        shape = model.create_entity(
            "IfcShapeRepresentation", ContextOfItems=context,
            RepresentationIdentifier=_BODY_ID,
            RepresentationType=_SWEPT_SOLID, Items=[solid],
        )
        proxies.append(
            model.create_entity(
                "IfcBuildingElementProxy",
                GlobalId=_guid(f"{key_prefix}|{node.node_id}"),
                OwnerHistory=owner, Name=node.node_id, Description=None,
                ObjectType=None, ObjectPlacement=placement,
                Representation=model.create_entity(
                    "IfcProductDefinitionShape", Name=None, Description=None,
                    Representations=[shape],
                ),
                Tag=None, PredefinedType=None,
            )
        )
    # 空间包含（L5R G1-02）：元素逐个挂 building——无 storey 层时 building
    # 即最低空间结构（IFC4 规范位）；仅摆放链挂接的元素在 BIM 查看器/
    # 校验器的空间树遍历中不可达（孤儿元素——主发现通道）。
    if proxies:
        model.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=_guid("containment:building"), OwnerHistory=owner,
            Name=None, Description=None, RelatingStructure=building,
            RelatedElements=proxies,
        )
    model.header.file_name.name = _FILE_NAME
    model.header.file_name.time_stamp = _FILE_TIME_STAMP
    return model


def write_ifc(model: object, path: Path) -> None:
    """IFC 落盘：同目录 .tmp 写出 → os.replace 原子替换（GR-38，R5）。"""
    tmp = path.with_name(path.name + ".tmp")
    cast("ifcopenshell.file", model).write(tmp)
    os.replace(tmp, path)
