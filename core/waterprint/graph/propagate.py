"""水量水质沿边传播 + 汇流加权混合（纯函数；工况语义的正确性住所）。

输入:  上游单元结果 + 边（含 recycle 标记）+ 当前工况
输出:  下游单元的 UnitContext 输入（inflows/inqualities）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/graph/test_propagate.py +
# 性质测试 properties_propagate.py）
#
# 【公开接口】
#   mix(qualities: Sequence[WaterQuality],
#       weights: Sequence[float]) -> WaterQuality
#       汇流加权混合：负荷加权（ΣCi·Qi / ΣQi），非浓度简单平均
#   propagate(upstream_results, edges, condition) -> Mapping[PortRef→量]
#       组装下游输入快照
#
# 【行为规格】
#   R1 汇流加权使用**当前工况流量**：design 工况用 q_design、avg 工况用
#      q_avg_daily——修正旧系统固定按 Q_design 加权的语义错误（§14.2，
#      本条语义必须写进实现 docstring 并被测试锁定）。
#   R2 Kz 取 max：多股进水汇流时，下游 WaterFlow 的 Kz 取各股最大值
#      （保守语义，§14.2 明示）。
#   R3 质量守恒（性质测试常驻）：混合后各指标负荷 ΣCi·Qi 守恒
#      （数值容差内）；混合出水各指标浓度必介于各股浓度 min/max 之间。
#   R4 WATER 与 SLUDGE 独立通道：水质混合只作用于 WATER 边；SLUDGE 边
#      走 sludge.mix（DS 求和守恒）。类型串混 = 领域异常。
#   R5 recycle 边在迭代期传播"上一次迭代的估计值"（由 loop.py 驱动），
#      本文件不感知迭代状态——纯函数边界。
#
# 【测试要求】两档工况加权差异断言（design≠avg 加权结果）、Kz=max、
#   守恒与 min/max 夹逼、通道类型隔离；性质：随机两股混合守恒（hypothesis）。
#
# 【参照】重写计划 §14.2/§14.1；ADR-005/ADR-007
# ══════════════════════════════════════════════════════════════════
