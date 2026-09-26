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
# 【私有面】_endpoint/_edges（B3-c 批 2c 收敛绑定件——逻辑/消息单源=
#   contracts.edge_parsing，本域拒绝载体 InvalidAssemblyError 注入；
#   原 B4 双胞胎复制已删）/ _checked_units_
#   eligibility（D4 资格）/ _FACTOR_SHARED_PREFIX + _unit_params（D4
#   系数投影——factor.*/removal.* + factor.screen.* 共用键并入 params）/
#   _CoefficientsUnit（投影包装单元）/ _check_grid_hits（grid 档命中）/
#   _isolated_unit_warnings（R2-P2-2 孤立单元警告——⑦甲呈报不阻断）
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

from waterprint.contracts.edge_parsing import edges_from, endpoint_from
from waterprint.contracts.ports import (
    Edge,
    InvalidConnection,
    Port,
    PortRef,
    validate_edge,
)
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.run_env import CoefficientsView, EngineParam, RunEnv
from waterprint.contracts.unit_api import Unit, UnitContext, UnitResult
from waterprint.graph.nodes import (
    InvalidNodeError,
    builtin_ports,
    builtin_unit,
    inlet_physics_errors,
)
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
from waterprint.units_lib import discover_units

_LOOP_KEYS: tuple[str, ...] = ("loop.tolerance", "loop.max_iterations", "loop.damping")


class InvalidAssemblyError(Exception):
    """装配非法（未知 unit_id/受检资格缺映射/边形态）——领域异常（GR-11 族）。"""


def _endpoint(raw: object, side: str, index: int) -> PortRef:
    """边端点转换绑定件：内核 endpoint_from + 本域拒绝载体（B3-c 收敛）。

    逻辑/消息单源=contracts.edge_parsing；本定义仅为 InvalidAssemblyError
    类型绑定（批 3a not_found 注入同型），app 侧消息文本零变
    （validate_design_structure 汇总面零连带——定案 J3/N2）。
    """
    return endpoint_from(raw, side, index, error=InvalidAssemblyError)


def _edges(raw_edges: Sequence[object]) -> tuple[Edge, ...]:
    """design.edges → Edge（绑定件：edges_from + InvalidAssemblyError 载体）。"""
    return edges_from(raw_edges, error=InvalidAssemblyError)


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


def validate_design_structure(design: DesignState) -> tuple[str, ...]:
    """设计结构校验（P0-3 呈裁④甲）：错误清单汇总非拒式（⑦甲——中间态
    合法工作流，结构发现=呈报不阻断）。

    三查（任务书 §三.2）：①边端点存在性（unit_id 在 design.nodes）；
    ②端口在册（端口声明真源=manifest——包单元 discover_units/内置
    builtin_ports 只读面）；③方向+流体匹配（contracts.validate_edge
    唯一裁判复用——R1/R2 语义零复制）+④孤立单元警告（R2-P2-2——
    无可解析边相连节点呈报，内置 kind 节点豁免，helper 后置追加）。
    单元解析口径同 assemble：值含
    kind 字符串=内置节点，否则 node_id=注册表键；未知单元/未知内置
    kind 亦汇总为错误（assemble 期拒的先呈报面）。边形状非法（缺
    src/dst、端点非双 string）在 _endpoint 同款窄化下汇总。
    """
    discovered = discover_units()
    errors: list[str] = []
    ports_index: dict[tuple[str, str], Port] = {}
    for node_id, node_value in design.nodes.items():
        kind = (
            node_value.get("kind")
            if isinstance(node_value, Mapping)
            else None
        )
        if isinstance(kind, str):
            try:
                decls = builtin_ports(kind)
            except InvalidNodeError as exc:
                errors.append(f"design.nodes[{node_id!r}]：{exc}")
                continue
            # R2-P1-4（round2 批）：进水物理域检红项（⑦甲呈报不阻断——
            # NH3N>TN 等物理不可能值旧实现静默放行）
            if kind == "municipal_input":
                errors.extend(
                    f"design.nodes[{node_id!r}]：{item}"
                    for item in inlet_physics_errors(node_value)
                )
        elif node_id in discovered:
            decls = discovered[node_id][0].ports
        else:
            errors.append(
                f"design.nodes[{node_id!r}] 不在单元注册表且无 kind 内置声明"
                f"（已发现单元 {sorted(discovered)}——GR-09 同 assemble 口径）"
            )
            continue
        for port in decls:
            ports_index[(node_id, port.port_id)] = port
    for index, element in enumerate(design.edges):
        if not isinstance(element, Mapping):
            errors.append(
                f"design.edges[{index}] 须为对象（src/dst/recycle）："
                f"得到 {type(element).__name__}"
            )
            continue
        try:
            src = _endpoint(element.get("src"), "src", index)
            dst = _endpoint(element.get("dst"), "dst", index)
        except InvalidAssemblyError as exc:
            errors.append(str(exc))
            continue
        dangling = [
            f"{side} 悬空 unit_id：{ref.unit_id} 不在 design.nodes"
            for side, ref in (("src", src), ("dst", dst))
            if ref.unit_id not in design.nodes
        ]
        if dangling:
            errors.extend(
                f"design.edges[{index}].{line}" for line in dangling
            )
            continue
        try:
            validate_edge(Edge(src=src, dst=dst), ports_index)
        except InvalidConnection as exc:
            errors.append(f"design.edges[{index}]：{exc}")
    errors.extend(_isolated_unit_warnings(design))
    return tuple(errors)


