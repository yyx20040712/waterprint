"""工程量提取：PlantResult 字段 ID → 分部分项工程量清单（零中文匹配）。

输入:  PlantResult（按 condition_key 索引的维度字段数组）
输出:  工程量清单（条目：定额项键 + 数量 + 单位，来自 dimensions 注册字段）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_takeoff.py）
#
# 【公开接口】
#   class TakeoffItem(不可变)：price_key（定额单价键）、quantity、
#       unit、source_field_ids（量来源于哪些结果字段——可审计）
#   takeoff_quantities(plant_result, condition_key) -> tuple[TakeoffItem, ...]
#
# 【行为规格】
#   R1 取数只按字段 ID：清单条目由"字段 ID → 定额项"映射表（数据，
#      data/unit_prices 侧配套）驱动；出现任何中文字符串匹配逻辑
#      = 评审拒绝（病灶根除点，§3 保证 4）。
#   R2 量纲正确：quantity 单位与 price_key 单价单位一致（混凝土 m3、
#      钢筋 t、土方 m3……）；不一致 = 提取错误即抛领域异常。
#   R3 source_field_ids 必填：每个量可回溯到结果字段与工况——审计链路
#      （M4"任一数字可回溯"）在概算侧的落点。
#   R4 按工况提取：condition_key 必填（检修工况的 n-1 池 → 工程量
#      不变还是变化由字段语义决定，但提取结果标注工况）。
#   R5 挖深联动（M3）：土方量消费 elevation.Profile 的实际埋深
#      （由 L4 app 装配传入，本文件不 import elevation——总线原则 §16 A4）。
#
# 【测试要求】字段 ID 映射正确、单位不匹配拒绝、source_field_ids 完整、
#   静态断言：源码无中文匹配 API 调用（如 str.find/in 判定）。
#
# 【参照】重写计划 §13.3/§16 A4；数据包 data/unit_prices/README.md
# ══════════════════════════════════════════════════════════════════
