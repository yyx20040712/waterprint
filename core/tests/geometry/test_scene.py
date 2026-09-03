"""scene 镜像测试：场景图装配（确定性/实例数/语义标签/纯投影接线）。

输入:  waterprint.geometry.scene 公开符号
输出:  场景图契约断言（§10.5 / §16 A7）
"""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict

import pytest

_mod = importlib.import_module("waterprint.geometry.scene")
build_scene = getattr(_mod, "build_scene", None)
SceneGraph = getattr(_mod, "SceneGraph", None)
Node = getattr(_mod, "Node", None)

pytestmark = pytest.mark.skipif(
    None in (build_scene, SceneGraph, Node),
    reason="实现未就绪：waterprint.geometry.scene（M2）",
)


def _plant():
    from waterprint.contracts.result_schema import (
        PlantResult,
        ReproTriple,
        UnitResultSnapshot,
    )

    def snap(uid: str, dims: dict[str, float]) -> UnitResultSnapshot:
        return UnitResultSnapshot(
            unit_id=uid, outflows={}, outqualities={}, dims=dims,
            warnings=(), formula_ids=(),
        )

    return PlantResult(
        conditions={"design": {
            "inlet": snap("inlet", {}),
            "municipal_cugeshan": snap(
                "municipal_cugeshan",
                {"L": 1.8, "B": 0.7, "H": 1.0, "n_gap": 20.0,
                 "mech_clean": 1.0},
            ),
            "municipal_chenshachi": snap(
                "municipal_chenshachi",
                {"l_straight": 4.5, "d": 3.0, "h2": 1.25, "h_total": 3.0},
            ),
            # L7：AAO 容积法池体——compute 几何段 8 键（golden 锚数值口径）
            "municipal_aao": snap(
                "municipal_aao",
                {"v_total": 17862.22, "h2": 5.0, "a_pool": 3572.444,
                 "l_pool_raw": 94.4647, "b_pool_raw": 37.7859,
                 "l_pool": 94.5, "b_pool": 38.0, "h_pool": 5.3,
                 "v_pool": 17955.0},
            ),
        }},
        summary={},
        trace=(),
        repro=ReproTriple(design_hash="", engine_version="", data_version=""),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


def test_node_carries_transform_and_semantic() -> None:
    """R1：节点 = 图元 + 局部变换 + 语义标签 + 实例数。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(Node)}
    assert {"primitive", "semantic", "instance_count"} <= names


def test_scene_carries_version_and_condition() -> None:
    """R4：场景图声明版本与工况（坐标约定/结果归属）。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(SceneGraph)}
    assert {"scene_version", "condition_key"} <= names


def test_scene_version_stepped_to_site() -> None:
    """L5a：SCENE_VERSION 步进 -2（site 摆放+rotation 放行——语义变即步进）。

    L5R 轴标签勘正：-2 未推送即就地正名 z-up（存储坐标 Z-up——X 东 Y 北
    Z 标高；步进时误记 y-up 系 G1-01 根因，渲染层换轴而非改存储）。
    L6 步进 -3：roads/corridors strip 图元收编（新 kind+新 semantic=
    场景图语义变——「语义变即步进」先例）。
    L7 步进 -4：AAO 容积法池体图元批——池壁/水面/渠道三节点入场景
    （新单元产图元=场景图语义变，沿 -3 先例）。
    """
    graph = build_scene(_plant(), _assumptions(), "design")
    assert graph.scene_version == "waterprint-scene-4/z-up/m"


