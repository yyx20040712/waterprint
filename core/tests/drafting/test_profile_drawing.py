"""profile_drawing 镜像测试：高程纵断图（四线/比例分设/工况标注接线）。

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


def _options():
    from waterprint.drafting.profile_drawing import ProfileOptions

    return ProfileOptions(h_scale=500, v_scale=100)


def test_entrypoint_frozen() -> None:
    """入口冻结：profile_sheet(profile, styles, options)（横纵比例分设）。"""
    assert callable(profile_sheet)


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
    # 测试零复制公式；x=站左/右界桩号）
    to_sheet = getattr(_mod, "_to_sheet")
    bounds = (0.0, 10.0, 20.0)  # 缺省等距 10m 站距的左右界桩号
    for entity in lines:
        field = entity.source_key.removeprefix("profile.")
        for station, left, right in zip(
            _profile().stations,
            bounds[:-1],
            bounds[1:],
            strict=True,
        ):
            for x_m in (left, right):
                point = to_sheet(x_m, getattr(station, field), factor,
                                 options)
                assert point in entity.points
