"""site 批迁移镜像测试：v1→v2 链（补默认空 site/来源版记录/正门路由/纯函数面）。

输入:  migration 公开符号 + 合成 v1 项目 fixture（七键 design+
       format_version "1.0"+旧哈希占位——golden_data/migrations 不动，
       回归证据由本件内置 fixture 承担，M1 简报 §二.4）
输出:  v1→v2 迁移链契约断言（未来版/未知历史版三分支已由本目录
       test_migration.py 覆盖，本件只补链新证据）
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from waterprint.app import load_project
from waterprint.contracts.project_schema import DesignState, SiteDesign
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


def test_v1_migrates_to_v2_adding_default_site() -> None:
    """v1→v2：format_version=="2.0"+migrated_from=="1.0"+site 全默认+七键逐键相等。

    逐键比对探针（数据策略 v2 口径，断言写死在本件）：v1 原七键值递归
    与迁移后逐键相等——旧项目零扰动。
    """
    v1 = _v1_project()
    migrated = migrate(v1)
    assert SUPPORTED_VERSIONS[-1] == "2.0"  # 链尾=当前版（迁移前提）
    assert migrated.format_version == "2.0"
    assert migrated.metadata.migrated_from == "1.0"
    assert migrated.design.site == SiteDesign()  # 补默认空 site（v2 新建态同构）
    expected = DesignState(**deepcopy(_V1_DESIGN))
    for field in _V1_DESIGN:  # 逐键递归相等（容器比对即递归）
        assert getattr(migrated.design, field) == getattr(expected, field), field
    assert "site" not in v1["design"]  # 纯函数面：调用方数据树零就地改写


def test_v1_with_existing_site_key_preserved() -> None:
    """防御路：v1 design 已含 site 键 → setdefault 不覆盖既有值（同值原样保留）。"""
    data = _v1_project()
    data["design"]["site"] = {"structures": {"u1": {"x": 1.0, "y": 2.0}}}
    migrated = migrate(data)
    assert migrated.format_version == "2.0"
    assert migrated.design.site.structures["u1"].x == 1.0  # 既有值未被默认空覆盖
    assert migrated.design.site.roads == []  # 其余子键补默认


def test_v2_current_version_passes_through_untouched() -> None:
    """v2 当前版直通：migrated_from 不动（None）——直通分支语义随升版保持。"""
    data = _v1_project()
    data["format_version"] = "2.0"
    direct = migrate(data)
    assert direct.format_version == "2.0"
    assert direct.metadata.migrated_from is None  # 直通零迁移写入


def test_app_load_project_routes_v1_file_through_chain(tmp_path: Path) -> None:
    """正门探针（质量门条款 3）：盘上合成 v1 文件 → app.load_project 迁移生效。"""
    path = tmp_path / "legacy_v1.wp.json"
    path.write_text(json.dumps(_v1_project(), ensure_ascii=False), encoding="utf-8")
    loaded = load_project(path)
    assert loaded.format_version == "2.0"  # 版本门路由进迁移链（非直通）
    assert loaded.design.site == SiteDesign()
    assert loaded.metadata.migrated_from == "1.0"
