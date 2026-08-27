"""出图取数对照契约类型面（UF-32 方案②）：UnitProjection 基型 + 纵断 L0 类型。

输入:  registry/dimensions 既有 DimKey + result_schema TraceNode + unit_api Warning
输出:  UnitProjection（六字段取数声明基型）/ ProfileStation / ElevationProfile
       （elevation 与 drafting 共同消费的 L0 类型——L3 互不 import 红线的解法）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3D1 D1 自 drawing_projection.py 原样迁出——纯类型声明面
#   语义零变更；对账锁定测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   class UnitProjection(不可变)：单单元取数声明六字段——
#       unit_id: str
#       plan_keys: Mapping[图纸语义→dims 键]   平面图取数（总尺寸/分格/标注类）
#       section_keys: Mapping[剖面语义→dims 键] 剖面取数（水深 water_depth/
#           池深 pool_depth/标高关联键——water_depth 语义键是 elevation
#           build_profile 定池底的取数口）
#       primitive_dims: Mapping[三维槽位→dims 键]（length/width/depth 或
#           diameter——box/cylinder 图元取数）
#       instance_counts: Mapping[实例语义→dims 键]（台数/格数/灯数→InstanceGroup）
#       non_drawn: tuple[str, ...]  不上图纯校核量显式列（禁静默遗漏）
#       dim_of: Mapping[dims 键→DimKey]  量纲列（逐键；公式输出按 FormulaSpec
#           output_dim 定[∗ 项]，参数复用键按 registry/dimensions 登记）
#   class ProfileStation(不可变)：单站纵断——unit_id/water_level/floor_elev/
#       ground_elev/bury_depth/freeboard/water_depth/loss_in/design_flow
#   class ElevationProfile(不可变)：stations（沿流程拓扑序）/condition_key/
#       trace（公式迹）/warnings（埋深越界等）+ station_of(unit_id) 查询
#
# 【行为规格】
#   R4 ElevationProfile 是标高唯一真源（L0）：elevation 产出、drafting
#      （section_view/profile_drawing）与 cost(M3) 消费同一类型——
#      本文件不 import 任何 L3（独立于两消费方，import-linter 绿）。
#   R5 本文件只读消费 dims 键名（字符串），不 import units_lib、
#      不做任何计算——纯声明面（L0 准入类别①冻结 schema，GR-36）。
#      （R1 表覆盖/R2 五类不静默/R3 量纲合法性等对账规则随分线表文件——
#      drawing_projection_municipal / drawing_projection_mine。）
#
# 【测试要求】tests/contracts/test_drawing_projection.py：21 单元
#   golden 实跑键集对账 + DimKey 合法性 + 分线键集 disjoint。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；ADR-009 B7；
#   重写计划 §10.2/§10.5/§12.5/§13.6；M3D1 简报 D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from waterprint.contracts.quantity import DimKey
from waterprint.contracts.result_schema import TraceNode
from waterprint.contracts.unit_api import Warning

__all__ = [
    "ElevationProfile",
    "ProfileStation",
    "UnitProjection",
]


@dataclass(frozen=True)
@final
class UnitProjection:
    """单单元出图取数声明（六字段，Mapping 字段构造即只读快照）。"""

    unit_id: str
    plan_keys: Mapping[str, str]
    section_keys: Mapping[str, str]
    primitive_dims: Mapping[str, str]
    instance_counts: Mapping[str, str]
    non_drawn: tuple[str, ...]
    dim_of: Mapping[str, DimKey]

    def __post_init__(self) -> None:
        """Mapping 只读快照（T3A-01 防线同款：外部改原容器不泄漏）。"""
        for name in ("plan_keys", "section_keys", "primitive_dims",
                     "instance_counts", "dim_of"):
            object.__setattr__(
                self, name, MappingProxyType(dict(getattr(self, name)))
            )

    def drawn_keys(self) -> frozenset[str]:
        """四类取数键并集（R1 对账面：∪ non_drawn == dims 全量）。"""
        return frozenset(self.plan_keys.values()) | frozenset(
            self.section_keys.values()
        ) | frozenset(self.primitive_dims.values()) | frozenset(
            self.instance_counts.values()
        )


@dataclass(frozen=True)
@final
class ProfileStation:
    """纵断单站（不可变）：水面/池底/地面/埋深/超高/水深/进站损失/设计流量。"""

    unit_id: str
    water_level: float
    floor_elev: float
    ground_elev: float
    bury_depth: float
    freeboard: float
    water_depth: float
    loss_in: float
    design_flow: float


@dataclass(frozen=True)
@final
class ElevationProfile:
    """纵断数据唯一真源（不可变，L0）：站位序列 + 工况 + 公式迹 + 警告。"""

    stations: tuple[ProfileStation, ...]
    condition_key: str
    trace: tuple[TraceNode, ...]
    warnings: tuple[Warning, ...]

    def station_of(self, unit_id: str) -> ProfileStation | None:
        """按 unit_id 查站（drafting section_view 取标高的正门）。"""
        for station in self.stations:
            if station.unit_id == unit_id:
                return station
        return None
