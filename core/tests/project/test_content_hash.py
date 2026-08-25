"""content_hash 镜像测试：设计态哈希（view 无关/参与项完备/顺序无关）。

输入:  waterprint.project.content_hash 公开符号
输出:  哈希契约断言（dirty 判定与可复算三元组的基石）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.project.content_hash")
design_hash = getattr(_mod, "design_hash", None)
_io = importlib.import_module("waterprint.project.io")
dumps = getattr(_io, "dumps", None)
_schema = importlib.import_module("waterprint.contracts.project_schema")
DesignState = getattr(_schema, "DesignState", None)
ViewState = getattr(_schema, "ViewState", None)

pytestmark = pytest.mark.skipif(
    design_hash is None,
    reason="实现未就绪：waterprint.project.content_hash（M1）",
)

_BASE: dict = {
    "nodes": {"u1": {"pool_length": 10.5}, "u2": {"n": 1}},
    "edges": [{"src": "u1:o", "dst": "u2:i"}],
    "constraint_choices": {"c1": "strict"},
    "checked_units": ["u1"],
    "assumption_overrides": {"safety.superheight": 0.3},
    "influent": {"q_avg_daily": 100.0},
    "standard_binding": {"out": "gb18918_1a"},
}


def _design() -> object:
    """基线 design：七字段全非空（参与项变更断言的前提）。"""
    return DesignState(**_BASE)


def test_hash_shape_is_sha256_hex() -> None:
    """R1：64 位十六进制（sha256）。"""
    value = design_hash(_design())
    assert len(value) == 64
    assert all(char in "0123456789abcdef" for char in value)


def test_view_changes_do_not_affect_hash_wiring() -> None:
    """R1 接线断言：view 态任何变化哈希不变（R10 病根终结）。"""
    design = _design()
    project_a = _schema.ProjectFile(
        format_version="1.0", design=design,
        view=ViewState(layout={"u1": {"x": 1, "y": 2}}),
        metadata=_schema.Metadata(
            format_version="1.0", content_hash="0" * 64,
            engine_version="0.1.0", data_version="coefficients@0.1.0"),
    )
    project_b = _schema.ProjectFile(
        format_version="1.0", design=design,
        view=ViewState(camera={"z": 9}, windows={"panel": 2},
                       timestamp="2026-08-25T08:00:00+00:00"),
        metadata=_schema.Metadata(
            format_version="1.0", content_hash="0" * 64,
            engine_version="0.1.0", data_version="coefficients@0.1.0"),
    )
    # view 变化真实生效（序列化字节确实不同）——对照有效性前提
    assert dumps(project_a) != dumps(project_b)
    assert design_hash(project_a.design) == design_hash(project_b.design)


def test_design_changes_flip_hash_wiring() -> None:
    """R3 接线断言：参数/边/假设覆盖任一变更 → 哈希必变。"""
    baseline = design_hash(_design())
    variants: dict[str, dict] = {
        "nodes": dict(_BASE, nodes={"u1": {"pool_length": 11.5}, "u2": {"n": 1}}),
        "edges": dict(_BASE, edges=[{"src": "u1:o", "dst": "u3:i"}]),
        "constraint_choices": dict(_BASE, constraint_choices={"c1": "loose"}),
        "checked_units": dict(_BASE, checked_units=["u2"]),
        "assumption_overrides": dict(
            _BASE, assumption_overrides={"safety.superheight": 0.35}
        ),
        "influent": dict(_BASE, influent={"q_avg_daily": 120.0}),
        "standard_binding": dict(_BASE, standard_binding={"out": "gb18918_1b"}),
    }
    for field, kwargs in variants.items():
        assert design_hash(DesignState(**kwargs)) != baseline, field
