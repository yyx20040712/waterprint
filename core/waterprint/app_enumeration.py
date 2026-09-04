"""用例编排伴生件：枚举选项/产出类型 + 产物导出薄壳 + 枚举上游快照重建。

输入:  app.run_enumeration 的编排部件（类型面 + 上游工况重建 + 导出分发）
输出:  EnumerationOptions/EnumerationOutcome/ArtifactKindNotReady/
       export_artifact/upstream_context（app.py 再导出——UF-33 单入口保持）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2-SOL D2 裁决 2026-08-26；app.py 500 行预算的宪法 §2
#   "超限拆文件"正解——伴生件承载类型与纯函数，装配语义仍归 app：
#   run_enumeration/assemble 留 app.py，本文件经 app 再导出对server
#   保持 UF-33 单入口）
#
# 【公开接口】
#   class EnumerationOptions(不可变)：constraints 序列（Constraint）/
#       sort_by（默认 "margin_min"）/ascending（默认 False=裕度宽优先）/
#       limit（None=取全部；分页默认 200 在服务层，§12.2）
#   class EnumerationOutcome(不可变)：rows/total_feasible/truncated/
#       diagnosis（无解时非 None）/grid（网格元信息）
#   class ArtifactKindNotReady(Exception)：产物 kind 未就绪——消息注明
#       归属（audit=M4/estimate=M3），禁静默空产物
#   export_artifact(kind, plant, template, out) -> bytes
#       分发薄壳：kind="calcbook"→render_calcbook（M1b trace 正门，
#       签名按其收口——plant 自带 trace）；kind="dxf"→M2 出图批
#       （unit_id 缺省+site_design=全厂总图——site_layout 接线，
#       M5 兑现）；kind="ifc"→SC1 BIM 模型批（build_scene→build_ifc
#       →write_ifc）；未就绪/未知 kind=ArtifactKindNotReady
#   class UpstreamSource(不可变)：上游取数面四字段束（units/edges/
#       design/plant——app 装配与执行产物快照，装配语义仍归 app）
#   upstream_context(source, unit_id, condition, env) -> UnitContext：
#       枚举上游快照重建（execute_graph 既有产物 UF-42 投影表反解入流
#       股——禁另写上游计算，D2）
#
# 【依赖足迹】（I-4 R1 修正 2026-08-26：二审实录——原"只消费 L0 契约
#   类型"表述失实撤回）零 waterprint.app 依赖（防 import 环成立）；
#   实消费=L0 契约九模块 + L3 solution 三模块（constraints/diagnose/
#   grid——类型面注解）+ L4.project-trace 正门（trace：render_calcbook
#   分发与 TraceCollector 占位）。DRAFT 批 D5（2026-08-26）dxf 分支
#   追加：L0 contracts.drawing_projection（UF-32 对照表）+ L3 elevation
#   两模块（losses/profile）+ L3 drafting 四模块（styles/plan_view/
#   section_view/dxf_writer）+ L1 registry.assumptions；SC1（2026-09-04）
#   ifc 分支追加：L0 contracts.project_schema（SiteDesign——site_design
#   透传参数）+ L3 geometry.scene（build_scene）+ L3 ifc_export 正门
#   （build_ifc/write_ifc）；M5（2026-09-04）dxf 总图分支追加：L3
#   drafting.site_plan（site_layout/SiteOptions——unit_id 缺省的全厂
#   总图编排；InvalidSitePlanError 不捕获直上）——全部沿
#   import-linter 层序向下合法边（app|app_enumeration 居 drafting/
#   elevation/registry 之上）；结构图谱 §1b 的 app_enumeration 行
#   未列上述边（真实 import 扫描=B3 待办，门禁暂不拦——SERVER 批
#   I-4 注记同款状态，报告申报）。该文件的 solution/trace 依赖边当前
#   不在 import-linter 层序管辖（pyproject 未列本模块）——structure-
#   graph §1a 节点行+pyproject 层序登记（waterprint.app |
#   app_enumeration 同层并列）+§1b 边表口径为 **server 批开工前置
#   条件**（I-4 升格）。
#
# 【行为规格】
#   R1 类型面不可变：两 dataclass frozen+final；Options 四字段默认值
#      为 core 侧口径（取全部/裕度宽优先）。
#   R2 上游重建确定性：水流股按 UF-42 三键槽反解 WaterFlow（q_design
#      派生重建无损）/泥股三键槽反解 SludgeFlow；水质按端口前缀逐指
#      标反解；参数面=manifest 默认 ∪ design 节点覆盖（execute_graph
#      已过 GR-02 守卫）。工况映射（ADR-007）当前 13 单元全空——非空
#      映射与网格行的优先序归 server 批定义（UF-36 注记并入记档）。
#   R3 产物导出字节确定性由 render_calcbook R4 承载（本文件零落盘逻辑）。
#
# 【参照】重写计划 §12.4/§13.1；ADR-005；简报 M2-SOL D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, final

from pandas import DataFrame  # type: ignore[import-untyped]  # pandas-stubs 未随包分发

from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.project_schema import DesignState, SiteDesign
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Unit, UnitContext
from waterprint.drafting.dxf_writer import DrawingMeta, write_dxf
from waterprint.drafting.plan_view import unit_plan
from waterprint.drafting.section_view import unit_section
from waterprint.drafting.site_plan import SiteOptions, site_layout
from waterprint.drafting.styles import EntityGroup, base_styles
from waterprint.elevation.losses import head_losses
from waterprint.elevation.profile import build_profile
from waterprint.geometry.scene import build_scene
from waterprint.ifc_export import build_ifc, write_ifc
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
from waterprint.solution.constraints import Constraint
from waterprint.solution.diagnose import DiagnosisReport
from waterprint.solution.grid import Grid
from waterprint.trace import TraceCollector, render_calcbook

__all__ = [
    "ArtifactKindNotReady",
    "Constraint",
    "EnumerationOptions",
    "EnumerationOutcome",
    "UpstreamSource",
    "export_artifact",
    "upstream_context",
]


@dataclass(frozen=True)
@final
class UpstreamSource:
    """上游取数面（不可变）：装配产物与执行结果四字段束（app 构造）。"""

    units: Mapping[str, Unit]
    edges: tuple[Edge, ...]
    design: DesignState
    plant: PlantResult


@dataclass(frozen=True)
@final
class EnumerationOptions:
    """枚举选项（不可变）：约束序列/排序键/方向/截断上限（None=取全部）。"""

    constraints: tuple[Constraint, ...] = ()
    sort_by: str = "margin_min"
    ascending: bool = False
    limit: int | None = None

    def __post_init__(self) -> None:
        """constraints 序列归一 tuple（裸 str 拒，I-2 同款防线）。"""
        if isinstance(self.constraints, str):
            raise TypeError(
                "EnumerationOptions.constraints 必须为约束序列，不接受裸 str"
                f"（逐字符拆解为伪键）：得到 {self.constraints!r}"
            )
        object.__setattr__(self, "constraints", tuple(self.constraints))


@dataclass(frozen=True)
@final
class EnumerationOutcome:
    """枚举产出（不可变）：有序行/可行总数/截断标注/无解诊断/网格元信息。"""

    rows: DataFrame
    total_feasible: int
    truncated: bool
    diagnosis: DiagnosisReport | None
    grid: Grid


class ArtifactKindNotReady(Exception):  # noqa: N818  # 名载归属批次（D2 冻结），LoopDivergence 先例
    """产物 kind 未就绪（audit=M4/dxf=M2 出图批/estimate=M3）——GR-11 族。"""


_EXPORT_OPTIONS: Final[frozenset[str]] = frozenset({"unit_id", "condition_key"})


def _check_export_options(options: Mapping[str, str | None]) -> None:
    """导出选项键白名单（未知键拒——GR-09 精神，防拼写漂移静默忽略）。"""
    unknown = frozenset(options) - _EXPORT_OPTIONS
    if unknown:
        raise ArtifactKindNotReady(
            f"export_artifact 未知选项：{sorted(unknown)}"
            f"（合法 {sorted(_EXPORT_OPTIONS)}）"
        )


def export_artifact(  # noqa: PLR0913  # SC1 D6 钦定 keyword-only 两参（assumptions/site_design——ifc 分支消费）；5 参预算与签名主授权冲突，行内豁免沿 N818 同款先例
    kind: str,
    plant: PlantResult,
    template: Path,
    out: Path,
    *,
    assumptions: Mapping[str, float] | None = None,
    site_design: SiteDesign | None = None,
    **options: str | None,
) -> bytes:
    """产物导出分发薄壳（UF-33）：calcbook 接 M1b trace 正门；dxf 接 M2 出图批；ifc 接 BIM 模型批。

    D5 扩展：unit_id 关键字参数（默认 None）——kind="dxf" 单单元出图必填；
    缺省+site_design=全厂总图（M5 兑现），缺省且无 site_design=诚实拒绝；
    calcbook 分支签名零变（unit_id 不消费）。
    R1-1 扩展（2026-08-26）：condition_key 关键字参数（默认 None）——
    dxf 工况显式选择；两选项经 **options 透传（签名 5 参预算合规——
    调用形态 export_artifact(kind, plant, template, out, unit_id=…,
    condition_key=…) 与命名参数完全同形）。
    SC1 扩展（2026-09-04）：keyword-only assumptions/site_design 两参
    （默认 None）——kind="ifc" 消费（build_scene 假设视图与 site 装配
    透传，services/scene.py R3/R5 同口径；None assumptions=默认假设表
    兜底）；其余分支零消费。
    M5 扩展（2026-09-04）：site_design 追及 dxf 分支（unit_id 缺省的
    全厂总图编排——site_layout 接线；dxf 链自建假设视图故 assumptions
    零涉）。
    """
    _check_export_options(options)
    if kind == "calcbook":
        return render_calcbook(plant.trace, plant, template, out).read_bytes()
    if kind == "dxf":
        if options.get("condition_key") is None and plant.conditions:
            warnings.warn(
                "未指定工况，取 design 档出图——多工况请显式传 condition_key",
                stacklevel=2,  # 栈级 2=指向 export_artifact 调用方
            )
        return _export_dxf(
            plant, options.get("unit_id"), out, options.get("condition_key"),
            site_design=site_design,
        )
    if kind == "ifc":
        if options.get("condition_key") is None and plant.conditions:
            warnings.warn(
                "未指定工况，取 design 档出模型——多工况请显式传 condition_key",
                stacklevel=2,  # 栈级 2=指向 export_artifact 调用方（dxf 同构）
            )
        merged = assumptions if assumptions is not None else {
            entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS
        }
        chosen = options.get("condition_key")
        if chosen is None and plant.conditions:
            chosen = sorted(plant.conditions)[0]
        if chosen is None:
            # R0（总控亲验收口）：空工况集禁裸传 build_scene（None 入
            # 「工况不在结果」消息=mypy arg-type 红）——UF-33 诚实拒绝。
            raise ArtifactKindNotReady(
                "产物 kind 'ifc' 需至少一个工况（结果集工况为空——"
                "先重算；禁静默空产物，UF-33）"
            )
        graph = build_scene(plant, merged, chosen, site_design=site_design)
        model = build_ifc(graph)
        write_ifc(model, out)
        return out.read_bytes()
    owners = {"audit": "M4", "estimate": "M3"}
    owner = owners.get(kind, "未知 kind（合法面 calcbook/audit/dxf/estimate/ifc）")
    raise ArtifactKindNotReady(
        f"产物 kind {kind!r} 未就绪（归属：{owner}；禁静默空产物，UF-33）"
    )


# DXF 导出 v1 基准面：未传设计标高时以 ±0.00 相对标高出图（工程相对标高
# 惯例；绝对标高设计输入通道随 server 批/M5 接线——进厂标高是 design
# 态输入非假设，profile R2 口径，此处零默认数值面[0/0 字面量]）。
_REL_DATUM: Final[Mapping[str, float]] = MappingProxyType(
    {"water_level": 0.0, "ground_elev": 0.0}
)


def _export_dxf(
    plant: PlantResult,
    unit_id: str | None,
    out: Path,
    condition_key: str | None = None,
    site_design: SiteDesign | None = None,
) -> bytes:
    """dxf 内部编排（D5）：elevation→plan+section（经 UF-32 对照表）→write_dxf。

    R1-1 工况显式化：condition_key=None 取首档（当前装配序=design）+
    UserWarning（不再静默——profile R3"禁静默取首档"口径对齐）；显式值
    未知即拒（合法面=plant.conditions 键集）。
    M5（2026-09-04）：unit_id 缺省分支=全厂总图编排——site_design 透传
    时 site_layout（design 态布置+工况快照纯投影）直接出图；无 site_design
    =诚实拒绝（server 单产物通道有透传，批量面暂不支持——M5 注记）。
    unit_id 给定路径原样零改（含不在工况图/无纵断站既有拒绝）。
    site_plan.InvalidSitePlanError 不捕获直上（L3 领域异常——server 侧
    映射归既有 exception handler 链）。
    """
    if condition_key is None:
        condition_key = next(iter(plant.conditions), "")  # Warning 已在上层发出
    elif condition_key not in plant.conditions:
        raise ArtifactKindNotReady(
            f"工况 {condition_key!r} 不在结果（合法 "
            f"{sorted(plant.conditions)}——dxf 出图工况校验，R1-1）"
        )
    if unit_id is None:
        if site_design is None:
            raise ArtifactKindNotReady(
                "产物 kind 'dxf' 全厂总图导出须传 site_design（server 单产物"
                "通道；批量面暂不支持——M5 注记）"
            )
        styles = base_styles()
        entities = site_layout(
            site_design,
            plant,
            styles,
            # 同构直读：schema SitePlanOptions{coord_grid,wind_rose} 与
            # drafting SiteOptions 字段同名同型（M5 总裁实证注——零换算面）。
            SiteOptions(
                coord_grid=site_design.options.coord_grid,
                wind_rose=site_design.options.wind_rose,
            ),
        )
        meta = DrawingMeta(
            title="全厂总图",
            condition_key=condition_key,
            repro=(plant.repro.design_hash,
                   plant.repro.engine_version, plant.repro.data_version),
        )
        return write_dxf(entities, styles, out, meta).read_bytes()
    snapshot = plant.conditions.get(condition_key, {}).get(unit_id)
    projection = PROJECTION_TABLE.get(unit_id)
    if snapshot is None or projection is None:
        raise ArtifactKindNotReady(
            f"dxf 目标单元 {unit_id!r} 不在当前工况图或 UF-32 对照表"
            f"（工况 {condition_key!r}；禁静默空产物）"
        )
    view = {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}
    losses = head_losses((), ctx=(unit_id, condition_key), assumptions=view)
    profile = build_profile(
        plant, losses, _REL_DATUM, view, condition_key
    )
    station = profile.station_of(unit_id)
    if station is None:
        raise ArtifactKindNotReady(
            f"dxf 目标单元 {unit_id!r} 无纵断站（工况 {condition_key!r}）"
        )
    styles = base_styles()
    plan = unit_plan(snapshot, projection, styles, condition_key)
    section = unit_section(snapshot, station, styles, condition_key)
    entities = EntityGroup(entities=plan.entities + section.entities)
    meta = DrawingMeta(
        title=unit_id,
        condition_key=condition_key,
        repro=(plant.repro.design_hash,
               plant.repro.engine_version, plant.repro.data_version),
    )
    write_dxf(entities, styles, out, meta)
    return out.read_bytes()


def upstream_context(
    source: UpstreamSource,
    unit_id: str,
    condition: OperatingCondition,
    env: RunEnv,
) -> UnitContext:
    """枚举上游快照（D2）：execute_graph 既有产物反解入流工况（R2 注记）。"""
    snapshots = source.plant.conditions[ConditionSet.key(condition)]
    inflows: dict[PortRef, WaterFlow | SludgeFlow] = {}
    inqualities: dict[PortRef, WaterQuality] = {}
    for edge in (item for item in source.edges if item.dst.unit_id == unit_id):
        snapshot = snapshots[edge.src.unit_id]
        flat, prefix = snapshot.outflows, f"{edge.src.unit_id}.{edge.src.port_id}"
        inflows[edge.dst] = (
            WaterFlow(
                q_avg_daily=flat[f"{prefix}.q_avg_daily"], kz=flat[f"{prefix}.kz"]
            )
            if f"{prefix}.q_avg_daily" in flat
            else SludgeFlow(
                q_wet=flat[f"{prefix}.q_wet"],
                ds=flat[f"{prefix}.ds"],
                moisture=flat[f"{prefix}.moisture"],
            )
        )
        inqualities[edge.dst] = WaterQuality(
            {
                dotted.rsplit(".", 1)[-1]: value
                for dotted, value in snapshot.outqualities.items()
                if dotted.startswith(f"{prefix}.")
            }
        )
    params = {
        spec.field_id: spec.default for spec in source.units[unit_id].manifest.params
    }
    for key, value in source.design.nodes[unit_id].items():
        if key != "kind":
            params[key] = float(value)  # 节点值已过 execute_graph 的 GR-02 守卫
    return UnitContext(
        unit_id=unit_id,
        inflows=inflows,
        inqualities=inqualities,
        params=params,
        condition=condition,
        assumptions=env.assumptions,
        trace=TraceCollector(),  # 占位（枚举行迹由 enumerate 内部空 sink 承载）
    )
