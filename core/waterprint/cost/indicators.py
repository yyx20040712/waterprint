"""单位造价指标合理性校核：概算结果 ↔ 行业经验指标带的对照（警告而非否决）。

输入:  EstimateSheet + 指标数据（单位水量投资 元/(m3·d−1) 等经验带）
输出:  指标对照结果（在带内/偏离 + 警告）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_indicators.py）
#
# 【公开接口】
#   check_indicators(estimate: EstimateSheet,
#                    indicators: IndicatorBand) -> IndicatorReport
#   class IndicatorBand(不可变)：indicator_key、formula DSL（如
#      grand_total / 设计规模）、band（下限, 上限）、source（经验出处）
#   class IndicatorReport：每项 {value, band, status: OK|WARN, reason}
#
# 【行为规格】
#   R1 指标带是数据：经验区间全部来自 data/coefficients 指标条目
#      （带出处），代码零经验数字。
#   R2 语义定位：校核结果是 Warning 不是 Error——偏离不阻塞交付，
#      但必须在 UI 诊断面板与计算书中可见（§19.3 反馈通道）。
#   R3 指标值计算经公式注册表（可溯源），规模取设计规模字段 ID
#      （q_avg_daily 换算 m3/d 仅在显示层发生）。
#   R4 无可算指标（数据包缺该工程类型条目）→ 显式"未校核"状态，
#      禁止静默通过。
#
# 【COST2 实装注记】（概算段二，2026-08-28）
#   - 带数据面：auxiliary.yaml indicator.* 条目（经 PriceBook 消费，
#     load_indicator_bands 按 min/max 成对合成带；单位造价带出处
#     T/BCEBCA 1-2023，3000~5000 元/(m3·d)）——代码零经验数字。
#   - 公式注册表（R3 可溯源）：_FORMULAS 按指标单位登记 DSL 表达式
#     （contracts.expr 受限求值；变量集 {grand_total, scale}）。
#     scale=设计规模 m3/d，经 check_indicators 关键字注入——
#     q_avg_daily（m3/s）×86400 的换算属显示层/装配层口径，本层
#     只收 m3/d 数（冻结 §二.6 通道裁决；自动取数挂段三）。
#   - R2 落点：越带 → status="WARN" + reason 非空（诊断面板与计算书
#     可见）；带内 → status="OK"。校核永不抛"偏离"异常。
#   - R4 落点：bands 为空 → IndicatorReport(checked=False)（显式
#     "未校核"，消费方禁当通过）。
#
# 【测试要求】带内 OK / 越带 WARN、缺指标显式未校核、指标值公式溯源。
#
# 【参照】重写计划 §13.3 职责表
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import final

from waterprint.contracts.expr import eval_checked, parse_checked
from waterprint.cost.estimate import EstimateSheet
from waterprint.cost.prices import PriceBook


class InvalidIndicatorError(Exception):
    """指标带/校核非法（带结构/公式 DSL/规模域）——领域异常（非偏离）。"""


STATUS_OK = "OK"
STATUS_WARN = "WARN"
_SUFFIX_MIN = ".min"
_SUFFIX_MAX = ".max"
_FORMULA_VARIABLES = frozenset({"grand_total", "scale"})

# 公式注册表（R3：指标值计算可溯源）——键=指标单位，值=受限 DSL 表达式。
_FORMULAS: dict[str, str] = {
    "元/(m3.d)": "grand_total / scale",
}


def _finite(value: object, what: str) -> float:
    """数值守卫：int/float（bool 除外）且有限。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidIndicatorError(
            f"{what} 必须为有限数值：得到 {value!r}（类型 {type(value).__name__}）"
        )
    number = float(value)
    if not math.isfinite(number):
        raise InvalidIndicatorError(f"{what} 非有限（NaN/±Inf）：{value!r}")
    return number


@dataclass(frozen=True)
@final
class IndicatorBand:
    """单条经验带：指标键+公式 DSL+（下限,上限）+单位+出处（R1 全数据面）。"""

    indicator_key: str
    formula: str
    band: tuple[float, float]
    unit: str
    source: str

    def __post_init__(self) -> None:
        """守卫：下限<上限且均有限（带结构即数据门槛）。"""
        lower, upper = self.band
        lower = _finite(lower, f"指标带 {self.indicator_key!r} 下限")
        upper = _finite(upper, f"指标带 {self.indicator_key!r} 上限")
        if not lower < upper:
            raise InvalidIndicatorError(
                f"指标带 {self.indicator_key!r} 区间非法：({lower!r}, {upper!r})"
                "（下限须小于上限）"
            )


