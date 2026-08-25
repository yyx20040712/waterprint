"""用例编排：run_full_calc(project, conditions)——内核对外的唯一大门（L4 装配点）。

输入:  ProjectFile + 工况选择 + 数据包（单价/系数/假设）+ 单元发现结果
输出:  全厂结果包（PlantResult + ElevationProfile + SceneGraph + 概算 + 迹树）；
       T7a 份额：load_project/save_project 薄封装 + RunEnv 再导出；
       T7b 份额：assemble/run_full_calc 装配执行闭环（本文件已落）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 薄封装份额 D7 + T7b D4/D5 裁决 2026-08-25；
#   镜像测试 tests/app/test_app.py）
#
# 【公开接口】
#   class RunEnv(不可变)：定义于 contracts/run_env.py（L0 契约），app
#       装配并重新导出——七字段（engine_version/data_version/
#       assumptions/coefficients/price_book/trace_sink/engine_params）
#   load_project(path: Path) -> ProjectFile / save_project(project:
#       ProjectFile, path: Path) -> None（UF-33）：load 走 M-3 版本门
#       （read_project_text → json.loads → migration.migrate——版本路由
#       唯一正门=migrate，T7a 二审移交定稿；JSONDecodeError 包装
#       InvalidProjectError from exc；migrate 已收 ValidationError；
#       R1-b 两闸：parse_constant 拒 NaN/±Inf + RecursionError 收编
#       ——二审 M-1/T7a-R1 同款；完整大小/深度闸留 M2/server 批）
#   assemble(project: ProjectFile, env: RunEnv) -> AssembledGraph
#       装配：units_lib.discover_units ∪ 内置节点（design.nodes 值含
#       "kind" 键者经 graph.nodes.builtin_unit 构造；无 kind=注册表查，
#       缺失=InvalidAssemblyError 带 unit_id）；edges 装配期转换存
#       AssembledGraph（executor _edges_from_design 同款语义、本文件
#       B4 双胞胎，拒绝载体=InvalidAssemblyError）；D4 受检资格校验：
#       checked_units 逐个 condition_mappings 非空（空/不在图中=
#       InvalidAssemblyError，判据=T3-D4 移交口径"须声明检修降级"宽松
#       安全侧）；重复 unit_id 由 discover_units 启动期拒（units_lib
#       铁律同款）
#   AssembledGraph(不可变)：design: DesignState / units: Mapping[str,
#       Unit] / edges: tuple[Edge, ...] 三字段——编排产物不进 contracts
#       （file-contracts 输出列同步）
#   run_full_calc(project, conditions, env) -> ResultBundle
#       内部 assemble → engine_params 补齐 → execute_graph →
#       design_hash 回填 → ResultBundle
#   ResultBundle(不可变)：T7b 落两字段子集 plant: PlantResult +
#       repro: ReproTriple（规格头愿景六字段中 profiles/scene/estimate
#       归 M1/M3 批，注记不删愿景）
#   class InvalidAssemblyError(Exception)（GR-11 族，本文件定义）
#   run_enumeration(...) / export_artifact(...)：保持缺省（UF-33 编排
#       薄壳归 M1/M3，注记保留）
#
# 【行为规格】
#   R1 装配/执行分离：assemble 阶段发现失败（重复 unit_id/清单非法/
#      失联引用/受检资格缺映射）= 启动期失败（全部报告）；run 阶段只执行。
#   R2 编排顺序（全流程用例）：execute_graph（逐工况）→ elevation
#      profile → geometry scene →（按需）cost estimate / drafting /
#      trace 消费——子系统经总线数据衔接（M1/M3 批）。
#   R3 幂等与可复算：同 (project, conditions, env) 双跑 ResultBundle
#      序列化字节级相同（CI 常驻断言——test_app 双跑用例）。
#   R4 旧项目导入（M4）：import_legacy 入口在此编排，与 run_full_calc
#      平行不混流。
#   R5 性能：全流程（32 单元 × 2+k 工况，含回路）<5s（§18.1 基准
#      门禁主测点，M1 批）。
#
# 【D4 系数投影（M1a 2026-08-25）】私有 _unit_params(unit_id, coefficients)
#   + _CoefficientsUnit 包装：注册表单元装配时把 coefficients 中
#   factor.<unit>.*/removal.<unit>.*（按单元短名过滤）+factor.screen.*
#   共用键并入 compute 期 params（全键名保留，design 参数优先、命名空间
#   不相交）；数值真源唯一 data/coefficients（GR-15 出处随 registry 条目）。
#   简报原文签名 (design_node, coefficients, unit_id) 的 design_node 份额
#   由 executor._unit_params 承担（T7b 装配现状——参数=manifest 默认 ∪
#   design 覆盖在 executor 侧合成，本函数只投影系数面），按简报"对齐
#   现状记档"条款落地。
#
# 【UF-08 投影闭环】（D5 定稿）不新增公开构造器——私有
#   _engine_params(assumptions)：合成视图（DEFAULT_ASSUMPTIONS +
#   design.assumption_overrides）提取 loop.* 三键构造 EngineParam
#   （value=合成值、source/note=registry 条目原文——GR-15 出处随行）；
#   run_full_calc 若 env.engine_params 缺 loop.* 任一键则补齐（纯函数
#   构造新 RunEnv 替换，原 env 不改；MappingProxyType 快照语义保持）。
#
# 【trace 装配收口】（M1b D3 裁决 2026-08-25，分层：trace 居 graph 上层，
#   executor 禁 import trace——executor.py 零改动；其 _NullSink 保留为
#   防御残留：仅当调用方直接走 execute_graph 且 env.trace_sink=None 时
#   生效，app 正门路径不再触达）：run_full_calc 入参 env.trace_sink 为
#   None 时构造 TraceCollector 并 dataclasses.replace(env, trace_sink=
#   collector)（_engine_params 同款"构造新 RunEnv 替换"先例）；非 None
#   时尊重调用方 sink——PlantResult.trace 回填仅当 sink 有可调 tree()
#   （getattr 探测），否则 trace=() 注记（收集语义归 sink 自身）。
#   execute_graph 后 dataclasses.replace(plant, trace=collector.tree())
#   （design_hash 回填同款先例）——PlantResult.trace 从 () 占位变实迹，
#   R4"计算迹完整"闭环（executor D10 冲突记档消除）；serialize 确定性
#   不受扰（TraceNode 平铺到达序，双跑同迹=双跑同序列化）。
#
# 【design_hash 回填】（D3/D5 定稿）：executor 置空串（分层契约禁其
#   import project.content_hash）——run_full_calc 以 dataclasses.replace
#   回填 ReproTriple(design_hash=content_hash.design_hash(design))，
#   app→project 边合法（load/save 先例）；可复算三元组 T7b 闭环。
#   【勘误注记】简报 D5 原文"model_copy"系 pydantic 习惯用语——
#   PlantResult 是 frozen dataclass，等价 API=dataclasses.replace
#   （非重裁决，机械修正记档报告）。
#
# 【测试要求】三单元 M1 切片端到端、装配失败清单完整、双跑 diff=0、
#   三元组传播、（golden 数据就绪后）两大案例全流程。
#
# 【参照】重写计划 §13.1 装配点/§14.3/§18.1；简报 T7a D7 / T7b D4/D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Final, NoReturn, final

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.project_schema import DesignState, ProjectFile
from waterprint.contracts.result_schema import PlantResult, ReproTriple
from waterprint.contracts.run_env import CoefficientsView, EngineParam, RunEnv
from waterprint.contracts.unit_api import Unit, UnitContext, UnitResult
from waterprint.graph.executor import execute_graph
from waterprint.graph.nodes import builtin_unit
from waterprint.project.content_hash import design_hash
from waterprint.project.io import (
    InvalidProjectError,
    read_project_text,
)
from waterprint.project.io import (
    save_project as _project_save,
)
from waterprint.project.migration import migrate
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
from waterprint.trace import TraceCollector, TraceTree
from waterprint.units_lib import discover_units

__all__ = [
    "AssembledGraph",
    "InvalidAssemblyError",
    "ResultBundle",
    "RunEnv",
    "assemble",
    "load_project",
    "run_full_calc",
    "save_project",
]

_LOOP_KEYS: Final[tuple[str, ...]] = (
    "loop.tolerance",
    "loop.max_iterations",
    "loop.damping",
)


class InvalidAssemblyError(Exception):
    """装配非法（未知 unit_id/受检资格缺映射/边形态）——领域异常（GR-11 族）。"""


def _reject_constant(name: str) -> NoReturn:
    """json.loads parse_constant 钩子：NaN/Infinity/-Infinity 一律拒（GR-02）。

    R1-b（二审 M-1，T7a-R1 io 同款语义双胞胎）：拒值经 InvalidProjectError
    上抛（非 JSONDecodeError 通道，直接冒出 json.loads）。
    """
    raise InvalidProjectError(
        f"项目 JSON 含非法常量：{name}（NaN/±Inf 禁——GR-02 输入即拒；"
        "JSON 规范外字面量）"
    )


def load_project(path: Path) -> ProjectFile:
    """项目装载（M-3 版本门）：read_project_text → json.loads → migrate 路由。

    版本路由唯一正门=migration.migrate（未来版拒/未知历史版拒/当前版直通）；
    JSONDecodeError 包装 InvalidProjectError from exc；migrate 已收
    ValidationError。R1-b 两道闸（二审 M-1 收编，T7a-R1 同款先例）：
    parse_constant 拒 NaN/±Inf + RecursionError 收编（超深嵌套防崩）；
    完整大小/深度闸留 M2/server 批（记档 T7b 报告 §6.2-8）。
    """
    text = read_project_text(path)
    try:
        data = json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise InvalidProjectError(
            f"项目 JSON 解析失败（app.load_project·M-3 migrate 路由）：{exc}"
        ) from exc
    except RecursionError as exc:
        raise InvalidProjectError(
            f"项目 JSON 嵌套过深（app.load_project·M-3 路由，解析器递归保护"
            f"触发）：{path}（二审 M-1 收编——T7a-R1 同款）"
        ) from exc
    return migrate(data)


def save_project(project: ProjectFile, path: Path) -> None:
    """项目保存薄封装：转发 project.io 正门（原子写+确定性序列化）。"""
    _project_save(project, path)


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
                f"design.edges[{index}] 须为对象（src/dst/recycle）："
                f"得到 {type(element).__name__}"
            )
        recycle = element.get("recycle", False)
        if not isinstance(recycle, bool):
            raise InvalidAssemblyError(
                f"design.edges[{index}].recycle 须为布尔：得到 {recycle!r}"
            )
        edges.append(
            Edge(
                src=_endpoint(element.get("src"), "src", index),
                dst=_endpoint(element.get("dst"), "dst", index),
                recycle=recycle,
            )
        )
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


# 【D4 系数投影（M1a 裁决 2026-08-25）】UnitContext 无 coefficients 通道且
# 字段锁定——装配层把 RunEnv.coefficients 中 factor.<unit>.*/removal.<unit>.*
# （按单元短名过滤）+ factor.screen.*（粗/细格栅共用常数，数据包命名形态）
# 合入该单元 compute 期 params 快照（prefix 保留全键名，compute 按
# ctx.params["factor.cugeshan.w1_slag"] 取）；params: Mapping[str, float]
# 契约容纳。系数真源唯一 data/coefficients 数据包（GR-15 出处随 registry
# 条目走），design 节点参数与系数键命名空间不相交（GR-26 禁点号 vs
# field_id），投影不覆盖用户参数面。ctx.assumptions 仍只承载 safety/loop 面。
_FACTOR_SHARED_PREFIX = "factor.screen."


def _unit_params(unit_id: str, coefficients: CoefficientsView) -> dict[str, float]:
    """D4 系数投影：单元短名过滤 factor.*/removal.* + factor.screen.* 共用键。"""
    # 短名 = 剥离业务线前缀后的全串（M2c R1-a 修正 2026-08-26：两词短名
    # bashi_jiliangcao/wushui_tisheng 的系数键含下划线，rsplit 尾段会错位；
    # mine_water 线名本身含下划线——勿用 rsplit 取尾段，恒取首个 "_" 后全串）。
    short = unit_id.split("_", 1)[1]
    prefixes = (f"factor.{short}.", f"removal.{short}.", _FACTOR_SHARED_PREFIX)
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
    """装配正门：单元发现 ∪ 内置节点构造 + 边转换 + 受检资格校验（R1）。

    design.nodes 值含 "kind" 键=内置节点（graph.nodes.builtin_unit 构造，
    params=除 kind 外键值）；无 kind=单元包单元经 discover_units 注册表查，
    缺失=InvalidAssemblyError 带 unit_id。重复 unit_id 由 discover_units
    启动期拒（units_lib 铁律同款）。env 为执行环境透传（装配期不消费，
    签名冻结）。"""
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
    return AssembledGraph(
        design=project.design, units=units, edges=_edges(project.design.edges)
    )


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


@dataclass(frozen=True)
@final
class ResultBundle:
    """全厂结果包（T7b 两字段子集）：plant + repro（愿景六字段归 M1/M3 批）。"""

    plant: PlantResult
    repro: ReproTriple


def _completed_env(env: RunEnv, design: DesignState) -> RunEnv:
    """engine_params 补齐（纯函数）：缺 loop.* 任一键经 _engine_params 投影补齐。"""
    if all(key in env.engine_params for key in _LOOP_KEYS):
        return env
    merged = dict(env.engine_params)
    merged.update(_engine_params(_assumption_view(design.assumption_overrides)))
    return replace(env, engine_params=merged)


def run_full_calc(
    project: ProjectFile, conditions: ConditionSet, env: RunEnv
) -> ResultBundle:
    """全厂计算唯一大门：装配 → env 补齐 → trace 装配 → 执行 → 回填（D3/D5）。"""
    assembled = assemble(project, env)
    effective = _completed_env(env, project.design)
    collector: TraceCollector | None = None
    if effective.trace_sink is None:
        collector = TraceCollector()
        effective = replace(effective, trace_sink=collector)
    plant = execute_graph(project.design, assembled.units, conditions, effective)
    tree: TraceTree = collector.tree() if collector is not None else _external_tree(env)
    filled = replace(
        plant,
        trace=tree,
        repro=ReproTriple(
            design_hash=design_hash(project.design),
            engine_version=plant.repro.engine_version,
            data_version=plant.repro.data_version,
        ),
    )
    return ResultBundle(plant=filled, repro=filled.repro)


def _external_tree(env: RunEnv) -> TraceTree:
    """调用方自带 sink 的回填口径：有可调 tree() 则回填，否则 () 注记。"""
    getter = getattr(env.trace_sink, "tree", None)
    if callable(getter):
        outcome = getter()
        if isinstance(outcome, tuple):
            return outcome
    return ()  # sink 无 tree()：收集语义归 sink 自身，PlantResult.trace 留空注记
