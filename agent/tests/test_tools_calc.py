"""test_tools_calc——计算组 #8~#10：全厂计算落盘+枚举 Top-N+可行域图。

输入:  tmp_path 沙箱（env 覆盖）+ municipal_34760 种子（真实 data 数据包）
输出:  结果文件 digest 命名/摘要形态/枚举与可行域产物断言（AI1-INTEG §3）
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.tools import calc, projects


@pytest.fixture
def seeded(sandbox_env_factory: Callable[[], Path]) -> dict[str, str]:
    """municipal_34760 种子项目（返回 project_id/design_digest）。"""
    created = asyncio.run(projects.wp_create_project(name="计算", seed="municipal_34760"))
    return created


@pytest.fixture
def sandbox_env_factory(tmp_path: Path, monkeypatch) -> Callable[[], Path]:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()

    def _factory() -> Path:
        return root

    yield _factory
    context.reset_context()


def test_run_calc_persists_digest_named_result(sandbox_env_factory, seeded) -> None:
    """#8：全厂计算——结果+诊断落沙箱 results/，文件名带 design_digest 前 10。"""
    result = asyncio.run(calc.wp_run_calc(seeded["project_id"]))
    assert "error" not in result, result
    digest = result["design_digest"]
    assert digest == seeded["design_digest"]  # 未改参=digest 不变（可复算三元组）
    stem = f"{seeded['project_id']}-{digest[:10]}"
    root = sandbox_env_factory()
    result_file = root / "results" / f"{stem}.result.json"
    diag_file = root / "results" / f"{stem}.diag.json"
    assert result_file.is_file() and diag_file.is_file()
    assert Path(result["result_path"]) == result_file  # normcase 归一比较
    assert result["artifact_path"] == result["result_path"]  # 门一 FIX-4：D3 统一名别名并存
    # 摘要形态：六指标+warnings 计数+质量闭合（≤1.5k token 口径）
    summary = result["summary"]
    for key in ("BOD5", "CODCR", "SS", "NH3N", "TN", "TP"):
        assert key in summary, key
    assert "warnings_total" in summary and "mass_closure_design" in summary
    # 缺省 conditions=checked_units（server worker 同语义）→ 2+k 工况
    assert set(result["condition_keys"]) >= {"design", "avg"}


def test_run_calc_conditions_override(sandbox_env_factory, seeded) -> None:
    """#8 conditions 透传：显式受检单元清单→工况集=2+k（ADR-007）。"""
    result = asyncio.run(
        calc.wp_run_calc(seeded["project_id"], conditions=["municipal_aao"])
    )
    assert "error" not in result, result
    assert set(result["condition_keys"]) == {
        "design", "avg", "design_offline_municipal_aao",
    }


def test_run_calc_unknown_project(sandbox_env_factory) -> None:
    """#8 错误面：未知项目→错误 dict（不 raise）。"""
    result = asyncio.run(calc.wp_run_calc("deadbeef"))
    assert "error" in result and "hint" in result


def test_run_enumeration_top_n(sandbox_env_factory, seeded) -> None:
    """#9：单单元枚举——Top-N 行摘要+全量行落 results/（digest 命名）。"""
    outcome = asyncio.run(
        calc.wp_run_enumeration(seeded["project_id"], "municipal_chenshachi", top_n=3)
    )
    assert "error" not in outcome, outcome
    assert outcome["unit_id"] == "municipal_chenshachi"
    assert 1 <= len(outcome["top_rows"]) <= 3
    assert isinstance(outcome["total_feasible"], int)
    assert outcome["artifact_path"].endswith(".json")
    full = json.loads(Path(outcome["artifact_path"]).read_text(encoding="utf-8"))
    assert len(full["rows"]) >= len(outcome["top_rows"])
    assert full["row_count"] == len(full["rows"])


def test_run_enumeration_unknown_unit(sandbox_env_factory, seeded) -> None:
    """#9 错误面：未知单元→错误 dict。"""
    outcome = asyncio.run(
        calc.wp_run_enumeration(seeded["project_id"], "ghost_unit")
    )
    assert "error" in outcome


def test_run_design_map(sandbox_env_factory, seeded) -> None:
    """#10：可行域图——可行比例+边界摘要+payload 全量落盘。"""
    outcome = asyncio.run(
        calc.wp_run_design_map(seeded["project_id"], "municipal_chenshachi")
    )
    assert "error" not in outcome, outcome
    assert 0.0 <= outcome["stats"]["feasible_ratio"] <= 1.0
    assert outcome["artifact_path"].endswith(".json")
    full = json.loads(Path(outcome["artifact_path"]).read_text(encoding="utf-8"))
    assert full["unit_id"] == "municipal_chenshachi"
    assert full["stats"] == outcome["stats"]