@dataclass(frozen=True)
@final
class IndicatorReading:
    """单项对照结果：值/带/状态/原因（R2 reason 越带必非空）。"""

    indicator_key: str
    value: float
    band: tuple[float, float]
    status: str
    reason: str


@dataclass(frozen=True)
@final
class IndicatorReport:
    """校核报告：逐项对照 + 是否已校核（R4 空带=显式未校核）。"""

    readings: tuple[IndicatorReading, ...]
    checked: bool


def load_indicator_bands(price_book: PriceBook) -> tuple[IndicatorBand, ...]:
    """带装载正门：单价包 indicator.*.min/max 成对合成（R1 数据面）。"""
    bands: list[IndicatorBand] = []
    seen: set[str] = set()
    for key in price_book.keys("indicator."):
        if not key.endswith(_SUFFIX_MIN):
            continue
        indicator_key = key[: -len(_SUFFIX_MIN)]
        if indicator_key in seen:
            continue
        seen.add(indicator_key)
        lower_item = price_book.get(key)
        upper_item = price_book.get(f"{indicator_key}{_SUFFIX_MAX}")
        if lower_item.unit != upper_item.unit:
            raise InvalidIndicatorError(
                f"指标带 {indicator_key!r} min/max 单位不一致："
                f"{lower_item.unit!r} ≠ {upper_item.unit!r}"
            )
        formula = _FORMULAS.get(lower_item.unit)
        if formula is None:
            raise InvalidIndicatorError(
                f"指标单位 {lower_item.unit!r} 无登记公式（公式注册表 "
                f"仅覆盖 {sorted(_FORMULAS)}——R3 可溯源拒绝未登记面）"
            )
        bands.append(
            IndicatorBand(
                indicator_key=indicator_key,
                formula=formula,
                band=(lower_item.price, upper_item.price),
                unit=lower_item.unit,
                source=lower_item.source,
            )
        )
    return tuple(bands)


def _formula_value(band: IndicatorBand, grand_total: float, scale: float) -> float:
    """公式 DSL 求值：contracts.expr 受限表达式（变量集 {grand_total, scale}）。"""
    parsed = parse_checked(band.formula, _FORMULA_VARIABLES)
    value = eval_checked(parsed, {"grand_total": grand_total, "scale": scale})
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidIndicatorError(
            f"指标 {band.indicator_key!r} 公式求值结果须为数值："
            f"{band.formula!r} → {value!r}"
        )
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise InvalidIndicatorError(
            f"指标 {band.indicator_key!r} 公式求值结果越数值域：{number!r}"
        )
    return number


def check_indicators(
    estimate: EstimateSheet,
    bands: tuple[IndicatorBand, ...],
    *,
    design_scale: float,
) -> IndicatorReport:
    """校核正门：逐带求值对照（越带 WARN 非阻塞，R2；空带显式未校核，R4）。

    design_scale=设计规模（m3/d 口径）——装配层注入（q_avg_daily 换算
    归显示层，R3）。
    """
    scale = _finite(design_scale, "design_scale（设计规模 m3/d）")
    if scale <= 0:
        raise InvalidIndicatorError(
            f"design_scale 必须 > 0：得到 {design_scale!r}"
            "（规模为零/负 = 指标值无定义，显式拒绝）"
        )
    if not bands:
        return IndicatorReport(readings=(), checked=False)
    readings: list[IndicatorReading] = []
    for band in bands:
        value = _formula_value(band, estimate.grand_total, scale)
        lower, upper = band.band
        if value < lower:
            status = STATUS_WARN
            reason = (
                f"指标 {band.indicator_key} 值 {value} 低于经验带下限 "
                f"{lower}（带 [{lower}, {upper}] {band.unit}，出处 "
                f"{band.source}；概算 condition={estimate.condition_key}）"
            )
        elif value > upper:
            status = STATUS_WARN
            reason = (
                f"指标 {band.indicator_key} 值 {value} 高于经验带上限 "
                f"{upper}（带 [{lower}, {upper}] {band.unit}，出处 "
                f"{band.source}；概算 condition={estimate.condition_key}）"
            )
        else:
            status = STATUS_OK
            reason = (
                f"指标 {band.indicator_key} 值 {value} 在经验带 "
                f"[{lower}, {upper}] {band.unit} 内（出处 {band.source}）"
            )
        readings.append(
            IndicatorReading(
                indicator_key=band.indicator_key,
                value=value,
                band=band.band,
                status=status,
                reason=reason,
            )
        )
    return IndicatorReport(readings=tuple(readings), checked=True)
