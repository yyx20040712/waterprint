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
#       diagnosis（无解时非 None）/grid（网格元信息）/condition_fields
#       （ADR-018 D2：枚举工况键中文标签族——按 manifest.out_dims 声明
#       序取 label_zh 真源，未声明降级 field_id；方案表条件列展示面）
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
#   enumerate_across_conditions(source, unit_id, conditions, grid, env)
#       -> DataFrame：枚举全工况化（ADR-018 D2）——逐工况 upstream_
#       context→enumerate_solutions→concat（行序=工况序×网格序确定；
#       condition_key 常量列各帧自标）
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
#   总图编排；InvalidSitePlanError 不捕获直上）；M6（2026-09-05）dxf
#   总图目录页追加：L3 drafting.catalog（catalog_sheet/sheet_origin_
#   below+常量桥 SITE_SHEET_NO/DEFAULT_SCALE——案乙 B 形态目录实体
#   拼接进总图文件）——全部沿
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
#   R4 全工况枚举确定性（ADR-018 D2）：帧序=conditions.iter_all() 工况
#      序 × 网格序；condition_key 逐帧常量自标；行数=grid.total×(2+k)。
#
# 【参照】重写计划 §12.4/§13.1；ADR-005；简报 M2-SOL D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（concat 面）
from pandas import DataFrame

from waterprint.app_export import (  # PROFILE3 拆分再导出——消费面零改动
    ArtifactKindNotReady,
    export_artifact,
)
from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.project_schema import DesignState
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Unit, UnitContext
from waterprint.solution.constraints import Constraint
from waterprint.solution.diagnose import DiagnosisReport
from waterprint.solution.enumerate import enumerate_solutions
from waterprint.solution.grid import Grid
from waterprint.trace import TraceCollector

__all__ = [
    "ArtifactKindNotReady",
    "Constraint",
    "EnumerationOptions",
    "EnumerationOutcome",
    "UpstreamSource",
    "enumerate_across_conditions",
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
    condition_fields: tuple[str, ...] = ()  # ADR-018 D2 工况键标签族（缺省=空兼容旧构造面）

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


def enumerate_across_conditions(
    source: UpstreamSource,
    unit_id: str,
    conditions: ConditionSet,
    grid: Grid,
    env: RunEnv,
) -> DataFrame:
    """枚举全工况化（ADR-018 D2）：逐工况重建上游快照→枚举→concat。

    行序=conditions.iter_all() 工况序 × 网格序（确定性，concat 保序——
    枚举序 tie_break 语义跨工况成立）；condition_key 常量列由各帧
    enumerate_solutions 自标（enumerate.py 既有机制）。行数=grid.total
    ×(2+k) 线性（ADR-007 决策 2 口径）。约束过滤/排序/诊断归
    app.run_enumeration 在 concat 整帧上执行一次（跨工况 margin_min
    全局排序，ADR-018 D5）。
    """
    unit = source.units[unit_id]
    frames = [
        enumerate_solutions(grid, upstream_context(source, unit_id, condition, env), unit, env)
        for condition in conditions.iter_all()
    ]
    return pandas.concat(frames, ignore_index=True)
