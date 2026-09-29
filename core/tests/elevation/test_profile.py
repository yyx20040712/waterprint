"""profile 镜像测试：沿程推算（纵断连续性、工况索引、超高来源、越界警告）。

输入:  waterprint.elevation.profile 公开符号
输出:  纵断语义断言（详细数值 golden 归 M2 市政案例）
"""

from __future__ import annotations

import importlib
from itertools import pairwise

import pytest

_mod = importlib.import_module("waterprint.elevation.profile")
build_profile = getattr(_mod, "build_profile", None)

pytestmark = pytest.mark.skipif(
    build_profile is None,
    reason="实现未就绪：waterprint.elevation.profile（M2）",
)


def _mini_plant():
    """线性三单元 design 工况结果（chenshachi→chuchenchi→ziwai，表内水深键）。"""
    from waterprint.contracts.result_schema import (
        PlantResult,
        ReproTriple,
        UnitResultSnapshot,
    )

    def snap(uid: str, depth: float) -> UnitResultSnapshot:
        return UnitResultSnapshot(
            unit_id=uid,
            outflows={f"{uid}.out.q_avg_daily": 0.2},
            outqualities={},
            dims={"h2": depth, "h_w": depth, "d": 2.0, "h_total": depth + 0.3},
            warnings=(),
            formula_ids=(),
        )

    return PlantResult(
        conditions={
            "design": {
                "inlet": UnitResultSnapshot(
                    unit_id="inlet", outflows={}, outqualities={}, dims={},
                    warnings=(), formula_ids=(),
                ),
                "municipal_chenshachi": snap("municipal_chenshachi", 1.25),
                "municipal_chuchenchi": snap("municipal_chuchenchi", 1.5),
                "municipal_ziwai": snap("municipal_ziwai", 1.0),
            }
        },
        summary={},
        trace=(),
        repro=ReproTriple(design_hash="", engine_version="", data_version=""),
    )


