"""compare 服务用例：最近完成结果集 → 多工况对比矩阵（指标×工况+警告计数）。

输入:  项目 id（路径）——无工况/标准参数（全工况聚合报告，ADR-018 D5）
输出:  CompareReportResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（P2 第三批 ADR-018 D5；镜像测试 server/tests/services/
#   test_compare.py）
#
# 【公开接口】
#   build_compare_for_project(ctx, project_id) -> CompareReportResponse
#       （多工况对比数据通道服务面正门——GET /api/calc/compare/{project_id}）
#   CompareReportResponse/CompareMetricModel/CompareWarningModel（响应
#       模型面——routers response_model 直用，trust「服务层 pydantic 冻结
#       模型」先例：禁协议层重复声明漂移面）
#   CompareSourceNotFoundError（404 面）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：_latest_calc_result 复制 services/trust
#      同款取数模式（scene R1 同口径——UF-37 统一；不 import trust 私有
#      名）；无结果集=CompareSourceNotFoundError（404，消息含
#      "先 POST /api/calc/run"）；结果文件缺失/损坏同归 404 面（裸 500 禁）。
#   R2 指标行（D5 聚合归 server）：行=各单元 manifest.out_dims 声明面
#      （单元级中文名真源——V2 批制式；其余 31 单元声明随批顺带挂账），
#      values=condition_key→有限值（NaN 无值键不出——JSON 面非法）；
#      全工况均无值的行不呈现（禁全空行冒充数据面）。行序=unit_id 字典
#      序 × 单元内 out_dims 声明序（确定性，R5 同口径）。
#   R3 警告计数行：全工况×全单元 warnings 总计数（severity 全级聚合；
#      分级明细归 trust 面不复刻——两数据通道语义分界）；零计数单元不
#      出行（矩阵稀疏面——非零即信号）。行序=unit_id 字典序。
#   R4 新鲜度（D3 比对面）：stale=result_is_stale（design_hash≠当前
#      digest——四端点+trust 同口径）；design_hash 回显=结果件
#      repro.design_hash（FE 锁定基准 pinned_hash 比对真源——改设计→
#      重算→新结果件 hash 不同→「基准已过期」判定，ADR-018 D3 记档）；
#      repro 三元组+task_id 回显（结果溯源面）。
#   R5 确定性：同结果集同响应（排序稳定——condition_keys/staleness
#      聚合键全字典序；双跑字节同端点测试常驻断言沿 trust 先例）。
#
# 【测试要求】矩阵形状/NaN 无值键/全空行不呈现/警告计数稀疏/404 两面
#   （无项目/无结果）/stale 语义/design_hash 回显/确定性双跑。
#
# 【参照】ADR-018；services/trust.py（取数母本+模型先例）；
#   services/scene.py（latest 取数母本）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from waterprint import app as core
from waterprint.contracts.result_schema import (
    InvalidResultError,
    deserialize,
)

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "CompareMetricModel",
    "CompareReportResponse",
    "CompareSourceNotFoundError",
    "CompareWarningModel",
    "build_compare_for_project",
]


class CompareSourceNotFoundError(Exception):
    """多工况对比源不可得（项目无结果集/结果文件损坏）——404 面。"""


class CompareMetricModel(BaseModel):
    """矩阵指标行：单元×字段 → 各工况取值（NaN 无值键不出——R2）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    field_id: str
    label_zh: str | None
    dim: str
    values: dict[str, float]


class CompareWarningModel(BaseModel):
    """警告计数行：单元 → 各工况警告总数（零计数单元不出——R3）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    counts: dict[str, int]


class CompareReportResponse(BaseModel):
    """多工况对比报告（全工况聚合——R2/R3/R4）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    task_id: str
    stale: bool
    design_hash: str
    engine_version: str
    data_version: str
    condition_keys: tuple[str, ...]
    metrics: tuple[CompareMetricModel, ...]
    warnings: tuple[CompareWarningModel, ...]


def _latest_calc_result(
    ctx: ServiceContext, project_id: str
) -> tuple[str, Mapping[str, Any]]:
    """最近完成计算结果集（services/trust 同款取数模式复制——R1）。

    携 task_id 返回（溯源回显面——result bag 不含 task_id 键）。"""
    task_id: str = ""
    latest: Mapping[str, Any] | None = None
    for candidate in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(candidate)
        if status.kind == "calc" and status.state == "done" and status.result:
            task_id, latest = candidate, status.result
    if latest is None:
        raise CompareSourceNotFoundError(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return task_id, latest


def _metric_rows(
    plant_conditions: Mapping[str, Mapping[str, Any]],
    condition_keys: tuple[str, ...],
) -> tuple[CompareMetricModel, ...]:
    """指标行投影（R2）：out_dims 声明面 × 工况取值——NaN 键剔除+全空行不呈现。"""
    rows: list[CompareMetricModel] = []
    for unit_id in sorted(
        {unit for snapshots in plant_conditions.values() for unit in snapshots}
    ):
        manifest = core.discover_units().get(unit_id)
        if manifest is None:
            continue  # 内置节点（inlet 等）无 manifest——不参与指标面
        for spec in manifest[0].out_dims:
            values: dict[str, float] = {}
            for key in condition_keys:
                snapshot = plant_conditions.get(key, {}).get(unit_id)
                if snapshot is None:
                    continue
                raw = snapshot.dims.get(spec.field_id)
                if raw is not None and math.isfinite(float(raw)):
                    values[key] = float(raw)
            if values:  # 全空行不呈现（R2）
                rows.append(
                    CompareMetricModel(
                        unit_id=unit_id,
                        field_id=spec.field_id,
                        label_zh=spec.label_zh,
                        dim=str(spec.dim),
                        values=values,
                    )
                )
    return tuple(rows)


def _warning_rows(
    plant_conditions: Mapping[str, Mapping[str, Any]],
    condition_keys: tuple[str, ...],
) -> tuple[CompareWarningModel, ...]:
    """警告计数行投影（R3）：全工况×全单元总数——零计数单元不出。"""
    counts: dict[str, dict[str, int]] = {}
    for key in condition_keys:
        for unit_id, snapshot in plant_conditions.get(key, {}).items():
            if snapshot.warnings:
                bucket = counts.setdefault(unit_id, {})
                bucket[key] = bucket.get(key, 0) + len(snapshot.warnings)
    return tuple(
        CompareWarningModel(unit_id=unit_id, counts=dict(counts[unit_id]))
        for unit_id in sorted(counts)
    )


def build_compare_for_project(
    ctx: ServiceContext, project_id: str
) -> CompareReportResponse:
    """多工况对比报告正门：项目校验 → 结果集取数 → 指标/警告聚合（R1~R5）。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    task_id, latest = _latest_calc_result(ctx, project_id)
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        raise CompareSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    condition_keys = tuple(sorted(plant.conditions))
    return CompareReportResponse(
        project_id=project_id,
        task_id=task_id,
        stale=result_is_stale(latest, project),
        design_hash=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version,
        condition_keys=condition_keys,
        metrics=_metric_rows(plant.conditions, condition_keys),
        warnings=_warning_rows(plant.conditions, condition_keys),
    )
