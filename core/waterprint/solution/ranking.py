"""裕度/成本排序与截断：可行方案 → 有序结果（浏览器千行流畅浏览的后端半）。

输入:  FilterResult + 排序键（裕度/成本/自定义字段 ID）+ 截断上限
输出:  排序后的方案切片与排序元信息
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_ranking.py）
#
# 【公开接口】
#   rank(filter_result: FilterResult, df: DataFrame,
#        key: RankingKey, limit: int) -> RankedSolutions
#   class RankingKey(不可变)：sort_by（字段 ID 或 "margin_min"/"cost"）、
#       ascending、tie_break（稳定的次序键列表）
#   class RankedSolutions：rows（截断后的有序 DataFrame）、
#       total_feasible、truncated（bool）
#
# 【行为规格】
#   R1 排序确定性：tie_break 保证全序稳定（同输入同排序，可复算）；
#      禁止不稳定排序导致的方案行序漂移（UI 抖动与快照漂移源头）。
#   R2 裕度排序键 "margin_min"：全部达标裕度字段的最小值（最紧指标
#      优先）——语义固定并测试锁定；成本键依赖概算子系统注入的成本列，
#      列缺失时抛领域异常（禁止静默回退裕度排序）。
#   R3 截断显式：limit 由服务层传入（分页），RankedSolutions 标注
#      truncated 与 total_feasible——前端必须可见"还有 N 条"。
#   R4 排序/过滤在 DataFrame 层完成（pandas 天然支持，§2 选型理由），
#      禁止手写行级循环。
#
# 【测试要求】确定性（乱序输入同输出）、tie_break 稳定、截断标注、
#   成本列缺失抛异常、margin_min 语义。
#
# 【参照】重写计划 §2/§12.2；ADR-005
# ══════════════════════════════════════════════════════════════════
