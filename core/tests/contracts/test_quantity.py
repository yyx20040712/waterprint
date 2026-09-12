"""quantity 镜像测试：量纲/规范单位/边界换算（ADR-002 三层策略的边界层）。

输入:  waterprint.contracts.quantity 公开符号
输出:  规范单位表/换算/拒绝路径断言（实现合入后必须全绿）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.quantity")
Quantity = getattr(_mod, "Quantity", None)
CANONICAL_UNITS = getattr(_mod, "CANONICAL_UNITS", None)
DimKey = getattr(_mod, "DimKey", None)
InvalidUnitError = getattr(_mod, "InvalidUnitError", None)
InvalidQuantityError = getattr(_mod, "InvalidQuantityError", None)
parse = getattr(_mod, "parse", None)
attach = getattr(_mod, "attach", None)

pytestmark = pytest.mark.skipif(
    None
    in (
        Quantity,
        CANONICAL_UNITS,
        DimKey,
        InvalidUnitError,
        InvalidQuantityError,
        parse,
        attach,
    ),
    reason="实现未就绪：waterprint.contracts.quantity 公开符号缺失（M1）",
)


def test_canonical_units_core_three() -> None:
    """规范单位表必含计划明示三项：流量 m3/s、浓度 mg/L、长度 m（§12.1）。"""
    assert CANONICAL_UNITS[DimKey.FLOW] == "m3/s"
    assert CANONICAL_UNITS[DimKey.CONCENTRATION] == "mg/L"
    assert CANONICAL_UNITS[DimKey.LENGTH] == "m"


def test_parse_converts_daily_flow_to_canonical() -> None:
    """golden 口径：34760 m3/d（市政案例规模）换算为 m3/s。"""
    assert parse(34760.0, "m3/d", DimKey.FLOW) == pytest.approx(34760.0 / 86400.0)


def test_parse_rejects_dimension_mismatch() -> None:
    """量纲不匹配直接拒绝（期望流量却给浓度单位）。"""
    with pytest.raises(InvalidUnitError):
        parse(1.0, "mg/L", DimKey.FLOW)


def test_parse_rejects_unknown_unit() -> None:
    """未知单位字符串拒绝，无默认单位回退。"""
    with pytest.raises(InvalidUnitError):
        parse(1.0, "立方千米每纳秒", DimKey.FLOW)


def test_attach_yields_canonical_quantity() -> None:
    """出口包装：规范单位裸值 → Quantity（数值不变，单位=规范单位）。"""
    value = parse(5.0, "m3/d", DimKey.FLOW)
    quantity = attach(value, DimKey.FLOW)
    assert quantity.magnitude == pytest.approx(value)
    assert quantity.unit == CANONICAL_UNITS[DimKey.FLOW]


# ── U-C2 批（2026-08-23 用户特别批准；UF-20 白名单/DIMENSIONLESS/非有限值）──


def test_parse_whitelist_positive_representative():
    """UF-20 正例：白名单内写法逐族代表可解析且换算正确（mg/L==g/m3 由性质测试覆盖）。"""
    assert parse(5.0, "mm", DimKey.LENGTH) == pytest.approx(5.0 / 1000.0)
    assert parse(1.0, "", DimKey.DIMENSIONLESS) == pytest.approx(1.0)


def test_parse_whitelist_negative_variants():
    """UF-20 负例：白名单外写法一律拒（含大小写/上标/未列工程单位）。"""
    for bad in ("M3/d", "m³/d", "L/s", "km", "dimensionless", "m**3/d"):
        with pytest.raises(InvalidUnitError, match="白名单"):
            parse(1.0, bad, DimKey.FLOW if bad != "km" else DimKey.LENGTH)


def test_parse_rejects_non_finite():
    """GR-02 输入即拒绝：NaN/±Inf → InvalidQuantityError（消息含值与原因）。"""
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(InvalidQuantityError, match="非有限"):
            parse(bad, "m3/d", DimKey.FLOW)


def test_attach_rejects_non_finite():
    """GR-02 出口同守：attach 对非有限值拒绝。"""
    with pytest.raises(InvalidQuantityError, match="非有限"):
        attach(float("nan"), DimKey.FLOW)


# ── DimKey 扩成员批（2026-09-12 用户裁定「HRT/泥龄应显示单位」；UF-20
#    白名单增补=规格变更，本组=补锁定测试）──


def test_scale_members_canonical_units():
    """扩档三成员规范刻度：TIME_H→h、TIME_D→d、FLOW_H→m3/h。"""
    assert CANONICAL_UNITS[DimKey.TIME_H] == "h"
    assert CANONICAL_UNITS[DimKey.TIME_D] == "d"
    assert CANONICAL_UNITS[DimKey.FLOW_H] == "m3/h"


def test_scale_members_parse_identity():
    """扩档成员：白名单内写法恒等换算（h/d/m3/h 均为自身规范串）。"""
    assert parse(4.0, "h", DimKey.TIME_H) == pytest.approx(4.0)
    assert parse(20.0, "d", DimKey.TIME_D) == pytest.approx(20.0)
    assert parse(50.0, "m3/h", DimKey.FLOW_H) == pytest.approx(50.0)


def test_scale_members_whitelist_negative():
    """扩档成员白名单负例：跨刻度写法与未列工程单位一律拒（UF-20）。"""
    # TIME_H 只收 h：s/d/min 均拒（跨档换算不做——刻度档=声明口径非自由换算面）
    for bad in ("s", "d", "min"):
        with pytest.raises(InvalidUnitError, match="白名单"):
            parse(1.0, bad, DimKey.TIME_H)
    with pytest.raises(InvalidUnitError, match="白名单"):
        parse(1.0, "h", DimKey.TIME_D)
    with pytest.raises(InvalidUnitError, match="白名单"):
        parse(1.0, "m3/d", DimKey.FLOW_H)
    with pytest.raises(InvalidUnitError, match="白名单"):
        parse(1.0, "m3/s", DimKey.FLOW_H)


# ── 参数面单位批同制补齐（2026-09-12 用户裁定「同制补齐」；UF-20 白名单
#    增补=规格变更，本组=补锁定测试）──


def test_time_min_and_temperature_members():
    """同制补齐两成员：TIME_MIN→min、TEMPERATURE→degC（恒等换算+跨档拒）。"""
    assert CANONICAL_UNITS[DimKey.TIME_MIN] == "min"
    assert CANONICAL_UNITS[DimKey.TEMPERATURE] == "degC"
    assert parse(1.5, "min", DimKey.TIME_MIN) == pytest.approx(1.5)
    assert parse(35.0, "degC", DimKey.TEMPERATURE) == pytest.approx(35.0)
    for bad in ("s", "h", "d"):
        with pytest.raises(InvalidUnitError, match="白名单"):
            parse(1.0, bad, DimKey.TIME_MIN)
    for bad in ("K", "degF", "℃"):
        with pytest.raises(InvalidUnitError, match="白名单"):
            parse(1.0, bad, DimKey.TEMPERATURE)
