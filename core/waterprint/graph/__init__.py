"""L3 图引擎包根：DAG + 回路迭代收敛，工况逐图计算。

输入:  项目 design 态图（节点/边）+ 工况集
输出:  按工况索引的全厂结果（executor 正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【导出白名单】
#   topo:       topological_layers, strongly_connected_components
#   propagate:  mix, propagate
#   loop:       solve_loop, LoopDivergence
#   executor:   execute_graph
#   incremental: recompute_scope
# 装配约束：executor 只依赖 contracts.unit_api 协议，具体单元由 L4 app.py
# 注入（import-linter "装配点唯一"契约强制）。
# ══════════════════════════════════════════════════════════════════
