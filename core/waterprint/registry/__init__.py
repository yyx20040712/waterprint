"""L1 注册表包根：元数据唯一真源（公式/维度/假设/系数四类注册表的聚合正门）。

输入:  各注册表声明的登记项、data/ 数据包
输出:  已实现注册表（formulas/dimensions）公开面的聚合正门（__all__ 显式枚举）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；ARCH1 D3 聚合落笔 2026-08-24，消"空正门+白名单漂移"）
#
# 【铁律】L1 只依赖 L0 contracts；四类注册表彼此独立、互不 import
#   （一个文件一个注册表，§13.2）。
#
# 【导出白名单】包根聚合已实现两注册表的全部公开面（符号=各文件规格头
#   【公开接口】；__all__ 显式枚举——contracts/__init__.py 同款先例，
#   mypy no-implicit-reexport 与 ruff F401 经 __all__ 认可）：
#   formulas:     FormulaSpec, InvalidFormulaError, ValidationReport,
#                 register, by_id, validate_all, apply
#   dimensions:   FieldSpec, InvalidDimensionError, register_dimension,
#                 dimension_of, dtype_of
#   待聚合（骨架，T5 实现后随公开面冻结再聚合）：
#   assumptions:  AssumptionSet, DEFAULT_ASSUMPTIONS, assumption（待 T5）
#   coefficients: load_coefficients, Coefficients（待 T5）
#   白名单外新导出必须先更新 docs/file-contracts.md。
# ══════════════════════════════════════════════════════════════════

from waterprint.registry.dimensions import (
    FieldSpec,
    InvalidDimensionError,
    dimension_of,
    dtype_of,
    register_dimension,
)
from waterprint.registry.formulas import (
    FormulaSpec,
    InvalidFormulaError,
    ValidationReport,
    apply,
    by_id,
    register,
    validate_all,
)

__all__ = [
    "FieldSpec",
    "FormulaSpec",
    "InvalidDimensionError",
    "InvalidFormulaError",
    "ValidationReport",
    "apply",
    "by_id",
    "dimension_of",
    "dtype_of",
    "register",
    "register_dimension",
    "validate_all",
]
