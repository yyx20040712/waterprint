"""工况契约：flow_case 全局档 × pool 逐单元检修敏感性（ADR-007 冻结语义）。

输入:  工况轴取值（用户勾选的受检单元集合）
输出:  OperatingCondition / ConditionSet / condition_key（稳定可序列化）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_condition.py）
#
# 【公开接口】
#   class FlowCase(Enum)：design（最高日最高时）/ avg（平均时）
#   class OperatingCondition(不可变)：
#       flow_case: FlowCase
#       offline_unit: str | None    非空 = "该单元 n-1 池、其余全池"敏感性校核
#   class ConditionSet：
#       baseline: tuple[OperatingCondition, ...]        # 恒为 design/avg 两档
#       sensitivity: tuple[OperatingCondition, ...]     # 每个受检单元一条
#       def iter_all(self) -> Iterator[OperatingCondition]
#       def key(c: OperatingCondition) -> str           # 稳定键（序列化/索引）
#   build_condition_set(checked_units: Sequence[str]) -> ConditionSet
#
# 【行为规格】
#   R1 运行次数 = 2 + k（k=受检单元数），线性；禁止 2^n 全组合——
#      build_condition_set 输出条数断言进测试（ADR-007，§16 A3 曾有两版
#      矛盾表述，本文件是冻结后的唯一语义源）。
#   R2 condition_key 确定性：同工况同键；用于结果索引、缓存键、SSE 通道、
#      日志字段（§15 工程细节 2）。
#   R3 工况对参数的影响只经 manifest 工况映射（见 manifest.py R1c），
#      本契约只描述"跑哪些工况"，不描述"参数怎么变"。
#   R4 远期扩展轴（季节水温等）：只增 FlowCase 枚举值或新轴字段 + manifest
#      映射，不改引擎（开放封闭，§14.1）。
#   R5 汇流加权随工况：design 工况用 q_design、avg 用 q_avg_daily——
#      语义归属 propagate.py，本契约提供 flow_case 判别手段。
#
# 【测试要求】2+k 条数断言、key 确定性与唯一性、offline 语义字段、
#   空受检集合 = 仅基线两档。
#
# 【参照】重写计划 §14.1/§16 A3；ADR-007
# ══════════════════════════════════════════════════════════════════