def test_site_mode_places_units_and_boundary() -> None:
    """L5a site 模式：placement 定位（度→弧度 core 装配层换算）+未摆放不进图+红线图元。"""
    from math import isclose, pi

    from waterprint.contracts.project_schema import (
        SiteDesign,
        SitePoint,
        StructurePlacement,
    )

    site = SiteDesign(
        structures={
            "municipal_cugeshan": StructurePlacement(
                x=10.0, y=20.0, rotation=90.0, ground_elevation=0.5
            ),
        },
        boundary=[
            SitePoint(x=0.0, y=0.0),
            SitePoint(x=100.0, y=0.0),
            SitePoint(x=100.0, y=60.0),
        ],
    )
    graph = build_scene(_plant(), _assumptions(), "design", site_design=site)
    by_id = {node.node_id: node for node in graph.nodes}
    # 已摆放单元：position=(x, y, ground_elevation)（None→0.0 铁律由缺省摆放覆盖）
    pool = by_id["municipal_cugeshan::pool_wall"]
    assert pool.position == (10.0, 20.0, 0.5)
    # rotation=(0,0,radians(度))——度→弧度换算归 core 装配层
    assert isclose(pool.rotation[2], pi / 2)
    assert pool.rotation[0] == 0.0 and pool.rotation[1] == 0.0
    # 未摆放单元（在 nodes 不在 structures）不进场景图（总装语义=只摆已放）
    assert not any(key.startswith("municipal_chenshachi") for key in by_id)
    # 红线图元：semantic=site_boundary、z=0 零高度、顶点序压平进 dims
    boundary = by_id["site::boundary"]
    assert boundary.semantic == "site_boundary"
    assert boundary.primitive.kind == "polyline"
    assert boundary.position[2] == 0.0
    assert boundary.primitive.dims == {
        "x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 0.0, "x2": 100.0, "y2": 60.0,
    }
    # structures 空=回退现 X 轴排布（与 site_design=None 逐节点等价）
    fallback = build_scene(_plant(), _assumptions(), "design",
                           site_design=SiteDesign())
    plain = build_scene(_plant(), _assumptions(), "design")
    assert fallback.nodes == plain.nodes


def test_water_surface_and_channel_wired() -> None:
    """L5a 图元接线收口：有池体且有 water_depth 键单元附水面节点；渠道走既有 depth 槽。"""
    graph = build_scene(_plant(), _assumptions(), "design")
    by_id = {node.node_id: node for node in graph.nodes}
    # chenshachi（box 池体+h2 水深键）附水面节点：水位=池底+水深
    surface = by_id["municipal_chenshachi::water_surface"]
    assert surface.semantic == "water_surface"
    assert surface.position[2] == pytest.approx(1.25)
    # L5R A-S1：水面足迹=池面投影（box 池 length/width 同源键——
    # 前端 length/width 渲染池面，缺键=1×1 兜底方块即显性缺陷）
    assert surface.primitive.dims["length"] == pytest.approx(4.5)
    assert surface.primitive.dims["width"] == pytest.approx(3.0)
    # cugeshan 无 water_depth 键（section_keys 只有 pool_depth/head_loss）不附水面
    assert "municipal_cugeshan::water_surface" not in by_id
    # 渠道图元：extrusion 走既有 depth 槽（cugeshan H=1.0）
    channel = by_id["municipal_cugeshan::channel"]
    assert channel.semantic == "channel"
    assert channel.primitive.dims == {"depth": 1.0}


def test_aao_volume_pool_three_nodes_wired() -> None:
    """L7：AAO 容积法池体三节点接线——池壁 box/水面/渠道零几何层改动自动产出。

    D7 裁定：water_depth→h2（连续流常水位语义）；channel 连带=有 depth 槽
    单元的族一致行为（cugeshan::channel 同款）。水面足迹=l_pool×b_pool
    同源键（L5R A-S1 box 池先例）。
    """
    graph = build_scene(_plant(), _assumptions(), "design")
    by_id = {node.node_id: node for node in graph.nodes}
    # 池壁：box 三槽=l_pool/b_pool/h_pool（compute 几何键直取）
    wall = by_id["municipal_aao::pool_wall"]
    assert wall.semantic == "pool_wall"
    assert wall.primitive.kind == "box"
    assert wall.primitive.dims == {"length": 94.5, "width": 38.0, "depth": 5.3}
    # 水面：水位=池底+h2（5.0），足迹与池壁同源键
    surface = by_id["municipal_aao::water_surface"]
    assert surface.semantic == "water_surface"
    assert surface.position[2] == pytest.approx(5.0)
    assert surface.primitive.dims["length"] == pytest.approx(94.5)
    assert surface.primitive.dims["width"] == pytest.approx(38.0)
    assert surface.primitive.dims["level"] == pytest.approx(5.0)
    # 渠道：depth 槽连带（h_pool 族一致行为）
    channel = by_id["municipal_aao::channel"]
    assert channel.semantic == "channel"
    assert channel.primitive.dims == {"depth": 5.3}


