"""project_schema 镜像测试：design/view 双态 schema（ADR-004 分界与严格校验）。

输入:  waterprint.contracts.project_schema 公开符号
输出:  双态字段/严格拒绝断言
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.project_schema")
ProjectFile = getattr(_mod, "ProjectFile", None)
DesignState = getattr(_mod, "DesignState", None)
ViewState = getattr(_mod, "ViewState", None)
parse_project = getattr(_mod, "parse_project", None)

pytestmark = pytest.mark.skipif(
    None in (ProjectFile, DesignState, ViewState, parse_project),
    reason="实现未就绪：waterprint.contracts.project_schema（M1）",
)


def _names(cls: type) -> set[str]:
    if dataclasses.is_dataclass(cls):
        return {f.name for f in dataclasses.fields(cls)}
    return set(getattr(cls, "model_fields", {}))


def test_dual_state_fields_present() -> None:
    """双态模型齐备：ProjectFile = design + view + metadata。"""
    assert {"design", "view", "metadata"} <= _names(ProjectFile)


MINIMAL: dict = {
    "format_version": "1.0",
    "design": {},
    "view": {},
    "metadata": {
        "content_hash": "0" * 64,
        "engine_version": "0.1.0",
        "data_version": "0.1.0",
    },
}


def test_metadata_carries_repro_triple() -> None:
    """R3：metadata 含三元组四件（format_version/content_hash/engine_version/data_version）。"""
    project = parse_project(dict(MINIMAL))
    metadata = project.metadata
    for attr in ("format_version", "content_hash", "engine_version", "data_version"):
        assert hasattr(metadata, attr), f"metadata 缺 {attr}"


def test_unknown_field_rejected() -> None:
    """R2：未知字段拒绝（extra=forbid——安全面与漂移面双杀）。"""
    data = dict(MINIMAL)
    data["mystery_field"] = 42
    with pytest.raises(Exception, match=".+"):
        parse_project(data)
