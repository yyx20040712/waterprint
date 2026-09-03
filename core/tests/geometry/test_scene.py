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
    """L5a：SCENE_VERSION 步进 -2（site 摆放+rotation 放行——语义变即步进）。"""
    graph = build_scene(_plant(), _assumptions(), "design")
    assert graph.scene_version == "waterprint-scene-2/y-up/m"


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
    # cugeshan 无 water_depth 键（section_keys 只有 pool_depth/head_loss）不附水面
    assert "municipal_cugeshan::water_surface" not in by_id
    # 渠道图元：extrusion 走既有 depth 槽（cugeshan H=1.0）
    channel = by_id["municipal_cugeshan::channel"]
    assert channel.semantic == "channel"
    assert channel.primitive.dims == {"depth": 1.0}


def test_purity_wiring() -> None:
    """R1 接线断言（M2 实质化）：同 PlantResult 双跑场景图 JSON 相同。

    占位实质化（DRAFT 批总授权先例）：双跑 build_scene 序列化
    （asdict+sort_keys JSON）逐字节相同（纯投影确定性）；语义标签集合
    稳定（pool_wall/mech_cleaner 等来自对照表声明）。
    """
    first = build_scene(_plant(), _assumptions(), "design")
    second = build_scene(_plant(), _assumptions(), "design")
    dump1 = json.dumps(asdict(first), sort_keys=True, ensure_ascii=False)
    dump2 = json.dumps(asdict(second), sort_keys=True, ensure_ascii=False)
    assert dump1 == dump2
    semantics = {node.semantic for node in first.nodes}
    assert {"pool_wall", "mech_cleaner"} <= semantics  # 语义集合稳定
    assert first.condition_key == "design"
    assert first.scene_version  # R4 版本声明非空
    # 实例数汇总：n_gap 未列 instance_counts（分格数非设备台数），
    # mech_cleaner=1 → 节点 instance_count 取结果字段
    mech = next(n for n in first.nodes if n.semantic == "mech_cleaner")
    assert mech.instance_count == 1
