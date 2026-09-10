"""可行域引导服务用例：design-map 同步求值装配（FD PD6 甲案·同步直返）。

输入:  project_id + unit_id + 轴声明（field_id/step?/range?）
输出:  DesignMapResponse（core DesignMap payload 的服务层冻结响应面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FD 批 PD6 终裁 2026-09-09；镜像测试 server/tests/routers/
#   test_calc_design_map.py）
#
# 【公开接口】
#   compute_design_map(ctx, project_id, unit_id, axes) -> DesignMapResponse
#       （同步直返——≤2500 点 ~1s 级不进任务队列，PD6 呈裁②；
#        路由层 asyncio.to_thread 承载防事件循环阻塞）
#   DesignMapResponse 族（响应模型面——routers response_model 直用，
#       units/scene 先例：禁协议层重复声明漂移面；model_validate 消费
#       core payload=双面漂移防线）
#   class DesignMapSourceNotFoundError(Exception)：项目无该单元——404 面
#
# 【行为规格】
#   R1 固定参数装配（PD1 server 面）：manifest defaults ∪ design 覆盖值
#      （数值叶，剔除 kind 键——upstream_context 同口径；core 正门收
#      显式映射不自查项目，分层洁癖）。
#   R2 约束装配（PD2）：constraint_kb unit_kinds 过滤 ∩ 项目勾选
#      （design.constraint_choices 值 "on"——CP2 档位语义）——与枚举
#      EnumerationOptions.constraints 同数据源（webapp toPayloadItems
#      的 server 侧同式）。
#   R3 工况=design.checked_units（枚举提交同口径——build_condition_set
#      正门恒非空）。
#   R4 错误面：项目缺=ProjectNotFoundError 404；单元不在 design.nodes=
#      DesignMapSourceNotFoundError 404（PD6）；轴声明非法=core
#      InvalidDesignMapError 422；护栏超限=DesignMapTooLarge 400——
#      全部经 main 异常映射表（router 零 if 零业务）。
#
# 【实现注记】env 装配为 services 面首例直算（scene/elevation 消费
#   存量结果集无 env）：engine_version=ENGINE_VERSION（worker._build_env
#   同源）；系数经 app 再导出面 core.load_coefficients（CI 补笔：直连
#   registry 违 UF-33 server 单入口契约——server 面 import-linter 拦；
#   jobs/datapack._YamlCoefficients 为 worker 进程池镜像装载，
#   B4 双胞胎在册——同步面不经 spawn，直取 L1 唯一真源）；版本聚合
#   取 coefficients 单源（price_book 空——run_design_map 零消费）。
#
# 【测试要求】装配口径（fixed_params/constraints）、404/422/400 面、
#   端到端形态（axes/stats/segments）、双跑字节同。
#
# 【参照】briefs/task-FD-plan.md PD6/PD1/PD2；worker._run_enumerate 同构
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, ConfigDict
from waterprint import app as core
from waterprint.contracts.condition import build_condition_set
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.run_env import RunEnv

from waterprint_server.services import ServiceContext
from waterprint_server.services import constraints as constraints_service
from waterprint_server.services.projects import read_project
from waterprint_server.settings import ENGINE_VERSION

__all__ = [
    "DesignMapResponse",
    "DesignMapSourceNotFoundError",
    "compute_design_map",
]

_CHOICE_ON: Final[str] = "on"  # CP2 D1：勾选值恒 "on"（解勾=删键）


class DesignMapSourceNotFoundError(Exception):
    """项目内无可行域目标单元（design.nodes 未声明）——404 面。"""


class DesignAxisRange(BaseModel):
    """轴扫描区间（实际扫描范围=用户覆盖 ?? manifest——PD3 附注）。"""

    model_config = ConfigDict(frozen=True)

    min: float
    max: float


class DesignAxisMeta(BaseModel):
    """轴元数据（grid_fields 三字段同源+range/step/points——PD3）。"""

    model_config = ConfigDict(frozen=True)

    field_id: str
    dim: str
    label_zh: str | None
    range: DesignAxisRange
    step: float
    points: int


class DesignMapStats(BaseModel):
    """统计面（total/feasible/infeasible/feasible_ratio）。"""

    model_config = ConfigDict(frozen=True)

    total: int
    feasible: int
    infeasible: int
    feasible_ratio: float


class DesignSegment(BaseModel):
    """可行段（1D——[{start,end}] 值域对）。"""

    model_config = ConfigDict(frozen=True)

    start: float
    end: float


class DesignWidestSegment(BaseModel):
    """最宽可行段（诊断块——含质心）。"""

    model_config = ConfigDict(frozen=True)

    start: float
    end: float
    centroid: float


class DesignAxisDiagnosis(BaseModel):
    """诊断块逐轴面（PD9——无可行段 None 不编造）。"""

    model_config = ConfigDict(frozen=True)

    field_id: str
    magnitude: float | None
    widest_segment: DesignWidestSegment | None
    recommended_value: float | None


class DesignMapDiagnosis(BaseModel):
    """诊断块（feasible_ratio+逐轴面）。"""

    model_config = ConfigDict(frozen=True)

    feasible_ratio: float
    axes: tuple[DesignAxisDiagnosis, ...]


class DesignMapResponse(BaseModel):
    """可行域产物响应面（core DesignMap.payload 的冻结模型）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    axes: tuple[DesignAxisMeta, ...]
    stats: DesignMapStats
    axis_values: tuple[tuple[float, ...], ...]
    segments: tuple[DesignSegment, ...] | None
    mask: tuple[tuple[int, ...], ...] | None
    constraint_coverage: str
    diagnosis: DesignMapDiagnosis


