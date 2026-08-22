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
    raise AssertionError(
        "M3 接线断言：用测试单价包构造最小概算，逐级求和自洽校验——不得删除"
    )
