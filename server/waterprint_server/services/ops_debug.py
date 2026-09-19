"""操作链 debug 用例：项目任务时间线+最新结果三源（诊断/警告/trace）聚合。

输入:  项目 id（路径）——注册表任务面+最近 done calc 的 result/diag/trace
输出:  OpsChainResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-1 实现批 2026-09-19；《裁决书》方案五①——复用三源零新采集）
#
# 【公开接口】
#   build_ops_chain(ctx, project_id) -> OpsChainResponse
#       （操作链集中 debug 观测面正门——GET /api/debug/ops-chain/{project_id}）
#   OpsChainResponse/OpsTaskModel/LatestCalcBlockModel/DiagSummaryModel/
#   TraceSummaryModel（响应模型面——trust.py 先例：模型住服务件 routers
#   response_model 直用，禁协议层重复声明漂移面）
#
# 【行为规格】
#   R1 任务时间线：manager.task_ids_for_project 注册序（操作序=时间轴——
#      registry 落盘档案无时钟字段，注册序是唯一跨重启稳定序；finished_
#      at_unix=内存 WP4 值〔重启恢复记录=恢复时刻新租约，ENG5 D2 语义〕
#      非终态/未落点=None）；条目状态面经 services.calculation.task_status
#      正门（error_code 名义表回填+实时 stale 比对——操作链上任务状态的
#      唯一正确口径，禁复制）；result 句柄原样透传（IPC 边界 JSON 面已
#      保证可序列化；诊断面自选键呈现）。
#      〔W2 构造性一致注记（门一审推演收口）〕task_ids_for_project 与
#      status/snapshot/finished_at 三查询同读 manager._tasks 单 dict，
#      _task_entries 循环体全同步（无 await 点）=同事件循环轮次内无
#      sweep 并发删除窗口——条目集与逐条查询构造性不可缺档（KeyError
#      团灭路径不存在；重启恢复记录完备性=iter_restorable 装载面在案
#      〔损坏跳过+warning，ENG5〕，探针 P7 恢复矩阵独立实证）。
#   R2 深度聚合（latest done calc）：latest_calc_result 共享件（B3-a 槽位
#      第七消费面）取 (task_id, result)；无 done calc 或结果文件缺失/损坏
#      → latest_calc=None（诊断面语义=200 空面——时间线本体仍有效；与
#      trust 端点消费面 404 语义不同源不同判）。
#   R3 诊断摘要：diag 件读取降级面同 trust（缺文件/损坏→
#      diagnostics_available=False 空摘要，禁伪造——ADR-012 R2 精神）；
#      摘要=计数+极值（明细面走 GET /api/calc/trust 端点，本件不复制
#      LoopRunModel 全量投影）。
#   R4 警告计数：plant.conditions 全工况×全单元 warnings 按级计数（
#      severity→count；与 trust._warnings_of 同数据不同投影粒度——明细
#      聚合归 trust 正门，本件三行计数不构成复制收敛面）。
#   R5 trace 聚合：plant.trace（TraceNode 到达序平铺）→ total_nodes+
#      by_condition/by_unit/by_formula 公式应用计数（键字典序=确定性）；
#      不回全量节点（万级体积面；全量迹经 calcbook/audit 导出面消费）。
#   R6 确定性：零当前时间字段；排序=注册序/字典序；同状态同响应。
#   R7 404 面：项目不存在=read_project→ProjectNotFoundError（404）。
#
# 【测试要求】三源聚合/降级两态（无任务/无 done calc/结果坏档）/404/
#   确定性双跑（仓外探针承载——server/tests 锁面约束，任务书 D5）。
#
# 【参照】《裁决书》方案五①；ADR-012（diag artifact）；services/trust.py
#   （先例母本）；services/calculation.py task_status（状态正门）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.result_schema import (
    InvalidResultError,
    deserialize,
)
from waterprint.contracts.trust import (
    DiagnosticsReport,
    InvalidDiagnosticsError,
    deserialize_diag,
)

from waterprint_server.services import ServiceContext
from waterprint_server.services._shared.latest_calc import latest_calc_result
from waterprint_server.services.calculation import task_status
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "DiagSummaryModel",
    "LatestCalcBlockModel",
    "OpsChainResponse",
    "OpsTaskModel",
    "TraceSummaryModel",
    "build_ops_chain",
]


class _NoCompletedCalcError(Exception):
    """内部哨兵：项目无 done calc（注入共享件 not_found 槽位——诊断面
    空块语义，禁逃逸本模块；对外 404 面唯一=read_project 项目不存在）。"""


class OpsTaskModel(BaseModel):
    """时间线条目：任务状态快照+完成时刻+结果句柄（R1）。"""

    model_config = ConfigDict(frozen=True)

    task_id: str
    kind: str
    state: str
    progress: float
    stage: str
    condition_key: str | None
    stale: bool
    error: str | None
    error_type: str | None
    error_code: int | None
    snapshot_hash: str | None
    finished_at_unix: float | None
    result: Mapping[str, Any] | None = None


class DiagSummaryModel(BaseModel):
    """诊断摘要（R3：计数+极值——明细走 trust 端点）。"""

    model_config = ConfigDict(frozen=True)

    diagnostics_available: bool
    convergence_lines: int
    max_iterations: int
    worst_final_residual: float
    mass_balance_lines: int
    effluent_lines: int


class TraceSummaryModel(BaseModel):
    """trace 聚合统计（R5：公式应用计数，键字典序）。"""

    model_config = ConfigDict(frozen=True)

    total_nodes: int
    by_condition: dict[str, int]
    by_unit: dict[str, int]
    by_formula: dict[str, int]


class LatestCalcBlockModel(BaseModel):
    """最新 done calc 三源聚合块（R2~R5）。"""

    model_config = ConfigDict(frozen=True)

    task_id: str
    stale: bool
    design_hash: str
    engine_version: str
    data_version: str
    diagnostics: DiagSummaryModel
    warning_counts: dict[str, int]
    trace: TraceSummaryModel


class OpsChainResponse(BaseModel):
    """操作链观测面响应（R1/R6：任务时间线+深度聚合块）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    tasks: tuple[OpsTaskModel, ...]
    latest_calc: LatestCalcBlockModel | None


