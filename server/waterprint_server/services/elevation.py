"""elevation 服务用例：最近完成结果集 → 高程纵断+提升计划（core elevation 装配）。

输入:  项目 id + condition_key（可选——缺省=结果工况排序首键，显式回显）
输出:  ElevationResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE7 D1~D5/D10 2026-08-29；镜像测试 server/tests/test_elevation.py）
#
# 【公开接口】
#   build_elevation_for_project(ctx, project_id, condition_key=None)
#       -> ElevationResponse（elevation 数据通道服务面正门）
#   project_pump_stations(plan) -> tuple[PumpStationEntry, ...]
#       （D4 提升站位投影正门——PumpingPlan 五键直投影；R1 单测正门：
#       经端点非空 plan 结构性不可达[空损失水位单调不增——M5 接真损失
#       才可达]，直构非空 plan 的字段保真覆盖面走本函数）
#   ElevationResponse/ElevationStation/PumpStationEntry/WarningEntry
#       （响应模型面——routers response_model 直用，units.py 服务层
#       pydantic 冻结模型先例：禁协议层重复声明漂移面）
#   ElevationSourceNotFoundError（404 面）/InvalidElevationRequestError
#       （422 面）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：_latest_calc_result 复制 services/scene
#      同款取数模式（遍历 task_ids_for_project 取最末 done calc 的
#      status.result——消费时实时取，UF-37 统一口径；不 import scene
#      私有名，FE1 简报条款）；无结果集=ElevationSourceNotFoundError
#      （404，消息含"先 POST /api/calc/run"——SceneSourceNotFoundError
#      同语义）；结果文件缺失/损坏（OSError/InvalidResultError）同归
#      404 面（FE1 M4 路径安全族——裸 500 禁）。
#   R2 工况缺省：condition_key=None → sorted(plant.conditions)[0]（显式
#      回显于响应 condition_key——不猜测）；工况不在结果 = core.
#      build_profile 的 InvalidProfileError 转 InvalidElevationRequestError
#      （422 面，消息透传含合法工况集）。
#   R3 假设合成视图：{entry.key: entry.default for DEFAULT_ASSUMPTIONS}
#      + design.assumption_overrides（scene R3/jobs.worker._build_env
#      同款三行口径——计算与投影假设面一致）。
#   R4 装配口径（FE7 D2/D3/D4/D5）：
#      - losses=head_losses((), ...) 空段=沿程损失恒 0（管线几何归 M5
#        管线批——loss_in 如实呈现 0，前端注记）；
#      - inlet_config=_REL_DATUM ±0.00 相对标高常量（绝对标高设计输入
#        通道未接线——app_enumeration._REL_DATUM 同款先例；datum_note
#        下发注记，口径单一真源在服务面）；
#      - pumping=evaluate_pumping(profile, view) 一次装配（空站位列表
#        =全程自流合法终态，core pumps R4）；
#      - crest_elev=water_level+freeboard 服务端投影（响应 DTO 派生
#        字段——前端零标高推算红线不破）。
#   R5 确定性：同结果集同响应（core 纯投影+服务层零随机面——双跑
#      sort_keys 字节同，端点测试常驻断言）。
#
# 【测试要求】缺省工况回显、十字段恰合+crest 投影逐站、双跑字节同、
#   422/404 异常面、AU-1 穿越 4xx+目录快照零新增。
#
# 【参照】FE7 简报 D1~D5/D10；scene.py 服务先例；UF-33（core 调用经
#   waterprint.app+waterprint.contracts 允许面——waterprint.elevation
#   直连边经 docs/structure-graph.md §1b 补登，FE7 总控裁决 2026-08-29）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from pydantic import BaseModel, ConfigDict
from waterprint import app as core
from waterprint.contracts.result_schema import InvalidResultError, deserialize
from waterprint.contracts.unit_api import Severity
from waterprint.elevation import build_profile, evaluate_pumping, head_losses
from waterprint.elevation.profile import InvalidProfileError
from waterprint.elevation.pumps import PumpingPlan

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "ElevationResponse",
    "ElevationSourceNotFoundError",
    "ElevationStation",
    "InvalidElevationRequestError",
    "PumpStationEntry",
    "WarningEntry",
    "build_elevation_for_project",
    "project_pump_stations",
]

# D2 v1 基准面：±0.00 相对标高（工程相对标高惯例；绝对标高设计输入通道
# 未接线随 server 批/M5 沿册——进厂标高是 design 态输入非假设，profile
# R2 口径；app_enumeration._REL_DATUM 同款零默认数值面[0/0 字面量]）。
_REL_DATUM: Final[Mapping[str, float]] = MappingProxyType(
    {"water_level": 0.0, "ground_elev": 0.0}
)

# D2 口径注记（服务面单一真源下发——前端不硬编码）。
_DATUM_NOTE: Final[str] = "相对标高：进厂水面=±0.00——绝对标高输入通道未接线"


class ElevationSourceNotFoundError(RuntimeError):
    """无最近完成结果集可消费——404 面（先运行计算）。"""


class InvalidElevationRequestError(ValueError):
    """elevation 请求非法（工况不在结果）——422 面（透传 core 工况集文本）。"""


class WarningEntry(BaseModel):
    """core Warning 序列化形状（UF-17 冻结结构：来源+调节方向+影响面）。"""

    model_config = ConfigDict(frozen=True)

    severity: Severity
    source: str
    message: str
    param_key: str | None = None
    condition_key: str | None = None
    affected_unit_ids: tuple[str, ...] = ()


class ElevationStation(BaseModel):
    """纵断单站（ProfileStation 九字段+crest_elev 服务端投影=D5）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    water_level: float
    floor_elev: float
    ground_elev: float
    bury_depth: float
    freeboard: float
    water_depth: float
    loss_in: float
    design_flow: float
    crest_elev: float


