"""site 用例：间距校核装配（design.site 摆放+最近结果足迹+kb 阈值 → core 报告）。

输入:  项目 id + condition_key（可选——缺省=结果工况排序首键）+装配束
输出:  SpacingReportResponse（violations+uncalculated——L4b 黄红标示数据面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（L4b 2026-09-03；镜像测试 server/tests/services/test_site.py）
#
# 【公开接口】
#   build_spacing_for_project(ctx, project_id, condition_key=None)
#       -> SpacingReportResponse（间距校核服务面正门）
#   SpacingReportResponse/SpacingViolationEntry（响应模型——routers
#       response_model 直用，scene SceneResponse 先例）
#   InvalidSpacingRequestError（工况不在结果——422 面，ValueError 族）
#
# 【行为规格】
#   R1 装配三源（总控预裁 6——裁判在 core，服务层零几何）：
#      placements 自 project.design.site.structures（x/y/rotation 直取）；
#      footprints 自最近完成结果集 dims 投影（contracts PROJECTION_TABLE
#      primitive_dims 槽：length/width 直取、diameter→等宽[等宽方形]——
#      webapp 足迹同族口径；无槽/无键=该单元未计算）；thresholds 自 kb
#      spacing_check 条目（expression `min_clearance_m >= <float>` 本服务
#      唯一解析面——core 零 DSL；unit_kinds 空=全对通用 None/非空=经
#      design.nodes kind 解析为本项目 unit_id 成员集 frozenset）。
#   R2 降级不拒（预裁 4）：无完成计算/结果文件缺失或损坏/空工况集
#      =violations 空+uncalculated 全量 sorted 返回 200——编辑器部分可用
#      语义（与 scene 404 语义差异记档：scene 是数据源缺失，校核是可
#      降级辅助）；工况缺省=sorted(conditions)[0]（scene 同构不猜测），
#      显式工况不在结果=InvalidSpacingRequestError 422（消息含合法集）。
#   R3 fail-visible：kb spacing_check expression 形态越界=RuntimeError
#      显式拒（constraints 装载守卫同族——禁静默跳条）。
#   R4 确定性继承：同项目同结果双跑 JSON(sort_keys) 字节同（core 纯
#      函数 R4+服务层零加料；端点测试常驻断言）。
#
# 【测试要求】装配正路（通用 WARN 违规）/限定对解析（kind→unit_id 集）/
#   降级三面（无结果·文件缺失）/工况非法 422/项目不存在 404/双跑字节同/
#   kb 表达式越界 fail-visible。
#
# 【参照】L4 简报 §一 L4b/§三预裁 2·4·6·8；services/scene.py 同构先例
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.result_schema import (
    InvalidResultError,
    PlantResult,
    deserialize,
)
from waterprint.geometry import spacing as core_spacing

from waterprint_server.services import ServiceContext
from waterprint_server.services import constraints as constraints_service
from waterprint_server.services.projects import read_project

__all__ = [
    "InvalidSpacingRequestError",
    "SpacingReportResponse",
    "SpacingViolationEntry",
    "build_spacing_for_project",
]

# kb spacing_check expression 契约（README 钉面——唯一解析面 R3）
_MIN_CLEARANCE_RE: Final[re.Pattern[str]] = re.compile(
    r"^min_clearance_m >= ([0-9]+(?:\.[0-9]+)?)$"
)


class SpacingViolationEntry(BaseModel):
    """违规行（对内 a<b——core 全序继承；wire 形态=简报 §一冻结）。"""

    model_config = ConfigDict(frozen=True)

    a: str
    b: str
    clearance_m: float
    threshold_m: float
    severity: str


class SpacingReportResponse(BaseModel):
    """间距校核响应（violations+uncalculated——未计算=降级全量非拒）。"""

    model_config = ConfigDict(frozen=True)

    violations: tuple[SpacingViolationEntry, ...]
    uncalculated: tuple[str, ...]


class InvalidSpacingRequestError(ValueError):
    """间距校核请求非法（工况不在结果）——422 面（透传合法工况集）。"""


def _latest_done_result(ctx: ServiceContext, project_id: str) -> Mapping[str, Any] | None:
    """最近完成计算结果集（无= None——scene 同款取数模式的降级变体 R2）。"""
    latest: Mapping[str, Any] | None = None
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(task_id)
        if status.kind == "calc" and status.state == "done" and status.result:
            latest = status.result
    return latest


def _load_plant(latest: Mapping[str, Any]) -> PlantResult | None:
    """结果集反序列化（不可读/空工况集=None——R2 降级面两分支）。"""
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError):
        return None  # 结果不可读=降级（可降级辅助——scene 404 语义差异记档）
    if not plant.conditions:
        return None  # 空工况集=无足迹可投影（降级同面）
    return plant


def _footprint(unit_id: str, dims: Mapping[str, float]) -> tuple[float, float] | None:
    """结果 dims 投影足迹（PROJECTION_TABLE primitive_dims 槽——R1）。

    length/width 槽直取；缺则 diameter→等宽方形；无槽/无键=None（未计算）。
    """
    row = PROJECTION_TABLE.get(unit_id)
    if row is None:
        return None
    slots = row.primitive_dims
    length_key = slots.get("length")
    width_key = slots.get("width")
    if (
        length_key is not None
        and width_key is not None
        and length_key in dims
        and width_key in dims
    ):
        return (float(dims[length_key]), float(dims[width_key]))
    diameter_key = slots.get("diameter")
    if diameter_key is not None and diameter_key in dims:
        diameter = float(dims[diameter_key])
        return (diameter, diameter)
    return None


def _thresholds_from_kb(
    ctx: ServiceContext, project_id: str
) -> tuple[core_spacing.SpacingThreshold, ...]:
    """kb spacing_check → 结构化阈值（expression 解析+kind→unit_id 成员集）。

    unit_kinds 空=全对通用（None）；非空=design.nodes 中 kind ∈ 键集的
    unit_id 集（frozenset——无成员=空集恒不命中，core R3 语义）。
    """
    project = read_project(ctx, project_id)  # 缓存一致面（正门同款取数）
    kinds_of = {
        unit_id: str(params.get("kind", unit_id))
        for unit_id, params in project.design.nodes.items()
    }
    catalog = constraints_service.list_constraints(ctx.settings.data_dir)
    thresholds: list[core_spacing.SpacingThreshold] = []
    for entry in catalog.entries:
        if entry.kind != "spacing_check":
            continue
        match = _MIN_CLEARANCE_RE.match(entry.expression)
        if match is None:
            raise RuntimeError(
                f"spacing_check 条目 {entry.key!r} expression 形态非法："
                f"{entry.expression!r}（契约 `min_clearance_m >= <float>`——"
                "README 钉面，本服务唯一解析面 R3）"
            )
        scope = (
            None
            if not entry.unit_kinds
            else frozenset(
                unit_id for unit_id, kind in kinds_of.items() if kind in set(entry.unit_kinds)
            )
        )
        thresholds.append(
            core_spacing.SpacingThreshold(
                unit_kinds=scope,
                min_clearance_m=float(match.group(1)),
                severity=entry.severity,
            )
        )
    return tuple(thresholds)


def build_spacing_for_project(
    ctx: ServiceContext, project_id: str, condition_key: str | None = None
) -> SpacingReportResponse:
    """间距校核正门：项目校验 → 三源装配 → core 报告（R2 降级不拒）。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    placements = {
        unit_id: (structure.x, structure.y, structure.rotation)
        for unit_id, structure in project.design.site.structures.items()
    }
    uncalculated_full = tuple(sorted(placements))
    latest = _latest_done_result(ctx, project_id)
    plant = _load_plant(latest) if latest is not None else None
    if plant is None:
        return SpacingReportResponse(violations=(), uncalculated=uncalculated_full)
    chosen = (
        condition_key if condition_key is not None else sorted(plant.conditions)[0]
    )
    if chosen not in plant.conditions:
        raise InvalidSpacingRequestError(
            f"工况 {chosen!r} 不在结果（合法 {sorted(plant.conditions)}——"
            "spacing 按工况索引足迹，R2）"
        )
    snapshots = plant.conditions[chosen]
    footprints = {
        unit_id: (
            _footprint(unit_id, snapshots[unit_id].dims)
            if unit_id in snapshots
            else None
        )
        for unit_id in placements
    }
    report = core_spacing.spacing_report(
        placements, footprints, _thresholds_from_kb(ctx, project_id)
    )
    return SpacingReportResponse(
        violations=tuple(
            SpacingViolationEntry(
                a=row.a, b=row.b, clearance_m=row.clearance_m,
                threshold_m=row.threshold_m, severity=row.severity,
            )
            for row in report.violations
        ),
        uncalculated=report.uncalculated,
    )
