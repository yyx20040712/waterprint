"""profile_drawing 镜像测试：高程纵断图（四线/比例分设/桩号轴/工况标注接线）。

批6i 桩号轴：站位横轴=桩号（真实站距）——axis 必填单源（build_chainage_axis
构造，本图零自建）；v1 station_lengths 通道退役（全仓零消费勘察在案）。

输入:  waterprint.drafting.profile_drawing 公开符号
输出:  纵断图契约断言
"""

from __future__ import annotations

import importlib

_mod = importlib.import_module("waterprint.drafting.profile_drawing")
profile_sheet = getattr(_mod, "profile_sheet", None)


def _profile():
    """两站最小 ElevationProfile 夹具（九字段实值，直接构造零推算链）。"""
    from waterprint.contracts.drawing_projection import (
        ElevationProfile,
        ProfileStation,
    )

    return ElevationProfile(
        stations=(
            ProfileStation(
                unit_id="u1", water_level=10.0, floor_elev=8.0,
                ground_elev=12.0, bury_depth=4.0, freeboard=0.3,
                water_depth=2.0, loss_in=0.2, design_flow=100.0,
            ),
            ProfileStation(
                unit_id="u2", water_level=9.5, floor_elev=7.5,
                ground_elev=12.0, bury_depth=4.5, freeboard=0.3,
                water_depth=2.0, loss_in=0.3, design_flow=100.0,
            ),
        ),
        condition_key="design",
        trace=(),
        warnings=(),
    )


def _axis(profile=None):
    """fallback 桩号轴（build_chainage_axis 单源构造——site_design=None
    整表 fallback+INFO Warning，本测试零自建轴）。"""
    from waterprint.elevation.profile import build_chainage_axis

    return build_chainage_axis(profile if profile is not None else _profile(), None)


def _options():
    from waterprint.drafting.profile_drawing import ProfileOptions

    return ProfileOptions(h_scale=500, v_scale=100, axis=_axis())


def test_entrypoint_frozen() -> None:
    """入口冻结：profile_sheet(profile, styles, options)（横纵比例分设+轴必填）。"""
    assert callable(profile_sheet)


def test_station_lengths_channel_retired() -> None:
    """批6i 通道退役断言：ProfileOptions 无 station_lengths 字段（占位宽
    单源化——平台占宽经 ChainageAxis.platform_widths 承载，双占位常量
    消除）。"""
    from waterprint.drafting.profile_drawing import ProfileOptions

    assert not hasattr(ProfileOptions(h_scale=500, v_scale=100, axis=_axis()),
                       "station_lengths")


def test_four_lines_wiring() -> None:
    """R1 接线断言：地面/水面/池底/管底四线实体存在且标高取自
    ElevationProfile（值==被引用字段经模块统一换算的结果——管底线
    引用 floor_elev，语义由 LAYER_PIPE 图层承载，PROFILE 批 PD1/PD6）。

    〔原 M5 占位断言语义保留注记：「M5 接线断言：纵断图四线实体
    存在且标高取自 ElevationProfile——不得删除」——PROFILE 批实现
    后由本真断言承载〕
    """
    from waterprint.contracts.quantity import DimKey, parse
    from waterprint.drafting.styles import (
        LAYER_ELEV,
        LAYER_PIPE,
        LAYER_POOL,
        base_styles,
    )

    options = _options()
    group = profile_sheet(_profile(), base_styles(), options)  # type: ignore[misc]
    lines = [e for e in group.entities if e.kind == "line"]
    factor = 1.0 / parse(1.0, "mm", DimKey.LENGTH)
    # 四线各按 (字段, 图层) 定位——管底与池底同 source_key 字段、
    # 图层分取（LAYER_POOL/LAYER_PIPE）。
    expected = (
        ("ground_elev", LAYER_ELEV),
        ("water_level", LAYER_ELEV),
        ("floor_elev", LAYER_POOL),
        ("floor_elev", LAYER_PIPE),
    )
    found = {(e.source_key.removeprefix("profile."), e.layer) for e in lines}
    for pair in expected:
        assert pair in found, f"四线缺 {pair}"
    # 每线 y 值==被引用字段经 _to_sheet 统一换算（换算入口直调——
    # 测试零复制公式；x=平台左/右界〔中心锚：桩号 c±w/2〕）
    to_sheet = getattr(_mod, "_to_sheet")
    axis = _axis()
    for entity in lines:
        field = entity.source_key.removeprefix("profile.")
        for station in _profile().stations:
            chainage = axis.chainages[station.unit_id]
            half = axis.platform_widths[station.unit_id] / 2
            for x_m in (chainage - half, chainage + half):
                point = to_sheet(x_m, getattr(station, field), factor,
                                 options)
                assert point in entity.points


def test_chainage_axis_wiring() -> None:
    """R2 桩号轴接线断言：每站桩号 K 图式标注在场（K{km}+{m:06.3f} 零
    填充）+图脚站距源注记在场（三态计数行——fallback 通道可定位）。"""
    from waterprint.drafting.styles import base_styles

    group = profile_sheet(_profile(), base_styles(), _options())  # type: ignore[misc]
    texts = [e for e in group.entities if e.kind == "text"]
    km_texts = [e for e in texts if e.source_key == "chainage.km"]
    assert {e.text for e in km_texts} == {"K0+000.000", "K0+010.000"}
    notes = [e for e in texts if e.source_key == "chainage.source_note"]
    assert notes, "图脚站距源注记缺席（R5 三态图面化）"
    assert any("站距源" in e.text for e in notes)
    assert any("u1->u2" in e.text for e in notes), "fallback 边明细缺席"
