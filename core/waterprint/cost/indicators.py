"""单位造价指标合理性校核：概算结果 ↔ 行业经验指标带的对照（警告而非否决）。

输入:  EstimateSheet + 指标数据（单位水量投资 元/(m3·d−1) 等经验带）
输出:  指标对照结果（在带内/偏离 + 警告）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_indicators.py）
#
# 【公开接口】
#   check_indicators(estimate: EstimateSheet,
#                    indicators: IndicatorBand) -> IndicatorReport
#   class IndicatorBand(不可变)：indicator_key、formula DSL（如
#      grand_total / 设计规模）、band（下限, 上限）、source（经验出处）
#   class IndicatorReport：每项 {value, band, status: OK|WARN, reason}
#
# 【行为规格】
#   R1 指标带是数据：经验区间全部来自 data/coefficients 指标条目
#      （带出处），代码零经验数字。
#   R2 语义定位：校核结果是 Warning 不是 Error——偏离不阻塞交付，
#      但必须在 UI 诊断面板与计算书中可见（§19.3 反馈通道）。
#   R3 指标值计算经公式注册表（可溯源），规模取设计规模字段 ID
#      （q_avg_daily 换算 m3/d 仅在显示层发生）。
#   R4 无可算指标（数据包缺该工程类型条目）→ 显式"未校核"状态，
#      禁止静默通过。
#
# 【测试要求】带内 OK / 越带 WARN、缺指标显式未校核、指标值公式溯源。
#
# 【参照】重写计划 §13.3 职责表
# ══════════════════════════════════════════════════════════════════
