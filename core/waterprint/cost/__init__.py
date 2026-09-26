"""L3 概算子系统包根：工程量/单价/汇总/校核（按字段 ID 取数，非中文名）。

输入:  PlantResult（结果契约）+ data/unit_prices 数据包
输出:  概算表（estimate 正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【导出白名单】
#   takeoff:    takeoff_quantities, load_field_mapping
#   prices:     load_prices
#   estimate:   build_estimate, load_fee_rules
#   indicators: check_indicators
#   批2b 2026-09-25 增：solution.joint_enumeration.final_eval capex 装配束
#   经包根消费（五函数+PriceBook/FeeRule/FieldMapping 三类型——同层边
#   import 收敛面，structure-graph §1c 声明承载）
#   批6c 2026-09-26 增：EstimateSheet 类型再导出（四类型——final_eval
#   capex_annualized 消费 equipment_subtotal/grand_total 分级，§1c 既定边内）
# 病灶背景：旧概算 4 级中文模糊匹配、80+ 关键词表、361 条影子标签——
# 本子系统的一切取数按字段 ID（§3 保证 4），中文匹配代码出现 = 评审拒绝。
# ══════════════════════════════════════════════════════════════════

from waterprint.cost.estimate import (
    EstimateSheet,
    FeeRule,
    build_estimate,
    load_fee_rules,
)
from waterprint.cost.prices import PriceBook, load_prices
from waterprint.cost.takeoff import (
    FieldMapping,
    load_field_mapping,
    takeoff_quantities,
)

__all__ = [
    "EstimateSheet",
    "FeeRule",
    "FieldMapping",
    "PriceBook",
    "build_estimate",
    "load_fee_rules",
    "load_field_mapping",
    "load_prices",
    "takeoff_quantities",
]
