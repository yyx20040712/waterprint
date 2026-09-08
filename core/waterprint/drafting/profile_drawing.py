"""高程纵断图：沿流程拓扑的纵断面（水面/池底/管底/地面线 + 标高标注）。

输入:  ElevationProfile（elevation 子系统总线产出）
输出:  纵断图 DXF 实体组（流程纵断面，比例横纵分设）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_profile_drawing.py
#   +实现测试 tests/drafting/test_profile_drawing_impl.py）
#
# 【公开接口】
#   profile_sheet(profile: ElevationProfile, styles,
#                 options: ProfileOptions) -> EntityGroup
#   class ProfileOptions：h_scale / v_scale（横纵比例分设，如横 1:500
#      纵 1:100——工程惯例，取值来自 options 数据非硬编码；比例分母
#      整数必填）+station_lengths（站间距米值映射，缺省等距）+pumping
#      （PumpingPlan 标注数据，None 跳过——经 app 装配传入 R3）
#
# 【行为规格】
#   R1 四线齐备：地面线/水面线/池底线/管底线（§12.5 高程纵断图定义：
#      "沿流程拓扑生成纵断面（水面/池底/管底/地面线+标高标注）"）；
#      数据全部来自 ElevationProfile，本文件零标高推算（纯投影）。
#      〔管底线语义注记（PROFILE 批 PD1）：重力流管道贴池底敷设、忽略
#      管壁厚——管底=池底近似投影，source_key 与池底同指 floor_elev，
#      语义由 LAYER_PIPE 图层区分；独立管底高程需求挂账 L0 扩展流程〕
#   R2 站位横轴 = 流程拓扑序（topo 分层的展开序），站名标注经 i18n
#      显示键取中文（显示层职责——core 面站名=unit_id 原文，catalog
#      "图名=unit_id 原文"同款先例）；站间距按构筑物长度字段
#      （station_lengths 米值映射，缺省等距）。
#   R3 标高标注：每站标注水面/池底/地面三值（剖面图 R2 同源规则）；
#      提升泵站与跌水点从 PumpingPlan 标注（经 options.pumping 装配
#      传入——纯读标注，零水力计算）。
#   R4 横纵比例分设的坐标换算集中在本文件入口一处（可审计），
#      禁散落各图元。
#   R5 纯投影 + 零 ezdxf（同 plan_view R2）；工况标注（condition_key）
#      ——不同工况水位不同，图纸必须可区分。
#
# 【数值纪律】m→mm 因子经 quantity.parse 契约求值（dxf_writer.
#   _mm_per_meter 同款——1 mm=m 换算不抄系数）；缺省等距站距占位
#   10 m（section_view _DEFAULT_SPAN 同源工程占位）；标高文本 .3f
#   格式串非数值字面量（AST 门禁面外）。
#
# 【依赖足迹】waterprint.elevation.pumps（PumpingPlan 类型——L3 同层
#   消费边，import-linter ignore_imports 显式豁免登记，ifc_export→
#   geometry 2026-09-03 先例；structure-graph.md §1b 注记承载）。
#
# 【测试要求】四线实体存在且值 == Profile、比例换算正确、
#   工况标注、快照回归（内容哈希自锚——test_profile_drawing_impl）。
#
# 【参照】重写计划 §12.5 高程纵断图行；ADR-006；PROFILE 批简报
#   （task-PROFILE-plan.md PD1~PD9）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from waterprint.contracts.drawing_projection import ElevationProfile
from waterprint.contracts.quantity import DimKey, parse
from waterprint.drafting.styles import (
    LAYER_ELEV,
    LAYER_PIPE,
    LAYER_POOL,
    Entity,
    EntityGroup,
    StyleTable,
)

if TYPE_CHECKING:
    from waterprint.elevation.pumps import PumpingPlan

__all__ = ["InvalidProfileDrawingError", "ProfileOptions", "profile_sheet"]


class InvalidProfileDrawingError(Exception):
    """纵断图生成非法（空站位/比例非正）——GR-11 族。"""


# 缺省等距站距占位（R2 站间距兜底；section_view._DEFAULT_SPAN 同源
# 工程占位——10 ∈ 魔法数字白名单，具名化防同型字面量搭车）。
_DEFAULT_SPAN: Final[float] = 10.0


@dataclass(frozen=True)
@final
class ProfileOptions:
    """纵断图选项（不可变）：横纵比例分母 + 站距映射 + 提升计划标注。

    h_scale/v_scale=比例分母整数（如横 1:500 纵 1:100 → 500/100——
    必填，工程出图比例显式传入不设默认）；station_lengths=unit_id→
    站距米值（缺省等距 _DEFAULT_SPAN）；pumping=None 时泵/跌水注记
    整体跳过（PumpingPlan 双空合法语义沿承）。
    """

    h_scale: int
    v_scale: int
    station_lengths: Mapping[str, float] | None = None
    pumping: PumpingPlan | None = None


def _mm_per_meter() -> float:
    """m→mm 换算因子（R4 唯一换算点用；quantity.parse 契约求值——
    dxf_writer._mm_per_meter 同款：1 mm=m 经 pint 换算，因子=1/0.001）。"""
    return 1.0 / parse(1.0, "mm", DimKey.LENGTH)


def _to_sheet(x_m: float, elev_m: float, factor: float,
              options: ProfileOptions) -> tuple[float, float]:
    """模型坐标（m）→ 图面坐标（mm）：x=桩距×因子÷横比例分母，
    y=标高×因子÷纵比例分母（R4 换算集中唯一入口——y=实际高程直投影
    零基准平移，PD5）。"""
    return (
        x_m * factor / options.h_scale,
        elev_m * factor / options.v_scale,
    )


def _station_spans(profile: ElevationProfile,
                   options: ProfileOptions) -> tuple[float, ...]:
    """各站横轴占宽（米）：station_lengths 实值 > 缺省等距占位（R2）。"""
    if options.station_lengths is None:
        return (_DEFAULT_SPAN,) * len(profile.stations)
    return tuple(
        float(options.station_lengths.get(station.unit_id, _DEFAULT_SPAN))
        for station in profile.stations
    )


# 四线声明表（R1）：(字段, 图层)——管底与池底同指 floor_elev、图层分
# 取 LAYER_POOL/LAYER_PIPE（语义区分——R1 注记；表驱动=四线齐备可对账）。
_FOUR_LINES: Final[tuple[tuple[str, str], ...]] = (
    ("ground_elev", LAYER_ELEV),
    ("water_level", LAYER_ELEV),
    ("floor_elev", LAYER_POOL),
    ("floor_elev", LAYER_PIPE),
)


def _polyline_of(line: tuple[str, str], spans: tuple[float, ...],
                 profile: ElevationProfile, factor: float,
                 options: ProfileOptions) -> Entity:
    """四线之一（line=(字段, 图层)）：全站折点序列——每站站内平台两折点
    （x=累计桩号左/右界，y=该站字段值）；坐标全经 _to_sheet 唯一换算
    入口；source_key=被引用字段。"""
    field, layer = line
    points: list[tuple[float, float]] = []
    x_m = 0.0
    for station, span in zip(profile.stations, spans, strict=True):
        points.append(
            _to_sheet(x_m, getattr(station, field), factor, options)
        )
        x_m += span
        points.append(
            _to_sheet(x_m, getattr(station, field), factor, options)
        )
    return Entity("line", layer, tuple(points),
                  text=field, source_key=f"profile.{field}")


def profile_sheet(
    profile: ElevationProfile,
    styles: StyleTable,
    options: ProfileOptions,
) -> EntityGroup:
    """纵断图正门（纯投影）：四线+每站标高/站名标注+泵/跌水注记+工况。

    实体生成顺序固定（确定性）：四线（地面/水面/池底/管底）→逐站
    标高三值与站名→泵站/跌水注记（options.pumping）→工况标注。
    """
    if not profile.stations:
        raise InvalidProfileDrawingError(
            "纵断站位为空（ElevationProfile.stations 至少一站——"
            "空站纵断无图面语义，禁静默空产物）"
        )
    if options.h_scale <= 0 or options.v_scale <= 0:
        raise InvalidProfileDrawingError(
            f"比例分母非正：h={options.h_scale} v={options.v_scale}"
            "（1:N 比例分母须正整数——R4 换算前提）"
        )
    factor = _mm_per_meter()
    spans = _station_spans(profile, options)
    entities: list[Entity] = [
        _polyline_of(line, spans, profile, factor, options)
        for line in _FOUR_LINES
    ]
    right_of: dict[str, float] = {}  # unit_id → 站右界桩号（泵标注定位）
    x_m = 0.0
    for station, span in zip(profile.stations, spans, strict=True):
        x_right = x_m + span
        right_of[station.unit_id] = x_right
        for field in ("water_level", "floor_elev", "ground_elev"):
            value = getattr(station, field)
            entities.append(
                Entity("text", LAYER_ELEV,
                       (_to_sheet(x_right, value, factor, options),),
                       text=f"{value:.3f}", source_key=f"profile.{field}")
            )
        entities.append(
            Entity("text", LAYER_ELEV,
                   (_to_sheet(x_m, station.ground_elev, factor, options),),
                   text=station.unit_id, source_key="profile.unit_id")
        )
        x_m = x_right
    if options.pumping is not None:
        for pump in options.pumping.stations:
            pump_station = profile.station_of(pump.unit_id)
            if pump_station is None:
                continue  # 泵站位不在本纵断（工况差异）——跳过非异常
            entities.append(
                Entity("elev_symbol", LAYER_ELEV,
                       (_to_sheet(right_of[pump.unit_id],
                                  pump_station.water_level, factor,
                                  options),),
                       text=f"提升 total_head={pump.total_head:.3f}"
                            f" design_flow={pump.design_flow:.3f}",
                       source_key="pumping.total_head")
            )
        for drop in options.pumping.drop_warnings:
            entities.append(
                Entity("text", LAYER_ELEV, ((0.0, 0.0),),
                       text=drop.message,
                       source_key="pumping.drop_warnings")
            )
    entities.append(
        Entity("text", LAYER_ELEV, ((0.0, 0.0),),
               text=f"condition={profile.condition_key}",
               source_key="condition_key")
    )
    return EntityGroup(entities=tuple(entities))
