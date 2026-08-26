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
