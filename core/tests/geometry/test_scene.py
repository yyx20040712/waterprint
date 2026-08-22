"""scene 镜像测试：场景图装配（确定性/实例数/语义标签/纯投影接线）。

输入:  waterprint.geometry.scene 公开符号
输出:  场景图契约断言（§10.5 / §16 A7）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.geometry.scene")
build_scene = getattr(_mod, "build_scene", None)
SceneGraph = getattr(_mod, "SceneGraph", None)
Node = getattr(_mod, "Node", None)

pytestmark = pytest.mark.skipif(
    None in (build_scene, SceneGraph, Node),
    reason="实现未就绪：waterprint.geometry.scene（M2）",
)


def test_node_carries_transform_and_semantic() -> None:
    """R1：节点 = 图元 + 局部变换 + 语义标签 + 实例数。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(Node)}
    assert {"primitive", "semantic", "instance_count"} <= names


def test_scene_carries_version_and_condition() -> None:
    """R4：场景图声明版本与工况（坐标约定/结果归属）。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(SceneGraph)}
    assert {"scene_version", "condition_key"} <= names


def test_purity_wiring() -> None:
    """R1 接线断言：同结果双跑场景图 JSON 相同（纯投影——M2 首批单元后接线）。"""
    raise AssertionError(
        "M2 接线断言：同 PlantResult 双跑 build_scene 输出一致——不得删除"
    )