def _isolated_unit_warnings(design: DesignState) -> list[str]:
    """孤立单元警告（R2-P2-2——⑦甲呈报不阻断）：无可解析边相连的非内置节点。

    内置 kind 节点豁免（源/汇物理端点常无完整双边——municipal_input
    仅 OUT 口）；连通面=design.edges 逐侧独立收集（任一侧端点为对象且
    unit_id 为字符串即计该节点连通——非整体连通性判定，形状非法边由
    主查先行呈报）。
    """
    connected: set[str] = set()
    for element in design.edges:
        if isinstance(element, Mapping):
            for side in ("src", "dst"):
                endpoint = element.get(side)
                if (isinstance(endpoint, Mapping)
                        and isinstance(endpoint.get("unit_id"), str)):
                    connected.add(endpoint["unit_id"])
    isolated = sorted(
        node_id
        for node_id, node_value in design.nodes.items()
        if node_id not in connected
        and not (isinstance(node_value, Mapping)
                 and isinstance(node_value.get("kind"), str))
    )
    if isolated:
        return [f"警告（孤立单元——未与任何可解析边相连）：{isolated}"]
    return []


# ── 批5 2026-09-26 迁入：env 补齐装配链（自 app.py——app_enumeration_
#    gates 伴生件消费面单源防环；语义零变，app.py 顶部再导出同名）──────

def _engine_params(assumptions: Mapping[str, float]) -> Mapping[str, EngineParam]:
    """UF-08 投影：合成视图的 loop.* 三键 → EngineParam（source/note=registry 原文）。"""
    projected: dict[str, EngineParam] = {}
    defaults = {item.key: item for item in DEFAULT_ASSUMPTIONS}
    for key in _LOOP_KEYS:
        entry = defaults.get(key)
        if entry is None or key not in assumptions:
            raise InvalidAssemblyError(
                f"假设缺 {key!r}（合成视图=DEFAULT_ASSUMPTIONS + "
                "design.assumption_overrides——投影前提失败，UF-08）"
            )
        projected[key] = EngineParam(
            value=assumptions[key], source=entry.source, note=entry.note
        )
    return MappingProxyType(projected)


def _assumption_view(overrides: Mapping[str, float]) -> dict[str, float]:
    """合成视图：DEFAULT_ASSUMPTIONS 全量默认 + design 覆盖优先。"""
    view = {item.key: item.default for item in DEFAULT_ASSUMPTIONS}
    view.update(overrides)
    return view


def completed_env(env: RunEnv, design: DesignState) -> RunEnv:
    """engine_params 补齐（纯函数）：缺 loop.* 任一键经 _engine_params 投影补齐。

    原 app._completed_env 同名同义（批5 迁入装配域——三用例正门共享）。
    """
    if all(key in env.engine_params for key in _LOOP_KEYS):
        return env
    merged = dict(env.engine_params)
    merged.update(_engine_params(_assumption_view(design.assumption_overrides)))
    return replace(env, engine_params=merged)
