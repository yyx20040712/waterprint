"""site_plan 镜像测试：厂区总平面（坐标网/风玫瑰/构筑物投影/道路走廊/边界红线/图框标题）。

输入:  waterprint.drafting.site_plan 公开符号
输出:  总平面图契约断言（结构断言+确定性 repr 哈希锚，简报 §三.7 形态；
       L4a 增 boundary 闭合折线+「边界红线」注记用例——哈希锚样本无
       boundary，锚 d5dad837 预期恒）
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import math

import pytest

from waterprint.contracts.project_schema import (
    Corridor,
    Road,
    SiteDesign,
    SitePlanOptions,
    SitePoint,
    StructurePlacement,
)
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    UnitResultSnapshot,
)
from waterprint.drafting.styles import (
    ANNO_OFFSET_LEVEL,
    LAYER_AXIS,
    LAYER_BORDER,
    LAYER_LABEL,
    LAYER_PIPE,
    LAYER_POOL,
    LAYER_TITLE,
    EntityGroup,
    base_styles,
)

_mod = importlib.import_module("waterprint.drafting.site_plan")
site_layout = getattr(_mod, "site_layout", None)
SiteOptions = getattr(_mod, "SiteOptions", None)
InvalidSitePlanError = getattr(_mod, "InvalidSitePlanError", None)

pytestmark = pytest.mark.skipif(
    site_layout is None,
    reason="实现未就绪：waterprint.drafting.site_plan（M4 L3）",
)


def _snap(uid: str, dims: dict[str, float]) -> UnitResultSnapshot:
    return UnitResultSnapshot(
        unit_id=uid, outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _plant(units_by_condition: dict[str, dict[str, UnitResultSnapshot]]) -> PlantResult:
    return PlantResult(
        conditions={ck: dict(units) for ck, units in units_by_condition.items()},
        summary={}, trace=(), repro=ReproTriple("h", "e", "d"),
    )


def _placement(
    x: float, y: float, rotation: float = 0.0, ground_elevation: float | None = None
) -> StructurePlacement:
    return StructurePlacement(
        x=x, y=y, rotation=rotation, ground_elevation=ground_elevation
    )


def _rich_site() -> SiteDesign:
    """全要素样例：矩形+圆形+缺键+悬空构筑物/道路/走廊/风玫瑰（含未知方位）。"""
    return SiteDesign(
        structures={
            "rect1": _placement(5.0, 5.0, ground_elevation=105.5),
            "circ1": _placement(20.0, 5.0, rotation=30.0),
            "nodim": _placement(30.0, 30.0),
            "ghost": _placement(-10.0, -10.0),
        },
        roads=[Road(
            centerline=[SitePoint(x=0.0, y=-8.0), SitePoint(x=40.0, y=-8.0)],
            width_m=4.0,
        )],
        corridors=[Corridor(
            centerline=[SitePoint(x=0.0, y=0.0), SitePoint(x=0.0, y=25.0)],
            width_m=2.0, kind="water",
        )],
        options=SitePlanOptions(
            coord_grid=10.0, wind_rose={"N": 12.5, "E": 6.25, "XX": 9.0}
        ),
    )


def _rich_plant() -> PlantResult:
    return _plant({"design": {
        "rect1": _snap("rect1", {"length": 4.0, "width": 2.0}),
        "circ1": _snap("circ1", {"diameter": 6.0}),
        "nodim": _snap("nodim", {"volume": 100.0}),
    }})


def _seg(entity: object, expected: tuple[tuple[float, float], ...]) -> bool:
    """折线逐点 approx（嵌套序列不走 approx 整比的守卫形态）。"""
    return len(entity.points) == len(expected) and all(
        point == pytest.approx(want)
        for point, want in zip(entity.points, expected, strict=True)
    )


def test_entrypoint_frozen() -> None:
    """R1 入口冻结：site_layout(site_design, plant_result, styles, options=None)。"""
    assert callable(site_layout)
    signature = inspect.signature(site_layout)
    assert list(signature.parameters) == [
        "site_design", "plant_result", "styles", "options",
    ]
    assert signature.parameters["options"].default is None


def test_empty_site_minimal_window() -> None:
    """§三.3/13 空 site=原点邻域最小窗：±coord_grid×2（y 向下沿至含标题注记锚
    ——G1-05 注记入包络：ymin=-3.6-20）图框+两向各 5 条网格线。"""
    group = site_layout(SiteDesign(), _plant({"design": {}}), base_styles())
    rects = [e for e in group.entities if e.layer == LAYER_BORDER and e.kind == "rect"]
    assert len(rects) == 1
    (x0, y0), (x1, y1) = rects[0].points
    assert [x0, y0, x1, y1] == pytest.approx(
        [-20.0, ANNO_OFFSET_LEVEL - 20.0, 20.0, 20.0]
    )
    grid = [e for e in group.entities if e.layer == LAYER_AXIS and e.kind == "line"]
    vertical = [e for e in grid if e.points[0][0] == e.points[1][0]]
    horizontal = [e for e in grid if e.points[0][1] == e.points[1][1]]
    assert len(vertical) == 5 and len(horizontal) == 5  # -20..20 每 10 一条
    assert sorted({e.points[0][0] for e in vertical}) == pytest.approx(
        [-20.0, -10.0, 0.0, 10.0, 20.0]
    )
    for e in vertical:
        assert [e.points[0][1], e.points[1][1]] == pytest.approx(
            [ANNO_OFFSET_LEVEL - 20.0, 20.0]
        )
    assert {e.source_key for e in grid} == {"coord_grid"}
    assert not [e for e in group.entities if e.layer in (LAYER_POOL, LAYER_PIPE)]


def test_structures_rect_circle_missing_outline() -> None:
    """R3 纯投影：矩形 4 段线/圆形 16 段折线逼近/缺键=占位注记；ground_elevation 标高。"""
    group = site_layout(_rich_site(), _rich_plant(), base_styles())
    pool = [e for e in group.entities if e.layer == LAYER_POOL and e.kind == "line"]
    rect_segs = [e for e in pool if e.source_key == "rect1"]
    assert len(rect_segs) == 4  # 闭合矩形=逐段独立 line（§三.8 通用旋转同一路径）
    corners = {(round(p[0], 6), round(p[1], 6)) for e in rect_segs for p in e.points}
    assert corners == {(3.0, 4.0), (7.0, 4.0), (7.0, 6.0), (3.0, 6.0)}
    circ_segs = [e for e in pool if e.source_key == "circ1"]
    assert len(circ_segs) == _mod.CIRCLE_SEGMENTS == 16  # §三.9 幂积常量
    radii = {round(math.hypot(p[0] - 20.0, p[1] - 5.0), 6)
             for e in circ_segs for p in e.points}
    assert radii == {3.0}  # 折线顶点全在半径圆上（rotation 仅转起始角）
    no_outline = [e for e in group.entities if "无轮廓数据" in e.text]
    assert len(no_outline) == 1 and "nodim" in no_outline[0].text
    assert no_outline[0].points[0] == pytest.approx((30.0, 30.0))  # §三.5 占位
    elevs = [e for e in group.entities if e.kind == "elev_symbol"]
    assert len(elevs) == 1  # §三.12 ground_elevation=结构位置+LEVEL 偏移
    assert elevs[0].params["ground_elevation"] == pytest.approx(105.5)
    assert elevs[0].points[0] == pytest.approx((5.0, 5.0 + ANNO_OFFSET_LEVEL))
    assert elevs[0].source_key == "ground_elevation[rect1]"


def test_elev_source_key_unit_disambiguated() -> None:
    """R-2/G1-02：多标高单元 elev_symbol source_key 含 unit_id（roads[i] 索引
    消歧同族——多单元聚合面回溯唯一）；text 保留语义串。"""
    site = SiteDesign(structures={
        "poolA": _placement(0.0, 0.0, ground_elevation=105.5),
        "poolB": _placement(20.0, 0.0, ground_elevation=103.0),
    })
    plant = _plant({"design": {
        "poolA": _snap("poolA", {"length": 4.0, "width": 2.0}),
        "poolB": _snap("poolB", {"diameter": 4.0}),
    }})
    group = site_layout(site, plant, base_styles())
    elevs = [e for e in group.entities if e.kind == "elev_symbol"]
    assert len(elevs) == 2
    assert {e.source_key for e in elevs} == {
        "ground_elevation[poolA]", "ground_elevation[poolB]",
    }
    assert {e.text for e in elevs} == {"ground_elevation"}


def test_dangling_structure_annotated() -> None:
    """§三.6 悬空面：快照无该单元=跳过轮廓+text 记档（不抛——投影非校验）。"""
    site = SiteDesign(structures={"ghost": _placement(3.0, 4.0)})
    group = site_layout(site, _plant({"design": {}}), base_styles())
    assert not [e for e in group.entities if e.layer == LAYER_POOL]
    notes = [e for e in group.entities if "未入工况" in e.text]
    assert len(notes) == 1
    assert "ghost" in notes[0].text and notes[0].source_key == "ghost"
    assert notes[0].points[0] == pytest.approx((3.0, 4.0))


def test_road_corridor_polylines() -> None:
    """§三.10/11 道路走廊：中心线+两侧 ±width_m/2 边线（逐段独立 line）；走廊 kind 注记。"""
    site = SiteDesign(
        roads=[Road(
            centerline=[SitePoint(x=0.0, y=0.0), SitePoint(x=10.0, y=0.0)],
            width_m=4.0,
        )],
        corridors=[Corridor(
            centerline=[SitePoint(x=0.0, y=0.0), SitePoint(x=0.0, y=8.0)],
            width_m=2.0, kind="water",
        )],
    )
    group = site_layout(site, _plant({"design": {}}), base_styles())
    pipe = [e for e in group.entities if e.layer == LAYER_PIPE and e.kind == "line"]
    road = [e for e in pipe if e.source_key == "roads[0]"]
    assert len(road) == 3  # 中心线+两边线
    assert any(_seg(e, ((0.0, 0.0), (10.0, 0.0))) for e in road)
    assert any(_seg(e, ((0.0, 2.0), (10.0, 2.0))) for e in road)
    assert any(_seg(e, ((0.0, -2.0), (10.0, -2.0))) for e in road)
    corridor = [e for e in pipe if e.source_key == "corridors[0]"]
    assert len(corridor) == 3
    assert any(_seg(e, ((0.0, 0.0), (0.0, 8.0))) for e in corridor)
    assert any(_seg(e, ((-1.0, 0.0), (-1.0, 8.0))) for e in corridor)
    assert any(_seg(e, ((1.0, 0.0), (1.0, 8.0))) for e in corridor)
    kind_notes = [e for e in group.entities if e.text == "kind=water"]
    assert len(kind_notes) == 1
    assert kind_notes[0].points[0] == pytest.approx((0.0, 4.0))  # 走廊中点注记


def test_single_point_corridor_defended() -> None:
    """R-1/G1-01 防御深度：centerline<2 点（model_construct 绕 schema 面）=零段
    走廊——kind 注记跳过不抛 IndexError（span≤0 守卫同类）。"""
    degenerate = Corridor.model_construct(
        centerline=[SitePoint(x=1.0, y=1.0)], width_m=2.0, kind="water"
    )
    group = site_layout(
        SiteDesign(corridors=[degenerate]), _plant({"design": {}}), base_styles()
    )
    assert not [e for e in group.entities if e.source_key == "corridors[0]"]
    assert not [e for e in group.entities if e.text == "kind=water"]


def _boundary_site() -> SiteDesign:
    """L4a 红线样例：30×20 矩形闭合顶点序（4 点——闭合段末→首由投影补）。"""
    return SiteDesign(boundary=[
        SitePoint(x=0.0, y=0.0),
        SitePoint(x=30.0, y=0.0),
        SitePoint(x=30.0, y=20.0),
        SitePoint(x=0.0, y=20.0),
    ])


def test_boundary_closed_polyline_and_annotation() -> None:
    """L4a boundary 投影：N 顶点=N 段闭合折线（含末→首段）+「边界红线」注记。

    层复用零新层：折线=LAYER_BORDER（图框同层——红线=用地边界制图族）、
    注记=LAYER_LABEL（kind 注记同族先例）；source_key="boundary" 回溯。
    """
    group = site_layout(_boundary_site(), _plant({"design": {}}), base_styles())
    lines = [e for e in group.entities if e.source_key == "boundary" and e.kind == "line"]
    assert len(lines) == 4  # 4 顶点=4 段（闭合段在内——逐段独立 line 同轮廓族）
    assert all(e.layer == LAYER_BORDER for e in lines)
    assert any(_seg(e, ((0.0, 0.0), (30.0, 0.0))) for e in lines)
    assert any(_seg(e, ((0.0, 20.0), (0.0, 0.0))) for e in lines)  # 末→首闭合段
    notes = [e for e in group.entities if e.text == "边界红线"]
    assert len(notes) == 1
    assert notes[0].kind == "text" and notes[0].layer == LAYER_LABEL
    assert notes[0].source_key == "boundary"
    assert notes[0].points[0] == pytest.approx((0.0, 0.0))  # 注记锚=首顶点（确定性）


def test_boundary_extends_content_envelope() -> None:
    """L4a：红线顶点入内容包络——图框窗必含全体 boundary 顶点与注记锚（G1-05 同族）。"""
    site = SiteDesign(
        structures={"rect1": _placement(5.0, 5.0)},
        boundary=[
            SitePoint(x=-40.0, y=-30.0),
            SitePoint(x=60.0, y=-30.0),
            SitePoint(x=60.0, y=45.0),
            SitePoint(x=-40.0, y=45.0),
        ],
    )
    plant = _plant({"design": {"rect1": _snap("rect1", {"length": 4.0, "width": 2.0})}})
    group = site_layout(site, plant, base_styles())
    border = next(e for e in group.entities if e.kind == "rect")
    (bx0, by0), (bx1, by1) = border.points
    for vertex in ((-40.0, -30.0), (60.0, -30.0), (60.0, 45.0), (-40.0, 45.0)):
        assert bx0 <= vertex[0] <= bx1 and by0 <= vertex[1] <= by1
    note = next(e for e in group.entities if e.text == "边界红线")
    assert bx0 <= note.points[0][0] <= bx1 and by0 <= note.points[0][1] <= by1


def test_boundary_degenerate_defended() -> None:
    """L4a 防御深度：boundary<3 点（model_construct 绕 schema validator 面）=
    零实体零注记（投影非校验——corridor 单点先例同族，不抛不编造）。"""
    forged = SiteDesign.model_construct(
        boundary=[SitePoint(x=1.0, y=1.0), SitePoint(x=2.0, y=2.0)]
    )
    group = site_layout(forged, _plant({"design": {}}), base_styles())
    assert not [e for e in group.entities if e.source_key == "boundary"]
    assert not [e for e in group.entities if e.text == "边界红线"]


def test_boundary_min_vertices_anchor_matches_schema() -> None:
    """L4-R 同值锚（二审 G1-06）：schema 侧 _BOUNDARY_MIN_POINTS 与投影侧
    _BOUNDARY_MIN_VERTICES 恒同值——两侧行为各自有测（validator 1/2 点拒+
    退化零实体），但值漂移（单侧改 1+3）两行为测试各自仍绿，本锚抓双胞胎
    漂移。getattr 形态沿本件 site_layout 同款（实现未就绪时 AttributeError
    先行红，符合镜像测试先红后绿）。"""
    from waterprint.contracts.project_schema import _BOUNDARY_MIN_POINTS

    assert getattr(_mod, "_BOUNDARY_MIN_VERTICES") == _BOUNDARY_MIN_POINTS


def test_wind_rose_family() -> None:
    """§三.2 风玫瑰：sorted 方位族+频率/max 归一×基准半径（coord_grid×2）；None/空=不画。"""
    site = SiteDesign(options=SitePlanOptions(
        coord_grid=10.0, wind_rose={"N": 12.5, "E": 6.25, "XX": 9.0}
    ))
    group = site_layout(site, _plant({"design": {}}), base_styles())
    spokes = {e.source_key: e for e in group.entities
              if e.kind == "line" and e.source_key.startswith("wind_rose[")}
    assert set(spokes) == {"wind_rose[N]", "wind_rose[E]"}  # 未知方位 XX=跳过
    assert spokes["wind_rose[N]"].points[1] == pytest.approx((0.0, 20.0))  # max 频率→全半径
    assert spokes["wind_rose[E]"].points[1] == pytest.approx((10.0, 0.0))  # 6.25/12.5×20
    labels = {e.text: e for e in group.entities
              if e.kind == "text" and e.source_key.startswith("wind_rose[")}
    assert set(labels) == {"N", "E"}
    assert labels["N"].points[0] == pytest.approx((0.0, 20.0))  # 方位标注在基准半径圈
    for quiet_rose in (None, {}):
        quiet = SiteDesign(options=SitePlanOptions(
            coord_grid=10.0, wind_rose=quiet_rose
        ))
        quiet_group = site_layout(quiet, _plant({"design": {}}), base_styles())
        assert not [e for e in quiet_group.entities
                    if e.source_key.startswith("wind_rose[")]


def test_wind_rose_negative_frequency_clamped() -> None:
    """R-3/G1-03：负频率方位钳 0=零长 spoke 于中心（方位族/标注保留完整——
    不画反象限穿心线编造几何）。"""
    site = SiteDesign(options=SitePlanOptions(
        coord_grid=10.0, wind_rose={"N": 10.0, "S": -5.0}
    ))
    group = site_layout(site, _plant({"design": {}}), base_styles())
    spokes = {e.source_key: e for e in group.entities
              if e.kind == "line" and e.source_key.startswith("wind_rose[")}
    assert set(spokes) == {"wind_rose[N]", "wind_rose[S]"}
    assert spokes["wind_rose[N]"].points[1] == pytest.approx((0.0, 20.0))
    assert spokes["wind_rose[S]"].points[1] == pytest.approx(
        spokes["wind_rose[S]"].points[0]
    )  # 钳 0=零长（中心点）
    labels = {e.text for e in group.entities
              if e.kind == "text" and e.source_key.startswith("wind_rose[")}
    assert labels == {"N", "S"}  # 标注族仍完备


def test_coord_grid_spacing_range_and_options_chain() -> None:
    """§三.3/15 坐标网：间距=coord_grid 透传；范围=内容包络外扩 ×2；SiteOptions 覆盖链。"""
    site = SiteDesign(structures={"rect1": _placement(0.0, 0.0)})
    plant = _plant({"design": {
        "rect1": _snap("rect1", {"length": 10.0, "width": 10.0})
    }})
    group = site_layout(site, plant, base_styles())
    border = next(e for e in group.entities if e.kind == "rect")
    (x0, y0), (x1, y1) = border.points
    # 包络 ±5 外扩 20；y 向下沿至含标题注记锚（-5-3.6-20，G1-05）
    assert [x0, y0, x1, y1] == pytest.approx(
        [-25.0, -5.0 + ANNO_OFFSET_LEVEL - 20.0, 25.0, 25.0]
    )
    grid = [e for e in group.entities if e.layer == LAYER_AXIS and e.kind == "line"]
    vertical = sorted({e.points[0][0] for e in grid
                       if e.points[0][0] == e.points[1][0]})
    assert vertical == pytest.approx([-20.0, -10.0, 0.0, 10.0, 20.0])  # ceil(-2.5)..floor(2.5)
    overridden = site_layout(site, plant, base_styles(), SiteOptions(coord_grid=5.0))
    grid5 = [e for e in overridden.entities
             if e.layer == LAYER_AXIS and e.kind == "line"]
    vertical5 = sorted({e.points[0][0] for e in grid5
                        if e.points[0][0] == e.points[1][0]})
    assert vertical5 == pytest.approx([-15.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0])
    fallback = SiteDesign(
        structures={"rect1": _placement(0.0, 0.0)},
        options=SitePlanOptions(coord_grid=5.0),
    )
    chained = site_layout(fallback, plant, base_styles(), SiteOptions())  # None=回退
    grid_fb = [e for e in chained.entities
               if e.layer == LAYER_AXIS and e.kind == "line"]
    vertical_fb = sorted({e.points[0][0] for e in grid_fb
                          if e.points[0][0] == e.points[1][0]})
    assert vertical_fb == pytest.approx(vertical5)


def test_rotation_rotates_corners() -> None:
    """§三.8 rotation：cos/sin 通用旋转——90° 恰为轴对齐交换（中心=摆放点）。"""
    site = SiteDesign(structures={"rot": _placement(10.0, 10.0, rotation=90.0)})
    plant = _plant({"design": {"rot": _snap("rot", {"length": 4.0, "width": 2.0})}})
    group = site_layout(site, plant, base_styles())
    segs = [e for e in group.entities if e.layer == LAYER_POOL and e.kind == "line"]
    assert len(segs) == 4
    corners = {(round(p[0], 6), round(p[1], 6)) for e in segs for p in e.points}
    assert corners == {(9.0, 8.0), (11.0, 8.0), (11.0, 12.0), (9.0, 12.0)}


def test_title_annotations_condition_and_sheet_no() -> None:
    """§三.1/4 R4 收窄：工况=sorted 首键+sheet_no 进标题栏注记（title_block 形态）。"""
    plant = _plant({"zeta": {}, "alpha": {}})
    group = site_layout(SiteDesign(), plant, base_styles())
    titles = [e for e in group.entities if e.layer == LAYER_TITLE]
    assert {e.source_key for e in titles} == {"condition", "sheet_no"}
    assert all(e.kind == "text" for e in titles)
    by_key = {e.source_key: e for e in titles}
    assert by_key["condition"].text == "condition=alpha"  # sorted 首键（确定性）
    assert by_key["sheet_no"].text.startswith("sheet_no=")
    border = next(e for e in group.entities if e.kind == "rect")
    (bx0, by0), (bx1, by1) = border.points
    for e in titles:  # G1-05：注记锚点并入包络——恒在图框内
        assert bx0 <= e.points[0][0] <= bx1
        assert by0 <= e.points[0][1] <= by1


def test_layers_subset_no_new_layers() -> None:
    """§三.14 层用法：实体层 ⊆ base_styles 八层真源（零新层零 styles 触碰）。"""
    group = site_layout(_rich_site(), _rich_plant(), base_styles())
    known = {layer.name for layer in base_styles().layers}
    assert {e.layer for e in group.entities} <= known
    assert {e.layer for e in group.entities} == {
        LAYER_AXIS, LAYER_BORDER, LAYER_LABEL, LAYER_PIPE, LAYER_POOL, LAYER_TITLE,
    }  # ELEV/DIM 本图不启用（标高注记沿 plan_view 用 LABEL 层先例）


def _canonical(group: EntityGroup) -> str:
    """sorted entities 归一字符串（kind/层/文字/键/坐标 round10/参数）——防漂移基。"""

    def one(entity: object) -> str:
        pts = ";".join(
            f"{round(x, 10)!r},{round(y, 10)!r}" for x, y in entity.points
        )
        params = ";".join(
            f"{key}={round(value, 10)!r}"
            for key, value in sorted(entity.params.items())
        )
        return "|".join(
            (entity.kind, entity.layer, entity.text, entity.source_key, pts, params)
        )

    return "\n".join(sorted(one(e) for e in group.entities))


def _digest(group: EntityGroup) -> str:
    return hashlib.sha256(_canonical(group).encode("utf-8")).hexdigest()[:16]


def test_entitygroup_determinism_and_hash_anchor() -> None:
    """§三.7 golden 锚：双调同哈希+冻结 head16（实体漂移即红）。"""
    first = site_layout(_rich_site(), _rich_plant(), base_styles())
    second = site_layout(_rich_site(), _rich_plant(), base_styles())
    assert _digest(first) == _digest(second)  # 双调哈希同（确定性）
    assert _digest(first) == "d5dad837e42ea8fd"  # 锚（R 轮五修重录，2026-09-03）


def test_exception_faces() -> None:
    """GR-11 异常面：空 conditions/coord_grid 非正=结构性非法拒；轮廓键缺=占位不抛。"""
    with pytest.raises(InvalidSitePlanError):
        site_layout(SiteDesign(), _plant({}), base_styles())
    with pytest.raises(InvalidSitePlanError):
        site_layout(
            SiteDesign(options=SitePlanOptions(coord_grid=0.0)),
            _plant({"design": {}}), base_styles(),
        )
    with pytest.raises(InvalidSitePlanError):  # 覆盖链值同守卫
        site_layout(
            SiteDesign(), _plant({"design": {}}), base_styles(),
            SiteOptions(coord_grid=-5.0),
        )
    for bad_grid in (float("nan"), float("inf")):  # G1-04：非有限双拦（NaN/Inf）
        with pytest.raises(InvalidSitePlanError):
            site_layout(
                SiteDesign(), _plant({"design": {}}), base_styles(),
                SiteOptions(coord_grid=bad_grid),
            )
