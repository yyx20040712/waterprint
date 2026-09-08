"""profile_drawing 实现测试：比例分设/站距/工况/泵注记/哈希自锚/边界。

输入:  waterprint.drafting.profile_drawing（PROFILE 批实现，总裁定
       简报 task-PROFILE-plan.md PD8——与锁内契约件分离的实现面用例）
输出:  纵断图行为断言（六用例：比例换算/station_lengths/工况标注/
       pumping 注入/内容哈希自锚/单站边界）
"""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.drafting.profile_drawing")
profile_sheet = getattr(_mod, "profile_sheet")
ProfileOptions = getattr(_mod, "ProfileOptions")


def _profile():
    """两站夹具（与锁内契约件同构——九字段实值直接构造）。"""
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


def _single_station():
    """单站夹具（边界用例——两折点=站左右界，不崩）。"""
    from waterprint.contracts.drawing_projection import (
        ElevationProfile,
        ProfileStation,
    )

    return ElevationProfile(
        stations=(
            ProfileStation(
                unit_id="solo", water_level=5.0, floor_elev=3.0,
                ground_elev=6.0, bury_depth=3.0, freeboard=0.3,
                water_depth=2.0, loss_in=0.1, design_flow=50.0,
            ),
        ),
        condition_key="avg",
        trace=(),
        warnings=(),
    )


def _styles():
    from waterprint.drafting.styles import base_styles

    return base_styles()


def test_scale_split_independent_axes() -> None:
    """PD4：横纵比例分设独立换算——x=桩距×因子÷h、y=标高×因子÷v。"""
    from waterprint.contracts.quantity import DimKey, parse

    options = ProfileOptions(h_scale=500, v_scale=100)
    group = profile_sheet(_profile(), _styles(), options)
    ground = next(
        e for e in group.entities
        if e.kind == "line" and e.layer.endswith("anno-elev")
        and e.source_key == "profile.ground_elev"
    )
    factor = 1.0 / parse(1.0, "mm", DimKey.LENGTH)
    # 站 u1 左界 (0, 12.0)：x=0，y=12×factor/100；右界 (10, 12.0)：
    # x=10×factor/500（横纵分母不同——独立验证）
    assert pytest.approx(0.0) == ground.points[0][0]
    assert pytest.approx(12.0 * factor / 100) == ground.points[0][1]
    assert pytest.approx(10.0 * factor / 500) == ground.points[1][0]
    assert pytest.approx(12.0 * factor / 100) == ground.points[1][1]


def test_station_lengths_override_and_default() -> None:
    """PD2：station_lengths 实值生效（未列站回落缺省等距 10m）。"""
    options = ProfileOptions(
        h_scale=1, v_scale=1, station_lengths={"u1": 30.0}
    )
    group = profile_sheet(_profile(), _styles(), options)
    water = next(
        e for e in group.entities
        if e.kind == "line" and e.source_key == "profile.water_level"
    )
    # u1 平台右界=30 m 实值、u2 平台=30~40 m（缺省 10）——图面坐标为
    # mm（x=桩距×mm 因子÷h_scale，h_scale=1 时 x=桩距×1000）
    assert water.points[1][0] == pytest.approx(30.0 * 1000.0)
    assert water.points[3][0] == pytest.approx(40.0 * 1000.0)


def test_condition_annotation_present() -> None:
    """R5：工况标注实体文本==condition_key（不同工况图纸可区分）。"""
    group = profile_sheet(_profile(), _styles(), ProfileOptions(1, 1))
    conditions = [
        e for e in group.entities
        if e.kind == "text" and e.source_key == "condition_key"
    ]
    assert len(conditions) == 1
    assert "design" in conditions[0].text


def _pumping():
    """提升计划夹具：一站提升 + 一条跌水警告。"""
    from waterprint.contracts.unit_api import Severity, Warning
    from waterprint.elevation.pumps import PumpingPlan, PumpStation

    return PumpingPlan(
        stations=(
            PumpStation(unit_id="u2", static_head=0.5, total_head=0.8,
                        design_flow=100.0, condition_key="design"),
        ),
        drop_warnings=(
            Warning(severity=Severity.WARN, source="test",
                    message="跌水警告注记", condition_key="design",
                    affected_unit_ids=("u2",)),
        ),
    )


