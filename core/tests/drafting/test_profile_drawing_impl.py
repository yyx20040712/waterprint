"""profile_drawing 实现测试：比例分设/桩号轴/工况/泵注记/哈希自锚/边界。

输入:  waterprint.drafting.profile_drawing（批6i 桩号轴实现——中心锚
       平台+K 图式标注+图脚站距源注记；与锁内契约件分离的实现面用例）
输出:  纵断图行为断言（比例换算/桩号中心锚/工况标注/pumping 注入[含
       异工况过滤与跌水锚定]/内容哈希自锚/单站边界/入口校验拒/轴不匹
       配拒——批6i R2/R5+R 轮 G1-02/G1-03 承接）
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


def _axis(profile=None, overrides=None, site=None):
    """桩号轴单源构造（build_chainage_axis——fallback/覆盖/布置三态经
    正门构造，测试零自建轴=零双行为面）。"""
    from waterprint.elevation.profile import build_chainage_axis

    return build_chainage_axis(
        profile if profile is not None else _profile(), site, overrides
    )


def _styles():
    from waterprint.drafting.styles import base_styles

    return base_styles()


def test_scale_split_independent_axes() -> None:
    """PD4：横纵比例分设独立换算——x=桩距×因子÷h、y=标高×因子÷v
    （批6i 中心锚：u1 平台左界=桩号 0−半宽 5=−5 m，负域合法）。"""
    from waterprint.contracts.quantity import DimKey, parse

    options = ProfileOptions(h_scale=500, v_scale=100, axis=_axis())
    group = profile_sheet(_profile(), _styles(), options)
    ground = next(
        e for e in group.entities
        if e.kind == "line" and e.layer.endswith("anno-elev")
        and e.source_key == "profile.ground_elev"
    )
    factor = 1.0 / parse(1.0, "mm", DimKey.LENGTH)
    # 站 u1 左界 (−5, 12.0)：x=−5×factor/500，y=12×factor/100；右界
    # (5, 12.0)：x=5×factor/500（横纵分母不同——独立验证）
    assert pytest.approx(-5.0 * factor / 500) == ground.points[0][0]
    assert pytest.approx(12.0 * factor / 100) == ground.points[0][1]
    assert pytest.approx(5.0 * factor / 500) == ground.points[1][0]
    assert pytest.approx(12.0 * factor / 100) == ground.points[1][1]


def test_chainage_center_anchor_and_manual_override() -> None:
    """批6i R2：中心锚桩号定位+手动覆盖生效——u2 覆盖 30 m 后桩号=30，
    平台 [25, 35]；u1 桩号 0 平台 [−5, 5]（占位宽 10 半宽 5）。"""
    options = ProfileOptions(
        h_scale=1, v_scale=1, axis=_axis(overrides={"u2": 30.0})
    )
    group = profile_sheet(_profile(), _styles(), options)
    water = next(
        e for e in group.entities
        if e.kind == "line" and e.source_key == "profile.water_level"
    )
    # 图面坐标 mm（x=桩距×mm 因子÷h_scale，h_scale=1 时 x=桩距×1000）
    assert water.points[0][0] == pytest.approx(-5.0 * 1000.0)  # u1 左
    assert water.points[1][0] == pytest.approx(5.0 * 1000.0)   # u1 右
    assert water.points[2][0] == pytest.approx(25.0 * 1000.0)  # u2 左（30−5）
    assert water.points[3][0] == pytest.approx(35.0 * 1000.0)  # u2 右（30+5）


def test_condition_annotation_present() -> None:
    """R5：工况标注实体文本==condition_key（不同工况图纸可区分）。"""
    group = profile_sheet(
        _profile(), _styles(), ProfileOptions(1, 1, axis=_axis())
    )
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


def _pumping_mixed():
    """混合工况夹具：同工况（design）一站提升+一跌水 + 异工况（avg）
    一站提升+一跌水——证注记按 condition_key 过滤（R 轮 G1-02）。"""
    from waterprint.contracts.unit_api import Severity, Warning
    from waterprint.elevation.pumps import PumpingPlan, PumpStation

    design = _pumping()
    return PumpingPlan(
        stations=(
            *design.stations,
            PumpStation(unit_id="u1", static_head=9.0, total_head=9.9,
                        design_flow=1.0, condition_key="avg"),
        ),
        drop_warnings=(
            *design.drop_warnings,
            Warning(severity=Severity.WARN, source="test",
                    message="异工况跌水不应出现", condition_key="avg",
                    affected_unit_ids=("u1",)),
        ),
    )


def test_pumping_annotation_injected_or_skipped() -> None:
    """PD3：pumping 注入产泵/跌水注记；None 整体跳过；异工况条目
    过滤不混注（R 轮 G1-02）；跌水注记锚定受影响站右界非原点堆叠。"""
    plain = profile_sheet(
        _profile(), _styles(), ProfileOptions(1, 1, axis=_axis())
    )
    assert not [e for e in plain.entities
                if e.source_key.startswith("pumping.")]
    injected = profile_sheet(
        _profile(), _styles(),
        ProfileOptions(1, 1, axis=_axis(), pumping=_pumping_mixed()),
    )
    pumps = [e for e in injected.entities
             if e.source_key == "pumping.total_head"]
    drops = [e for e in injected.entities
             if e.source_key == "pumping.drop_warnings"]
    assert len(pumps) == 1 and "0.800" in pumps[0].text  # 仅 design 泵
    assert len(drops) == 1 and drops[0].text == "跌水警告注记"  # 仅 design 跌水
    # 跌水锚定受影响站 u2 右界（fallback 轴桩号 10+半宽 5=15 m×factor）
    assert drops[0].points[0][0] == pytest.approx(15.0 * 1000.0)


def test_axis_mismatch_rejected() -> None:
    """批6i 轴覆盖守卫：axis 缺站位桩号=装配缺陷显式拒（禁静默等距
    回退——v1 双行为面退役，R 轮 G1-03 fail-closed 承接）。"""
    from waterprint.drafting.profile_drawing import (
        InvalidProfileDrawingError,
    )

    axis = _axis()  # 两站轴
    solo_axis = _axis(_single_station())  # 单站轴（站集不匹配）
    with pytest.raises(InvalidProfileDrawingError, match="桩号轴缺站位"):
        profile_sheet(
            _profile(), _styles(), ProfileOptions(1, 1, axis=solo_axis)
        )
    assert axis.chainages.keys() == {"u1", "u2"}  # 对照组：匹配轴可出图


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
    确定性约束背书；锚值=批6i 桩号轴版实测冻结——v2 中心锚/K 标注/
    图脚注记三面位移）。"""
    options = ProfileOptions(500, 100, axis=_axis(), pumping=_pumping())
    first = profile_sheet(_profile(), _styles(), options)
    second = profile_sheet(_profile(), _styles(), options)
    digest = _canonical(first)
    assert digest == _canonical(second)  # 双跑恒等（确定性）
    assert len(digest) == 64  # sha256 十六进制形态
    assert digest == (  # 批6i 重锚二（2026-09-29 d1-r2 W1 实修后）：
        # INFO 记档行不再入图脚警告行（fallback 明细行已载——重复+语义
        # 错级消除）→一行减；一版锚 daa0e1ec…/v1 锚 296450a1… 漂移链在档
        "4da978d2c3a84d4f451b44e8b629a8f7591d8e46aba9ce12f0b62116f739ebad"
    )


