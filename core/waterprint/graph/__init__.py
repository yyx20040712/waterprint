"""L3 图引擎包根：DAG + 回路迭代收敛，工况逐图计算。

输入:  项目 design 态图（节点/边）+ 工况集
输出:  按工况索引的全厂结果（executor 正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T6 D6 聚合落笔 2026-08-24；registry/__init__ 同款先例）
#
# 【导出白名单】包根聚合已实现模块的全部公开面（符号=各文件规格头
#   【公开接口】/file-contracts 输出列；__all__ 显式枚举——mypy
#   no-implicit-reexport 与 ruff F401 经 __all__ 认可）：
#   topo:       topological_layers, strongly_connected_components,
#               split_graph（T6 实现）
#   propagate:  mix, propagate, InvalidPropagationError（T6 实现）
#   loop:       solve_loop, LoopDivergence（待 T7——骨架，暂不聚合）
#   executor:   execute_graph（待 T7——骨架，暂不聚合）
#   incremental: recompute_scope（待 T7——骨架，暂不聚合）
#   白名单外新导出必须先更新 docs/file-contracts.md。
#
# 装配约束：executor 只依赖 contracts.unit_api 协议，具体单元由 L4 app.py
# 注入（import-linter "装配点唯一"契约强制）。
# ══════════════════════════════════════════════════════════════════

from waterprint.graph.propagate import InvalidPropagationError, mix, propagate
from waterprint.graph.topo import (
    split_graph,
    strongly_connected_components,
    topological_layers,
)

__all__ = [
    "InvalidPropagationError",
    "mix",
    "propagate",
    "split_graph",
    "strongly_connected_components",
    "topological_layers",
]
