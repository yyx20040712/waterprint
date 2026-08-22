"""result_schema 镜像测试：全架构总线的结构契约（字段 ID 制 + 三元组绑定）。

输入:  waterprint.contracts.result_schema 公开符号
输出:  结构/索引/三元组断言（elevation/cost/drafting/前端的共同消费契约）
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.result_schema")
PlantResult = getattr(_mod, "PlantResult", None)
TraceNode = getattr(_mod, "TraceNode", None)
UnitResultSnapshot = getattr(_mod, "UnitResultSnapshot", None)
serialize = getattr(_mod, "serialize", None)
deserialize = getattr(_mod, "deserialize", None)

pytestmark = pytest.mark.skipif(
    None in (PlantResult, TraceNode, UnitResultSnapshot, serialize, deserialize),
    reason="实现未就绪：waterprint.contracts.result_schema（M1）",
)


def _names(cls: type) -> set[str]:
    if dataclasses.is_dataclass(cls):
        return {f.name for f in dataclasses.fields(cls)}
    return set(getattr(cls, "model_fields", {}))


def test_trace_node_carries_audit_fivesome() -> None:
    """R1：迹节点五要素 formula_id/输入/输出/条文/来源定位。"""
    names = _names(TraceNode)
    assert {
        "formula_id", "inputs", "output", "norm_ref", "unit_id", "condition_key",
    } <= names


def test_plant_result_indexes_by_condition() -> None:
    """R1：结果按 condition_key 索引（工况一等公民的 schema 落点）。"""
    names = _names(PlantResult)
    assert {"conditions", "summary", "trace", "repro"} <= names


def test_repro_triple_is_mandatory_field() -> None:
    """R4：repro 三元组是必填结构（结果永不脱离三元组存在）。"""
    names = _names(PlantResult)
    assert "repro" in names


def test_unit_snapshot_exposes_formula_ids() -> None:
    """快照保留审计通道（formula_ids/_warnings 不丢）。"""
    names = _names(UnitResultSnapshot)
    assert {"formula_ids", "warnings"} <= names
