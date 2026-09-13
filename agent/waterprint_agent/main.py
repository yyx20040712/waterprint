"""MCP server 入口（D1）：FastMCP 懒加载装配+stdio 运行（console: waterprint-mcp）。

输入:  MCP 客户端（ZCode 等）stdio 挂载；env WATERPRINT_AI_SANDBOX 定沙箱
输出:  21 工具（知识组 #1~#3+项目编辑组 #4~#7+计算组 #8~#10+结果组
       #11~#16+导出组 #17~#21）——spawn→tools/list 目标 <1.5s
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13；AI1-INTEG-2026-09-13 扩至 21 工具）
#   路径：agent/waterprint_agent/main.py
#   职责：FastMCP 实例懒加载装配（get_mcp 单例）+入口 main()（读 env
#       定沙箱→init_workspace→mcp.run() stdio）。
#   禁区：模块顶层零 core/server/fastmcp 之外重依赖 import（懒加载铁律
#       ——本文件顶层只许 stdlib 与 waterprint_agent 纯 stdlib 子模块；
#       重依赖全部在工具函数体内首次调用时触发）。
#
# 【行为规格】
#   R1 懒加载：import waterprint_agent.main 后 sys.modules 零
#      waterprint.app/waterprint_server/ezdxf/fastapi 触达（测试断言）；
#      tools/list 只走 fastmcp 注册表（<1.5s 首响目标）。
#   R2 入口序：main()=sandbox_root()（env 覆盖）→init_workspace()（幂等
#      建树）→get_mcp()→mcp.run()（默认 stdio transport——fastmcp 3.0
#      run() 无参即 stdio）。
#   R3 工具装配：knowledge/projects/calc/results/exports 五组 register
#      （权威表 #1~#21——签名冻结，技能文档按此写；全部经 context.
#      run_tool 包装=会话日志自动记账）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from waterprint_agent import sandbox
from waterprint_agent.tools import calc, exports, knowledge, projects, results

__all__ = ["get_mcp", "main"]

_INSTRUCTIONS = (
    "WaterPrint 污水处理工艺设计 MCP 服务：先用 wp_list_units/wp_get_unit_manifest/"
    "wp_query_knowledge 查单元与知识，wp_create_project 建项目（blank 或 golden 四"
    "种子），wp_get_project_outline 看摘要，wp_validate_design 结构校验，"
    "wp_update_params 批量改参（清单式部分接受），wp_run_calc 全厂计算，"
    "wp_get_result_summary/wp_get_diagnostics 读结果与诊断迭代，"
    "wp_get_unit_detail/wp_get_trace_excerpt/wp_get_estimate_summary/"
    "wp_get_layout_summary 按需回取，导出走 wp_export_* 五件套"
    "（calcbook/audit/dxf/ifc/report）。AI 只编排不算数（ADR-019）。"
)

_MCP: object | None = None  # FastMCP 实例（类型不顶层导入——懒加载）


def get_mcp() -> object:
    """FastMCP 懒加载单例（首次调用装配 21 工具——仅 import fastmcp）。"""
    global _MCP  # noqa: PLW0603
    if _MCP is None:
        from fastmcp import FastMCP

        mcp = FastMCP(name="waterprint-agent", instructions=_INSTRUCTIONS)
        knowledge.register(mcp)
        projects.register(mcp)
        calc.register(mcp)
        results.register(mcp)
        exports.register(mcp)
        _MCP = mcp
    return _MCP


def main() -> None:
    """console 入口（waterprint-mcp）：定沙箱→建树→stdio 运行。"""
    sandbox.init_workspace()  # 读 env WATERPRINT_AI_SANDBOX 定根（幂等建树）
    mcp = get_mcp()
    mcp.run()  # type: ignore[attr-defined]  # 默认 transport=stdio（fastmcp 3.0 实证）
