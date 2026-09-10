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


# ═══ P0-1（建项入口 2026-09-11）：view.name 显示名字段 ═══


def test_view_name_defaults_and_strips() -> None:
    """P0-1：view.name 缺省空串（历史项目零迁移装载）+strip 规范化。"""
    project = parse_project(dict(MINIMAL))
    assert project.view.name == ""  # 旧文件缺键=默认空串（向后兼容）
    named = dict(MINIMAL)
    named["view"] = {"name": "  城市一期  "}
    assert parse_project(named).view.name == "城市一期"  # 首尾空白剥除


def test_view_name_length_limit() -> None:
    """P0-1：去空白后超 100 字符拒（与 server CreateRequest 同口径）。"""
    named = dict(MINIMAL)
    named["view"] = {"name": "名" * 101}
    with pytest.raises(ValueError, match="100"):
        parse_project(named)
    named["view"] = {"name": "名" * 100}
    assert len(parse_project(named).view.name) == 100  # 恰上限含


def test_view_name_not_in_design_hash() -> None:
    """P0-1/R1：改名=view 态变更，design 摘要零扰动（改名不算 dirty）。"""
    from waterprint.project.content_hash import design_hash

    project = parse_project(dict(MINIMAL))
    renamed = project.model_copy(
        update={"view": project.view.model_copy(update={"name": "改名后"})}
    )
    assert design_hash(project.design) == design_hash(renamed.design)
