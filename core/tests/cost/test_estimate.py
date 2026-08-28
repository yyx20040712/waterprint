"""estimate 镜像测试：概算汇总（分级自洽、费率出处、双跑确定性）。

输入:  waterprint.cost.estimate 公开符号
输出:  汇总语义断言
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.cost.estimate")
build_estimate = getattr(_mod, "build_estimate", None)
EstimateSheet = getattr(_mod, "EstimateSheet", None)
FeeRule = getattr(_mod, "FeeRule", None)

pytestmark = pytest.mark.skipif(
    None in (build_estimate, EstimateSheet, FeeRule),
    reason="实现未就绪：waterprint.cost.estimate（M3）",
)


def test_fee_rule_requires_source() -> None:
    """R1：费率规则必须带出处字段（数据驱动——代码零费率）。"""
    names = {f.name for f in dataclasses.fields(FeeRule)}
    assert {"fee_key", "rate", "base", "source"} <= names


def test_sheet_carries_repro_triple() -> None:
    """R3：概算结果挂三元组（数据包更新后旧概算必须过期）。"""
    names = {f.name for f in dataclasses.fields(EstimateSheet)}
    assert {"detail_rows", "grand_total", "repro"} <= names


def test_summation_self_consistency_wiring() -> None:
    """R1 接线断言：明细求和=小计、小计+费用=总价（M3 数据包就绪后接线）。"""
    import tempfile
    from pathlib import Path

    from waterprint.cost.estimate import FeeRule, build_estimate
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
            "- key: EQ-TEST",
            "  name: 测试设备",
            "  unit: 万元/台",
            "  price: 10.0",
            "  source: 测试询价",
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
        TakeoffItem(
            price_key="EQ-TEST",
            quantity=3.0,
            unit="万元/台",
            source_field_ids=("municipal_cass.n_decant",),
            cost_class="equipment",
            condition_key="design",
        ),
    )
    fee_rules = (
        FeeRule("rate.installation", 0.15, "equipment_subtotal",
                "GB50500-2013", "measure"),
        FeeRule("rate.management", 0.05, "construction_subtotal",
                "GB50500-2013", "indirect"),
        FeeRule("rate.contingency", 0.10, "subtotal",
                "GB50500-2013", "reserve"),
        FeeRule("rate.tax", 0.09, "subtotal + reserve_subtotal",
                "GB50500-2013", "tax"),
    )
    sheet = build_estimate(quantities, book, fee_rules)
    assert sum(row.amount for row in sheet.detail_rows) == pytest.approx(
        sheet.detail_subtotal
    )
    assert sheet.detail_subtotal + sum(
        line.amount for line in sheet.measure
    ) == pytest.approx(sheet.construction_subtotal)
    assert sheet.construction_subtotal + sum(
        line.amount for line in sheet.indirect
    ) == pytest.approx(sheet.subtotal)
    assert sheet.subtotal + sheet.reserve_subtotal + sum(
        line.amount for line in sheet.tax
    ) == pytest.approx(sheet.grand_total)
