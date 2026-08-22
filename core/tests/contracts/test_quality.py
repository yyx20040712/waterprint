"""quality 镜像测试：水质契约 + 出水标准（标准是数据不是分支）。

输入:  waterprint.contracts.quality 公开符号
输出:  裕度语义/数据驱动/校验拒绝断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.quality")
WaterQuality = getattr(_mod, "WaterQuality", None)
EffluentStandard = getattr(_mod, "EffluentStandard", None)
margin = getattr(_mod, "margin", None)
INDICATORS = getattr(_mod, "INDICATORS", None)
InvalidQualityError = getattr(_mod, "InvalidQualityError", None)

pytestmark = pytest.mark.skipif(
    None in (WaterQuality, EffluentStandard, margin, INDICATORS, InvalidQualityError),
    reason="实现未就绪：waterprint.contracts.quality 公开符号缺失（M1）",
)


def _standard(bod_limit: float) -> object:
    return EffluentStandard(
        standard_id="test-std", name_i18n="test", limits={"BOD5": bod_limit}
    )


def test_indicator_set_is_frozen_six() -> None:
    """冻结六指标字段 ID（BOD5/CODCR/SS/NH3N/TN/TP）。"""
    assert set(INDICATORS) == {"BOD5", "CODCR", "SS", "NH3N", "TN", "TP"}


def test_margin_sign_semantics() -> None:
    """裕度 = (限值 − 计算值)/限值：>=0 达标，<0 超限。"""
    std = _standard(10.0)
    assert margin(5.0, std, "BOD5") == pytest.approx(0.5)
    assert margin(10.0, std, "BOD5") == pytest.approx(0.0)
    assert margin(12.0, std, "BOD5") < 0


def test_standards_are_data_not_branches() -> None:
    """R1：两个不同限值的标准走同一代码路径产出不同裕度（无标准名分支）。"""
    strict = _standard(10.0)
    loose = _standard(20.0)
    assert margin(8.0, strict, "BOD5") < 0
    assert margin(8.0, loose, "BOD5") > 0


def test_negative_concentration_rejected() -> None:
    """R2：负浓度构造拒绝。"""
    with pytest.raises(InvalidQualityError):
        WaterQuality({"BOD5": -1.0})


def _get(quality: object, indicator: str) -> object:
    """字段 ID 取值容错：属性或映射访问皆可（契约只冻结字段 ID）。"""
    if hasattr(quality, indicator):
        return getattr(quality, indicator)
    return quality[indicator]  # type: ignore[index]


def test_missing_indicator_is_none_not_zero() -> None:
    """缺项语义：未提供指标为 None（传播时不参与混合），不得伪装成 0。"""
    quality = WaterQuality({"BOD5": 20.0})
    assert _get(quality, "BOD5") == 20.0
    assert _get(quality, "TP") is None
