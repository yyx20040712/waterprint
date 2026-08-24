"""L1 注册表包根：元数据唯一真源（公式/维度/假设/系数四类注册表的聚合正门）。

输入:  各注册表声明的登记项、data/ 数据包
输出:  注册表查询 API 与启动期静态校验结果
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【铁律】L1 只依赖 L0 contracts；四类注册表彼此独立、互不 import
#   （一个文件一个注册表，§13.2）。
#
# 【导出白名单】（T4 D10 校准至四注册表实际公开面）
#   formulas:     FormulaSpec, InvalidFormulaError, ValidationReport,
#                 register, by_id, validate_all, apply
#   dimensions:   FieldSpec, InvalidDimensionError, register_dimension,
#                 dimension_of, dtype_of
#   assumptions:  AssumptionSet, DEFAULT_ASSUMPTIONS, assumption
#   coefficients: load_coefficients, Coefficients
# 白名单外新导出必须先更新 docs/file-contracts.md。
# ══════════════════════════════════════════════════════════════════
