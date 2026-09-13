"""test_tools_projects——项目组三工具：blank/municipal 种子建项目+outline/validate 闭环。

输入:  tmp_path 沙箱（env 覆盖）+ golden municipal_34760 种子（正式区只读装载）
输出:  建项/摘要/校验/会话日志断言（AI1-TRACK-B §3 工具 #4~#6）
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest

from waterprint_agent import context, sandbox
from waterprint_agent.tools import projects

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def test_create_project_blank(sandbox_env: Path) -> None:
    """blank 种子（E3 空白路径）：零节点骨架落沙箱 projects/，返回三键。"""
    result = asyncio.run(projects.wp_create_project(name="空白测试", seed="blank"))
    assert set(result) == {"project_id", "name", "design_digest"}
    assert result["name"] == "空白测试"
    assert re.match(r"^[0-9a-f]{32}$", result["project_id"])
    assert _HEX64.match(result["design_digest"])
    stored = sandbox_env / "projects" / f"{result['project_id']}.wp.json"
    assert stored.is_file()  # 落沙箱 projects/ 区
    design = json.loads(stored.read_text(encoding="utf-8"))["design"]
    assert design["nodes"] == {} and design["edges"] == []


def test_create_project_municipal_seed(sandbox_env: Path) -> None:
    """municipal_34760 种子：golden input_project.json 经正式区只读门拷入沙箱。"""
    result = asyncio.run(projects.wp_create_project(name="市政副本", seed="municipal_34760"))
    stored = sandbox_env / "projects" / f"{result['project_id']}.wp.json"
    design = json.loads(stored.read_text(encoding="utf-8"))["design"]
    assert len(design["nodes"]) == 19
    assert len(design["edges"]) == 17
    outline = asyncio.run(projects.wp_get_project_outline(result["project_id"]))
    assert outline["name"] == "市政副本"  # 请求名覆盖种子自带名
    assert outline["node_count"] == 19 and outline["edge_count"] == 17


def test_create_project_invalid_seed(sandbox_env: Path) -> None:
    """非法 seed→错误 dict（不 raise）。"""
    result = asyncio.run(projects.wp_create_project(name="x", seed="golden_loop"))  # type: ignore[arg]
    assert "error" in result and "hint" in result


def test_outline_token_friendly_projection(sandbox_env: Path) -> None:
    """outline 投影：节点(unit_id/kind/参数计数)+边清单+进水+工况勾选。"""
    created = asyncio.run(projects.wp_create_project(name="摘要", seed="municipal_34760"))
    outline = asyncio.run(projects.wp_get_project_outline(created["project_id"]))
    assert outline["project_id"] == created["project_id"]
    inlet = next(n for n in outline["nodes"] if n["unit_id"] == "inlet")
    assert inlet["kind"] == "municipal_input" and inlet["type"] == "builtin"
    assert inlet["param_count"] == 8  # q_avg_daily+kz+六指标（kind 键不计参）
    aao = next(n for n in outline["nodes"] if n["unit_id"] == "municipal_aao")
    assert aao["type"] == "unit" and aao["param_count"] == 0  # golden 未设任何参数
    assert outline["edges"][0] == {
        "src": "inlet:out", "dst": "municipal_wushui_tisheng:in"
    }
    assert "influent" in outline and isinstance(outline["checked_units"], list)
    assert outline["design_digest"] == created["design_digest"]


def test_outline_unknown_project(sandbox_env: Path) -> None:
    """未知项目→错误 dict（不 raise 裸异常）。"""
    result = asyncio.run(projects.wp_get_project_outline("deadbeef"))
    assert "error" in result and "hint" in result


def test_outline_rejects_path_injection(sandbox_env: Path) -> None:
    """project_id 路径注入（../）→PathGuard 拒绝面=错误 dict。"""
    result = asyncio.run(projects.wp_get_project_outline("../../outside"))
    assert "error" in result


def test_validate_design_closed_loop(sandbox_env: Path) -> None:
    """validate 闭环：golden 结构校验 valid=True；空白骨架亦 valid=True。"""
    seeded = asyncio.run(projects.wp_create_project(name="校验", seed="municipal_34760"))
    ok = asyncio.run(projects.wp_validate_design(seeded["project_id"]))
    assert ok["valid"] is True and ok["error_count"] == 0 and ok["errors"] == []
    blank = asyncio.run(projects.wp_create_project(name="空"))
    ok_blank = asyncio.run(projects.wp_validate_design(blank["project_id"]))
    assert ok_blank["valid"] is True


def test_tool_calls_logged_to_session_jsonl(sandbox_env: Path) -> None:
    """会话日志接线：每工具调用自动记 tool_call/tool_result 事件行。"""
    asyncio.run(projects.wp_create_project(name="日志"))
    ctx = context.get_context()
    jsonl = sandbox_env / "sessions" / f"{ctx.session_id}.jsonl"
    assert jsonl.is_file()
    events = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
    types = [(e["type"], e["actor"]) for e in events]
    assert ("tool_call", "tool") in types
    assert ("tool_result", "tool") in types
    tool_names = {e["payload"].get("tool") for e in events if e["type"] == "tool_call"}
    assert "wp_create_project" in tool_names


def test_golden_seed_source_exists() -> None:
    """种子源在位性：golden input_project.json 经 PathGuard 正式区只读门可用。"""
    golden = sandbox.repo_root() / (
        "core/tests/golden/golden_data/municipal_34760/input_project.json"
    )
    assert golden.is_file(), f"golden 种子缺失：{golden}"
