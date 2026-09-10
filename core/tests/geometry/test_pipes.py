"""管廊装配镜像测试：两色制/管端缩进/架顶净空/防御跳过（C2-3d V5）。

输入:  waterprint.geometry.scene.build_scene（edges 关键字——管廊经
       pipes.pipe_nodes 装配；本件按镜像规则锁 pipes.py 行为面）
输出:  契约断言（§10.5/A7——golden 数值锚归 golden e2e，此处构造性
       fixture 断装配接线）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.geometry.scene")
build_scene = getattr(_mod, "build_scene", None)

pytestmark = pytest.mark.skipif(
    build_scene is None,
    reason="实现未就绪：waterprint.geometry.scene",
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
            "municipal_aao": snap(
                "municipal_aao",
                {"v_total": 17862.22, "h2": 5.0, "a_pool": 3572.444,
                 "l_pool_raw": 94.4647, "b_pool_raw": 37.7859,
                 "l_pool": 94.5, "b_pool": 38.0, "h_pool": 5.3,
                 "v_pool": 17955.0},
            ),
        }},
        summary={},
        trace=(),
        repro=ReproTriple(design_hash="", engine_version="", data_version=""),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}



def test_pipe_rack_wired_two_colors() -> None:
    """C2-3d 管廊：双端在场景的边→高架方管（两色制+中心连线+架顶净空）。"""
    from math import isclose

    edges = [
        {"src": {"unit_id": "municipal_cugeshan", "port_id": "out"},
         "dst": {"unit_id": "municipal_chenshachi", "port_id": "in"}},
        {"src": {"unit_id": "municipal_aao", "port_id": "out"},
         "dst": {"unit_id": "sludge_missing", "port_id": "in"}},  # 不在场景→跳过
    ]
    graph = build_scene(_plant(), _assumptions(), "design", edges=edges)
    pipes = [n for n in graph.nodes if n.semantic.startswith("pipe_")]
    assert len(pipes) == 1
    pipe = pipes[0]
    assert pipe.semantic == "pipe_water"
    assert pipe.primitive.kind == "box"
    assert set(pipe.primitive.dims) == {"length", "width", "depth"}
    assert pipe.primitive.dims["width"] == 0.8
    # 架顶=最高构筑物顶+1.2 净空（glm 一轮 0.8→1.2——圆池顶视觉贴管收口）
    assert isclose(pipe.position[2], 5.3 + 1.2)
    # 中心连线几何：fallback 排布 y=0 → rz=0（atan2 同款）
    assert isclose(pipe.rotation[2], 0.0)
    assert pipe.node_id.startswith("pipe::")
    assert pipe.node_id in graph.root


def test_pipe_sludge_end_brown_and_dedupe() -> None:
    """C2-3d 管廊：任一端 sludge_ 前缀归泥语义+单元对去重+inlet/泥端缺失跳过。"""
    from waterprint.contracts.result_schema import UnitResultSnapshot

    graph = build_scene(
        _plant(), _assumptions(), "design",
        edges=[
            {"src": {"unit_id": "sludge_nongsuo", "port_id": "out"},
             "dst": {"unit_id": "municipal_aao", "port_id": "in"}},  # 泥端不在场景→跳过
            {"src": {"unit_id": "municipal_chenshachi", "port_id": "out"},
             "dst": {"unit_id": "municipal_aao", "port_id": "in"}},
            {"src": {"unit_id": "municipal_aao", "port_id": "out2"},
             "dst": {"unit_id": "municipal_chenshachi", "port_id": "in2"}},  # 同对反向→去重
            {"src": {"unit_id": "inlet", "port_id": "out"},
             "dst": {"unit_id": "municipal_cugeshan", "port_id": "in"}},  # inlet 端→跳过
        ],
    )
    pipes = [n for n in graph.nodes if n.semantic.startswith("pipe_")]
    assert len(pipes) == 1
    assert pipes[0].semantic == "pipe_water"
    # 两色制泥分支：注入 sludge 快照后同款边语义翻泥（前缀判据直测）
    # （PlantResult 不可变——replace 构造新工况字典注入快照）
    import dataclasses

    plant_sludge = dataclasses.replace(
        _plant(),
        conditions={"design": {
            **_plant().conditions["design"],
            "sludge_nongsuo": UnitResultSnapshot(
                unit_id="sludge_nongsuo", outflows={}, outqualities={},
                dims={"d": 12.0, "h_total": 5.0}, warnings=(),
                formula_ids=(),
            ),
        }},
    )
    graph2 = build_scene(
        plant_sludge, _assumptions(), "design",
        edges=[{"src": {"unit_id": "sludge_nongsuo", "port_id": "out"},
                "dst": {"unit_id": "municipal_aao", "port_id": "in"}}],
    )
    pipes2 = [n for n in graph2.nodes if n.semantic.startswith("pipe_")]
    assert len(pipes2) == 1
    assert pipes2[0].semantic == "pipe_sludge"


def test_pipe_no_edges_no_nodes_and_malformed_skip() -> None:
    """C2-3d 管廊：edges=None 零管节点（既有调用方零改动）+畸形/自环边静默跳过。"""
    graph = build_scene(_plant(), _assumptions(), "design")
    assert not [n for n in graph.nodes if n.semantic.startswith("pipe_")]
    bad = build_scene(
        _plant(), _assumptions(), "design",
        edges=[
            {"src": "not-a-mapping", "dst": {"unit_id": "municipal_aao"}},
            {"src": {"unit_id": "municipal_cugeshan"}},
            {"src": {"unit_id": "municipal_cugeshan", "port_id": "o"},
             "dst": {"unit_id": "municipal_cugeshan", "port_id": "i"}},  # 自环
        ],
    )
    assert not [n for n in bad.nodes if n.semantic.startswith("pipe_")]
