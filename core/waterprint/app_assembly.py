"""装配域伴生件：单元发现∪内置节点构造+边转换+装配校验（app 装配份额）。

输入:  ProjectFile + RunEnv（coefficients 系数投影面）+ 单元发现结果
输出:  assemble/AssembledGraph/InvalidAssemblyError/_unit_params 系数投影
       （app.py 顶部 import 同名再导出——消费面零改动，UF-33 单入口保持）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3 R1 拆分 2026-09-05：装配域自 app.py L199-361 整域外迁
#   ——app_enumeration.py 伴生件先例第二例（app.py 500 行预算减压）；
#   搬运零行为变化（签名/语义/报文/__all__ 面零变），app.py 顶部显式
#   符号清单再导入（禁 import *，防 __all__ 漂移）；零 waterprint.app
#   依赖防环（本文件仅 import contracts/graph/units_lib 层符号——
#   assemble 的 discover_units 调用随域整迁，units_lib 边为域内必需）
#
# 【公开接口】（定义面迁此、app 再导出——消费面 from waterprint.app
#   import 不变；语义注记全文见 app.py 规格说明【公开接口】节）
#   assemble(project, env) -> AssembledGraph：单元发现 ∪ 内置节点构造
#       + 边转换 + D4 受检资格校验 + Ruling ④ grid 档命中校验
#   AssembledGraph(不可变)：design/units/edges 三字段
#   InvalidAssemblyError（GR-11 族，域内异常随域同迁）
# 【私有面】_endpoint/_edges（B4 双胞胎边转换）/ _checked_units_
#   eligibility（D4 资格）/ _FACTOR_SHARED_PREFIX + _unit_params（D4
#   系数投影——factor.*/removal.* + factor.screen.* 共用键并入 params）/
#   _CoefficientsUnit（投影包装单元）/ _check_grid_hits（grid 档命中）
#
# 【行为规格】与 app.py 原文逐字同构（R1 装配/执行分离等——见 app.py
#   规格说明）；测试经 app 再导出面由既有镜像测试覆盖（test_app/
#   test_unit_params_projection 等），B3-R11 增 test_app_assembly 恒等钉面。
#
# 【参照】B3 简报 R1；重写计划 §13.1 装配点；简报 T7b D4/D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from math import isclose
from types import MappingProxyType
from typing import final

from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.run_env import CoefficientsView, RunEnv
from waterprint.contracts.unit_api import Unit, UnitContext, UnitResult
from waterprint.graph.nodes import builtin_unit
from waterprint.units_lib import discover_units


class InvalidAssemblyError(Exception):
    """装配非法（未知 unit_id/受检资格缺映射/边形态）——领域异常（GR-11 族）。"""


def _endpoint(raw: object, side: str, index: int) -> PortRef:
    """边端点转换（executor._endpoint 的 B4 双胞胎，拒绝载体=装配异常）。"""
    if not isinstance(raw, Mapping):
        raise InvalidAssemblyError(
            f"design.edges[{index}].{side} 须为对象（含 unit_id/port_id）："
            f"得到 {type(raw).__name__}"
        )
    unit_id = raw.get("unit_id")
    port_id = raw.get("port_id")
    if not isinstance(unit_id, str) or not isinstance(port_id, str):
        raise InvalidAssemblyError(
            f"design.edges[{index}].{side} 须含字符串 unit_id/port_id："
            f"得到 {unit_id!r}, {port_id!r}"
        )
    return PortRef(unit_id=unit_id, port_id=port_id)


def _edges(raw_edges: Sequence[object]) -> tuple[Edge, ...]:
    """design.edges → Edge（executor._edges_from_design 同款语义的装配期转换）。"""
    edges: list[Edge] = []
    for index, element in enumerate(raw_edges):
        if not isinstance(element, Mapping):
            raise InvalidAssemblyError(
                f"design.edges[{index}] 须为对象（src/dst/recycle）：得到 {type(element).__name__}"
            )
        recycle = element.get("recycle", False)
        if not isinstance(recycle, bool):
            raise InvalidAssemblyError(
                f"design.edges[{index}].recycle 须为布尔：得到 {recycle!r}"
            )
        edges.append(Edge(
            src=_endpoint(element.get("src"), "src", index),
            dst=_endpoint(element.get("dst"), "dst", index),
            recycle=recycle))
    return tuple(edges)


@dataclass(frozen=True)
@final
class AssembledGraph:
    """装配产物（不可变）：design + 单元表 + 边（编排产物不进 contracts）。"""

    design: DesignState
    units: Mapping[str, Unit]
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        """units 构造即快照（T3A-01 防线同款）。"""
        object.__setattr__(self, "units", MappingProxyType(dict(self.units)))


def _checked_units_eligibility(
    design: DesignState, units: Mapping[str, Unit]
) -> None:
    """D4 受检资格校验：checked_units 逐个 condition_mappings 非空（T3-D4 移交义务）。"""
    for unit_id in design.checked_units:
        unit = units.get(unit_id)
        if unit is None:
            raise InvalidAssemblyError(
                f"受检单元 {unit_id!r} 不在图中（checked_units 须引用"
                " design.nodes 既有节点——D4 资格校验）"
            )
        if not unit.manifest.condition_mappings:
            raise InvalidAssemblyError(
                f"受检单元 {unit_id!r} 须声明检修降级映射（ADR-007）——"
                "manifest.condition_mappings 为空"
            )


# 【D4 系数投影（M1a 裁决 2026-08-25）】UnitContext 无 coefficients 通道——装配层把
# RunEnv.coefficients 的 factor.<短名>.*/removal.<短名>.*+factor.screen.*（格栅共用）
# 合入单元 compute 期 params（全键名保留；系数真源唯一 data/coefficients，GR-15；
# 与 design 参数命名空间不相交，GR-26；投影不覆盖用户参数面——详见 M1a 报告）。
_FACTOR_SHARED_PREFIX = "factor.screen."


def _unit_params(unit_id: str, coefficients: CoefficientsView) -> dict[str, float]:
    """D4 系数投影：单元短名过滤 factor.*/removal.* + factor.screen.* 共用键。"""
    # 短名=业务线全前缀感知剥离（M3a1 D1 修正：线名含下划线——单段 split 对
    # mine_water_* 只剥 "mine" 系 M2c R1-a 矛盾复发点；线名表硬编码函数内、
    # 禁 import units_lib 私有 _LINES——跨包 "_" 前缀访问违宪 §1）。
    lines = ("municipal_", "mine_water_", "sludge_", "conveyance_")
    line = next((p for p in lines if unit_id.startswith(p)), "")
    short = unit_id[len(line):]
    # 矿井水线键名带 mine_ 限定=§14.3 物理隔离在数据键面的镜像（防市政同名
    # 构筑物键误投影）；其余线裸短名——0.1.0~0.4.0 既有键零扰动。
    ns = f"mine_{short}" if line == "mine_water_" else short
    prefixes = (f"factor.{ns}.", f"removal.{ns}.", _FACTOR_SHARED_PREFIX)
    projected: dict[str, float] = {}
    for prefix in prefixes:
        for key in coefficients.keys(prefix):
            projected[key] = coefficients.get(key).value
    return projected


@final
class _CoefficientsUnit:
    """系数投影包装单元：compute 前把投影键并入 ctx.params（原 ctx 不改）。"""

    def __init__(self, unit: Unit, extra: Mapping[str, float]) -> None:
        self._unit = unit
        self.manifest = unit.manifest
        self._extra = dict(extra)

    def compute(self, ctx: UnitContext) -> UnitResult:
        """合并参数面（design 覆盖优先，命名空间不相交）后转发内层单元。"""
        merged = dict(self._extra)
        merged.update(ctx.params)
        return self._unit.compute(replace(ctx, params=merged))


def assemble(project: ProjectFile, env: RunEnv) -> AssembledGraph:
    """装配正门：单元发现 ∪ 内置节点构造 + 边转换 + 资格/grid 校验（R1）。

    design.nodes 值含 "kind"=内置节点（builtin_unit 构造）；无 kind=discover_units
    注册表查，缺失=InvalidAssemblyError 带 unit_id；重复 unit_id 由
    discover_units 启动期拒。env 透传（装配期不消费）。"""
    discovered = discover_units()
    units: dict[str, Unit] = {}
    for node_id, node_value in project.design.nodes.items():
        if not isinstance(node_value, Mapping):
            raise InvalidAssemblyError(
                f"design.nodes[{node_id!r}] 须为对象：得到 {type(node_value).__name__}"
            )
        kind = node_value.get("kind")
        if isinstance(kind, str):
            units[node_id] = builtin_unit(
                kind,
                {key: value for key, value in node_value.items() if key != "kind"},
            )
        elif node_id in discovered:
            units[node_id] = _CoefficientsUnit(
                discovered[node_id][1](), _unit_params(node_id, env.coefficients)
            )
        else:
            raise InvalidAssemblyError(
                f"装配失败：节点 {node_id!r} 不在单元注册表且无 kind 内置"
                f"声明（已发现单元 {sorted(discovered)}——GR-09）"
            )
    _checked_units_eligibility(project.design, units)
    _check_grid_hits(project.design, units)
    return AssembledGraph(
        design=project.design, units=units, edges=_edges(project.design.edges)
    )


def _check_grid_hits(design: DesignState, units: Mapping[str, Unit]) -> None:
    """D3 Ruling ④ 装配校验：grid 声明参数终值（design 覆盖或 default）须命中档。"""
    for node_id, unit in units.items():
        node = design.nodes[node_id]
        for spec in unit.manifest.params:
            if spec.grid is None:
                continue
            value = node.get(spec.field_id, spec.default)
            if isinstance(value, bool) or not isinstance(value, int | float) or not any(
                isclose(float(value), step) for step in spec.grid
            ):
                raise InvalidAssemblyError(
                    f"单元 {node_id!r} 参数 {spec.field_id!r} 值 {value!r} 未命中"
                    f" grid 档位 {list(spec.grid)}（Ruling ④ 档位归 grid 层——"
                    "浮点容差 math.isclose 默认相对 1e-9；系数投影键 factor.* "
                    "不在此面）"
                )
