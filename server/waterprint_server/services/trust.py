"""trust 服务用例：最近完成结果集 → 结果可信度报告（诊断+警告聚合+新鲜度）。

输入:  项目 id（路径）——无工况/标准参数（全工况聚合报告）
输出:  TrustReportResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（P2 次批 ADR-012 D7/D8；镜像测试 server/tests/test_trust.py）
#
# 【公开接口】
#   build_trust_for_project(ctx, project_id) -> TrustReportResponse
#       （可信度数据通道服务面正门——GET /api/calc/trust/{project_id}）
#   TrustReportResponse/LoopRunModel/ClosureLineModel/UnitImbalanceModel/
#   FlowClosureModel/IndicatorMarginModel/TrustWarningModel（响应模型面
#   ——routers response_model 直用，elevation"服务层 pydantic 冻结模型"
#   先例：禁协议层重复声明漂移面）
#   TrustSourceNotFoundError（404 面）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：_latest_calc_result 复制 services/scene
#      同款取数模式（scene R1 同口径——UF-37 统一；不 import scene 私有
#      名，FE1 简报条款）；无结果集=TrustSourceNotFoundError（404，消息
#      含"先 POST /api/calc/run"）；结果文件缺失/损坏同归 404 面
#      （FE1 M4 路径安全族——裸 500 禁）。
#   R2 诊断降级（ADR-012 R1）：旧结果无 diag 文件（task result 缺
#      diag_file 键或文件不可读/损坏）→ diagnostics_available=False +
#      convergence/mass_balance/effluent 空面（禁止伪造空诊断冒充——
#      布尔显式区分"已算但无数据"与"未算"）；warnings 面恒给
#      （PlantResult 总线自有——旧结果也有）。
#   R3 警告聚合（D7）：plant.conditions 全工况×全单元 warnings 六键
#      1:1 透传+unit_id 定位（WarningEntry 复用 elevation 冻结形状——
#      UF-17 同源，本件加 unit_id 维度）；warning_counts 按级计数
#      （仅在场级——零级不出键）。
#   R4 新鲜度：stale=result_is_stale（design_hash≠当前 digest——scene/
#      elevation/cost/site 四端点同口径）；repro 三元组+task_id 回显
#      （结果溯源面）。
#   R5 确定性：同结果集同响应（core 纯投影+聚合排序稳定——工况键/
#      unit_id/indicator 字典序，双跑字节同端点测试常驻断言）。
#
# 【测试要求】全字段聚合/降级两态/404 两面（无项目/无结果）/stale 语义/
#   双跑字节同/警告计数。
#
# 【参照】ADR-012；services/elevation.py（服务先例+WarningEntry）；
# services/scene.py（latest 取数母本）；P2 真源 briefs/task-p2-trust-plan.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.result_schema import (
    InvalidResultError,
    UnitResultSnapshot,
    deserialize,
)
from waterprint.contracts.trust import (
    DiagnosticsReport,
    InvalidDiagnosticsError,
    deserialize_diag,
)
from waterprint.contracts.unit_api import Severity

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "ClosureLineModel",
    "FlowClosureModel",
    "IndicatorMarginModel",
    "LoopRunModel",
    "TrustReportResponse",
    "TrustSourceNotFoundError",
    "TrustWarningModel",
    "UnitImbalanceModel",
    "build_trust_for_project",
]


class TrustSourceNotFoundError(Exception):
    """可信度报告源不可得（项目无结果集/结果文件损坏）——404 面。"""


class LoopRunModel(BaseModel):
    """回路收敛统计条目（contracts.trust.LoopRunStats 直投影）。"""

    model_config = ConfigDict(frozen=True)

    condition_key: str
    loop_nodes: tuple[str, ...]
    iterations: int
    final_residual: float


class ClosureLineModel(BaseModel):
    """单流体线厂级闭合（contracts.trust.ClosureLine 直投影）。"""

    model_config = ConfigDict(frozen=True)

    fluid: str
    q_sources_total: float
    q_sinks_total: float
    closure_rel: float


class UnitImbalanceModel(BaseModel):
    """单元×流体进出闭合（contracts.trust.UnitImbalance 直投影）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    fluid: str
    q_in: float
    q_out: float
    delta_rel: float


class FlowClosureModel(BaseModel):
    """单工况水量闭合审计（contracts.trust.FlowClosure 直投影）。"""

    model_config = ConfigDict(frozen=True)

    condition_key: str
    lines: tuple[ClosureLineModel, ...]
    unit_imbalances: tuple[UnitImbalanceModel, ...]


class IndicatorMarginModel(BaseModel):
    """出水指标裕度条目（contracts.trust.IndicatorMargin 直投影）。"""

    model_config = ConfigDict(frozen=True)

    condition_key: str
    standard_id: str
    indicator: str
    value: float
    limit: float
    margin: float


