"""pumps 镜像测试：提升判定（跌水警告、自流空计划、扬程不等式、工况标注）。

输入:  waterprint.elevation.pumps 公开符号
输出:  判定语义断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.elevation.pumps")
evaluate_pumping = getattr(_mod, "evaluate_pumping", None)

pytestmark = pytest.mark.skipif(
    evaluate_pumping is None,
    reason="实现未就绪：waterprint.elevation.pumps（M2）",
)


def _station(uid: str, water_level: float, flow: float = 0.2):
    from waterprint.contracts.drawing_projection import ProfileStation

    return ProfileStation(
        unit_id=uid, water_level=water_level, floor_elev=water_level - 1.0,
        ground_elev=water_level + 1.0, bury_depth=2.0, freeboard=0.3,
        water_depth=1.0, loss_in=0.0, design_flow=flow,
    )


def _profile(stations, condition_key: str = "design"):
    from waterprint.contracts.drawing_projection import ElevationProfile

    return ElevationProfile(
        stations=tuple(stations), condition_key=condition_key,
        trace=(), warnings=(),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


def test_evaluate_pumping_is_the_single_entry() -> None:
    """入口冻结：evaluate_pumping(profile, assumptions) -> PumpingPlan。"""
    assert callable(evaluate_pumping)


def test_gravity_flow_yields_empty_stations_and_no_warnings() -> None:
    """R4：全程自流 = 空站位列表是合法结果（非异常）。

    占位实质化（DRAFT 批总授权先例）：自流纵断（缓降 0.2 m/站，均低于
    1 m 阈值）→ stations 为空且 drop_warnings 为空。
    """
    plan = evaluate_pumping(
        _profile([_station("u1", 10.0), _station("u2", 9.8), _station("u3", 9.6)]),
        _assumptions(),
    )
    assert plan.stations == ()
    assert plan.drop_warnings == ()


def test_two_meter_drop_emits_warning_with_correct_head() -> None:
    """R1：2 m 跌水 → Warning 且高差正确（阈值默认 1 m 来自 assumptions）。"""
    plan = evaluate_pumping(
        _profile([_station("u1", 10.0), _station("u2", 8.0)]), _assumptions()
    )
    assert plan.stations == ()  # 跌水不需提升
    assert len(plan.drop_warnings) == 1
    warning = plan.drop_warnings[0]
    assert warning.condition_key == "design"
    assert "u2" in warning.message
    assert "2.000" in warning.message  # 高差 10.0-8.0=2 m 入消息


def test_required_lift_produces_station_and_head_invariant() -> None:
    """R1：需提升（下游水面高于上游）→ 站位+扬程；total_head >= static_head。"""
    plan = evaluate_pumping(
        _profile([_station("u1", 5.0), _station("u2", 8.0, flow=0.2)]),
        _assumptions(),
    )
    assert len(plan.stations) == 1
    station = plan.stations[0]
    assert station.unit_id == "u2"
    assert station.static_head == pytest.approx(3.0)
    assert station.total_head >= station.static_head  # 管路损失经 EL-F1 ≥0
    assert station.design_flow == pytest.approx(0.2)
    assert station.condition_key == "design"  # R3 工况标注
