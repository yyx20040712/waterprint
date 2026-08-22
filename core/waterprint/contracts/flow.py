"""水量契约与构造校验（消除 Q_design/Q_avg 双轨的病灶根除点）。

输入:  带单位的日平均流量、总变化系数 Kz（来自边界层，规范单位由 quantity 保证）
输出:  WaterFlow（规范单位：Q_avg_daily 与派生 Q_design，m3/s）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_flow.py）
#
# 【公开接口】
#   class WaterFlow(不可变)：
#       q_avg_daily: float        平均日流量，规范单位 m3/s（唯一输入源）
#       kz: float                 总变化系数（最高日最高时 / 平均日平均时）
#       q_design: float           派生属性 = q_avg_daily * kz，禁止独立赋值
#   make_flow(q_avg_daily: Quantity, kz: float) -> WaterFlow
#       唯一构造正门（经 quantity.parse 完成单位换算与量纲校验）
#
# 【行为规格】
#   R1 q_design 是派生量：属性而非输入字段——同对象上双轨不可能存在（病灶
#      "Q_design/Q_avg 双轨"的架构级根除，§3 保证 2）。
#   R2 构造校验：q_avg_daily > 0、kz >= 1；违反抛 InvalidFlowError（领域异常）。
#   R3 Kz 的行业上下限校验属于 constraint_kb 数据（约束），不属于本契约；
#      契约只守数学不变量。
#   R4 m3/d 等外部单位输入必须在 make_flow 内经 quantity.parse 换算，
#      WaterFlow 内部永远是规范单位 m3/s 裸值。
#   R5 工况关联：flow_case=design 用 q_design、avg 用 q_avg_daily
#      （ADR-007；分支发生在图引擎/单元映射，不在本契约）。
#
# 【测试要求】双轨消除断言（q_design 派生只读）、非法构造拒绝、
#   34760 m3/d == 34760/86400 m3/s 换算、kz=1 合法。
#
# 【参照】重写计划 §3-2/§14.1；ADR-002/ADR-007
# ══════════════════════════════════════════════════════════════════
