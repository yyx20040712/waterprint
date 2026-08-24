"""L1 注册表包根：元数据唯一真源（公式/维度/假设/系数四类注册表的聚合正门）。

输入:  各注册表声明的登记项、data/ 数据包
输出:  四注册表（formulas/dimensions/assumptions/coefficients）公开面的
       聚合正门（__all__ 显式枚举）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；ARCH1 D3 聚合落笔 2026-08-24，消"空正门+白名单漂移"；
# T5 D7 扩展聚合 assumptions/coefficients 2026-08-24——四注册表全部激活）
#
# 【铁律】L1 只依赖 L0 contracts；四类注册表彼此独立、互不 import
#   （一个文件一个注册表，§13.2）。
#
# 【导出白名单】包根聚合已实现四注册表的全部公开面（符号=各文件规格头
#   【公开接口】；__all__ 显式枚举——contracts/__init__.py 同款先例，
#   mypy no-implicit-reexport 与 ruff F401 经 __all__ 认可）：
#   formulas:     FormulaSpec, InvalidFormulaError, ValidationReport,
#                 register, by_id, validate_all, apply
#   dimensions:   FieldSpec, InvalidDimensionError, register_dimension,
#                 dimension_of, dtype_of
#   assumptions:  Assumption, AssumptionSet, DEFAULT_ASSUMPTIONS,
#                 assumption, InvalidAssumptionError, TuningImpact
#                 （TuningImpact 为构造面公开——Assumption 六字段之一）
#   coefficients: Coefficients, CoefficientValue, load_coefficients,
#                 InvalidCoefficientError（data_version 经 Coefficients
#                 属性透出不单列；get/keys/require_keys 为 Coefficients
#                 方法同不单列）
#   白名单外新导出必须先更新 docs/file-contracts.md。
# ══════════════════════════════════════════════════════════════════

from waterprint.registry.assumptions import (
    DEFAULT_ASSUMPTIONS,
    Assumption,
    AssumptionSet,
    InvalidAssumptionError,
    TuningImpact,
    assumption,
)
from waterprint.registry.coefficients import (
    Coefficients,
    CoefficientValue,
    InvalidCoefficientError,
    load_coefficients,
)
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
    "DEFAULT_ASSUMPTIONS",
    "Assumption",
    "AssumptionSet",
    "CoefficientValue",
    "Coefficients",
    "FieldSpec",
    "FormulaSpec",
    "InvalidAssumptionError",
    "InvalidCoefficientError",
    "InvalidDimensionError",
    "InvalidFormulaError",
    "TuningImpact",
    "ValidationReport",
    "apply",
    "assumption",
    "by_id",
    "dimension_of",
    "dtype_of",
    "load_coefficients",
    "register",
    "register_dimension",
    "validate_all",
]
