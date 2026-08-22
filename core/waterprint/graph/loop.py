"""回路固定点迭代：阻尼/容差/发散诊断（污泥回流、内回流的求解器）。

输入:  回路组（SCC）+ compute 回调（由 executor 提供）+ 迭代参数
输出:  收敛结果或 LoopDivergence 诊断（含迭代历史）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/graph/test_loop.py）
#
# 【公开接口】
#   class LoopDivergence(Exception)：
#       loop_nodes、iterations、history（最近若干步残差）——
#       供 UI 给出"用户拆环"建议（ADR-003）
#   class LoopConfig(不可变)：tolerance（默认来自 assumptions，带出处）、
#       max_iterations、damping（阻尼系数 0<ω<=1）
#   solve_loop(loop_group, compute, init_guess, config) -> 收敛解
#       固定点迭代：x_{n+1} = x_n + ω·(F(x_n) − x_n)
#
# 【行为规格】
#   R1 收敛判据：全部回路变量相对残差 < tolerance；达到即返回。
#   R2 发散/不收敛：超过 max_iterations 仍不收敛 → 抛 LoopDivergence
#      （禁止静默返回最后一次迭代值——那是最危险的谎言）；诊断信息
#      必须足以定位是哪个回路、震不震荡。
#   R3 阻尼默认开启（ω 来自 assumptions，出处入库）；高回流比震荡场景
#      依赖阻尼收敛（§16 A2 残余风险：个别拓扑需人工拆环，UI 提示）。
#   R4 迭代历史进计算迹：每次迭代记录残差（审计可见收敛过程）。
#   R5 纯函数语义：同输入同收敛路径（确定性，禁随机初始化；
#      init_guess 由调用方确定性地提供）。
#   R6 远期：Broyden/Anderson 加速作为可替换策略注入，接口不变（§16 A2）。
#
# 【测试要求】已知线性回路收敛到解析解、发散回路抛 LoopDivergence
#   且 history 非空、阻尼=1 与阻尼<1 的迭代步数对比、
#   确定性（同输入双跑迭代路径相同）。
#
# 【参照】重写计划 §3-3/§8 风险行/§16 A2；ADR-003
# ══════════════════════════════════════════════════════════════════
