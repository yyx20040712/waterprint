"""L0 契约层包根：全系统共同语言，零内部依赖（只允许标准库与 pint）。

输入:  无
输出:  契约子模块公开面的聚合正门（__all__ 显式枚举，跨包只走正门，AGENTS §1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（ARCH1 D3 聚合落笔，2026-08-24；消"空正门+白名单漂移"）
#
# 【零依赖铁律】本包内文件禁止 import 任何其他内部层；quantity.py 是全库
#   唯一允许 import pint 的文件（import-linter 强制）。
#
# 【聚合口径】包根聚合 13 个已实现子模块中 12 个的公开面（符号=各子模块
#   规格头【公开接口】/file-contracts 输出列；__all__ 显式枚举——
#   manifest.py 再导出先例，mypy no-implicit-reexport 与 ruff F401 经
#   __all__ 认可）：
#   quantity:      Quantity, DimKey, InvalidUnitError, InvalidQuantityError
#   flow:          WaterFlow, make_flow, InvalidFlowError
#   quality:       WaterQuality, EffluentStandard, margin, INDICATORS,
#                  InvalidQualityError
#   sludge:        SludgeFlow, make_sludge, mix, InvalidSludgeError
#   ports:         Port, PortRef, Edge, FluidKind, Direction, validate_edge,
#                  InvalidConnection
#   unit_api:      UnitContext, UnitResult, Unit, Severity, Warning
#   manifest:      ParamSpec, ConditionMapping, UnitManifest, load_manifest,
#                  bind_dimension_lookup, InvalidUnitConfig
#   condition:     FlowCase, OperatingCondition, ConditionSet,
#                  build_condition_set（InvalidUnitConfig 同层引用 manifest）
#   project_schema: ProjectFile, DesignState, ViewState, Metadata,
#                  parse_project
#   result_schema: PlantResult, UnitResultSnapshot, TraceNode, ReproTriple,
#                  serialize, deserialize, InvalidResultError
#   expr:          ExprSyntaxError, ALLOWED_FUNCS, parse_checked, eval_checked
#   trace_api:     TraceNodeSpec, TraceSink（协议面）
#   不直接聚合：manifest_validation（内部文件，其公开符号
#   InvalidUnitConfig/bind_dimension_lookup 经 manifest 再导出已可达）；
#   run_env（规格骨架，待 T7 装配实现后随其公开面冻结再聚合）。
#   全库零 `from waterprint.contracts import` 包根消费（深查 B5 实证），
#   本聚合为纯增量正门，不改变任何既有 import 路径。
#   白名单外的新导出名必须先更新 docs/file-contracts.md。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.condition import (
    ConditionSet,
    FlowCase,
    OperatingCondition,
    build_condition_set,
)
from waterprint.contracts.expr import (
    ALLOWED_FUNCS,
    ExprSyntaxError,
    eval_checked,
    parse_checked,
)
from waterprint.contracts.flow import InvalidFlowError, WaterFlow, make_flow
from waterprint.contracts.manifest import (
    ConditionMapping,
    InvalidUnitConfig,
    ParamSpec,
    UnitManifest,
    bind_dimension_lookup,
    load_manifest,
)
from waterprint.contracts.ports import (
    Direction,
    Edge,
    FluidKind,
    InvalidConnection,
    Port,
    PortRef,
    validate_edge,
)
from waterprint.contracts.project_schema import (
    DesignState,
    Metadata,
    ProjectFile,
    ViewState,
    parse_project,
)
from waterprint.contracts.quality import (
    INDICATORS,
    EffluentStandard,
    InvalidQualityError,
    WaterQuality,
    margin,
)
from waterprint.contracts.quantity import (
    DimKey,
    InvalidQuantityError,
    InvalidUnitError,
    Quantity,
)
from waterprint.contracts.result_schema import (
    InvalidResultError,
    PlantResult,
    ReproTriple,
    TraceNode,
    UnitResultSnapshot,
    deserialize,
    serialize,
)
from waterprint.contracts.sludge import (
    InvalidSludgeError,
    SludgeFlow,
    make_sludge,
    mix,
)
from waterprint.contracts.trace_api import TraceNodeSpec, TraceSink
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)

__all__ = [
    "ALLOWED_FUNCS",
    "INDICATORS",
    "ConditionMapping",
    "ConditionSet",
    "DesignState",
    "DimKey",
    "Direction",
    "Edge",
    "EffluentStandard",
    "ExprSyntaxError",
    "FlowCase",
    "FluidKind",
    "InvalidConnection",
    "InvalidFlowError",
    "InvalidQualityError",
    "InvalidQuantityError",
    "InvalidResultError",
    "InvalidSludgeError",
    "InvalidUnitConfig",
    "InvalidUnitError",
    "Metadata",
    "OperatingCondition",
    "ParamSpec",
    "PlantResult",
    "Port",
    "PortRef",
    "ProjectFile",
    "Quantity",
    "ReproTriple",
    "Severity",
    "SludgeFlow",
    "TraceNode",
    "TraceNodeSpec",
    "TraceSink",
    "Unit",
    "UnitContext",
    "UnitManifest",
    "UnitResult",
    "UnitResultSnapshot",
    "ViewState",
    "Warning",
    "WaterFlow",
    "WaterQuality",
    "bind_dimension_lookup",
    "build_condition_set",
    "deserialize",
    "eval_checked",
    "load_manifest",
    "make_flow",
    "make_sludge",
    "margin",
    "mix",
    "parse_checked",
    "parse_project",
    "serialize",
    "validate_edge",
]
