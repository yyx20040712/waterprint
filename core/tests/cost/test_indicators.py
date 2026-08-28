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
    import tempfile
    from pathlib import Path

    from waterprint.cost.estimate import FeeRule, build_estimate
    from waterprint.cost.indicators import IndicatorBand, check_indicators
    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import TakeoffItem

    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "unit_prices"
        pkg.mkdir()
        (pkg / "manifest.yaml").write_text(
            "price_data_version: '1.0.0-test'\n", encoding="utf-8"
        )
        (pkg / "buildings.yaml").write_text("\n".join([
            "- key: C30-TEST",
            "  name: 测试混凝土",
            "  unit: m3",
            "  price: 100.0",
            "  source: 测试定额",
        ]), encoding="utf-8")
        book = load_prices(pkg)
    quantities = (
        TakeoffItem(
            price_key="C30-TEST",
            quantity=20.0,
            unit="m3",
            source_field_ids=("municipal_chuchenchi.v_concrete",),
            cost_class="civil",
            condition_key="design",
        ),
    )
    fee_rules = (
        FeeRule("rate.contingency", 0.10, "subtotal",
                "GB50500-2013", "reserve"),
        FeeRule("rate.tax", 0.09, "subtotal + reserve_subtotal",
                "GB50500-2013", "tax"),
    )
    sheet = build_estimate(quantities, book, fee_rules)
    band = IndicatorBand(
        indicator_key="indicator.unit_cost",
        formula="grand_total / scale",
        band=(3000.0, 5000.0),
        unit="元/(m3.d)",
        source="T/BCEBCA 1-2023",
    )
    report = check_indicators(sheet, (band,), design_scale=1.0)
    assert report.checked
    reading = report.readings[0]
    assert reading.status == "WARN"
    assert reading.reason
