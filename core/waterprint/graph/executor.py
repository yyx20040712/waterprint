"""图执行编排：工况 × 拓扑 × 传播 × 回路的总指挥（不认识任何具体单元）。

输入:  项目 design 图 + 单元注册表（manifest→Unit 实例，由 app.py 装配）+ 工况集
输出:  PlantResult（按 condition_key 索引，含计算迹与三元组）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/graph/test_executor.py）
#
# 【公开接口】
#   class UnitRegistry(Protocol)：unit_id → Unit 实例（按 manifest 装配，
#       由 L4 app.py 构建；executor 不 import units_lib）
#   execute_graph(design: DesignState, units: UnitRegistry,
#                 conditions: ConditionSet, env: RunEnv) -> PlantResult
#       唯一执行正门；RunEnv 携带 assumptions/coefficients/trace 收集器/
#       三元组（design_hash, engine_version, data_version）
#
# 【行为规格】
#   R1 逐工况整图计算：ConditionSet.iter_all() 每个工况独立完整执行，
#      结果按 condition_key 索引（§14.1）；工况间零共享可变状态。
#   R2 执行序：split_graph 分层 → 逐层（可并行）执行 → propagate 组装
#      下游输入 → SCC 回路组交 solve_loop；每单元 compute 经
#      manifest 工况映射先变换参数（n_active 等），compute 本体无工况分支。
#   R3 可复算：同 (design, conditions, env 三元组) 双跑结果字节级相同
#      （CI 常驻测试）；缓存不参与语义（incremental.py 只做等价优化）。
#   R4 计算迹完整：每单元每次 compute 的公式应用都进 trace；
#      PlantResult.trace 可逐条审计到条文（§3 保证 5）。
#   R5 单元异常隔离：单单元 compute 抛领域异常 → 整图该工况失败并携带
#      unit_id 上下文（禁止吞掉继续跑出半截结果）。
#   R6 内置图节点（市政输入/汇流/水质编辑节点）走 unit_api 协议的内置
#      实现（本包内提供，非 units_lib 单元包，§14.3 归属表）。
#
# 【测试要求】三单元线性图端到端（M1 切片形状）、工况集 2+k 全部有结果、
#   回路图经 loop 收敛、双跑 diff=0、单单元异常带 unit_id 上抛。
#
# 【参照】重写计划 §13.1 装配点/§14.1；ADR-003/ADR-007
# ══════════════════════════════════════════════════════════════════
