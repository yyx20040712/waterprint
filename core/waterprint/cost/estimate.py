"""概算汇总：分部分项 + 措施 + 间接 + 预备 + 税（计算全部在 Python，模板只展示）。

输入:  工程量清单（takeoff）+ PriceBook（单价）
输出:  概算表（分级汇总结构，含每一笔的单价×数量可追溯记录）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_estimate.py）
#
# 【公开接口】
#   build_estimate(quantities, price_book,
#                  fee_config) -> EstimateSheet
#   class EstimateSheet(不可变)：
#       detail_rows（分部分项：价 = 量 × 单价，逐笔挂 price_key 与
#                    source_field_ids）
#       measure / indirect / reserve / tax：各级费用行（费率出处必填）
#       grand_total
#       repro（design_hash, engine_version, data_version 三元组）
#   class FeeRule：fee_key、rate、base（取费基数表达式 DSL）、source
#
# 【行为规格】
#   R1 费率是数据：措施/间接/预备/税率的取值与取费基数全部来自
#      fee_config（数据包，带出处）；代码零费率常量。
#   R2 计算在 Python 单点完成（§11 R12）：Excel 输出只是渲染——
#      模板禁止 Excel 公式，渲染器见 trace/calcbook.py。
#   R3 汇总可复算：grand_total = f(工程量, 单价, 费率)，确定性；
#      同输入双跑字节级相同；结果挂三元组。
#   R4 工况标注：概算基于哪个 condition_key 的工程量必须显式
#      （默认基线 design 档；检修工况变化量由用户选择后单独出表）。
#
# 【测试要求】分级汇总数字自洽（明细求和=小计、小计+费用=总价）、
#   费率缺出处拒绝、双跑确定性、三元组记录。
#
# 【参照】重写计划 §11 R12/§13.3/§16 A8
# ══════════════════════════════════════════════════════════════════
