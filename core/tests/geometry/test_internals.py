"""internals 镜像测试：内部构件布局（数量唯一真源/阵列展开/语义白名单）。

输入:  waterprint.geometry.internals 公开符号
输出:  构件布局契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.geometry.internals")
internal_instances = getattr(_mod, "internal_instances", None)
InstanceGroup = getattr(_mod, "InstanceGroup", None)

pytestmark = pytest.mark.skipif(
    None in (internal_instances, InstanceGroup),
    reason="实现未就绪：waterprint.geometry.internals（M2）",
)


def _snap(uid: str, dims: dict[str, float]):
    from waterprint.contracts.result_schema import UnitResultSnapshot

    return UnitResultSnapshot(
        unit_id=uid, outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


def test_instance_group_carries_array_params() -> None:
    """R3：阵列表达优先（origin/step/rows/cols 或显式坐标列表）。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(InstanceGroup)}
    assert {"semantic", "prototype", "count", "placements"} <= names


def test_count_matches_result_field_wiring() -> None:
    """R1 接线断言（M2 实质化）：曝气头/灯管 count == 结果字段值（不重新推算）。

    占位实质化（DRAFT 批总授权先例）：ziwai n_lamp/n_module 台数字段
    → InstanceGroup.count 逐组相等 + 阵列展开 rows×cols ≥ count 且
    缺额 < cols（末行不空一列）+ 数量来源键随 placements.source_key 回溯。
    """
    groups = internal_instances(
        _snap("municipal_ziwai",
              {"n_lamp": 40.0, "n_module": 8.0, "n_module_series": 4.0,
               "h_w": 1.0, "l_channel": 12.0}), _assumptions()
    )
    by_semantic = {group.semantic: group for group in groups}
    assert by_semantic["lamp"].count == 40  # == dims.n_lamp（零重推算）
    assert by_semantic["module"].count == 8
    assert by_semantic["module_series"].count == 4
    lamp = by_semantic["lamp"]
    rows, cols = lamp.placements["rows"], lamp.placements["cols"]
    assert rows * cols >= lamp.count  # 阵列展开数 ≥ count
    assert rows * cols - lamp.count < cols  # 末行缺额 < 一列
    assert lamp.placements["source_key"] == "n_lamp"  # 来源键回溯
    assert lamp.semantic in {"aerator", "paddle", "media", "gate", "lamp",
                             "module", "decant", "pump", "mech_cleaner",
                             "pipe", "opening"}  # R4 语义白名单


def test_units_without_counts_yield_explicit_empty() -> None:
    """无实例计数键单元（chuchenchi 纯校核）= 显式空组（数量真源在结果）。"""
    groups = internal_instances(
        _snap("municipal_chuchenchi",
              {"d": 9.0, "h_total": 4.0, "h2": 3.0}), _assumptions()
    )
    assert groups == ()
