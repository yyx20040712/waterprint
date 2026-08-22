"""takeoff 镜像测试：工程量提取（字段 ID 取数、单位一致、溯源完整）。

输入:  waterprint.cost.takeoff 公开符号
输出:  提取语义断言（中文匹配零容忍——§3 保证 4）
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.cost.takeoff")
takeoff_quantities = getattr(_mod, "takeoff_quantities", None)
TakeoffItem = getattr(_mod, "TakeoffItem", None)

pytestmark = pytest.mark.skipif(
    None in (takeoff_quantities, TakeoffItem),
    reason="实现未就绪：waterprint.cost.takeoff（M3）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：takeoff_quantities(plant_result, condition_key)。"""
    assert callable(takeoff_quantities)


def test_takeoff_item_carries_audit_fields() -> None:
    """R3：清单条目必含 price_key/quantity/unit/source_field_ids（可审计四件）。"""
    names = {f.name for f in dataclasses.fields(TakeoffItem)}
    assert {"price_key", "quantity", "unit", "source_field_ids"} <= names


def test_unit_mismatch_wiring_assertion() -> None:
    """R2 接线断言：量单位与单价单位不一致 → 领域异常（不得静默换算）。

    需要 PriceBook 与 PlantResult 可构造（M3）后接线；实现者不得删除。
    """
    raise AssertionError(
        "M3 接线断言：构造 m3 计价的量与 t 单价的条目，断言提取抛领域异常"
        "——不得删除"
    )
