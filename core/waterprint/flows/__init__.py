"""用例流编排层（AI1 轨道甲 2026-09-13）：CLI/MCP 两壳共用的纯 core 编排。

输入:  ProjectFile/ConditionSet/RunEnv/PlantResult 既有契约对象 + data_dir 数据包根
输出:  冻结签名 flows 函数族（env/conditions/standards/calc/persist/validate/
       export/audit/estimate/enumeration/design_map/params_guard）+
       CalcFlowResult/EstimateFlowResult/ParamVerdict 值对象 +
       InvalidFlowError 领域异常（校验失败→CLI 退出码 3）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（任务书 AI1-TRACK-A-2026-09-13 §3 预裁决签名冻结——禁改名
#   改义，并行轨道乙与集成批按此接线；镜像测试 tests/app/test_flows.py）
#
# 【定位】layers 链 cli → flows → app|app_enumeration|app_export → …；
#   禁 import server/cli/fastapi（零 server 概念）；许可面=app 门面+
#   contracts+trace.audit（audit 渲染包装）+cost 四模块链（estimate_
#   summary_flow 签名冻结正文专项授权的既有公开函数）。
#
# 【公开接口】（签名冻结原文——改动即规格漂移；参数语义注记见各函数
#   docstring，此处总纲）
#   build_env_flow(data_dir, project) -> RunEnv   假设合成+系数正门+
#       UF-10 版本聚合（engine 真源=core 包根 __version__——server settings
#       串不可 import，记档偏离）。
#   build_condition_flow(project, keys) -> ConditionSet
#       keys=None 基线（design+avg）；否则受检单元清单（2+k，ADR-007）。
#   build_standards_flow(data_dir) -> tuple[EffluentStandard, ...]
#       constraint_kb 装载；缺失 → () 并警告（ADR-012 宽容面）。
#   run_calc_flow(project, conditions, env, standards, *,
#                 result_out=None) -> CalcFlowResult（plant/result_path/
#       design_digest）= run_full_calc 直通；result_out 给定→persist。
#   result_persist_flow(plant, out) -> Path   serialize 原子落盘（GR-38
#       同目录唯一 tmp→os.replace——worker K-01 并发双写收口同款）。
#   validate_flow(project) -> tuple[str, ...] validate_design_structure
#       直通（清单式不拒——退出码语义归 CLI 壳）。
#   export_flow(kind, project, plant, *, template_dir, out, unit_id=None,
#               condition_key=None, sheet=None, site_design=None,
#               h_scale=None, v_scale=None, assumptions=None) -> Path
#       kind 路由：calcbook→模板解析+export_artifact；dxf/ifc→透传；
#       audit→audit_render_flow；模板缺失/路径非法→InvalidFlowError。
#   audit_render_flow(project, plant, out) -> Path   discover_units 装载
#       前置→render_audit_html→原子落盘（cli export audit 同款语义）。
#   estimate_summary_flow(plant, *, condition_key, data_dir)
#       -> EstimateFlowResult(sheet, report)   cost 四模块链：load_prices
#       →fee_rules/field_mapping(unit_prices)→takeoff→build→check_indicators
#       （design_scale=快照 outflows 输入节点流量×pint 因子——server 同源）。
#   enumeration_flow / design_map_flow（同形）→ app 正门直通。
#   params_guard(project, unit_id, params) -> tuple[ParamVerdict, ...]
#       清单式逐条三面守护（server calculation._validate_apply_params
#       移植语义）：①值=有限数值（bool/str/NaN 拒）②键=单元目录已知参数
#       （kind 通道同款）③grid 声明时须命中档位。与 server 版差异：
#       server 版整批拒（raise），本版逐条判定不拒整批——CLI/MCP 共用。
#
# 【行为规格】
#   R1 异常族：InvalidFlowError=校验失败面（CLI 3）；计算失败沿用 core
#      既有领域异常（LoopDivergence 等——CLI 4）。
#   R2 路径安全：out 相对路径以 cwd 为基准、'..' 分量拒（audit 同口径）。
#   R3 数值纪律：零工程数值字面量（m3/d 换算经 quantity parse 因子）。
#   R4 builtin kind 参数键面=graph.nodes 各 __init__ 校验语义镜像声明
#      （core 无声明面——server units.py 同款声明面先例；收敛挂账数据批）。
#
# 【测试要求】tests/app/test_flows.py（golden 实跑全流+守护拒绝路径）。
# 【参照】AI1 路线设计书 v2 D6/E4；任务书 §3 预裁决；ADR-022（flows
#   用例流层定位——治理登记归集成批）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import contextlib
import os
import uuid
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Final, final

import yaml

from waterprint import __version__ as _engine_version
from waterprint.app import (  # app 门面（许可面①——UF-33 单入口）
    DEFAULT_ASSUMPTIONS,
    DesignMap,
    DesignMapOptions,
    EnumerationOptions,
    EnumerationOutcome,
    discover_units,
    export_artifact,
    load_coefficients,
    load_effluent_standards,
    run_design_map,
    run_enumeration,
    run_full_calc,
    validate_design_structure,
)
from waterprint.contracts.condition import ConditionSet, build_condition_set
from waterprint.contracts.manifest import ParamSpec
from waterprint.contracts.project_schema import ProjectFile, SiteDesign
from waterprint.contracts.quality import INDICATORS, EffluentStandard
from waterprint.contracts.quantity import DimKey, parse
from waterprint.contracts.result_schema import PlantResult, serialize
from waterprint.contracts.run_env import RunEnv
from waterprint.cost.estimate import EstimateSheet, build_estimate, load_fee_rules
from waterprint.cost.indicators import IndicatorReport, check_indicators, load_indicator_bands
from waterprint.cost.prices import load_prices
from waterprint.cost.takeoff import load_field_mapping, takeoff_quantities
from waterprint.trace.audit import render_audit_html  # 许可面③（audit 渲染包装）

__all__ = [
    "CalcFlowResult", "EstimateFlowResult", "InvalidFlowError", "ParamVerdict",
    "audit_render_flow", "build_condition_flow", "build_env_flow",
    "build_standards_flow", "design_map_flow", "enumeration_flow",
    "estimate_summary_flow", "export_flow", "params_guard",
    "result_persist_flow", "run_calc_flow", "validate_flow",
]


class InvalidFlowError(Exception):
    """用例流校验失败（守护/模板/路径面）——CLI 退出码 3 的领域源。"""


# ── 数据包相对件名（声明面字符串常量——零数值字面量） ────────────────────
_COEFFICIENTS_DIR: Final[str] = "coefficients"
_UNIT_PRICES_DIR: Final[str] = "unit_prices"
_PRICE_MANIFEST: Final[str] = "manifest.yaml"
_PRICE_VERSION_KEY: Final[str] = "price_data_version"
_CONSTRAINT_KB: Final[str] = "constraint_kb"
_CONSTRAINTS_FILE: Final[str] = "constraints.json"
_FIELD_MAPPING: Final[str] = "field_mapping.yaml"
_CALCBOOK_TEMPLATE: Final[str] = "calcbook_plant.xlsx"
_FLOW_KEY: Final[str] = "q_avg_daily"


def build_env_flow(data_dir: Path, project: ProjectFile) -> RunEnv:
    """env 装配流：假设合成视图+系数正门装载+UF-10 版本聚合（worker 口径）。

    data_version 包集={coefficients, unit_prices}（后者 manifest 缺席时省略
    ——包名排序后 name@version 以 + 拼接）；engine_version 真源=core 包根
    __version__（server 串不可 import——记档见规格头）。"""
    coefficients = load_coefficients(data_dir / _COEFFICIENTS_DIR)
    versions: dict[str, str] = {"coefficients": coefficients.data_version}
    price_manifest = data_dir / _UNIT_PRICES_DIR / _PRICE_MANIFEST
    if price_manifest.is_file():
        raw = yaml.safe_load(price_manifest.read_text(encoding="utf-8"))
        if isinstance(raw, Mapping) and isinstance(raw.get(_PRICE_VERSION_KEY), str):
            versions[_UNIT_PRICES_DIR] = raw[_PRICE_VERSION_KEY]
    assumptions = {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}
    assumptions.update(project.design.assumption_overrides)
    return RunEnv(
        engine_version=_engine_version,
        data_version="+".join(
            f"{name}@{versions[name]}" for name in sorted(versions)
        ),
        assumptions=assumptions,
        coefficients=coefficients,
        price_book={},  # M3 单价包装载后收紧（GR-21 注记，RunEnv 规格）
        trace_sink=None,
        engine_params={},  # app._completed_env 按缺 loop.* 补齐（UF-08 投影）
    )


def build_condition_flow(project: ProjectFile, keys: Sequence[str] | None
                         ) -> ConditionSet:
    """conditions 流：keys=None 基线两档（design+avg）；否则受检单元 2+k。

    project 形参为冻结签名占位（工况集构造不消费项目态——CLI
    --conditions 语义=server/worker 同款受检单元清单）。"""
    return build_condition_set(tuple(keys) if keys is not None else ())


def build_standards_flow(data_dir: Path) -> tuple[EffluentStandard, ...]:
    """standards 流：constraint_kb 出水标准装载；缺失=() + 警告（宽容面）。"""
    path = data_dir / _CONSTRAINT_KB / _CONSTRAINTS_FILE
    if not path.is_file():
        warnings.warn(
            f"出水标准文件缺失：{path}（诊断 effluent 面空元组合法——"
            "ADR-012 fail-fast 的 CLI/MCP 宽容面，先补数据包）",
            stacklevel=2,
        )
        return ()
    return load_effluent_standards(path)


# ── calc / persist / validate ────────────────────────────────────────────


@dataclass(frozen=True)
@final
class CalcFlowResult:
    """calc 流产物：结果对象+可选落盘路径+design_digest（stale 衔接）。"""
    plant: PlantResult
    result_path: Path | None
    design_digest: str


def run_calc_flow(
    project: ProjectFile,
    conditions: ConditionSet,
    env: RunEnv,
    standards: tuple[EffluentStandard, ...],
    *,
    result_out: Path | None = None,
) -> CalcFlowResult:
    """calc 流：run_full_calc 直通；result_out 给定→确定性序列化原子落盘。"""
    bundle = run_full_calc(project, conditions, env, standards=standards)
    path = (
        result_persist_flow(bundle.plant, result_out)
        if result_out is not None
        else None
    )
    return CalcFlowResult(
        plant=bundle.plant,
        result_path=path,
        design_digest=bundle.repro.design_hash,
    )


def result_persist_flow(plant: PlantResult, out: Path) -> Path:
    """persist 流：serialize 字节 GR-38 原子落盘（唯一 tmp 防并发互覆）。

    父目录缺失则建（network --out 语义对齐——CLI/MCP 两壳同径）。"""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_bytes(serialize(plant))
        os.replace(tmp, out)
    except OSError:
        with contextlib.suppress(OSError):
            os.remove(tmp)  # 半写 .tmp 不留
        raise
    return out


def validate_flow(project: ProjectFile) -> tuple[str, ...]:
    """validate 流：设计结构校验清单直通（⑦甲呈报不拒——退出码语义归壳层）。"""
    return validate_design_structure(project.design)


# ── export / audit ───────────────────────────────────────────────────────


def _flow_out(out: Path) -> Path:
    """输出路径裁定（R2）：cwd 基准绝对化 + '..' 分量拒（audit 同口径）。"""
    resolved = out if out.is_absolute() else Path.cwd() / out
    for part in resolved.parts:
        if part == "..":
            raise InvalidFlowError(
                f"输出路径含越界分量 '..'：{out!r}（§18 路径安全——audit._validate_out 同款）"
            )
    return resolved.resolve()


def export_flow(  # noqa: PLR0913  # 签名冻结选项面（§3——export_artifact 豁免先例）
    kind: str,
    project: ProjectFile,
    plant: PlantResult,
    *,
    template_dir: Path,
    out: Path,
    unit_id: str | None = None,
    condition_key: str | None = None,
    sheet: str | None = None,
    site_design: SiteDesign | None = None,
    h_scale: str | None = None,
    v_scale: str | None = None,
    assumptions: Mapping[str, float] | None = None,
) -> Path:
    """export 流：kind 路由（calcbook 模板解析/dxf、ifc 透传/audit 包装）。

    dxf、ifc 分支 template 形参不消费（export_artifact 签名占位——传
    template_dir 本体）；h/v 比例仅 dxf 合法（选项闸同款）。"""
    target = _flow_out(out)
    if kind == "audit":
        return audit_render_flow(project, plant, target)
    if kind == "calcbook":
        template = template_dir / _CALCBOOK_TEMPLATE
        if not template.is_file():
            raise InvalidFlowError(
                f"calcbook 模板缺失：{template}（数据包 templates 面——"
                "先补 data/templates，禁静默空产物）")
        export_artifact("calcbook", plant, template, target)
        return target
    if kind == "dxf":
        export_artifact(
            "dxf", plant, template_dir, target,
            site_design=site_design, unit_id=unit_id,
            condition_key=condition_key, sheet=sheet,
            h_scale=h_scale, v_scale=v_scale,
        )
        return target
    if kind == "ifc":
        export_artifact(
            "ifc", plant, template_dir, target,
            assumptions=assumptions, site_design=site_design,
            condition_key=condition_key,
        )
        return target
    raise InvalidFlowError(
        f"export_flow 未知 kind {kind!r}（合法面 calcbook/dxf/ifc/audit——UF-33）"
    )


def audit_render_flow(project: ProjectFile, plant: PlantResult, out: Path) -> Path:
    """audit 流：注册表装载前置→render_audit_html→原子落盘（cli 同款）。

    project 形参为冻结签名占位（一致性警告归 CLI 壳 stderr——审计对象
    =该份计算，HTML 头部三元组自证版本）。"""
    discover_units()  # 迹公式反查的注册表前置（app.assemble 内部同款装载）
    target = _flow_out(out)
    tmp = target.with_name(target.name + ".tmp")
    try:
        render_audit_html(plant.trace, plant, tmp)
        os.replace(tmp, target)
    except OSError:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise
    return target


# ── estimate（cost 四模块链） ────────────────────────────────────────────


@dataclass(frozen=True)
@final
class EstimateFlowResult:
    """estimate 流产物：概算表+指标校核报告（内存投影——T4 无文件面）。"""
    sheet: EstimateSheet
    report: IndicatorReport


def _design_scale_of(plant: PlantResult, condition_key: str) -> float:
    """设计规模（m3/d）：快照 outflows 输入节点流量换算（server 同源口径）。

    换算经 contracts.quantity parse 因子（R3 禁手写 86400）；sorted 遍历=
    确定性取数；outflows 键域天然限定输入节点（zM-1 收窄同款）。"""
    factor = parse(1.0, "m3/d", DimKey.FLOW)
    units = plant.conditions.get(condition_key, {})
    for unit_id in sorted(units):
        value = units[unit_id].outflows.get(f"{unit_id}.out.{_FLOW_KEY}")
        if isinstance(value, bool) or not isinstance(value, int | float):
            continue
        return float(value) / factor
    raise InvalidFlowError(
        f"结果集快照无 *.out.{_FLOW_KEY} 输入节点流量（指标设计规模无定义"
        f"——工况 {condition_key!r} sorted 单元集 {sorted(units)}）"
    )


def estimate_summary_flow(
    plant: PlantResult, *, condition_key: str, data_dir: Path
) -> EstimateFlowResult:
    """estimate 流：装载→提取→汇总→校核（cost 四模块链，内存投影）。"""
    unit_prices = data_dir / _UNIT_PRICES_DIR
    book = load_prices(unit_prices)
    fees = load_fee_rules(unit_prices / _FIELD_MAPPING, book)
    mapping = load_field_mapping(unit_prices / _FIELD_MAPPING)
    items = takeoff_quantities(
        plant, condition_key, price_book=book, field_mapping=mapping
    )
    sheet = build_estimate(
        items, book, fees, repro=plant.repro, condition_key=condition_key
    )
    report = check_indicators(
        sheet,
        load_indicator_bands(book),
        design_scale=_design_scale_of(plant, condition_key),
    )
    return EstimateFlowResult(sheet=sheet, report=report)


# ── enumeration / design_map（app 正门直通） ─────────────────────────────


def enumeration_flow(
    project: ProjectFile,
    unit_id: str,
    conditions: ConditionSet,
    env: RunEnv,
    *,
    options: EnumerationOptions | None = None,
) -> EnumerationOutcome:
    """enumeration 流：run_enumeration 直通（单单元枚举正门——UF-33）。"""
    return run_enumeration(project, unit_id, conditions, env, options)


def design_map_flow(
    project: ProjectFile,
    unit_id: str,
    conditions: ConditionSet,
    env: RunEnv,
    *,
    options: DesignMapOptions | None = None,
) -> DesignMap:
    """design_map 流：run_design_map 直通（可行域引导正门——FD 批）。"""
    return run_design_map(project, unit_id, conditions, env, options)


# ── params_guard（三面守护纯函数——server AUDIT2 C-4 移植） ───────────────


@dataclass(frozen=True)
@final
class ParamVerdict:
    """单参数守护判定：键/原值/接受位/拒因（清单式不拒整批）。"""
    key: str
    value: object
    accepted: bool
    reason: str | None


# builtin kind 参数键面（R4）：graph.nodes 各 __init__ 校验语义镜像声明
# （junction/recycle_junction 零参数；grid 档位面 builtin 恒无——
# server units.py _BUILTIN_PARAM_DIMS 同款声明面先例）。
_BUILTIN_PARAM_KEYS: Final[Mapping[str, frozenset[str]]] = MappingProxyType({
    "municipal_input": frozenset(("q_avg_daily", "kz")) | frozenset(INDICATORS),
    "quality_edit": frozenset(INDICATORS),
    "junction": frozenset(),
    "recycle_junction": frozenset(),
})


def _guard_reason(
    key: object,
    value: object,
    unit_id: str,
    specs: Mapping[str, ParamSpec],
    known: frozenset[str],
) -> str | None:
    """三面判定单条拒因：①值有限数值 ②键已知 ③grid 档位（首命中即返）。"""
    if not isinstance(key, str) or not key:
        return f"方案参数 {key!r} 非法（字段 ID: str）"
    if key not in known:
        return (
            f"方案参数 {key!r} 不在单元 {unit_id!r} 目录参数面"
            f"（合法 {sorted(known)}——ADR-005 grid 字段投影语义）"
        )
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not isfinite(value)
    ):
        return (
            f"方案参数 {key!r}={value!r} 非法（数值: int/float 有限值"
            "——bool/字符串/NaN 拒，ADR-005「值全 number」服务端口径）"
        )
    spec = specs.get(key)
    if (
        spec is not None
        and spec.grid is not None
        and float(value) not in {float(g) for g in spec.grid}
    ):
        return (
            f"方案参数 {key!r} 值 {value!r} 未命中 grid 档位 {list(spec.grid)}"
            "（枚举维——§12.4，与 core 装配期同口径前置）"
        )
    return None


def params_guard(
    project: ProjectFile, unit_id: str, params: Mapping[str, float]
) -> tuple[ParamVerdict, ...]:
    """guard 流：三面清单式逐条判定（server 版整批拒——本版不拒整批）。

    kind 通道：design.nodes[unit_id] 覆写含 kind 用 kind 查目录，否则
    unit_id 直查（32 包 manifest）；目录外=前置结构错误 InvalidFlowError
    （server 转调面同消息映射 422）。"""
    node = project.design.nodes.get(unit_id)
    if node is None:
        raise InvalidFlowError(
            f"方案目标单元 {unit_id!r} 不在项目 design.nodes（不可应用）"
        )
    kind = node.get("kind") if isinstance(node.get("kind"), str) else None
    catalog_key = kind if kind is not None else unit_id
    discovered = discover_units()
    if catalog_key in discovered:
        specs: Mapping[str, ParamSpec] = {
            spec.field_id: spec for spec in discovered[catalog_key][0].params}
        known = frozenset(specs)
    elif catalog_key in _BUILTIN_PARAM_KEYS:
        specs = {}
        known = _BUILTIN_PARAM_KEYS[catalog_key]
    else:
        raise InvalidFlowError(
            f"方案目标单元 {unit_id!r} 无单元目录声明（kind={catalog_key!r}"
            "——META1 目录外不可应用）"
        )
    verdicts = tuple(
        ParamVerdict(
            key=key if isinstance(key, str) else str(key),
            value=value,
            accepted=(reason := _guard_reason(key, value, unit_id, specs, known))
            is None,
            reason=reason,
        )
        for key, value in params.items()
    )
    return verdicts