class TrustWarningModel(BaseModel):
    """结果警告条目（WarningEntry 六键+unit_id 定位——R3）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    severity: Severity
    source: str
    message: str
    param_key: str | None = None
    condition_key: str | None = None
    affected_unit_ids: tuple[str, ...] = ()


class TrustReportResponse(BaseModel):
    """结果可信度报告（全工况聚合——R2/R4）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    task_id: str
    stale: bool
    design_hash: str
    engine_version: str
    data_version: str
    diagnostics_available: bool
    loop_params: dict[str, float]
    convergence: tuple[LoopRunModel, ...]
    mass_balance: tuple[FlowClosureModel, ...]
    effluent: tuple[IndicatorMarginModel, ...]
    warnings: tuple[TrustWarningModel, ...]
    warning_counts: dict[str, int]


_NO_DIAGNOSTICS: DiagnosticsReport | None = None


def _latest_calc_result(
    ctx: ServiceContext, project_id: str
) -> tuple[str, Mapping[str, Any]]:
    """最近完成计算结果集（services/scene 同款取数模式复制——R1）。

    携 task_id 返回（溯源回显面——result bag 不含 task_id 键）。"""
    task_id: str = ""
    latest: Mapping[str, Any] | None = None
    for candidate in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(candidate)
        if status.kind == "calc" and status.state == "done" and status.result:
            task_id, latest = candidate, status.result
    if latest is None:
        raise TrustSourceNotFoundError(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return task_id, latest


def _load_diagnostics(latest: Mapping[str, Any]) -> DiagnosticsReport | None:
    """诊断件读取（R2 降级面：缺键/缺文件/损坏 → None 显式降级）。"""
    diag_file = latest.get("diag_file")
    if not isinstance(diag_file, str) or not diag_file:
        return _NO_DIAGNOSTICS
    try:
        return deserialize_diag(Path(diag_file).read_bytes())
    except (OSError, InvalidDiagnosticsError):
        return _NO_DIAGNOSTICS


def _warnings_of(
    plant_conditions: Mapping[str, Mapping[str, UnitResultSnapshot]],
) -> tuple[TrustWarningModel, ...]:
    """警告聚合（R3）：全工况×全单元六键透传+unit_id——排序稳定（R5）。"""
    entries: list[TrustWarningModel] = []
    for condition_key in sorted(plant_conditions):
        units = plant_conditions[condition_key]
        for unit_id in sorted(units):
            for warning in units[unit_id].warnings:
                entries.append(
                    TrustWarningModel(
                        unit_id=unit_id,
                        severity=warning.severity,
                        source=warning.source,
                        message=warning.message,
                        param_key=warning.param_key,
                        condition_key=warning.condition_key or condition_key,
                        affected_unit_ids=warning.affected_unit_ids,
                    )
                )
    return tuple(entries)


def build_trust_for_project(ctx: ServiceContext, project_id: str) -> TrustReportResponse:
    """可信度报告正门：项目校验 → 结果集取数 → 诊断/警告聚合（R1~R5）。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    task_id, latest = _latest_calc_result(ctx, project_id)
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        raise TrustSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    diagnostics = _load_diagnostics(latest)
    warnings = _warnings_of(plant.conditions)
    counts: dict[str, int] = {}
    for entry in warnings:
        counts[entry.severity.value] = counts.get(entry.severity.value, 0) + 1
    return TrustReportResponse(
        project_id=project_id,
        task_id=task_id,
        stale=result_is_stale(latest, project),
        design_hash=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version,
        diagnostics_available=diagnostics is not None,
        loop_params=dict(diagnostics.loop_params) if diagnostics else {},
        convergence=(
            tuple(
                LoopRunModel(
                    condition_key=item.condition_key,
                    loop_nodes=item.loop_nodes,
                    iterations=item.iterations,
                    final_residual=item.final_residual,
                )
                for item in diagnostics.convergence
            )
            if diagnostics
            else ()
        ),
        mass_balance=(
            tuple(
                FlowClosureModel(
                    condition_key=item.condition_key,
                    lines=tuple(
                        ClosureLineModel(
                            fluid=line.fluid,
                            q_sources_total=line.q_sources_total,
                            q_sinks_total=line.q_sinks_total,
                            closure_rel=line.closure_rel,
                        )
                        for line in item.lines
                    ),
                    unit_imbalances=tuple(
                        UnitImbalanceModel(
                            unit_id=unit.unit_id,
                            fluid=unit.fluid,
                            q_in=unit.q_in,
                            q_out=unit.q_out,
                            delta_rel=unit.delta_rel,
                        )
                        for unit in item.unit_imbalances
                    ),
                )
                for item in diagnostics.mass_balance
            )
            if diagnostics
            else ()
        ),
        effluent=(
            tuple(
                IndicatorMarginModel(
                    condition_key=item.condition_key,
                    standard_id=item.standard_id,
                    indicator=item.indicator,
                    value=item.value,
                    limit=item.limit,
                    margin=item.margin,
                )
                for item in diagnostics.effluent
            )
            if diagnostics
            else ()
        ),
        warnings=warnings,
        warning_counts=counts,
    )
