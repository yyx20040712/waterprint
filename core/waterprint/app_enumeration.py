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
#       归属（audit=M4/dxf=M2 出图批/estimate=M3），禁静默空产物
#   export_artifact(kind, plant, template, out) -> bytes
#       分发薄壳：kind="calcbook"→render_calcbook（M1b trace 正门，
#       签名按其收口——plant 自带 trace）；未就绪/未知 kind=
#       ArtifactKindNotReady（零 app 依赖防 import 环，L0 类型面）
#   class UpstreamSource(不可变)：上游取数面四字段束（units/edges/
#       design/plant——app 装配与执行产物快照，装配语义仍归 app）
#   upstream_context(source, unit_id, condition, env) -> UnitContext：
#       枚举上游快照重建（execute_graph 既有产物 UF-42 投影表反解入流
#       股——禁另写上游计算，D2；只消费 L0 契约类型）
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

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import final

from pandas import DataFrame  # type: ignore[import-untyped]  # pandas-stubs 未随包分发

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
from waterprint.solution.grid import Grid
from waterprint.trace import TraceCollector, render_calcbook

__all__ = [
    "ArtifactKindNotReady",
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


def export_artifact(
    kind: str, plant: PlantResult, template: Path, out: Path
) -> bytes:
    """产物导出分发薄壳（UF-33）：calcbook 接 M1b trace 正门；未就绪 kind 拒。"""
    if kind == "calcbook":
        return render_calcbook(plant.trace, plant, template, out).read_bytes()
    owners = {"audit": "M4", "dxf": "M2 出图批", "estimate": "M3"}
    owner = owners.get(kind, "未知 kind（合法面 calcbook/audit/dxf/estimate）")
    raise ArtifactKindNotReady(
        f"产物 kind {kind!r} 未就绪（归属：{owner}；禁静默空产物，UF-33）"
    )


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
