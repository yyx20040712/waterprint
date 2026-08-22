"""定额单价加载与版本管理：YAML 数据包 → 不可变单价库（版本 = 三元组成员）。

输入:  data/unit_prices/*.yaml（每条带出处与版本）
输出:  PriceBook 查询对象 + price_data_version
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_prices.py）
#
# 【公开接口】
#   class PriceBook(不可变)：data_version、get(price_key) -> PriceItem、
#       keys(prefix) 列举（按章节/定额编号分组）
#   load_prices(path) -> PriceBook        加载正门（严格校验）
#   class PriceItem：price、unit、source（定额编号+出处，如 2019 黑龙江
#      建筑工程计价定额子目号）、note
#
# 【行为规格】
#   R1 数据驱动迁移：旧 src/models/cost/unit_prices.py 的单价迁移为
#      YAML，每条带出处；迁移时人工抽验 10%（§5 迁移清单——抽验流程
#      归 M0 数据整理，代码侧保证：无 source 条目加载即失败）。
#   R2 price_data_version 进入可复算三元组（data_version 聚合系数包与
#      单价包版本，三元组任一变化 = 概算结果过期，§16 A8）。
#   R3 takeoff 的 price_key 必须可解析：失联键 = 启动失败（静态校验，
#      与 coefficients 同门槛）。
#   R4 单价只读：不提供写入 API（数据维护走版本化发布流程）。
#
# 【测试要求】加载往返、失联键拒绝、无 source 拒绝、版本传播进三元组。
#
# 【参照】重写计划 §5/§16 A8；数据规格 data/unit_prices/README.md
# ══════════════════════════════════════════════════════════════════