def _task_entries(ctx: ServiceContext, project_id: str) -> tuple[OpsTaskModel, ...]:
    """任务时间线（R1：注册序+task_status 正门+finished_at 投影）。"""
    entries: list[OpsTaskModel] = []
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = task_status(ctx, task_id)
        entries.append(
            OpsTaskModel(
                task_id=status.task_id,
                kind=status.kind,
                state=status.state,
                progress=status.progress,
                stage=status.stage,
                condition_key=status.condition_key,
                stale=status.stale,
                error=status.error,
                error_type=status.error_type,
                error_code=status.error_code,
                snapshot_hash=ctx.manager.snapshot(task_id),
                finished_at_unix=ctx.manager.finished_at(task_id),
                result=status.result,
            )
        )
    return tuple(entries)


def _empty_diag_summary() -> DiagSummaryModel:
    """降级摘要（R3：diagnostics_available=False 显式空——禁伪造）。"""
    return DiagSummaryModel(
        diagnostics_available=False,
        convergence_lines=0,
        max_iterations=0,
        worst_final_residual=0.0,
        mass_balance_lines=0,
        effluent_lines=0,
    )


def _diag_summary(
    diagnostics: DiagnosticsReport | None,
) -> DiagSummaryModel:
    """诊断摘要聚合（R3：计数+极值；None=降级空摘要）。"""
    if diagnostics is None:
        return _empty_diag_summary()
    convergence = diagnostics.convergence
    return DiagSummaryModel(
        diagnostics_available=True,
        convergence_lines=len(convergence),
        max_iterations=max((run.iterations for run in convergence), default=0),
        worst_final_residual=max(
            (run.final_residual for run in convergence), default=0.0
        ),
        mass_balance_lines=len(diagnostics.mass_balance),
        effluent_lines=len(diagnostics.effluent),
    )


def _warning_counts(plant_conditions: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    """警告按级计数（R4：plant 总线自有面——与 trust 同数据不同粒度投影）。"""
    counts: dict[str, int] = {}
    for units in plant_conditions.values():
        for snapshot in units.values():
            for warning in snapshot.warnings:
                key = warning.severity.value
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _trace_summary(nodes: tuple[Any, ...]) -> TraceSummaryModel:
    """trace 聚合统计（R5：单遍三桶计数，键字典序确定性）。"""
    by_condition: dict[str, int] = {}
    by_unit: dict[str, int] = {}
    by_formula: dict[str, int] = {}
    for node in nodes:
        by_condition[node.condition_key] = (
            by_condition.get(node.condition_key, 0) + 1
        )
        by_unit[node.unit_id] = by_unit.get(node.unit_id, 0) + 1
        by_formula[node.formula_id] = by_formula.get(node.formula_id, 0) + 1
    return TraceSummaryModel(
        total_nodes=len(nodes),
        by_condition=dict(sorted(by_condition.items())),
        by_unit=dict(sorted(by_unit.items())),
        by_formula=dict(sorted(by_formula.items())),
    )


def _load_diagnostics(latest: Mapping[str, Any]) -> DiagnosticsReport | None:
    """诊断件读取（R3 降级面——trust._load_diagnostics 同判不同件：本件为
    观测摘要消费方，判据逐字同源〔缺键/缺文件/损坏→None〕）。"""
    diag_file = latest.get("diag_file")
    if not isinstance(diag_file, str) or not diag_file:
        return None
    try:
        return deserialize_diag(Path(diag_file).read_bytes())
    except (OSError, InvalidDiagnosticsError):
        return None


def _latest_calc_block(
    ctx: ServiceContext, project_id: str
) -> LatestCalcBlockModel | None:
    """深度聚合块（R2：共享件取数+plant 反序列化+三源投影；不可得=None）。"""
    try:
        task_id, latest = latest_calc_result(
            ctx, project_id, not_found=_NoCompletedCalcError
        )
    except _NoCompletedCalcError:  # 无 done calc——降级空块（R2 诚实空面）
        return None
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError, KeyError):
        return None  # 结果文件缺失/损坏/句柄残缺——降级 None（R2 诚实空面）
    return LatestCalcBlockModel(
        task_id=task_id,
        stale=result_is_stale(latest, read_project(ctx, project_id)),
        design_hash=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version,
        diagnostics=_diag_summary(_load_diagnostics(latest)),
        warning_counts=_warning_counts(plant.conditions),
        trace=_trace_summary(plant.trace),
    )


def build_ops_chain(ctx: ServiceContext, project_id: str) -> OpsChainResponse:
    """操作链观测面正门：项目校验 → 任务时间线 → 深度聚合（R1~R7）。"""
    read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404 面）
    return OpsChainResponse(
        project_id=project_id,
        tasks=_task_entries(ctx, project_id),
        latest_calc=_latest_calc_block(ctx, project_id),
    )
