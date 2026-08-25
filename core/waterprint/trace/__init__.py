"""L4 审计包根：计算迹收集、溯源审计报告、Excel 计算书渲染。

输入:  执行过程（公式应用记录）+ PlantResult
输出:  迹树（collector 正门）；HTML 审计报告 / xlsx 计算书（下游）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1b 实现 collector/calcbook 2026-08-25；audit 骨架留 M4）
#
# 【导出白名单】
#   collector: TraceCollector, TraceTree, collect, InvalidTraceError
#   calcbook:  render_calcbook, TEMPLATE_REGISTRY, InvalidTemplateError
#   audit:     render_audit_html（M4 批实现，本批不导出）
# 【铁律】审计链路完整 = 任一输出数字可回溯条文与输入（M4 验收）；
#   calcbook 模板驱动（模板禁公式，§11 R12）。
# ══════════════════════════════════════════════════════════════════

from waterprint.trace.collector import (
    InvalidTraceError,
    TraceCollector,
    TraceTree,
    collect,
)

__all__ = [
    "InvalidTraceError",
    "TraceCollector",
    "TraceTree",
    "collect",
]
