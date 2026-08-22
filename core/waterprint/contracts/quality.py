"""水质契约 + 出水标准库（标准是数据不是分支，一级A/III类各一条数据）。

输入:  6 项常规指标值（规范单位 mg/L）+ 标准名（如 "GB18918-2002-1A"）
输出:  WaterQuality、EffluentStandard、达标裕度 margin
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_quality.py）
#
# 【公开接口】
#   INDICATORS: 常规六指标字段 ID（冻结）：BOD5 / CODCR / SS / NH3N / TN / TP
#   class WaterQuality(不可变)：按字段 ID 存浓度（mg/L 裸值），
#       支持缺项（None）——缺项在传播中按"不参与混合"处理并记录警告
#   class EffluentStandard(不可变)：standard_id、名称、限值 dict[字段ID→float]
#   STANDARDS: 出水标准库（数据驱动加载自 data/coefficients，构造时注入）
#   margin(value: float, standard: EffluentStandard, indicator: str) -> float
#       裕度 = (限值 − 计算值) / 限值；>=0 达标，负值即超限幅度
#
# 【行为规格】
#   R1 双水线标准差异 = 库里两条数据（市政一级A / 矿井水 III类），
#      代码中禁止出现 if 标准名 的分支（§14.2，病灶"标准硬编码分支"）。
#   R2 浓度非负；负值构造抛 InvalidQualityError。
#   R3 标准库加载失败/标准 ID 未知 → 领域异常，禁止回退默认标准。
#   R4 指标集合开放：六指标为最小冻结集，新增指标走 dimensions 注册表 +
#      标准库数据同步，不改本契约代码。
#
# 【测试要求】裕度符号语义、数据驱动（同库不同标准结果不同而代码路径相同）、
#   负浓度拒绝、缺项语义。
#
# 【参照】重写计划 §3-4/§14.2；数据包 data/coefficients/README.md
# ══════════════════════════════════════════════════════════════════
