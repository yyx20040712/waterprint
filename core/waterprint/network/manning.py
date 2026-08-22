"""曼宁水力计算（充满度分档）：圆管非满流的速度/坡度/充满度关系。

输入:  管断面（管径/粗糙系数）+ 设计流量
输出:  流速/水力坡度/充满度（全部经公式注册表求值，挂条文溯源）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/network/test_manning.py）
#
# 【公开接口】
#   manning_velocity(diameter, slope, roughness) -> float   满流流速
#   partial_flow(diameter, slope, roughness,
#                depth_ratio) -> PartialFlowResult          非满流分档
#   class PartialFlowResult：velocity、flow、depth_ratio、area、
#       wetted_perimeter、hydraulic_radius
#   solve_depth(diameter, slope, roughness, flow) -> float
#       已知流量反解充满度（数值求根，容差来自 assumptions）
#
# 【行为规格】
#   R1 充满度分档：圆管非满流水力特性按充满度表/公式分档计算
#      （分档数据与公式条文出处由实现期领域专家核定后登记公式
#      注册表——禁止无出处公式）。
#   R2 粗糙系数（塑料管/混凝土管等）来自 coefficients 数据包
#      （带出处），零代码常量。
#   R3 物理不变量（性质测试）：充满度 ∈ (0,1]、流速 > 0、
#      非满流最大流量出现在充满度约 0.94 附近（教科书结论作为
#      性质断言的容差带，出处入 assumptions/coefficients）。
#   R4 单调性（性质测试）：同断面流速随坡度单调增；
#      同坡度流量随管径单调增。
#   R5 迭代求根（solve_depth）：容差/最大迭代来自 assumptions；
#      不收敛抛领域异常（复用 loop 思想但不 import graph——独立域）。
#
# 【测试要求】满流基准数值（golden，来源 docs/norms 手算对照）、
#   非满流分档查表正确、性质四条、求根收敛与不收敛路径。
#
# 【参照】重写计划 §13.3 管网行/§14.3 独立域
# ══════════════════════════════════════════════════════════════════
