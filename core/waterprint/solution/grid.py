"""自由参数离散网格：manifest 离散配置 → 参数矩阵（向量化枚举的输入形态）。

输入:  单元 manifest 的 ParamSpec 离散网格声明（值域/步长/枚举值）
输出:  参数矩阵（numpy 结构化数组，dtype 由 dimensions 注册表生成）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_grid.py）
#
# 【公开接口】
#   build_grid(param_specs: Sequence[ParamSpec]) -> Grid
#   class Grid：fields（字段序）、array（结构化数组：笛卡尔积展平）、
#       shape（各维取值数）、total（总组合数 = 各维乘积）
#
# 【行为规格】
#   R1 组合数护栏：total > 4^k 上限（默认上限来自 assumptions，出处入库）
#      → 抛 GridTooLarge（附建议：缩小某维步长/范围）——§12.4
#      "自由参数网格 ≤4^k" 的机器强制。
#   R2 网格确定性：同 manifest 同 Grid（字段序按 field_id 字典序稳定）。
#   R3 网格值只来自 manifest 声明（枚举值或起止步长生成）；
#      代码不注入任何隐含取值。
#   R4 结构化数组 dtype 经 dimensions.dtype_of 生成——单位作为元数据
#      在注册表，数组内是规范单位裸值（§11 R1，pint 不进热路径）。
#
# 【测试要求】笛卡尔积正确、字典序稳定性、超限抛 GridTooLarge、
#   dtype 字段与 manifest 一致。
#
# 【参照】重写计划 §12.4；ADR-005
# ══════════════════════════════════════════════════════════════════
