"""section_view 镜像测试：单体剖面图（三线齐备/标高同源/剖切联动接线）。

输入:  waterprint.drafting.section_view 公开符号
输出:  剖面图契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.section_view")
unit_section = getattr(_mod, "unit_section", None)

pytestmark = pytest.mark.skipif(
    unit_section is None,
    reason="实现未就绪：waterprint.drafting.section_view（M2）",
)


def _station():
    from waterprint.contracts.drawing_projection import ProfileStation

    return ProfileStation(
        unit_id="municipal_chenshachi", water_level=8.75, floor_elev=7.5,
        ground_elev=10.0, bury_depth=2.5, freeboard=0.3, water_depth=1.25,
        loss_in=0.05, design_flow=0.2,
    )


def _snap():
    from waterprint.contracts.result_schema import UnitResultSnapshot

    return UnitResultSnapshot(
        unit_id="municipal_chenshachi", outflows={}, outqualities={},
        dims={"h2": 1.25, "h_total": 3.0}, warnings=(), formula_ids=(),
    )


def test_entrypoint_frozen() -> None:
    """入口冻结：unit_section(unit_result, profile_station, styles, condition_key, options)。"""
    assert callable(unit_section)


def test_three_lines_wiring() -> None:
    """R2 接线断言（M2 实质化）：三线实体存在且标高取自 ElevationProfile。

    占位实质化（DRAFT 批总授权先例）：地面/水面/池底三线实体齐备，
    线位 y 值逐线 == ProfileStation 的 ground/water/floor（标高唯一真源，
    本文件零推算）；水深标注 measurement == 池底→水面高差。
    """
    from waterprint.drafting.styles import base_styles

    group = unit_section(_snap(), _station(), base_styles(), "design")
    lines = {e.text: e for e in group.entities if e.kind == "line"
             and e.text in ("ground", "water", "floor")}
    assert set(lines) == {"ground", "water", "floor"}  # 三线齐备
    station = _station()
    assert lines["ground"].points[0][1] == pytest.approx(station.ground_elev)
    assert lines["water"].points[0][1] == pytest.approx(station.water_level)
    assert lines["floor"].points[0][1] == pytest.approx(station.floor_elev)
    depth = next(e for e in group.entities if e.kind == "dim_linear")
    assert depth.params["measurement"] == pytest.approx(station.water_depth)
    assert any("condition=design" in e.text for e in group.entities)


def test_cut_position_links_plan_and_section() -> None:
    """R1 剖切联动：CutPosition 值对象经 SectionOptions 驱动剖切线图元。"""
    from waterprint.drafting.section_view import CutPosition, SectionOptions
    from waterprint.drafting.styles import base_styles

    cut = CutPosition(id="1-1", origin=(2.0, 0.0), direction=(2.0, 3.0))
    group = unit_section(
        _snap(), _station(), base_styles(), "design",
        SectionOptions(cut_position=cut),
    )
    cut_lines = [e for e in group.entities if e.kind == "cut_line"]
    assert len(cut_lines) == 1
    assert cut_lines[0].text == "1-1"
    assert cut_lines[0].points == (cut.origin, cut.direction)