def test_pumping_annotation_injected_or_skipped() -> None:
    """PD3：pumping 注入产泵/跌水注记；None 整体跳过。"""
    plain = profile_sheet(_profile(), _styles(), ProfileOptions(1, 1))
    assert not [e for e in plain.entities
                if e.source_key.startswith("pumping.")]
    injected = profile_sheet(
        _profile(), _styles(), ProfileOptions(1, 1, pumping=_pumping())
    )
    pumps = [e for e in injected.entities
             if e.source_key == "pumping.total_head"]
    drops = [e for e in injected.entities
             if e.source_key == "pumping.drop_warnings"]
    assert len(pumps) == 1 and "0.800" in pumps[0].text
    assert len(drops) == 1 and drops[0].text == "跌水警告注记"


def _canonical(group) -> str:
    """EntityGroup 规范化序列化（内容哈希自锚——PD8/D5 选 b）：
    kind/layer/text/source_key/params 键值排序/坐标定点格式化逐实体拼接。"""
    parts: list[str] = []
    for entity in group.entities:
        params = ";".join(
            f"{k}={v!r}" for k, v in sorted(entity.params.items())
        )
        points = ";".join(
            f"({x:.6f},{y:.6f})" for x, y in entity.points
        )
        parts.append(
            f"{entity.kind}|{entity.layer}|{entity.text}|"
            f"{entity.source_key}|{params}|{points}"
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def test_content_hash_snapshot_anchor() -> None:
    """内容哈希自锚（快照回归替代形态——不动 tests/snapshots/ambr）：
    同输入双跑规范化哈希恒等+锚字面量（改图必走重锚+入批注记——
    确定性约束背书；锚值=PROFILE 批首版实测冻结）。"""
    options = ProfileOptions(500, 100, pumping=_pumping())
    first = profile_sheet(_profile(), _styles(), options)
    second = profile_sheet(_profile(), _styles(), options)
    digest = _canonical(first)
    assert digest == _canonical(second)  # 双跑恒等（确定性）
    assert len(digest) == 64  # sha256 十六进制形态
    assert digest == (  # PROFILE 批首版实测冻结锚
        "692780c8ecd019bb9881b1c2ccc5d5fee962dc2ad68f6401d74fc34fd806b725"
    )


def test_single_station_two_point_platform() -> None:
    """单站边界：平台两折点=站左右界（缺省 10m 跨），不崩不退化。"""
    group = profile_sheet(_single_station(), _styles(), ProfileOptions(1, 1))
    lines = [e for e in group.entities if e.kind == "line"]
    assert lines, "单站仍须产出四线"
    for entity in lines:
        assert len(entity.points) == 2  # 单站=左界 0/右界 10m 两折点
        assert entity.points[0][0] == pytest.approx(0.0)
        assert entity.points[1][0] == pytest.approx(
            10.0 * 1000.0
        )  # 图面 mm（h_scale=1）


def test_empty_stations_and_bad_scale_rejected(tmp_path: Path) -> None:
    """入口校验 fail-closed：空站位/比例非正拒（GR-11 族）。"""
    from waterprint.contracts.drawing_projection import ElevationProfile
    from waterprint.drafting.profile_drawing import (
        InvalidProfileDrawingError,
    )

    empty = ElevationProfile(
        stations=(), condition_key="design", trace=(), warnings=()
    )
    with pytest.raises(InvalidProfileDrawingError):
        profile_sheet(empty, _styles(), ProfileOptions(1, 1))
    with pytest.raises(InvalidProfileDrawingError):
        profile_sheet(_profile(), _styles(), ProfileOptions(0, 100))
    with pytest.raises(InvalidProfileDrawingError):
        profile_sheet(_profile(), _styles(), ProfileOptions(500, -1))
