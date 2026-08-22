"""管径枚举/并联/跌水井判定：管段序列的下游衔接设计。

输入:  管段模型序列（excel_io 读入：流量/长度/起终点地面标高…）
输出:  设计结果（各段管径/坡度/充满度/井底标高 + 跌水井与并联判定）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/network/test_solver.py）
#
# 【公开接口】
#   design_pipes(segments: Sequence[PipeSegment],
#                options: DesignOptions) -> NetworkDesign
#   class PipeSegment：segment_id、design_flow、length、
#       ground_start / ground_end（地面标高）、upstream_invert
#   class DesignOptions：available_diameters（可选管径序列——数据，
#      来自 coefficients/assumptions）、max_depth、min_velocity、
#      max_velocity（约束值全部带出处）
#   class NetworkDesign：各段 {diameter, slope, velocity, depth_ratio,
#       invert_start, invert_end}、drop_wells（跌水井位与跌差）、
#       parallel（并联管段组）、warnings
#
# 【行为规格】
#   R1 管径枚举：按可选管径序列自小到大试算，首个满足流速/充满度/
#      埋深约束的组合入选（枚举语义显式、确定性——同输入同设计）。
#   R2 衔接规则：下游管底 <= 上游管底（管底衔接）；覆土/埋深不足或
#      超深 → 跌水井判定（跌差进结果，警示标注）；坡度异常段
#      （过陡/倒坡）生成 Warning。
#   R3 并联判定：单管不满足（充满度超限）→ 并联双管方案（同沟敷设
#      水力等效拆分），并联组标注（用户可否决）。
#   R4 约束是数据：流速/埋深/覆土限值来自 options/coefficients，
#      零代码常量（§3 保证 7 精神延伸到管网域）。
#   R5 无解段（任何管径都不满足）→ 显式失败段 + 原因（最小冲突
#      语义：列出违反的约束），禁止静默选最接近的。
#
# 【测试要求】已知三段管线 golden 设计（docs/norms 手算对照）、
#   跌水井触发/不触发、并联触发、无解段原因完整、确定性。
#
# 【参照】重写计划 §13.3 管网行/§14.3
# ══════════════════════════════════════════════════════════════════
