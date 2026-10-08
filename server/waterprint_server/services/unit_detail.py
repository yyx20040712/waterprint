"""unit_detail 服务用例：最近完成结果集 → 单单元结果明细切片（行模型=out_dims 声明面联表）。

输入:  ServiceContext + 项目 id + unit_id + condition_key（缺省 design）
输出:  UnitDetailResponse（含 stale/design_hash 回显——R4 compare 同口径）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B2 结果与方案批 2026-10-09 任务书 §二.①——形源 agent 侧
#   #13 wp_get_unit_detail；镜像测试 server/tests/routers/
#   test_unit_detail.py）
#
# 【公开接口】
#   build_unit_detail(ctx, project_id, unit_id, condition_key)
#       -> UnitDetailResponse（单单元明细数据通道服务面正门——
#       GET /api/calc/projects/{project_id}/units/{unit_id}/results）
#   UnitDetailResponse/UnitDetailRowModel/UnitDetailWarningModel
#       （响应模型面——routers response_model 直用，compare「服务层
#       pydantic 冻结模型」先例：禁协议层重复声明漂移面）
#   UnitDetailSourceNotFoundError / UnitDetailEntryNotFoundError
#       （404 两面：源不可得 / 工况·单元不在——文案区分）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：latest_calc_result 共享件取数（compare
#      同层同源——零重算）；项目不存在=ProjectNotFoundError（404）；
#      无结果集/结果文件损坏=UnitDetailSourceNotFoundError（404，消息
#      含 /api/calc/run 引导）。
#   R2 行模型（服务端联表单源——FE 不自带 out_dims 副本）：行=该单元
#      manifest.out_dims 声明面（field_id/label_zh/dim 三元组——B5 447
#      键基线），value=快照 dims 取值（NaN/缺键→None——JSON 面非法值
#      不出）；**超集键（compute 实产⊃out_dims——R-3 呈裁位三类）不
#      呈现不扩面**（任务书 §二.⑥：阅读面只消费现 out_dims；行集对
#      out_dims 键集变化前向兼容=数据驱动非硬编码）。行序=out_dims
#      声明序（确定性，compare R2 同口径）。
#   R3 端口与数据面：outflows/outqualities=快照端口流量水质投影
#      （agent #13 同形）；warnings=Warning 六键投影（trust R3 同形）；
#      formula_ids=公式 id 集（数据面透传——渲染=B6 批，本批不呈现）。
#   R4 新鲜度：stale=result_is_stale（design_hash≠当前 digest——四端点
#      同口径）；design_hash 回显=结果件 repro.design_hash（FE 锁定
#      基准比对真源 D3 惯例）；repro 三元组+task_id 回显（溯源面）。
#   R5 确定性：同结果集同响应（键全排序/声明序稳定）。
#
# 【测试要求】200 载荷形状/行模型对账/condition_key 显式与 404/404 三面
#   文案区分/stale 流转（test_unit_detail.py 五用例）。
#
# 【参照】B2 任务书 §二.①；services/compare.py（取数母本+模型先例）；
#   agent/waterprint_agent/tools/results.py _unit_detail_impl（形源）
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
from waterprint_server.services._shared.latest_calc import latest_calc_result
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "UnitDetailEntryNotFoundError",
    "UnitDetailResponse",
    "UnitDetailRowModel",
    "UnitDetailSourceNotFoundError",
    "UnitDetailWarningModel",
    "build_unit_detail",
]

_DESIGN_KEY = "design"


class UnitDetailSourceNotFoundError(Exception):
    """单单元明细源不可得（项目无结果集/结果文件损坏）——404 面。"""


class UnitDetailEntryNotFoundError(Exception):
    """明细目标不在（工况/单元缺席结果快照）——404 面（文案区分）。"""


class UnitDetailRowModel(BaseModel):
    """明细行（R2）：out_dims 声明三元组+快照取值（缺值 None 诚实呈现）。"""

    model_config = ConfigDict(frozen=True)

    field_id: str
    label_zh: str | None
    dim: str
    value: float | None


class UnitDetailWarningModel(BaseModel):
    """警告条目（R3）：Warning 六键+unit_id 定位——trust R3 同形。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    severity: str
    source: str
    message: str
    param_key: str | None = None
    condition_key: str | None = None
    affected_unit_ids: tuple[str, ...] = ()


class UnitDetailResponse(BaseModel):
    """单单元结果明细切片（R1~R5——agent #13 形源+服务端联表行模型）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    task_id: str
    unit_id: str
    condition_key: str
    stale: bool
    design_hash: str
    engine_version: str
    data_version: str
    rows: tuple[UnitDetailRowModel, ...]
    outflows: dict[str, float]
    outqualities: dict[str, float]
    warnings: tuple[UnitDetailWarningModel, ...]
    formula_ids: tuple[str, ...]


def _finite_or_none(raw: Any) -> float | None:
    """快照取值→JSON 面（非有限数→None——NaN 非法值不出）。"""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _rows_of(unit_id: str, dims: Mapping[str, Any]) -> tuple[UnitDetailRowModel, ...]:
    """行模型投影（R2）：manifest out_dims 声明面 × dims 取值——超集键不呈现。"""
    entry = core.discover_units().get(unit_id)
    if entry is None:
        return ()  # 内置节点（inlet 等）无 manifest——声明面空（端口段仍在）
    return tuple(
        UnitDetailRowModel(
            field_id=spec.field_id,
            label_zh=spec.label_zh,
            dim=str(spec.dim),
            value=_finite_or_none(dims.get(spec.field_id)),
        )
        for spec in entry[0].out_dims
    )


def build_unit_detail(
    ctx: ServiceContext,
    project_id: str,
    unit_id: str,
    condition_key: str | None,
) -> UnitDetailResponse:
    """单单元明细正门：项目校验 → 结果集取数 → 行模型/端口/数据面投影（R1~R5）。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    task_id, latest = latest_calc_result(
        ctx, project_id, not_found=UnitDetailSourceNotFoundError
    )
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        raise UnitDetailSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    chosen = condition_key if condition_key is not None else _DESIGN_KEY
    view = plant.conditions.get(chosen)
    if view is None:
        raise UnitDetailEntryNotFoundError(
            f"工况 {chosen!r} 不在结果集（合法 {sorted(plant.conditions)}）"
        )
    snap = view.get(unit_id)
    if snap is None:
        raise UnitDetailEntryNotFoundError(
            f"单元 {unit_id!r} 不在工况 {chosen!r} 结果快照"
        )
    return UnitDetailResponse(
        project_id=project_id,
        task_id=task_id,
        unit_id=unit_id,
        condition_key=chosen,
        stale=result_is_stale(latest, project),
        design_hash=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version,
        rows=_rows_of(unit_id, snap.dims),
        outflows={key: float(value) for key, value in sorted(snap.outflows.items())},
        outqualities={
            key: float(value) for key, value in sorted(snap.outqualities.items())
        },
        warnings=tuple(
            UnitDetailWarningModel(
                unit_id=unit_id,
                severity=warning.severity.value,
                source=warning.source,
                message=warning.message,
                param_key=warning.param_key,
                condition_key=warning.condition_key or chosen,
                affected_unit_ids=tuple(warning.affected_unit_ids),
            )
            for warning in snap.warnings
        ),
        formula_ids=tuple(snap.formula_ids),
    )
