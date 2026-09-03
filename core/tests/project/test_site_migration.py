"""site 批迁移镜像测试：v1→v2/v2→v3 链（补默认键/来源版记录/正门路由/纯函数面）。

输入:  migration 公开符号 + 合成 v1/v2 项目 fixture（七键 design 起+
       format_version 字面+旧哈希占位——golden_data/migrations 样本对另由
       本目录 test_migration.py 接线，本件内置 fixture 承担逐项比对，M1
       简报 §二.4 先例）
输出:  v1→v2（M1 site 键）与 v2→v3（L4a boundary 键）迁移链契约断言
       （未来版/未知历史版三分支已由本目录 test_migration.py 覆盖，本件
       只补链新证据）
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from waterprint.app import load_project
from waterprint.contracts.project_schema import DesignState, SiteDesign
from waterprint.project.io import InvalidProjectError
from waterprint.project.migration import SUPPORTED_VERSIONS, migrate

_V1_DESIGN: dict = {  # v1 七键全非空（逐键比对探针的对照源）
    "nodes": {"u1": {"pool_length": 10.5}},
    "edges": [{"src": "u1:o", "dst": "u2:i"}],
    "constraint_choices": {"c1": "strict"},
    "checked_units": ["u1"],
    "assumption_overrides": {"safety.superheight": 0.3},
    "influent": {"q_avg_daily": 100.0},
    "standard_binding": {"out": "gb18918_1a"},
}

_V2_SITE: dict = {  # v2 形 site 全子键（boundary 缺=未划界——v2→v3 补键面载体）
    "structures": {"u1": {"x": 1.0, "y": 2.0, "rotation": 90.0}},
    "roads": [
        {"centerline": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}], "width_m": 6.0}
    ],
    "corridors": [
        {
            "centerline": [{"x": 0.0, "y": 1.0}, {"x": 0.0, "y": 20.0}],
            "width_m": 2.0,
            "kind": "water",
        }
    ],
    "options": {"coord_grid": 10.0, "wind_rose": {"N": 12.5}},
}


def _v1_project() -> dict:
    """合成 v1 项目（旧盘实态形：零 site 键+format_version "1.0"+v1 哈希占位）。"""
    return {
        "format_version": "1.0",
        "design": deepcopy(_V1_DESIGN),
        "view": {},
        "metadata": {
            "content_hash": "0" * 64,  # v1 哈希占位（升版后自然失效——io R6 版本头语义）
            "engine_version": "0.1.0",
            "data_version": "coefficients@0.1.0",
        },
    }


def _v2_project() -> dict:
    """合成 v2 项目（M1 后盘实态形：site 全子键零 boundary+format_version "2.0"）。"""
    project = _v1_project()
    project["format_version"] = "2.0"
    project["design"]["site"] = deepcopy(_V2_SITE)
    return project


def test_v1_migrates_to_current_adding_default_site() -> None:
    """v1→当前版（链式复合 v1→v2→v3）：format_version=="3.0"+migrated_from=="1.0"
    +site 全默认（含 boundary）+七键逐键相等。

    逐键比对探针（数据策略 v2 口径，断言写死在本件）：v1 原七键值递归
    与迁移后逐键相等——旧项目零扰动。
    """
    v1 = _v1_project()
    migrated = migrate(v1)
    assert SUPPORTED_VERSIONS[-1] == "3.0"  # 链尾=当前版（迁移前提）
    assert migrated.format_version == "3.0"
    assert migrated.metadata.migrated_from == "1.0"
    assert migrated.design.site == SiteDesign()  # 补默认空 site（含 L4a boundary=[]）
    expected = DesignState(**deepcopy(_V1_DESIGN))
    for field in _V1_DESIGN:  # 逐键递归相等（容器比对即递归）
        assert getattr(migrated.design, field) == getattr(expected, field), field
    assert "site" not in v1["design"]  # 纯函数面：调用方数据树零就地改写


def test_v1_with_existing_site_key_preserved() -> None:
    """防御路：v1 design 已含 site 键 → setdefault 不覆盖既有值（同值原样保留）。"""
    data = _v1_project()
    data["design"]["site"] = {"structures": {"u1": {"x": 1.0, "y": 2.0}}}
    migrated = migrate(data)
    assert migrated.format_version == "3.0"
    assert migrated.design.site.structures["u1"].x == 1.0  # 既有值未被默认空覆盖
    assert migrated.design.site.roads == []  # 其余子键补默认
    assert migrated.design.site.boundary == []  # L4a：v2→v3 步补默认空 boundary


def test_v2_migrates_to_v3_adding_default_boundary() -> None:
    """v2→v3（L4a 链步）：boundary=[] 补入+既有 site 四子键逐键保留+七键不动。

    setdefault 先例（M1 _migrate_add_site 同形态）：旧项目零扰动——
    structures/roads/corridors/options 与 design 其余键迁移前后逐键相等。
    """
    v2 = _v2_project()
    migrated = migrate(v2)
    assert migrated.format_version == "3.0"
    assert migrated.metadata.migrated_from == "2.0"
    assert migrated.design.site.boundary == []  # 补默认空（未划界合法态）
    expected_site = SiteDesign.model_validate(deepcopy(_V2_SITE))
    for field in ("structures", "roads", "corridors", "options"):
        assert getattr(migrated.design.site, field) == getattr(expected_site, field), field
    expected = DesignState(**{k: deepcopy(v) for k, v in _V1_DESIGN.items()})
    for field in _V1_DESIGN:  # design 七键逐键递归相等（site 外零扰动）
        assert getattr(migrated.design, field) == getattr(expected, field), field
    assert "boundary" not in v2["design"]["site"]  # 纯函数面：调用方树零改写


def test_v2_with_existing_boundary_preserved() -> None:
    """防御路：v2 site 已含 boundary 键 → setdefault 不覆盖既有顶点序。"""
    data = _v2_project()
    data["design"]["site"]["boundary"] = [
        {"x": 0.0, "y": 0.0}, {"x": 30.0, "y": 0.0}, {"x": 0.0, "y": 20.0}
    ]
    migrated = migrate(data)
    assert migrated.format_version == "3.0"
    assert [(p.x, p.y) for p in migrated.design.site.boundary] == [
        (0.0, 0.0), (30.0, 0.0), (0.0, 20.0),
    ]  # 既有红线未被默认空覆盖


def test_v3_current_version_passes_through_untouched() -> None:
    """v3 当前版直通：migrated_from 不动（None）——直通分支语义随升版保持。"""
    data = _v2_project()
    data["format_version"] = "3.0"
    data["design"]["site"]["boundary"] = []
    direct = migrate(data)
    assert direct.format_version == "3.0"
    assert direct.metadata.migrated_from is None  # 直通零迁移写入


def test_metadata_format_version_conflict_rejected() -> None:
    """R 轮 G1-01：顶层 "1.0"+metadata.format_version "2.0" → 双写冲突拒。

    链源版与 metadata 声明不一致=真冲突——升版写回前拒（防 _apply_chain
    静默吞冲突；口径同 project_schema._sync_format_version）。
    """
    data = _v1_project()
    data["metadata"]["format_version"] = "2.0"
    with pytest.raises(InvalidProjectError, match="双写冲突"):
        migrate(data)


def test_migrate_rejects_non_mapping_design() -> None:
    """R 轮 G1-02：design 非 mapping → InvalidProjectError（禁 AttributeError 逃逸）。"""
    data = _v1_project()
    data["design"] = "garbage"
    with pytest.raises(InvalidProjectError, match="design"):
        migrate(data)


def test_app_load_project_routes_v1_file_through_chain(tmp_path: Path) -> None:
    """正门探针（质量门条款 3）：盘上合成 v1 文件 → app.load_project 迁移生效。"""
    path = tmp_path / "legacy_v1.wp.json"
    path.write_text(json.dumps(_v1_project(), ensure_ascii=False), encoding="utf-8")
    loaded = load_project(path)
    assert loaded.format_version == "3.0"  # 版本门路由进迁移链（非直通）
    assert loaded.design.site == SiteDesign()
    assert loaded.metadata.migrated_from == "1.0"


def test_app_load_project_routes_v2_file_through_chain(tmp_path: Path) -> None:
    """正门探针（L4a）：盘上合成 v2 文件 → app.load_project 单步链补 boundary。"""
    path = tmp_path / "legacy_v2.wp.json"
    path.write_text(json.dumps(_v2_project(), ensure_ascii=False), encoding="utf-8")
    loaded = load_project(path)
    assert loaded.format_version == "3.0"
    assert loaded.design.site.boundary == []  # v2→v3 补默认空红线
    assert loaded.design.site.structures["u1"].x == 1.0  # 既有摆放保留
    assert loaded.metadata.migrated_from == "2.0"
