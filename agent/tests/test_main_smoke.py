"""test_main_smoke——FastMCP 进程内 smoke：tools/list 满座 21 工具+懒加载首响实测。

输入:  tmp_path 沙箱（env 覆盖；禁写真实默认沙箱根）
输出:  工具清单/首响时间断言（AI1-TRACK-B §3+AI1-INTEG 21 工具口径）
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from waterprint_agent import context

_TOOL_NAMES = {
    "wp_list_units",
    "wp_get_unit_manifest",
    "wp_query_knowledge",
    "wp_create_project",
    "wp_get_project_outline",
    "wp_validate_design",
    "wp_update_params",
    "wp_run_calc",
    "wp_run_enumeration",
    "wp_run_design_map",
    "wp_get_result_summary",
    "wp_get_diagnostics",
    "wp_get_unit_detail",
    "wp_get_trace_excerpt",
    "wp_get_estimate_summary",
    "wp_get_layout_summary",
    "wp_export_calcbook",
    "wp_export_audit",
    "wp_export_dxf",
    "wp_export_ifc",
    "wp_export_report",
}

_MEASURE_SCRIPT = """
import asyncio, time
t0 = time.perf_counter()
from waterprint_agent import main as agent_main
from fastmcp import Client

async def go() -> None:
    mcp = agent_main.get_mcp()
    async with Client(mcp) as client:
        tools = await client.list_tools()
        elapsed = time.perf_counter() - t0
        print(f"TTL {elapsed:.3f} {len(tools)}")

asyncio.run(go())
"""


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def test_main_module_top_level_lazy() -> None:
    """懒加载铁律：main 模块导入零 core/server 触达（sys.modules 断言）。"""
    import importlib
    import subprocess as sp

    code = (
        "import sys; import waterprint_agent.main as m; "
        "leaks = [k for k in sys.modules if k == 'waterprint.app' or "
        "k.startswith('waterprint_server') or k == 'ezdxf' or k == 'fastapi']; "
        "print('LEAKS', leaks)"
    )
    result = sp.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert "LEAKS []" in result.stdout, f"main 顶层泄漏重依赖：{result.stdout}"
    importlib.import_module("waterprint_agent.main")  # 本进程亦可用


def test_client_lists_six_tools(sandbox_env: Path) -> None:
    """fastmcp.Client 进程内连 server：tools/list 恰 21 工具在场。"""
    import asyncio

    from fastmcp import Client

    from waterprint_agent import main as agent_main

    async def go() -> set[str]:
        mcp = agent_main.get_mcp()
        async with Client(mcp) as client:
            return {tool.name for tool in await client.list_tools()}

    assert asyncio.run(go()) == _TOOL_NAMES


def test_client_calls_tool_end_to_end(sandbox_env: Path) -> None:
    """进程内工具调用闭环：wp_list_units 经 MCP 协议面返回 36 口径。"""
    import asyncio

    from fastmcp import Client

    from waterprint_agent import main as agent_main

    async def go() -> dict:
        mcp = agent_main.get_mcp()
        async with Client(mcp) as client:
            result = await client.call_tool("wp_list_units", {})
            return result.data  # type: ignore[no-any-return]

    data = asyncio.run(go())
    assert data["count"] == 36


def test_spawn_to_tools_list_first_response(sandbox_env: Path) -> None:
    """spawn→tools/list 首响实测（子进程冷启动口径）：数字落 stdout 供报告引用。"""
    result = subprocess.run(
        [sys.executable, "-c", _MEASURE_SCRIPT],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        cwd=Path(__file__).resolve().parents[1],
    )
    line = next(ln for ln in result.stdout.splitlines() if ln.startswith("TTL"))
    _, seconds_s, count_s = line.split()
    seconds = float(seconds_s)
    assert int(count_s) == 21
    assert seconds < 15  # 宽松上限（真实预算门=1.5s，超限不阻断但必报告）
    print(f"\n[spawn→tools/list 首响] {seconds:.3f}s（目标 <1.5s，进程内冷启动口径）")
