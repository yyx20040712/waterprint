"""test_chat_toolspec——工具清单：21 工具 schema+dispatch（经 run_tool 记账）。

输入:  tmp_path 沙箱+清单表
输出:  覆盖计数/唯一性/schema 形态/分发冒烟/未知工具拒绝
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.chat import toolspec


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


def test_schema_covers_23_unique() -> None:
    """清单恰 23 工具（MCP 面同源——B4-4b 子批 3 扩 #22/#23）；名字唯一。"""
    schema = toolspec.tools_schema()
    names = [entry["function"]["name"] for entry in schema]
    assert len(names) == 23
    assert len(set(names)) == 23
    for entry in schema:
        assert entry["type"] == "function"
        assert entry["function"]["description"]
        assert isinstance(entry["function"]["parameters"], dict)


def test_dispatch_list_units_smoke(sandbox_env: Path) -> None:
    """分发冒烟：wp_list_units 经 run_tool 正常返回单元目录。"""
    ctx = context.get_context()
    result = toolspec.dispatch(ctx, "wp_list_units", {})
    assert "error" not in result
    assert result["count"] > 0


def test_dispatch_unknown_tool(sandbox_env: Path) -> None:
    """未知工具：错误 dict（不 raise）+hint。"""
    ctx = context.get_context()
    result = toolspec.dispatch(ctx, "wp_no_such_tool", {})
    assert "error" in result and "hint" in result
