"""unit_api 镜像测试：单元计算协议结构契约（装配边界与纯函数模板）。

输入:  waterprint.contracts.unit_api 公开符号
输出:  协议字段/不可变断言（供 32 个单元包镜像套用的母版）
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.unit_api")
UnitContext = getattr(_mod, "UnitContext", None)
UnitResult = getattr(_mod, "UnitResult", None)
Unit = getattr(_mod, "Unit", None)

pytestmark = pytest.mark.skipif(
    None in (UnitContext, UnitResult, Unit),
    reason="实现未就绪：waterprint.contracts.unit_api 公开符号缺失（M1）",
)


def _field_names(cls: type) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


def test_unit_context_carries_the_five_inputs() -> None:
    """UnitContext 五要素：inflows/inqualities/params/condition/assumptions。"""
    names = _field_names(UnitContext)
    assert {"inflows", "inqualities", "params", "condition", "assumptions"} <= names


def test_unit_result_carries_audit_channel() -> None:
    """UnitResult 审计通道：formula_ids 与 warnings 必须是字段（§3-5）。"""
    names = _field_names(UnitResult)
    assert {"outflows", "outqualities", "dims", "warnings", "formula_ids"} <= names


def test_unit_is_protocol_not_class() -> None:
    """Unit 是 Protocol（结构性接口——执行器据此与具体单元解耦）。"""
    from typing import Protocol

    bases = getattr(Unit, "__mro__", ())
    assert any(base is Protocol for base in bases), "Unit 必须是 typing.Protocol"


def test_unit_context_is_immutable() -> None:
    """R1 纯函数前提：上下文不可变（防执行期篡改输入快照）。"""
    assert UnitContext.__dataclass_params__.frozen, "UnitContext 必须 frozen"
