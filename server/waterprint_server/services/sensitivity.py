"""sensitivity 服务用例：最近完成结果集 → 全工况投影（design_offline_* 指标差）。

输入:  项目 id（路径）——design 基线 + 逐检修工况 summary 平键值与差全量
输出:  SensitivityReportResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批6e 2026-09-26——wave6-master-plan §批6e；镜像测试
#   server/tests/services/test_sensitivity.py）
#
# 【公开接口】
#   build_sensitivity_for_project(ctx, project_id) -> SensitivityReportResponse
#       （全工况投影数据通道服务面正门——GET /api/calc/sensitivity/{project_id}）
#   SensitivityReportResponse/SensitivityMetricModel（响应模型面——routers
#       response_model 直用，trust/compare「服务层 pydantic 冻结模型」先例：
#       禁协议层重复声明漂移面）
#   SensitivitySourceNotFoundError（404 面）
#
# 【行为规格】
#   R1 取数（最近完成结果集，零重算）：latest_calc_result 共享件取数
#      （B3-a 单源第八消费面——trust/compare 同款模式复制；携 task_id
#      溯源回显）；无结果集=not_found 注入 SensitivitySourceNotFoundError
#      （404，消息含 "先 POST /api/calc/run"）；结果文件缺失/损坏同归
#      404 面（裸 500 禁）。快照绑定语义（§12）：结果集只读投影——输入
#      变更经 stale 显式标记回显，禁止静默覆盖/重算。
#   R2 幅度行（design_offline_* 指标差全量返回）：行=结果集 summary 的
#      design 基线键域（厂级平键族：六出水指标+能耗+进水负荷+opex+碳——
#      run_full_calc summary 覆盖全工况，本端点纯投影零重算）；行序=
#      field_id 字典序（确定性）；design_value=基线值，values/deltas=
#      逐检修工况值与差（offline−design 绝对差——相对率归 FE 呈现面，
#      除零防御 FE 侧诚实跳过=tornadoBars design=0 同口径）；工况值缺席
#      （sparse）=键不出（NaN 无值键不出——compare R2 同口径）；全量含
#      零差行（当前零单元声明检修降级=pool.all_pools DSL 引擎就绪而
#      manifest condition_mappings 空——诚实零差非缺陷，b6e 设计档 §一.2；
#      单元侧未来声明映射后数值自然分化）。capex 不在 summary 平键链
#      （概算经装配链）——本端点无 capex 行（与「capex 无 avg 对」同
#      口径；逐工况概算装配=重算面，违背零重算冻结）。
#   R3 新鲜度（§12 口径）：stale=result_is_stale（design_hash≠当前
#      digest——trust/compare 同口径）；design_hash 回显=结果件
#      repro.design_hash（FE 比对真源）；repro 三元组+task_id 回显
#      （结果溯源面）。
#   R4 工况键集：condition_keys=plant.conditions 键域 design_offline_ 前缀
#      过滤（GR-20 冻结字面量镜像——core contracts.condition key() 拼接
#      规则，core 无导出常量，服务面解析用镜像注记）字典序；baseline_key
#      ="design"（ConditionSet.key 派生非字面量）；design 基线工况缺席
#      （结果集异形）=not_found 404 面 fail-loud（禁空基线冒充幅度面）。
#   R5 确定性：同结果集同响应（行序/键序全字典序；双跑字节同端点测试
#      常驻断言沿 compare 先例）。
#
# 【测试要求】端点集增量/形状与零差现状/无条件空集/确定性双跑/stale
#   语义/404 两面/AU-1 路径安全。
#
# 【参照】wave6-master-plan §批6e；批2d 欠账①（b2d-brief L32-33）；
#   services/compare.py（取数母本+模型先例）；services/trust.py
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.result_schema import (
    InvalidResultError,
    deserialize,
)

from waterprint_server.services import ServiceContext
from waterprint_server.services._shared.latest_calc import latest_calc_result
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "SensitivityMetricModel",
    "SensitivityReportResponse",
    "SensitivitySourceNotFoundError",
    "build_sensitivity_for_project",
]

# GR-20 冻结字面量镜像（R4）：design_offline_<unit_id> 前缀——core
# contracts.condition.ConditionSet.key 拼接规则的解析面镜像（core 无导出
# 常量；webapp jointView 键族镜像同款纪律）。
_OFFLINE_PREFIX: str = "design_offline_"


class SensitivitySourceNotFoundError(Exception):
    """全工况投影源不可得（项目无结果集/结果文件损坏/基线工况缺席）——404 面。"""


class SensitivityMetricModel(BaseModel):
    """幅度行：summary 平键 → design 基线值+逐检修工况值与差（R2）。"""

    model_config = ConfigDict(frozen=True)

    field_id: str
    design_value: float
    values: dict[str, float]
    deltas: dict[str, float]


class SensitivityReportResponse(BaseModel):
    """全工况投影报告（design_offline_* 指标差全量——R2/R3/R4）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    task_id: str
    stale: bool
    design_hash: str
    engine_version: str
    data_version: str
    baseline_key: str
    condition_keys: tuple[str, ...]
    rows: tuple[SensitivityMetricModel, ...]


def _metric_rows(
    summary: Mapping[str, Mapping[str, float]],
    offline_keys: tuple[str, ...],
    baseline_key: str,
) -> tuple[SensitivityMetricModel, ...]:
    """幅度行投影（R2）：design 基线键域 × 逐检修工况值与差——sparse 键不出。"""
    baseline = summary.get(baseline_key, {})
    rows: list[SensitivityMetricModel] = []
    for field_id in sorted(baseline):
        base = float(baseline[field_id])
        if not math.isfinite(base):
            continue  # NaN 无值键不出（compare R2 同口径）
        values: dict[str, float] = {}
        deltas: dict[str, float] = {}
        for key in offline_keys:
            raw = summary.get(key, {}).get(field_id)
            if raw is not None and math.isfinite(float(raw)):
                values[key] = float(raw)
                deltas[key] = float(raw) - base
        rows.append(
            SensitivityMetricModel(
                field_id=field_id,
                design_value=base,
                values=values,
                deltas=deltas,
            )
        )
    return tuple(rows)


def build_sensitivity_for_project(
    ctx: ServiceContext, project_id: str
) -> SensitivityReportResponse:
    """全工况投影正门：项目校验 → 结果集取数 → 幅度行聚合（R1~R5）。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    task_id, latest = latest_calc_result(
        ctx, project_id, not_found=SensitivitySourceNotFoundError
    )
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        raise SensitivitySourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    baseline_key = ConditionSet.key(OperatingCondition(flow_case=FlowCase.DESIGN))
    if baseline_key not in plant.summary:
        raise SensitivitySourceNotFoundError(
            f"项目 {project_id!r} 结果集缺 design 基线工况（结果集异形——先重算）"
        )
    offline_keys = tuple(
        sorted(key for key in plant.conditions if key.startswith(_OFFLINE_PREFIX))
    )
    return SensitivityReportResponse(
        project_id=project_id,
        task_id=task_id,
        stale=result_is_stale(latest, project),
        design_hash=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version,
        baseline_key=baseline_key,
        condition_keys=offline_keys,
        rows=_metric_rows(plant.summary, offline_keys, baseline_key),
    )
