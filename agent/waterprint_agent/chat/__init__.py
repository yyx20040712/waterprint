"""chat 编排面（B4-4b AI 集成深化段子批 1）——环/会话/LLM/清单/回退/提示。

输入:  AgentContext+用户文本+ChatConfig（三中性键 env）
输出:  run_turn/single_shot（编排环入口）+sessions 会话面再导出
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/__init__.py
#   职责：编排面包门面——环入口（loop.run_turn/single_shot）+会话面
#       （sessions.*）再导出；顶层零 core/server/fastmcp import
#       （懒加载铁律——与 main.py 同构，测试断言 sys.modules 干净）。
#   禁区：禁在本层加逻辑（纯门面）；禁 MCP 注册（chat 非 MCP 工具，
#       面向 CLI/webapp 中继）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

__all__ = ["loop", "run_turn", "sessions", "single_shot"]


def __getattr__(name: str):  # PEP 562：懒导出（顶层零重依赖）
    if name in {"run_turn", "single_shot"}:
        from waterprint_agent.chat import loop

        return getattr(loop, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
