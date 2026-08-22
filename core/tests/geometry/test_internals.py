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


def test_instance_group_carries_array_params() -> None:
    """R3：阵列表达优先（origin/step/rows/cols 或显式坐标列表）。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(InstanceGroup)}
    assert {"semantic", "prototype", "count", "placements"} <= names


def test_count_matches_result_field_wiring() -> None:
    """R1 接线断言：曝气头 count == 结果字段值（不重新推算——双源根除）。"""
    raise AssertionError(
        "M2 接线断言：构造台数字段，断言 InstanceGroup.count 相等——不得删除"
    )
