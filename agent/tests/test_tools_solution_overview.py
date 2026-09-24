"""方案/观测组工具镜像测试：#22 联合枚举+#23 概览+第三源假设（B4-4b 子批 3 TDD）。

输入:  tmp_path 沙箱+两单元项目（联合枚举载体）
输出:  护栏拒绝回显/top-N 投影/概览聚合/assumptions 检索断言
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.tools import knowledge, overview, solution


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def _two_unit_payload() -> dict[str, object]:
    """两单元项目（inlet→aao→cass——联合枚举最小载体）。"""
    return {
        "format_version": "1.0",
        "design": {
            "nodes": {
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "NH3N": 26.0,
                    "TN": 43.0,
                    "TP": 6.5,
                },
                "municipal_aao": {},
                "municipal_cass": {},
            },
            "edges": [
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": "municipal_aao", "port_id": "in"}},
                {"src": {"unit_id": "municipal_aao", "port_id": "out"},
                 "dst": {"unit_id": "municipal_cass", "port_id": "in"}},
            ],
        },
        "view": {},
        "metadata": {
            "format_version": "1.0", "content_hash": "0",
            "engine_version": "0", "data_version": "0",
        },
    }


async def _project_id(sandbox_env: Path, payload: dict[str, object]) -> str:
    """经 services.create_project 全量建项（content_hash 由服务计算——
    不变量保真；直写文件绕过哈希会令 stale 判定失真）。"""
    from waterprint_server.services import projects as projects_service

    ctx = context.get_context()
    outcome = projects_service.create_project(ctx.service_ctx, {"name": "联合测试", "project": payload})
    return str(outcome.project_id)


def test_joint_single_unit_rejected(sandbox_env: Path) -> None:
    """R4 域下界：unit_ids<2 → status=rejected（单单元走既有正门）。"""
    ctx = context.get_context()
    result = solution._run_joint_enumeration_impl(ctx, "p-any", ["municipal_aao"])
    assert result["status"] == "rejected"
    assert "wp_run_enumeration" in str(result["reason"])


def test_joint_unknown_project_guarded(sandbox_env: Path) -> None:
    """PathGuard 面：路径注入→PathGuardError 穿透（run_tool 包装面转错误 dict）。"""
    from waterprint_agent.pathguard import PathGuardError

    ctx = context.get_context()
    with pytest.raises(PathGuardError, match="逃逸"):
        solution._run_joint_enumeration_impl(
            ctx, "../escape", ["municipal_aao", "municipal_cass"]
        )


@pytest.mark.anyio
async def test_joint_full_chain_top_n(sandbox_env: Path) -> None:
    """全链：两单元联合枚举（缺省网格档）→ok 投影 top/budget/semantics。"""
    pid = await _project_id(sandbox_env, _two_unit_payload())
    ctx = context.get_context()
    result = solution._run_joint_enumeration_impl(
        ctx, pid, ["municipal_aao", "municipal_cass"], top_n=3
    )
    assert result.get("status") == "ok", result
    assert 0 < len(result["top"]) <= 3
    assert "budget_usage" in result and "search_semantics" in result
    for combo in result["top"]:
        assert "params" in combo and "feasible" in combo


@pytest.mark.anyio
async def test_overview_aggregates_results(sandbox_env: Path) -> None:
    """#23 概览：计算落盘后 results 聚合（计数+stale+scope 面在场）。"""
    from waterprint_agent.tools import calc

    pid = await _project_id(sandbox_env, _two_unit_payload())
    calc_result = await calc.wp_run_calc(project_id=pid, conditions=None)
    assert "error" not in calc_result
    ctx = context.get_context()
    result = overview._overview_impl(ctx, limit=5)
    assert result["total_results"] >= 1
    assert result["count"] >= 1
    assert result["stale_results"] == 0  # 刚算完=新鲜
    assert result["results"][0]["project_id"] == pid
    assert "agent-sandbox" in result["scope"]


def test_overview_stale_after_param_change(sandbox_env: Path) -> None:
    """R2 stale 门：改项目文件（digest 变）→既有结果判失配。"""
    ctx = context.get_context()
    # 直构最小结果件+项目件（绕过计算——stale 判定单测面）
    pid = "staleprobe0000000000000000000000ff"
    projects_dir = sandbox_env / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    (projects_dir / f"{pid}.wp.json").write_text(
        json.dumps({"metadata": {"content_hash": "newdigest"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    results_dir = sandbox_env / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / f"{pid}-olddigest1.result.json").write_text(
        json.dumps({"design_digest": "olddigest"}), encoding="utf-8"
    )
    result = overview._overview_impl(ctx)
    assert result["stale_results"] == 1
    assert result["results"][0]["stale"] is True


def test_knowledge_assumptions_source(sandbox_env: Path) -> None:
    """第三源：assumptions 检索 solution.joint.* 键（程序化单源）。"""
    ctx = context.get_context()
    result = knowledge._query_knowledge_impl(ctx, "solution.joint", "assumptions")
    assert result["source"] == "assumptions"
    assert result["total_hits"] >= 1
    keys = [hit["key"] for hit in result["hits"]]
    assert any(key.startswith("solution.joint.") for key in keys)
    # 碳键族也可检索（B4-2abc 假设面）
    assert "error" not in result