def _fixed_params(project: ProjectFile, unit_id: str) -> dict[str, float]:
    """R1 固定参数装配：manifest defaults ∪ design 覆盖（PD1 server 面）。"""
    fixed: dict[str, float] = {}
    discovered = core.discover_units()
    if unit_id in discovered:
        fixed.update(
            {spec.field_id: spec.default for spec in discovered[unit_id][0].params}
        )
    node = project.design.nodes.get(unit_id)
    if isinstance(node, dict):
        for key, value in node.items():
            if key != "kind" and isinstance(value, int | float) and not isinstance(value, bool):
                fixed[key] = float(value)
    return fixed


def _constraints(
    ctx: ServiceContext, project: ProjectFile, unit_id: str
) -> tuple[core.Constraint, ...]:
    """R2 约束装配：kb unit_kinds ∩ 项目勾选（"on"——CP2 档位语义）。"""
    chosen = project.design.constraint_choices
    return tuple(
        core.Constraint(key=entry.key, expression=entry.expression, source=entry.source)
        for entry in constraints_service.list_constraints(ctx.settings.data_dir).entries
        if unit_id in entry.unit_kinds and chosen.get(entry.key) == _CHOICE_ON
    )


def _env(data_dir: Path, project: ProjectFile) -> RunEnv:
    """RunEnv 装配（services 直算首例注记见规格头）。"""
    lib = core.load_coefficients(data_dir / "coefficients")
    assumptions = {entry.key: entry.default for entry in core.DEFAULT_ASSUMPTIONS}
    assumptions.update(project.design.assumption_overrides)
    return RunEnv(
        engine_version=ENGINE_VERSION,
        data_version=f"coefficients@{lib.data_version}",
        assumptions=assumptions,
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def compute_design_map(
    ctx: ServiceContext,
    project_id: str,
    unit_id: str,
    axes: list[dict[str, Any]],
) -> DesignMapResponse:
    """可行域同步求值正门（甲案：装配→core.run_design_map→响应模型校验）。"""
    project = read_project(ctx, project_id)
    if unit_id not in project.design.nodes:
        raise DesignMapSourceNotFoundError(
            f"项目 {project_id!r} 无单元 {unit_id!r}（可行域目标须为 design.nodes "
            "已声明单元——FD 单单元语义，PD6 404 面）"
        )
    product = core.run_design_map(
        project,
        unit_id,
        build_condition_set(list(project.design.checked_units)),
        _env(ctx.settings.data_dir, project),
        core.DesignMapOptions(
            axes=tuple(axes),
            fixed_params=_fixed_params(project, unit_id),
            constraints=_constraints(ctx, project, unit_id),
        ),
    )
    return DesignMapResponse.model_validate(product.payload())
