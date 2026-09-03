"""ifc_export 镜像测试：SceneGraph → IFC 模型（IfcBuildingElementProxy 原型级）。

输入:  waterprint.ifc_export.builder 公开符号 + ifcopenshell 回读（L5c）
输出:  IFC 导出契约断言（层级/图元回读往返/摆放链/双跑 bytes 恒等）
"""

from __future__ import annotations

import importlib
from math import isclose, pi

import pytest

_mod = importlib.import_module("waterprint.ifc_export.builder")
build_ifc = getattr(_mod, "build_ifc", None)
write_ifc = getattr(_mod, "write_ifc", None)

pytestmark = pytest.mark.skipif(
    None in (build_ifc, write_ifc),
    reason="实现未就绪：waterprint.ifc_export.builder（L5c）",
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
            "municipal_chuchenchi": snap(
                "municipal_chuchenchi",
                {"d": 9.0, "d_center": 1.4, "h_total": 4.0, "h2": 3.0},
            ),
        }},
        summary={},
        trace=(),
        repro=ReproTriple(design_hash="", engine_version="", data_version=""),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


def _scene():
    from waterprint.geometry.scene import build_scene

    return build_scene(_plant(), _assumptions(), "design")


def test_roundtrip_hierarchy_and_elements(tmp_path) -> None:
    """回读往返：project/site/building 三级 IfcRelAggregates+element 计数=池壳体。"""
    import ifcopenshell

    graph = _scene()
    out = tmp_path / "plant.ifc"
    write_ifc(build_ifc(graph), out)
    model = ifcopenshell.open(out)
    project = model.by_type("IfcProject")[0]
    site = model.by_type("IfcSite")[0]
    building = model.by_type("IfcBuilding")[0]
    relates = {
        rel.RelatingObject: set(rel.RelatedObjects or ())
        for rel in model.by_type("IfcRelAggregates")
    }
    assert site in relates.get(project, ())
    assert building in relates.get(site, ())
    # element 计数 == 场景图 pool_wall 图元数（水面/内部构件/渠道/红线不含）
    proxies = model.by_type("IfcBuildingElementProxy")
    pool_walls = [n for n in graph.nodes if n.semantic == "pool_wall"]
    assert len(proxies) == len(pool_walls) == 3
    # 建筑语义禁用（原型级中性形态）：IfcWall 族零实体
    assert not model.by_type("IfcWall")
    assert not model.by_type("IfcWallStandardCase")
    # box 拉伸：矩形断面 XDim/YDim 与深度同源 dims（cugeshan L/B/H）
    box = next(
        p for p in proxies if p.Name == "municipal_cugeshan::pool_wall"
    )
    solid = box.Representation.Representations[0].Items[0]
    assert solid.SweptArea.is_a("IfcRectangleProfileDef")
    assert solid.SweptArea.XDim == pytest.approx(1.8)
    assert solid.SweptArea.YDim == pytest.approx(0.7)
    assert solid.Depth == pytest.approx(1.0)
    # cylinder 拉伸：IfcCircleProfileDef 半径=直径/2（chuchenchi d=9）
    cylinder = next(
        p for p in proxies if p.Name == "municipal_chuchenchi::pool_cylinder"
    )
    cylinder_solid = cylinder.Representation.Representations[0].Items[0]
    assert cylinder_solid.SweptArea.is_a("IfcCircleProfileDef")
    assert cylinder_solid.SweptArea.Radius == pytest.approx(9.0 / 2)
    assert cylinder_solid.Depth == pytest.approx(4.0)


def test_site_placement_carried_into_local_placement(tmp_path) -> None:
    """摆放链：site 摆放（位置+绕 Z 旋转）进元素 IfcLocalPlacement。"""
    import ifcopenshell

    from waterprint.contracts.project_schema import (
        SiteDesign,
        StructurePlacement,
    )
    from waterprint.geometry.scene import build_scene

    site = SiteDesign(
        structures={
            "municipal_cugeshan": StructurePlacement(
                x=10.0, y=20.0, rotation=90.0, ground_elevation=0.5
            ),
        },
    )
    graph = build_scene(
        _plant(), _assumptions(), "design", site_design=site
    )
    out = tmp_path / "site.ifc"
    write_ifc(build_ifc(graph), out)
    model = ifcopenshell.open(out)
    proxy = next(
        p for p in model.by_type("IfcBuildingElementProxy")
        if p.Name == "municipal_cugeshan::pool_wall"
    )
    placement = proxy.ObjectPlacement.RelativePlacement
    assert placement.Location.Coordinates == pytest.approx((10.0, 20.0, 0.5))
    ref = placement.RefDirection.DirectionRatios
    assert isclose(ref[0], 0.0, abs_tol=1e-9)  # 90°：RefDirection≈(0,1,0)
    assert isclose(ref[1], 1.0, abs_tol=1e-9)


def test_deterministic_bytes(tmp_path) -> None:
    """确定性：同 SceneGraph 双跑写出 bytes 恒等（OwnerHistory 时间戳固定值定槽）。"""
    graph = _scene()
    first = tmp_path / "first.ifc"
    second = tmp_path / "second.ifc"
    write_ifc(build_ifc(graph), first)
    write_ifc(build_ifc(graph), second)
    assert first.read_bytes() == second.read_bytes()