def test_handbuilt_axis_guards_fail_closed() -> None:
    """d1-r2 W2 回炉钉：手构轴守卫——占宽缺键拒+边长非正拒（v1 fail-
    closed 在公开可构造类型面复立）。"""
    from waterprint.contracts.drawing_projection import ChainageAxis
    from waterprint.drafting.profile_drawing import (
        InvalidProfileDrawingError,
    )

    base = _axis()
    stripped = ChainageAxis(
        chainages=dict(base.chainages),
        edges=base.edges,
        platform_widths={"u1": 10.0},  # u2 占宽缺
        warnings=(),
    )
    with pytest.raises(InvalidProfileDrawingError, match="平台占宽"):
        profile_sheet(_profile(), _styles(), ProfileOptions(1, 1, axis=stripped))
    negative = ChainageAxis(
        chainages={"u1": 0.0, "u2": -30.0},
        edges=(type(base.edges[0])("u1", "u2", -30.0, "manual"),),
        platform_widths=dict(base.platform_widths),
        warnings=(),
    )
    with pytest.raises(InvalidProfileDrawingError, match="边长非正"):
        profile_sheet(_profile(), _styles(), ProfileOptions(1, 1, axis=negative))


def test_km_text_carry_at_kilometer_boundary() -> None:
    """k1-W1 回炉钉：余量 ∈ [999.9995, 1000) 进位归一——07.3f 最小宽度
    非上限，"K0+1000.000" 缺陷形态修为 "K1+000.000"。"""
    km_text = getattr(_mod, "_km_text")
    assert km_text(999.9994) == "K0+999.999"
    assert km_text(999.99996) == "K1+000.000"  # 进位域上界形态
    assert km_text(1000.0) == "K1+000.000"
    assert km_text(5.2) == "K0+005.200"  # 零填充（N1 口径）


def test_single_station_two_point_platform() -> None:
    """单站边界：平台两折点=站左右界（桩号 0 中心锚跨 ±5 m），不崩不退化。"""
    group = profile_sheet(
        _single_station(), _styles(),
        ProfileOptions(1, 1, axis=_axis(_single_station())),
    )
    lines = [e for e in group.entities if e.kind == "line"]
    assert lines, "单站仍须产出四线"
    for entity in lines:
        assert len(entity.points) == 2  # 单站=左界 −5/右界 +5 两折点
        assert entity.points[0][0] == pytest.approx(-5.0 * 1000.0)
        assert entity.points[1][0] == pytest.approx(5.0 * 1000.0)


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
        profile_sheet(empty, _styles(), ProfileOptions(1, 1, axis=_axis(empty)))
    with pytest.raises(InvalidProfileDrawingError):
        profile_sheet(_profile(), _styles(), ProfileOptions(0, 100, axis=_axis()))
    with pytest.raises(InvalidProfileDrawingError):
        profile_sheet(_profile(), _styles(), ProfileOptions(500, -1, axis=_axis()))
