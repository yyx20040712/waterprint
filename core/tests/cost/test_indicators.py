"""indicators 镜像测试：单位造价指标校核（带内/越带警告/缺指标显式）。

输入:  waterprint.cost.indicators 公开符号
输出:  校核语义断言（警告制——偏离不阻塞交付但必须可见）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.cost.indicators")
check_indicators = getattr(_mod, "check_indicators", None)
IndicatorBand = getattr(_mod, "IndicatorBand", None)

pytestmark = pytest.mark.skipif(
    None in (check_indicators, IndicatorBand),
    reason="实现未就绪：waterprint.cost.indicators（M3）",
)


def test_band_requires_source() -> None:
    """R1：指标带必须带出处（经验区间是数据不是代码）。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(IndicatorBand)}
    assert {"indicator_key", "band", "source"} <= names


def test_status_is_warn_not_error_semantics() -> None:
    """R2 接线断言：越带状态为 WARN（非阻塞），UI 与计算书可见。

    需要可构造 EstimateSheet（M3）后接线；实现者不得删除。
    """
    raise AssertionError(
        "M3 接线断言：构造越带概算，断言 status 为 WARN 且 reason 非空——不得删除"
    )
