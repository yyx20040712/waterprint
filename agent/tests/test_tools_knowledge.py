"""test_tools_knowledge——知识组三工具：list_units 36 口径/manifest 投影/知识检索。

输入:  tmp_path 沙箱（env 覆盖）+ 真实 data 资产（只读）
输出:  投影断言（AI1-TRACK-B §3 工具 #1~#3）
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.tools import knowledge


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def test_list_units_36_baseline(sandbox_env: Path) -> None:
    """基线口径：无过滤恰 36 条（32 包+4 builtin），行三键。"""
    result = asyncio.run(knowledge.wp_list_units())
    assert result["count"] == 36
    assert len(result["units"]) == 36
    first = result["units"][0]
    assert set(first) == {"unit_id", "name_zh", "line"}
    assert all(u["name_zh"] for u in result["units"])  # 中文名映射全覆盖


def test_list_units_category_filter(sandbox_env: Path) -> None:
    """category 过滤：municipal=13 包+4 builtin=17；未知 category→错误 dict。"""
    result = asyncio.run(knowledge.wp_list_units(category="municipal"))
    assert result["count"] == 17
    assert all(u["line"] == "municipal" for u in result["units"])
    bad = asyncio.run(knowledge.wp_list_units(category="nonsense"))
    assert "error" in bad and "hint" in bad


def test_get_unit_manifest_projection(sandbox_env: Path) -> None:
    """manifest 裁剪投影：参数键/单位/grid 档位在，内部键（i18n_key/removal_refs/
    condition_mappings）去。"""
    result = asyncio.run(knowledge.wp_get_unit_manifest("municipal_aao"))
    assert result["unit_id"] == "municipal_aao"
    assert result["name_zh"] == "AAO 生物池"
    assert result["kind"] == "unit"
    params = {p["field_id"]: p for p in result["params"]}
    assert params["n"]["grid"] == [2.0, 3.0, 4.0, 5.0, 6.0]  # grid 档位在场
    assert params["n"]["dim"] == "DIMENSIONLESS"
    assert params["n"]["range"] is None or set(params["n"]["range"]) == {"min", "max"}
    assert result["ports"] and {"port_id", "fluid", "direction"} <= set(result["ports"][0])
    assert result["norm_refs"]  # 规范引用
    assert result["constraint_refs"]
    for internal in ("i18n_key", "removal_refs", "condition_mappings"):
        assert internal not in result


def test_get_unit_manifest_builtin_and_unknown(sandbox_env: Path) -> None:
    """builtin kind 投影可取；未知 unit_id→错误 dict（不 raise）。"""
    result = asyncio.run(knowledge.wp_get_unit_manifest("junction"))
    assert result["kind"] == "builtin"
    assert result["params"] == []
    assert len(result["ports"]) == 3  # in_1/in_2+out
    unknown = asyncio.run(knowledge.wp_get_unit_manifest("no_such_unit"))
    assert "error" in unknown and "hint" in unknown


def test_query_knowledge_constraints(sandbox_env: Path) -> None:
    """constraints 检索：键/标签/表达式命中，八键条目+limit 口径。"""
    by_label = asyncio.run(knowledge.wp_query_knowledge("滤速", source="constraints"))
    assert by_label["source"] == "constraints"
    assert by_label["total_hits"] >= 1
    keys = {h["key"] for h in by_label["hits"]}
    assert "vxinglvchi.v_filter_band" in keys
    hit = by_label["hits"][0]
    assert {"key", "kind", "unit_kinds", "label", "expression", "source", "severity",
            "value_basis"} <= set(hit)


def test_query_knowledge_coefficients_limit(sandbox_env: Path) -> None:
    """coefficients 键检索：命中含 value/unit/source（来源键），limit 20+截断标记。"""
    result = asyncio.run(knowledge.wp_query_knowledge("", source="coefficients"))
    assert result["source"] == "coefficients"
    assert len(result["hits"]) == 20
    assert result["truncated"] is True
    assert result["total_hits"] > 20
    hit = result["hits"][0]
    assert {"key", "value", "unit", "source", "note"} <= set(hit)
    targeted = asyncio.run(knowledge.wp_query_knowledge("mlss_band", source="coefficients"))
    assert any("mlss_band" in h["key"] for h in targeted["hits"])


def test_query_knowledge_invalid_source(sandbox_env: Path) -> None:
    """非法 source→错误 dict（不 raise）。"""
    result = asyncio.run(knowledge.wp_query_knowledge("x", source="bogus"))  # type: ignore[arg]
    assert "error" in result and "hint" in result