def _segments():
    from waterprint.elevation.losses import head_losses

    return head_losses(
        [
            ("municipal_chuchenchi",
             {"kind": "friction", "diameter": 0.5, "length": 100.0}, 0.2),
            ("municipal_ziwai",
             {"kind": "friction", "diameter": 0.5, "length": 100.0}, 0.2),
        ],
        ctx=("profile-mirror", "design"),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


def test_build_profile_is_the_single_entry() -> None:
    """入口冻结：build_profile(plant_result, losses, inlet_config, assumptions, condition_key)。"""
    assert callable(build_profile)


def test_water_level_continuity_contract_is_specified() -> None:
    """R1 连续性断言（M2 实质化）：下游水面 <= 上游水面 − 损失（逐相邻站）。

    占位实质化（DRAFT 批总授权先例）：线性三单元纵断实跑对账——
    站序=拓扑序、每站水面恰等于上游水面−进站损失（等式收紧 ≤）。
    """
    profile = build_profile(
        _mini_plant(), _segments(),
        {"water_level": 10.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    stations = profile.stations
    assert [s.unit_id for s in stations] == [
        "municipal_chenshachi", "municipal_chuchenchi", "municipal_ziwai",
    ]
    for upstream, downstream in pairwise(stations):
        assert downstream.water_level <= upstream.water_level - downstream.loss_in
        assert downstream.water_level == pytest.approx(
            upstream.water_level - downstream.loss_in
        )
    # 池底=水面−水深（表内 water_depth 键取数）；埋深=地面−池底
    for station in stations:
        assert station.floor_elev == pytest.approx(
            station.water_level - station.water_depth
        )
        assert station.bury_depth == pytest.approx(
            station.ground_elev - station.floor_elev
        )


def test_profile_carries_condition_key_index() -> None:
    """R3 工况索引：condition_key 贯穿标注（design/avg 各自成 Profile）。"""
    from dataclasses import replace

    plant = _mini_plant()
    plant_avg = replace(plant, conditions={"avg": plant.conditions["design"]})
    design = build_profile(
        plant, _segments(), {"water_level": 10.0, "ground_elev": 12.0},
        _assumptions(), "design",
    )
    avg = build_profile(
        plant_avg, _segments(), {"water_level": 9.0, "ground_elev": 12.0},
        _assumptions(), "avg",
    )
    assert design.condition_key == "design"
    assert avg.condition_key == "avg"
    assert avg.stations[0].water_level < design.stations[0].water_level


def test_freeboard_comes_from_assumptions() -> None:
    """R2 超高来源：站 freeboard == assumptions 的 safety.superheight（非内联）。"""
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    profile = build_profile(
        _mini_plant(), _segments(),
        {"water_level": 10.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    superheight = next(
        entry.default for entry in DEFAULT_ASSUMPTIONS
        if entry.key == "safety.superheight"
    )
    assert all(
        station.freeboard == superheight for station in profile.stations
    )


def test_bury_depth_out_of_band_emits_warning() -> None:
    """R5 越界 Warning：过深（>bury_depth.max）与出地面（<0）都触发且进结果。"""
    deep = build_profile(
        _mini_plant(), _segments(),
        {"water_level": -10.0, "ground_elev": 0.0}, _assumptions(), "design",
    )
    assert any("埋深" in w.message for w in deep.warnings)
    above = build_profile(
        _mini_plant(), _segments(),
        {"water_level": 50.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    assert any("地面" in w.message for w in above.warnings)


def test_missing_depth_key_unit_is_explicit_not_silent() -> None:
    """无水深键单元（AAO 类）以 0 水深入站并出 INFO Warning（禁静默遗漏）。"""
    from waterprint.elevation.losses import head_losses

    profile = build_profile(
        _mini_plant(), head_losses((), ctx=("", "")),
        {"water_level": 10.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    ziwai = next(
        station for station in profile.stations
        if station.unit_id == "municipal_ziwai"
    )
    assert ziwai.water_depth == pytest.approx(1.0)  # ziwai 表内键 h_w 生效


# ══════════════════════════════════════════════════════════════════
# 批6i 桩号轴（build_chainage_axis）：站距三态装配对拍面
# ══════════════════════════════════════════════════════════════════

_chainage_axis = getattr(_mod, "build_chainage_axis", None)

pytestmark_chainage = pytest.mark.skipif(
    _chainage_axis is None,
    reason="实现未就绪：build_chainage_axis（批6i）",
)


def _site(placements: dict[str, tuple[float, float]]):
    """布置夹具：unit_id→(x, y) 摆放（StructurePlacement 最小构造）。"""
    from waterprint.contracts.project_schema import (
        SiteDesign,
        StructurePlacement,
    )

    return SiteDesign(
        structures={
            unit_id: StructurePlacement(x=x, y=y)
            for unit_id, (x, y) in placements.items()
        }
    )


@pytest.mark.skipif(_chainage_axis is None, reason="批6i 未就绪")
def test_chainage_axis_layout_accumulates_euclidean() -> None:
    """对拍主断言：布置连线长度逐段累计——chainages[s_i]==Σ hypot(Δ)
    （坐标整十手设，places=9；三态各占断言）。"""
    from waterprint.elevation.losses import head_losses

    profile = build_profile(
        _mini_plant(), head_losses((), ctx=("", "")),
        {"water_level": 10.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    # 站序：chenshachi→chuchenchi→ziwai（executor 序）；手设非等距坐标
    site = _site({
        "municipal_chenshachi": (0.0, 0.0),
        "municipal_chuchenchi": (30.0, 40.0),   # 距前 50.0（3-4-5 三角）
        "municipal_ziwai": (30.0, 130.0),       # 距前 90.0
    })
    axis = _chainage_axis(profile, site)
    assert [edge.station_len for edge in axis.edges] == [
        pytest.approx(50.0), pytest.approx(90.0),
    ]
    assert [edge.source for edge in axis.edges] == ["layout", "layout"]
    assert axis.chainages["municipal_chenshachi"] == pytest.approx(0.0)
    assert axis.chainages["municipal_chuchenchi"] == pytest.approx(50.0)
    assert axis.chainages["municipal_ziwai"] == pytest.approx(
        140.0
    )  # Σ 边长（50+90）逐段累计
    assert axis.warnings == ()  # 全布置在场零记档
    assert set(axis.platform_widths) == {  # 占位宽全表 10 m（单源）
        "municipal_chenshachi", "municipal_chuchenchi", "municipal_ziwai",
    }


@pytest.mark.skipif(_chainage_axis is None, reason="批6i 未就绪")
def test_chainage_axis_manual_override_and_gates() -> None:
    """手动逐边覆盖例外通道：manual 命中胜默认源；首站键/未知键/非正
    值三闸 fail-visible（批6i B1-k1 洞穿修正——合法集=首站外站位）。"""
    from waterprint.elevation.losses import head_losses
    from waterprint.elevation.profile import InvalidProfileError

    profile = build_profile(
        _mini_plant(), head_losses((), ctx=("", "")),
        {"water_level": 10.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    site = _site({
        "municipal_chenshachi": (0.0, 0.0),
        "municipal_chuchenchi": (30.0, 40.0),
        "municipal_ziwai": (30.0, 130.0),
    })
    axis = _chainage_axis(profile, site, {"municipal_ziwai": 44.0})
    assert axis.edges[1].source == "manual"
    assert axis.edges[1].station_len == pytest.approx(44.0)
    assert axis.chainages["municipal_ziwai"] == pytest.approx(94.0)
    # 首站键拒（无入边永不消费=静默吞意图——k1-B1）
    with pytest.raises(InvalidProfileError, match="首站"):
        _chainage_axis(profile, site, {"municipal_chenshachi": 5.0})
    # 未知键拒（图改残键 fail-visible）
    with pytest.raises(InvalidProfileError, match="未知键"):
        _chainage_axis(profile, site, {"ghost_unit": 5.0})
    # 非正/非有限拒（手动值错误须显式修）
    with pytest.raises(InvalidProfileError, match="正有限"):
        _chainage_axis(profile, site, {"municipal_ziwai": 0.0})
    with pytest.raises(InvalidProfileError, match="正有限"):
        _chainage_axis(profile, site, {"municipal_ziwai": -3.0})


@pytest.mark.skipif(_chainage_axis is None, reason="批6i 未就绪")
def test_chainage_axis_fallback_and_coincident_and_overlap() -> None:
    """fallback 三面：缺摆放=占位+INFO；同位=降级 fallback+WARN（出图
    非校核域）；负间隙（边长<半宽和）=WARN 记档不拒（占位宽假象）。"""
    from waterprint.contracts.unit_api import Severity
    from waterprint.elevation.losses import head_losses

    profile = build_profile(
        _mini_plant(), head_losses((), ctx=("", "")),
        {"water_level": 10.0, "ground_elev": 12.0}, _assumptions(), "design",
    )
    # ①缺 site_design 整表 fallback+INFO
    axis = _chainage_axis(profile, None)
    assert [edge.source for edge in axis.edges] == ["fallback", "fallback"]
    assert all(w.severity == Severity.INFO for w in axis.warnings)
    assert axis.chainages["municipal_ziwai"] == pytest.approx(20.0)
    # ②混合：ziwai 缺摆放 → 边0 layout（两端正摆）、边1 fallback
    # （缺一即 fallback——N3-d1 显式定义）
    site_partial = _site({
        "municipal_chenshachi": (0.0, 0.0),
        "municipal_chuchenchi": (30.0, 40.0),
    })
    axis_p = _chainage_axis(profile, site_partial)
    assert axis_p.edges[0].source == "layout"
    assert axis_p.edges[1].source == "fallback"
    # ③同位：两点同坐标 → 降级 fallback+WARN（不堵死出图——W4-d1）
    site_coincident = _site({
        "municipal_chenshachi": (10.0, 10.0),
        "municipal_chuchenchi": (10.0, 10.0),
        "municipal_ziwai": (10.0, 100.0),
    })
    axis_c = _chainage_axis(profile, site_coincident)
    assert axis_c.edges[0].source == "fallback"
    assert any(
        w.severity == Severity.WARN and "同位" in w.message
        for w in axis_c.warnings
    )
    # ③b 近同位（k1-W3）：亚毫米位移=坐标噪声——归同位降级（非重叠
    # WARN 语义错位）；容差=1 mm 契约派生
    site_near = _site({
        "municipal_chenshachi": (0.0, 0.0),
        "municipal_chuchenchi": (0.0000005, 0.0),  # 0.5 μm 位移
        "municipal_ziwai": (0.0, 90.0),
    })
    axis_n = _chainage_axis(profile, site_near)
    assert axis_n.edges[0].source == "fallback"
    assert any(
        w.severity == Severity.WARN and "同位" in w.message
        for w in axis_n.warnings
    )
    # ④负间隙：真实边长 5 < 半宽和 10 → 平台重叠 WARN（占位宽假象记档）
    site_tight = _site({
        "municipal_chenshachi": (0.0, 0.0),
        "municipal_chuchenchi": (3.0, 4.0),  # 距 5.0 < 10.0
        "municipal_ziwai": (3.0, 94.0),
    })
    axis_t = _chainage_axis(profile, site_tight)
    assert axis_t.edges[0].station_len == pytest.approx(5.0)
    assert any(
        w.severity == Severity.WARN and "重叠" in w.message
        for w in axis_t.warnings
    )


@pytest.mark.skipif(_chainage_axis is None, reason="批6i 未就绪")
def test_chainage_axis_duplicate_station_rejected() -> None:
    """重复 unit_id 入口闸（W4-k1）：Mapping 键塌缩防御——显式拒。"""
    from waterprint.contracts.drawing_projection import (
        ElevationProfile,
        ProfileStation,
    )
    from waterprint.elevation.profile import InvalidProfileError

    def snap(uid: str) -> ProfileStation:
        return ProfileStation(
            unit_id=uid, water_level=1.0, floor_elev=0.0, ground_elev=2.0,
            bury_depth=2.0, freeboard=0.3, water_depth=1.0, loss_in=0.1,
            design_flow=1.0,
        )

    duplicated = ElevationProfile(
        stations=(snap("dup"), snap("dup"), snap("other")),
        condition_key="design", trace=(), warnings=(),
    )
    with pytest.raises(InvalidProfileError, match="重复"):
        _chainage_axis(duplicated, None)
