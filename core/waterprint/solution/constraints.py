"""布尔约束过滤（含 UI 覆盖）：可行方案子集与逐约束通过矩阵。

输入:  枚举 DataFrame + 约束集（constraint_kb 迁移 51 条 + UI 临时覆盖）
输出:  可行子集 + 每行×每约束的通过矩阵（供 diagnose）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_constraints.py）
#
# 【公开接口】
#   class Constraint(不可变)：key、表达式 DSL（受限比较式：
#      field_id 与常数的 </<=/>/>=/∈ 关系 + AND 组合）、
#      source（constraint_kb 键或 "ui:临时覆盖"）、severity
#   apply_constraints(df, constraints) -> FilterResult
#   class FilterResult：feasible（可行子集索引）、
#       pass_matrix（DataFrame 布尔矩阵，行=方案 列=约束）
#
# 【行为规格】
#   R1 约束是数据：知识库 51 条（旧 constraint_hints 迁移）+ UI 覆盖，
#      表达式走受限 DSL（白名单字段 ID 与运算符），禁止任意 Python
#      lambda 注入（安全与可序列化）。
#   R2 pass_matrix 必须完整产出（哪怕全 False）——diagnose 的输入，
#      禁止只返回可行集丢弃失败信息（否则无解诊断不可能）。
#   R3 UI 覆盖不落盘为代码：临时覆盖只在会话内（design 态可保存勾选，
#      表达式本体永远来自知识库数据）。
#   R4 约束求值向量化（numpy 布尔运算），万级行 <1s（§18.1 预算内）。
#
# 【测试要求】布尔矩阵正确性（含全 False 用例）、UI 覆盖生效与还原、
#   非法表达式（未知字段/运算符）拒绝、迁移知识库样例条目可用。
#
# 【参照】重写计划 §5/§12.4；数据包 data/constraint_kb/README.md
# ══════════════════════════════════════════════════════════════════