class PumpStationEntry(BaseModel):
    """需提升站位（core PumpStation 五字段直投影）。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    static_head: float
    total_head: float
    design_flow: float
    condition_key: str


class ElevationResponse(BaseModel):
    """高程纵断响应（D1~D5 契约面：工况索引+注记+站位+提升+双警告面）。

    AUDIT2 C-1：+stale 旗标（结果集 design_hash≠当前 design digest——
    投影含活档假设[I-1]时消费方据此显式提示，禁静默使用）。
    """

    model_config = ConfigDict(frozen=True)

    project_id: str
    condition_key: str
    conditions: tuple[str, ...]
    datum_note: str
    stations: tuple[ElevationStation, ...]
    pump_stations: tuple[PumpStationEntry, ...]
    drop_warnings: tuple[WarningEntry, ...]
    warnings: tuple[WarningEntry, ...]
    stale: bool


def _latest_calc_result(ctx: ServiceContext, project_id: str) -> Mapping[str, Any]:
    """最近完成计算结果集（scene._latest_calc_result 同款取数模式复制）。"""
    latest: Mapping[str, Any] | None = None
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(task_id)
        if status.kind == "calc" and status.state == "done" and status.result:
            latest = status.result
    if latest is None:
        raise ElevationSourceNotFoundError(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return latest


def project_pump_stations(plan: PumpingPlan) -> tuple[PumpStationEntry, ...]:
    """D4 提升站位投影（PumpingPlan.stations → 响应五键——R1 单测正门）。

    空站位列表=全程自流合法终态直投影（core pumps R4——空元组合法返回）。
    """
    return tuple(
        PumpStationEntry(
            unit_id=pump.unit_id,
            static_head=pump.static_head,
            total_head=pump.total_head,
            design_flow=pump.design_flow,
            condition_key=pump.condition_key,
        )
        for pump in plan.stations
    )


def build_elevation_for_project(
    ctx: ServiceContext, project_id: str, condition_key: str | None = None
) -> ElevationResponse:
    """纵断正门：项目校验 → 结果集取数 → 反序列化 → 假设合成 → core 装配 → 投影。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    latest = _latest_calc_result(ctx, project_id)
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        # FE1 M4（路径安全族）：结果文件缺失/损坏归一 404 领域面——裸 500 禁。
        raise ElevationSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    chosen = condition_key if condition_key is not None else sorted(plant.conditions)[0]
    assumptions = {entry.key: entry.default for entry in core.DEFAULT_ASSUMPTIONS}
    assumptions.update(project.design.assumption_overrides)
    # D3 空段损失：head_losses(()) 恒 0（管线几何归 M5——loss_in 如实呈现）。
    losses = head_losses((), ctx=(project_id, chosen), assumptions=assumptions)
    try:
        profile = build_profile(plant, losses, _REL_DATUM, assumptions, chosen)
    except InvalidProfileError as exc:
        raise InvalidElevationRequestError(str(exc)) from exc
    plan = evaluate_pumping(profile, assumptions)
    return ElevationResponse(
        project_id=project_id,
        condition_key=profile.condition_key,
        conditions=tuple(sorted(plant.conditions)),
        datum_note=_DATUM_NOTE,
        stale=result_is_stale(latest, project),
        stations=tuple(
            ElevationStation(
                unit_id=station.unit_id,
                water_level=station.water_level,
                floor_elev=station.floor_elev,
                ground_elev=station.ground_elev,
                bury_depth=station.bury_depth,
                freeboard=station.freeboard,
                water_depth=station.water_depth,
                loss_in=station.loss_in,
                design_flow=station.design_flow,
                crest_elev=station.water_level + station.freeboard,  # D5 服务端投影
            )
            for station in profile.stations
        ),
        pump_stations=project_pump_stations(plan),
        drop_warnings=tuple(
            WarningEntry(
                severity=warning.severity,
                source=warning.source,
                message=warning.message,
                param_key=warning.param_key,
                condition_key=warning.condition_key,
                affected_unit_ids=warning.affected_unit_ids,
            )
            for warning in plan.drop_warnings
        ),
        warnings=tuple(
            WarningEntry(
                severity=warning.severity,
                source=warning.source,
                message=warning.message,
                param_key=warning.param_key,
                condition_key=warning.condition_key,
                affected_unit_ids=warning.affected_unit_ids,
            )
            for warning in profile.warnings
        ),
    )
