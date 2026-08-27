"""drawing_projection_types 镜像测试：类型面三类型不变量（宪法 §6 镜像）。

输入:  waterprint.contracts.drawing_projection_types（UnitProjection/
       ProfileStation/ElevationProfile 三类型，M3D1 D1 拆出）
输出:  frozen 不可变/Mapping 只读快照防泄漏/drawn_keys 并集语义/
       station_of 查询行为断言（薄镜像——主对账面在
       test_drawing_projection.py，本文件只守类型面主概念）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3D1 R1 薄镜像（总控追加授权 2026-08-27 夜——宪法 §6 镜像
#   规则 CI 强制补齐；样本为纯声明面键名+量纲枚举，零数值计算）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses

import pytest

from waterprint.contracts.drawing_projection_types import (
    ElevationProfile,
    ProfileStation,
    UnitProjection,
)
from waterprint.contracts.quantity import DimKey


def _projection() -> UnitProjection:
    """最小构造样本（键名/量纲枚举声明面——本文件零数值计算）。"""
    return UnitProjection(
        "sample_unit",
        plan_keys={"overall_length": "l"},
        section_keys={"pool_depth": "h"},
        primitive_dims={"length": "l", "depth": "h"},
        instance_counts={"pump": "n_pump"},
        non_drawn=("v_concrete",),
        dim_of={"l": DimKey.LENGTH, "h": DimKey.LENGTH,
                "n_pump": DimKey.DIMENSIONLESS, "v_concrete": DimKey.VOLUME},
    )


def test_unit_projection_frozen_with_readonly_snapshot() -> None:
    """六字段不可变：赋值拒；Mapping 字段构造即只读快照（写拒）。"""
    projection = _projection()
    with pytest.raises(dataclasses.FrozenInstanceError):
        projection.unit_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        projection.plan_keys["overall_length"] = "x"  # type: ignore[index]
    with pytest.raises(TypeError):
        projection.dim_of["l"] = DimKey.AREA  # type: ignore[index]
    assert isinstance(projection.non_drawn, tuple)


def test_snapshot_isolates_external_containers() -> None:
    """外部改原容器不泄漏（T3A-01 防线：构造后即与传入 dict 脱钩）。"""
    plan = {"overall_length": "l"}
    dims = {"l": DimKey.LENGTH}
    projection = UnitProjection(
        "sample_unit", plan_keys=plan, section_keys={}, primitive_dims={},
        instance_counts={}, non_drawn=(), dim_of=dims,
    )
    plan["overall_length"] = "mutated"
    dims["l"] = DimKey.AREA
    assert projection.plan_keys["overall_length"] == "l"
    assert projection.dim_of["l"] is DimKey.LENGTH


def test_drawn_keys_is_union_of_four_categories() -> None:
    """drawn_keys=四类取数键并集（non_drawn 不进并集——R1 对账面）。"""
    projection = _projection()
    assert projection.drawn_keys() == frozenset({"l", "h", "n_pump"})
    empty = UnitProjection(
        "empty_unit", plan_keys={}, section_keys={}, primitive_dims={},
        instance_counts={}, non_drawn=("only_key",),
        dim_of={"only_key": DimKey.VOLUME},
    )
    assert empty.drawn_keys() == frozenset()


def test_elevation_profile_station_of_lookup() -> None:
    """station_of 命中返回站/未命中返回 None；ElevationProfile 不可变。"""
    first = ProfileStation(
        unit_id="unit_a", water_level=1.0, floor_elev=0.0, ground_elev=2.0,
        bury_depth=1.0, freeboard=1.0, water_depth=1.0, loss_in=0.0,
        design_flow=0.0,
    )
    second = ProfileStation(
        unit_id="unit_b", water_level=1.0, floor_elev=0.0, ground_elev=2.0,
        bury_depth=1.0, freeboard=1.0, water_depth=1.0, loss_in=0.0,
        design_flow=0.0,
    )
    profile = ElevationProfile(
        stations=(first, second), condition_key="design", trace=(),
        warnings=(),
    )
    assert profile.station_of("unit_b") is second
    assert profile.station_of("no_such_unit") is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        profile.condition_key = "avg"  # type: ignore[misc]