def _site_with_routes():
    """L6 purity fixture：roads/corridors 至少各 1 条（双跑确定性覆盖新图元）。"""
    from waterprint.contracts.project_schema import (
        Corridor,
        Road,
        SiteDesign,
        SitePoint,
    )

    return SiteDesign(
        roads=[Road(
            centerline=[SitePoint(x=0.0, y=0.0), SitePoint(x=30.0, y=0.0)],
            width_m=4.0,
        )],
        corridors=[Corridor(
            centerline=[SitePoint(x=0.0, y=5.0), SitePoint(x=0.0, y=25.0)],
            width_m=2.0,
            kind="water",
        )],
    )


def test_site_routes_strips_wired() -> None:
    """L6：roads/corridors 收编进 3D 场景图——strip 图元分段四边形角点 core 预计算。"""
    from waterprint.contracts.project_schema import (
        Corridor,
        Road,
        SiteDesign,
        SitePoint,
    )

    site = SiteDesign(
        roads=[Road(
            centerline=[
                SitePoint(x=0.0, y=0.0),
                SitePoint(x=30.0, y=0.0),
                SitePoint(x=30.0, y=20.0),
            ],
            width_m=4.0,
        )],
        corridors=[Corridor(
            centerline=[
                SitePoint(x=0.0, y=5.0),
                SitePoint(x=0.0, y=25.0),
            ],
            width_m=2.0,
            kind="water",
        )],
    )
    graph = build_scene(_plant(), _assumptions(), "design", site_design=site)
    by_id = {node.node_id: node for node in graph.nodes}
    # road：node_id 平铺下标、kind=strip、semantic 恒 site_road、零高度贴地
    road = by_id["site::road[0]"]
    assert road.semantic == "site_road"
    assert road.primitive.kind == "strip"
    assert road.position == (0.0, 0.0, 0.0)
    # 逐段法向 n=((y0−y1)/span,(x1−x0)/span)、half=width_m/2、环序 4 角点
    # （宽度消费归 core——前端零业务几何）：
    #   段1 (0,0)→(30,0)：n=(0,1) → (0,2),(30,2),(30,−2),(0,−2)
    #   段2 (30,0)→(30,20)：n=(−1,0) → (28,0),(28,20),(32,20),(32,0)
    assert road.primitive.dims == {
        "x0": 0.0, "y0": 2.0, "x1": 30.0, "y1": 2.0,
        "x2": 30.0, "y2": -2.0, "x3": 0.0, "y3": -2.0,
        "x4": 28.0, "y4": 0.0, "x5": 28.0, "y5": 20.0,
        "x6": 32.0, "y6": 20.0, "x7": 32.0, "y7": 0.0,
    }
    # corridor：semantic="site_corridor:"+kind（开放 str 装不进 dims[值域恒
    # float]，semantic 拼接是唯一可复原通道）
    corridor = by_id["site::corridor[0]"]
    assert corridor.semantic == "site_corridor:water"
    assert corridor.primitive.kind == "strip"
    # 段 (0,5)→(0,25)：n=(−1,0)、half=1 → (−1,5),(−1,25),(1,25),(1,5)
    assert corridor.primitive.dims == {
        "x0": -1.0, "y0": 5.0, "x1": -1.0, "y1": 25.0,
        "x2": 1.0, "y2": 25.0, "x3": 1.0, "y3": 5.0,
    }
    # 逐条平铺入 root（不设聚合节点）
    assert "site::road[0]" in graph.root
    assert "site::corridor[0]" in graph.root
    # 空 roads/corridors=零节点不占位（空 SiteDesign 与 None 等价面沿 boundary 先例）
    empty = build_scene(_plant(), _assumptions(), "design",
                        site_design=SiteDesign())
    assert not any(
        key.startswith(("site::road", "site::corridor"))
        for key in {node.node_id for node in empty.nodes}
    )


