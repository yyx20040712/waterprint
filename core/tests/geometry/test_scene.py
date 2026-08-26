"""scene 镜像测试：场景图装配（确定性/实例数/语义标签/纯投影接线）。

输入:  waterprint.geometry.scene 公开符号
输出:  场景图契约断言（§10.5 / §16 A7）
"""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict

import pytest

_mod = importlib.import_module("waterprint.geometry.scene")
build_scene = getattr(_mod, "build_scene", None)
SceneGraph = getattr(_mod, "SceneGraph", None)
Node = getattr(_mod, "Node", None)

pytestmark = pytest.mark.skipif(
    None in (build_scene, SceneGraph, Node),
    reason="实现未就绪：waterprint.geometry.scene（M2）",
)


def _plant():
    from waterprint.contracts.result_schema import (
        PlantResult,
        ReproTriple,
        UnitResultSnapshot,
    )

    def snap(uid: str, dims: dict[str, float]) -> UnitResultSnapshot:
        return UnitResultSnapshot(
            unit_id=uid, outflows={}, outqualities={}, dims=dims,
            warnings=(), formula_ids=(),
        )

    return PlantResult(
        conditions={"design": {
            "inlet": snap("inlet", {}),
            "municipal_cugeshan": snap(
                "municipal_cugeshan",
                {"L": 1.8, "B": 0.7, "H": 1.0, "n_gap": 20.0,
                 "mech_clean": 1.0},
            ),
            "municipal_chenshachi": snap(
                "municipal_chenshachi",
                {"l_straight": 4.5, "d": 3.0, "h2": 1.25, "h_total": 3.0},
            ),
        }},
        summary={},
        trace=(),
        repro=ReproTriple(design_hash="", engine_version="", data_version=""),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


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
    """R1 接线断言（M2 实质化）：同 PlantResult 双跑场景图 JSON 相同。

    占位实质化（DRAFT 批总授权先例）：双跑 build_scene 序列化
    （asdict+sort_keys JSON）逐字节相同（纯投影确定性）；语义标签集合
    稳定（pool_wall/mech_cleaner 等来自对照表声明）。
    """
    first = build_scene(_plant(), _assumptions(), "design")
    second = build_scene(_plant(), _assumptions(), "design")
    dump1 = json.dumps(asdict(first), sort_keys=True, ensure_ascii=False)
    dump2 = json.dumps(asdict(second), sort_keys=True, ensure_ascii=False)
    assert dump1 == dump2
    semantics = {node.semantic for node in first.nodes}
    assert {"pool_wall", "mech_cleaner"} <= semantics  # 语义集合稳定
    assert first.condition_key == "design"
    assert first.scene_version  # R4 版本声明非空
    # 实例数汇总：n_gap 未列 instance_counts（分格数非设备台数），
    # mech_cleaner=1 → 节点 instance_count 取结果字段
    mech = next(n for n in first.nodes if n.semantic == "mech_cleaner")
    assert mech.instance_count == 1
