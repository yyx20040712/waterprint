"""L0 契约层包根：全系统共同语言，零内部依赖（只允许标准库与 pint）。

输入:  无
输出:  契约类型的对外白名单（跨包只走正门，见 AGENTS.md §1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【零依赖铁律】本包内文件禁止 import 任何其他内部层；quantity.py 是全库
#   唯一允许 import pint 的文件（import-linter 强制）。
#
# 【导出白名单】__all__ 必须显式枚举；实现时按下列子模块聚合：
#   quantity: Quantity, DimKey, InvalidUnitError, InvalidQuantityError
#   flow: WaterFlow
#   quality: WaterQuality, EffluentStandard, margin
#   sludge: SludgeFlow, mix
#   ports: Port, Edge, FluidKind, InvalidConnection
#   unit_api: UnitContext, UnitResult, Unit
#   manifest: UnitManifest
#   condition: OperatingCondition, ConditionSet, FlowCase
#   project_schema: ProjectFile, DesignState, ViewState
#   result_schema: PlantResult, TraceNode
# 白名单外的新导出名必须先更新 docs/file-contracts.md。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.quantity import (
    DimKey,
    InvalidQuantityError,
    InvalidUnitError,
    Quantity,
)

__all__ = [
    "DimKey",
    "InvalidQuantityError",
    "InvalidUnitError",
    "Quantity",
]