def test_site_routes_degenerate_segments() -> None:
    """L6 退化面：span≤0 段跳过；全退化=整条不产出节点（3D 无面积即无图元）。"""
    from waterprint.contracts.project_schema import (
        Corridor,
        Road,
        SiteDesign,
        SitePoint,
    )

    site = SiteDesign(
        roads=[Road(
            centerline=[
                SitePoint(x=0.0, y=0.0),
                SitePoint(x=10.0, y=0.0),
                SitePoint(x=10.0, y=0.0),  # 重复点=退化段跳过（2D 先例同款）
                SitePoint(x=10.0, y=5.0),
            ],
            width_m=2.0,
        )],
        corridors=[Corridor(
            centerline=[
                SitePoint(x=5.0, y=5.0),
                SitePoint(x=5.0, y=5.0),  # 全退化（有效段数 0）=整条不产出
            ],
            width_m=1.0,
            kind="power",
        )],
    )
    graph = build_scene(_plant(), _assumptions(), "design", site_design=site)
    by_id = {node.node_id: node for node in graph.nodes}
    road = by_id["site::road[0]"]
    # 有效 2 段（重复点段不产出 4 角点）：段1 n=(0,1)、half=1；
    # 段3 (10,0)→(10,5) n=(−1,0) → (9,0),(9,5),(11,5),(11,0)
    assert road.primitive.dims == {
        "x0": 0.0, "y0": 1.0, "x1": 10.0, "y1": 1.0,
        "x2": 10.0, "y2": -1.0, "x3": 0.0, "y3": -1.0,
        "x4": 9.0, "y4": 0.0, "x5": 9.0, "y5": 5.0,
        "x6": 11.0, "y6": 5.0, "x7": 11.0, "y7": 0.0,
    }
    # 全退化 corridor=零节点零 root 占位（空族语义同构零节点）
    assert "site::corridor[0]" not in by_id
    assert "site::corridor[0]" not in graph.root


def test_purity_wiring() -> None:
    """R1 接线断言（M2 实质化）：同 PlantResult 双跑场景图 JSON 相同。

    占位实质化（DRAFT 批总授权先例）：双跑 build_scene 序列化
    （asdict+sort_keys JSON）逐字节相同（纯投影确定性）；语义标签集合
    稳定（pool_wall/mech_cleaner 等来自对照表声明）。L6 起 fixture 扩含
    roads/corridors 至少各 1 条（双跑 JSON 字节同自动覆盖新图元）。
    """
    site = _site_with_routes()
    first = build_scene(_plant(), _assumptions(), "design", site_design=site)
    second = build_scene(_plant(), _assumptions(), "design", site_design=site)
    dump1 = json.dumps(asdict(first), sort_keys=True, ensure_ascii=False)
    dump2 = json.dumps(asdict(second), sort_keys=True, ensure_ascii=False)
    assert dump1 == dump2
    semantics = {node.semantic for node in first.nodes}
    assert {"pool_wall", "mech_cleaner"} <= semantics  # 语义集合稳定
    assert {"site_road", "site_corridor:water"} <= semantics  # L6 strip 语义入集合
    assert first.condition_key == "design"
    assert first.scene_version  # R4 版本声明非空
    # 实例数汇总：n_gap 未列 instance_counts（分格数非设备台数），
    # mech_cleaner=1 → 节点 instance_count 取结果字段
    mech = next(n for n in first.nodes if n.semantic == "mech_cleaner")
    assert mech.instance_count == 1
