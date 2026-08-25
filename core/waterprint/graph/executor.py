"""图执行编排：工况 × 拓扑 × 传播 × 回路的总指挥（不认识任何具体单元）。

输入:  项目 design 图 + 单元注册表（manifest→Unit 实例，由 app.py 装配）+ 工况集
输出:  PlantResult（按 condition_key 索引，含计算迹与三元组）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7b 实现 D3 裁决 2026-08-25；镜像测试 tests/graph/test_executor.py）
#
# 【公开接口】
#   UnitRegistry(Protocol)：unit_id → Unit 实例（app.py 构建；executor
#       不 import units_lib——装配点唯一）
#   execute_graph(design: DesignState, units: UnitRegistry,
#                 conditions: ConditionSet, env: RunEnv) -> PlantResult
#       唯一执行正门（RunEnv 类型=contracts/run_env.py，UF-31）
#   InvalidExecutionError(Exception)（GR-11 族，本文件定义）
#   design.edges 元素形态（D3 冻结，此前无消费者）：{"src":
#       {"unit_id","port_id"}, "dst": {"unit_id","port_id"},
#       "recycle": bool=False}——私有 _edges_from_design 转 Edge（键
#       缺失/类型错=InvalidExecutionError）
#
# 【行为规格】
#   R1 逐工况整图计算：iter_all() 每工况独立完整执行（_RunState 每工况
#      新建，零共享可变状态），按 ConditionSet.key 索引（§14.1）。
#   R2 层-SCC 调度（Explore 缺口 7 裁决）：split_graph 得 (layers,
#      loop_groups)；回路组=超级节点占组最深成员层——当前层属组成员跳过
#      单节点执行，组最深成员层执行点整组联立求解；**同层内组先于单点**
#      （Kahn 层内无前向边，组不依赖同层单点；同层单点可为组成员的下游
#      消费者，先跑将读空池——次序推演记档）。v1 串行（UF-35 裁决落地；
#      并行预留=并串字节级等价常驻测试先行入锁）。每单元 compute 先经
#      manifest 工况映射变换参数（ADR-007，compute 无工况分支）。
#   R3 可复算：同 (design, conditions, env) 双跑字节级相同（incremental
#      只做等价优化——M1/M3 留白）。
#   R4 计算迹：**与 PlantResult.trace=()/summary={} 占位的冲突记档 D10**
#      （sink 通道经 UnitContext.trace 携带，TraceNodeSpec→TraceNode 收集
#      归 M1 collector；厂级汇总 M1 数值批填充）。
#   R5 异常隔离：单元 compute 抛领域异常（_DOMAIN_EXCEPTIONS 在册族，
#      新增族须同步本元组——记档）→ InvalidExecutionError（消息含
#      unit_id+condition_key+原异常摘要，from exc 保链）整工况失败上抛
#      禁吞；不做部分结果聚合（run_full_calc 异常上抛即失败）。
#   R6 内置图节点走 unit_api 协议（graph/nodes.py 本包提供，§14.3）。
#
# 【回路闭包口径】（D3 冻结）状态变量=组内 recycle 边源端口流股展开量，
#   键 f"{unit_id}.{port_id}.{field}"（GR-09 展示形态同款）；WATER 两量
#   q_avg_daily/kz（q_design 派生不入状态）、SLUDGE 三量 q_wet/ds/
#   moisture；初始 WATER=零流量+单位 kz、SLUDGE=零股（确定性 R5）。
#   F=写回估计（直接构造 GR-04，图内 Q=0 合法）→组内按层序重算→读源
#   端口新值（=dst 侧将收到值，传输无损两读法同值）。recycle 股**水质**
#   随迭代尾随更新（状态向量只含流量展开量）；解写回=以收敛解终跑一遍
#   闭包（快照/池/水质与收敛输入一致），组外下游照常 propagate。流体
#   取 recycle 边 dst 端口 manifest 声明（未声明=InvalidExecutionError）；
#   不落回路组的 recycle 边=执行期拒 InvalidExecutionError（带边上下文
#   ——recycle 边必须闭合成 SCC 回路组，前进向标记属装配异常；propagate
#   R5 的忽略是纯函数边界口径，executor 持完整图信息故异层；装配期前置
#   对账归 M1 加固——二审 I-1 方案(b) 裁决 2026-08-25）。
#
# 【工况映射 DSL】（D3 冻结）rule 经 parse_checked（白名单=manifest 参数
#   名 ∪ 裸名 ∪ 点式上下文 ∪ {"pool.all_pools"}——executor 侧重建，**B4
#   双胞胎禁私有 import**，与 manifest_validation 同源同步义务）+
#   eval_checked；bindings=params 全量 ∪ {"pool.all_pools": offline 判定
#   =condition.offline_unit==该 unit_id 时 False 否则 True}；结果写
#   params[target]（bool→float 归一）；ExprSyntaxError 上抛带 unit_id。
#
# 【参数面】ctx.params=manifest 默认值 ∪ design 节点值覆盖（bool 拒/
#   float 归一，GR-02）；节点值 "kind" 键=内置节点结构元数据（D5 装配
#   口径）不进参数面。
#
# 【UF-42 投影表】（Explore 缺口 6 裁决，私有 _snapshot）outflows：
#   WaterFlow → 三键槽 f"{unit_id}.{port_id}.q_avg_daily"/.kz/.q_design
#   （三量全随行）；SludgeFlow → .q_wet/.ds/.moisture；outqualities：
#   f"{unit_id}.{port_id}.{指标}" 全指标逐项；dims：str→float 逐项有限性
#   （GR-02），非该形状/非有限=InvalidExecutionError（带 unit_id）；
#   warnings/formula_ids 透传。**不动 result_schema**。
#
# 【design_hash 占位】（D3/D5 定稿）分层契约禁 executor import project.
#   content_hash（向上依赖）、RunEnv 七字段与四参签名锁定——置空串+
#   app.run_full_calc 回填（app→project 边合法）；三元组 T7b 闭环。
#
# 【数值纪律】字面量仅 0/1/2/10（recycle 初始估计 0.0/1.0——中性 kz）。
#
# 【测试要求】三单元线性图端到端、工况 2+k 全有结果、回路经 loop 收敛、
#   双跑 diff=0、单单元异常带 unit_id 上抛。
#
# 【参照】重写计划 §13.1 装配点/§14.1；ADR-003/ADR-007；简报 T7b D3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Final, Protocol, final

from waterprint.contracts.condition import ConditionSet, OperatingCondition
from waterprint.contracts.expr import ExprSyntaxError, eval_checked, parse_checked
from waterprint.contracts.flow import InvalidFlowError, WaterFlow
from waterprint.contracts.manifest import ConditionMapping, InvalidUnitConfig
from waterprint.contracts.ports import Edge, FluidKind, Port, PortRef
from waterprint.contracts.project_schema import DesignState
from waterprint.contracts.quality import InvalidQualityError, WaterQuality
from waterprint.contracts.result_schema import PlantResult, ReproTriple, UnitResultSnapshot
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.sludge import InvalidSludgeError, SludgeFlow
from waterprint.contracts.trace_api import TraceNodeSpec, TraceSink
from waterprint.contracts.unit_api import Unit, UnitContext, UnitResult
from waterprint.graph.loop import LoopConfig, LoopDivergence, solve_loop
from waterprint.graph.nodes import InvalidNodeError
from waterprint.graph.propagate import InvalidPropagationError, propagate
from waterprint.graph.topo import split_graph

# R5 领域异常族清单（宪法 §3 禁裸/过宽捕获 → 显式元组收口）：
# 新增领域异常族须同步本元组（漏项将令该族逃逸隔离包装——记档）。
_DOMAIN_EXCEPTIONS: Final[tuple[type[Exception], ...]] = (
    InvalidFlowError, InvalidQualityError, InvalidSludgeError,
    InvalidPropagationError, InvalidUnitConfig, InvalidNodeError, ExprSyntaxError,
)
_POOL_KEY: Final[str] = "pool.all_pools"
_WATER_FIELDS: Final[tuple[str, ...]] = ("q_avg_daily", "kz")
_SLUDGE_FIELDS: Final[tuple[str, ...]] = ("q_wet", "ds", "moisture")
_WATER_INIT: Final[dict[str, float]] = {"q_avg_daily": 0.0, "kz": 1.0}
_SLUDGE_INIT: Final[dict[str, float]] = {"q_wet": 0.0, "ds": 0.0, "moisture": 0.0}
_LOOP_KEYS: Final[tuple[str, ...]] = (
    "loop.tolerance", "loop.max_iterations", "loop.damping"
)


class InvalidExecutionError(Exception):
    """图执行非法（边形态/注册表缺项/DSL 求值/单元计算失败/回路发散）——GR-11 族。"""


class UnitRegistry(Protocol):
    """单元注册表协议：unit_id → Unit 实例（app.py 装配，R2 装配边界）。"""

    def __getitem__(self, unit_id: str) -> Unit: ...


@final
class _NullSink:
    """空迹收集器（env.trace_sink 缺省占位；trace 结果面归 M1——D10 记档）。"""

    def record(self, node: TraceNodeSpec) -> None:
        """丢弃记录（结构满足 TraceSink 协议）。"""


def _endpoint(raw: object, side: str, index: int) -> PortRef:
    """边端点转换：{"unit_id","port_id"} → PortRef（键缺失/类型错拒）。"""
    if not isinstance(raw, Mapping):
        raise InvalidExecutionError(
            f"design.edges[{index}].{side} 须为对象（含 unit_id/port_id）：{type(raw).__name__}")
    unit_id = raw.get("unit_id")
    port_id = raw.get("port_id")
    if not isinstance(unit_id, str) or not isinstance(port_id, str):
        raise InvalidExecutionError(
            f"design.edges[{index}].{side} 须含字符串 unit_id/port_id：{unit_id!r}, {port_id!r}")
    return PortRef(unit_id=unit_id, port_id=port_id)


def _edges_from_design(raw_edges: Sequence[object]) -> tuple[Edge, ...]:
    """design.edges（D3 冻结元素形态）→ contracts.ports.Edge 元组。"""
    edges: list[Edge] = []
    for index, element in enumerate(raw_edges):
        if not isinstance(element, Mapping):
            raise InvalidExecutionError(
                f"design.edges[{index}] 须为对象（src/dst/recycle）："
                f"得到 {type(element).__name__}")
        recycle = element.get("recycle", False)
        if not isinstance(recycle, bool):
            raise InvalidExecutionError(
                f"design.edges[{index}].recycle 须为布尔：得到 {recycle!r}")
        edges.append(
            Edge(src=_endpoint(element.get("src"), "src", index),
                 dst=_endpoint(element.get("dst"), "dst", index), recycle=recycle))
    return tuple(edges)


def _loop_config(env: RunEnv) -> LoopConfig:
    """RunEnv.engine_params 的 loop.* 三键 → LoopConfig（缺键=装配缺陷拒）。"""
    missing = [key for key in _LOOP_KEYS if key not in env.engine_params]
    if missing:
        raise InvalidExecutionError(
            f"RunEnv.engine_params 缺引擎参数键 {missing}"
            "（app 装配应经 _engine_params 投影补齐——UF-08）"
        )
    values = {key: env.engine_params[key].value for key in _LOOP_KEYS}
    count = values["loop.max_iterations"]
    if count != int(count):
        raise InvalidExecutionError(f"loop.max_iterations 须为整数值：得到 {count!r}")
    return LoopConfig(tolerance=values["loop.tolerance"], max_iterations=int(count),
                      damping=values["loop.damping"])


def _dotted(node: ast.AST) -> str | None:
    """Name/Attribute 链 → 点式扁平名（B4 双胞胎：与 manifest_validation 同款）。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        if base is not None:
            return f"{base}.{node.attr}"
    return None


def _rule_names(rule: str) -> frozenset[str]:
    """rule 引用名收集（裸名+点式链）——manifest_validation._referenced_names
    的 B4 双胞胎（禁私有 import，同源同步义务）。"""
    try:
        tree = ast.parse(rule, mode="eval")
    except SyntaxError as exc:
        raise ExprSyntaxError(f"工况映射 rule 语法非法：{rule!r}（{exc.msg}）") from exc
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            path = _dotted(node)
            if path is not None:
                names.add(path)
    return frozenset(names)


def _apply_mappings(
    unit_id: str,
    params: dict[str, float],
    mappings: tuple[ConditionMapping, ...],
    condition: OperatingCondition,
) -> dict[str, float]:
    """DSL 工况映射求值（bindings=params 全量 ∪ pool.all_pools；bool→float 归一）。"""
    result = dict(params)
    bindings: dict[str, float | bool] = dict(result)
    bindings[_POOL_KEY] = condition.offline_unit != unit_id
    for mapping in mappings:
        allowed = _rule_names(mapping.rule) | frozenset(result) | {_POOL_KEY}
        try:
            parsed = parse_checked(mapping.rule, allowed)
            value = eval_checked(parsed, bindings)
        except ExprSyntaxError as exc:
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 工况映射 rule 求值失败"
                f"（target={mapping.target!r}）：{exc}") from exc
        result[mapping.target] = float(value) if isinstance(value, bool) else value
    return result


def _unit_params(unit: Unit, node_value: Mapping[str, object]) -> dict[str, float]:
    """ctx.params 装配：manifest 默认值 ∪ design 节点值覆盖（bool 拒，GR-02）。"""
    params = {spec.field_id: spec.default for spec in unit.manifest.params}
    for key, value in node_value.items():
        if key == "kind":
            continue  # 内置节点结构元数据（D5 装配口径），不进参数面
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidExecutionError(
                f"design 节点参数 {key!r} 须为数值（bool 拒，GR-02）：得到 {value!r}")
        params[key] = float(value)
    return params


def _dims_of(dims: object, unit_id: str) -> dict[str, float]:
    """UF-42 dims 投影：str→float 逐项有限性校验（GR-02），他形状拒。"""
    if not isinstance(dims, Mapping):
        raise InvalidExecutionError(
            f"单元 {unit_id!r} 的 dims 须为 str→float 映射：得到 {type(dims).__name__}")
    projected: dict[str, float] = {}
    for key, value in dims.items():
        numeric = (
            isinstance(key, str)
            and not isinstance(value, bool)
            and isinstance(value, int | float)
        )
        if not numeric or not isfinite(float(value)):
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 的 dims[{key!r}]={value!r} 非法（GR-02：字符串键→有限数值）")
        projected[key] = float(value)
    return projected


def _snapshot(result: UnitResult, unit_id: str) -> UnitResultSnapshot:
    """UF-42 投影表：三键槽流量+指标键水质+dims 校验（规格头【UF-42 投影表】）。"""
    outflows: dict[str, float] = {}
    for ref, stock in result.outflows.items():
        prefix = f"{unit_id}.{ref.port_id}"
        if isinstance(stock, WaterFlow):
            outflows[f"{prefix}.q_avg_daily"] = stock.q_avg_daily
            outflows[f"{prefix}.kz"] = stock.kz
            outflows[f"{prefix}.q_design"] = stock.q_design
        elif isinstance(stock, SludgeFlow):
            outflows[f"{prefix}.q_wet"] = stock.q_wet
            outflows[f"{prefix}.ds"] = stock.ds
            outflows[f"{prefix}.moisture"] = stock.moisture
        else:
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 输出端口 {prefix} 股类型非法：{type(stock).__name__}")
    outqualities = {
        f"{unit_id}.{ref.port_id}.{indicator}": value
        for ref, quality in result.outqualities.items()
        for indicator, value in quality.concentrations.items()
    }
    return UnitResultSnapshot(
        unit_id=unit_id, outflows=outflows, outqualities=outqualities,
        dims=_dims_of(result.dims, unit_id), warnings=result.warnings,
        formula_ids=result.formula_ids)


def _fields(fluid: FluidKind) -> tuple[str, ...]:
    """流体 → 状态展开字段集（WATER 两量/SLUDGE 三量）。"""
    return _WATER_FIELDS if fluid is FluidKind.WATER else _SLUDGE_FIELDS


def _initial(fluid: FluidKind) -> dict[str, float]:
    """recycle 初始估计（确定性 R5）：WATER 零流量+单位 kz；SLUDGE 零股。"""
    return dict(_WATER_INIT if fluid is FluidKind.WATER else _SLUDGE_INIT)


def _estimate(
    fluid: FluidKind, prefix: str, flat: Mapping[str, float]
) -> WaterFlow | SludgeFlow:
    """估计值写回构造（直接构造——图内 Q=0 合法 GR-04，propagate 同款）。"""
    if fluid is FluidKind.WATER:
        return WaterFlow(
            q_avg_daily=flat[f"{prefix}.q_avg_daily"], kz=flat[f"{prefix}.kz"]
        )
    return SludgeFlow(q_wet=flat[f"{prefix}.q_wet"], ds=flat[f"{prefix}.ds"],
                      moisture=flat[f"{prefix}.moisture"])


@dataclass(frozen=True)
@final
class _ConditionContext:
    """单工况只读上下文（execute_graph 四参的内部展开，工况间零共享）。"""

    design: DesignState
    units: UnitRegistry
    condition: OperatingCondition
    env: RunEnv
    edges: tuple[Edge, ...]
    sink: TraceSink
    loop_config: LoopConfig


@final
class _RunState:
    """单工况可变执行状态（池+快照+recycle 估计；每工况新建，R1）。"""

    def __init__(self, ctx: _ConditionContext) -> None:
        self.ctx = ctx
        self.flows: dict[PortRef, WaterFlow | SludgeFlow] = {}
        self.qualities: dict[PortRef, WaterQuality] = {}
        self.snapshots: dict[str, UnitResultSnapshot] = {}
        self.recycle_flows: dict[PortRef, WaterFlow | SludgeFlow] = {}
        self.recycle_qualities: dict[PortRef, WaterQuality] = {}

    def _unit(self, unit_id: str) -> Unit:
        """注册表取单元（缺项=装配缺陷，InvalidExecutionError 保链）。"""
        try:
            return self.ctx.units[unit_id]
        except KeyError as exc:
            raise InvalidExecutionError(
                f"单元注册表缺 {unit_id!r}（app.assemble 应已校验完备）"
            ) from exc

    def _inflows(self, unit_id: str) -> tuple[
        dict[PortRef, WaterFlow | SludgeFlow], dict[PortRef, WaterQuality]]:
        """入流装配：非 recycle 边经 propagate（同 dst 多股=ADR-005 工况加权
        合并）；recycle 边取当前估计（键化到各自 dst ref）。"""
        forward = [e for e in self.ctx.edges if e.dst.unit_id == unit_id and not e.recycle]
        inflows, inqualities = propagate(
            {e.src: self.flows[e.src] for e in forward},
            {e.src: self.qualities[e.src] for e in forward}, forward, self.ctx.condition)
        merged: dict[PortRef, WaterFlow | SludgeFlow] = dict(inflows)
        qualities: dict[PortRef, WaterQuality] = dict(inqualities)
        for edge in (e for e in self.ctx.edges if e.dst.unit_id == unit_id and e.recycle):
            if edge.src not in self.recycle_flows:
                raise InvalidExecutionError(
                    f"recycle 边 {edge.src.unit_id}.{edge.src.port_id}→"
                    f"{edge.dst.unit_id}.{edge.dst.port_id} recycle 标记不构成回路"
                    "（装配异常：recycle 边必须闭合成 SCC 回路组——GR-09）")
            merged[edge.dst] = self.recycle_flows[edge.src]
            quality = self.recycle_qualities.get(edge.src)
            if quality is not None:
                qualities[edge.dst] = quality
        return merged, qualities

    def _compute(self, unit_id: str, ctx: UnitContext) -> UnitResult:
        """单元 compute + R5 异常隔离（领域异常族 → InvalidExecutionError）。"""
        try:
            return self.ctx.units[unit_id].compute(ctx)
        except _DOMAIN_EXCEPTIONS as exc:
            key = ConditionSet.key(self.ctx.condition)
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 在工况 {key!r} 计算失败：{type(exc).__name__}: {exc}") from exc

    def run(self, unit_id: str) -> None:
        """单单元执行：参数装配→DSL 变换→入流装配→compute→池+快照落账。"""
        unit = self._unit(unit_id)
        params = _apply_mappings(
            unit_id,
            _unit_params(unit, self.ctx.design.nodes[unit_id]),
            unit.manifest.condition_mappings,
            self.ctx.condition,
        )
        inflows, inqualities = self._inflows(unit_id)
        ctx = UnitContext(
            unit_id=unit_id, inflows=inflows, inqualities=inqualities, params=params,
            condition=self.ctx.condition, assumptions=self.ctx.env.assumptions,
            trace=self.ctx.sink)
        result = self._compute(unit_id, ctx)
        self.flows.update(result.outflows)
        self.qualities.update(result.outqualities)
        self.snapshots[unit_id] = _snapshot(result, unit_id)

    def run_all(self) -> None:
        """层-SCC 调度主循环：组先于同层单点（R2 次序推演记档）。"""
        layers, loop_groups = split_graph(list(self.ctx.design.nodes), self.ctx.edges)
        layer_of = {node: index for index, layer in enumerate(layers) for node in layer}
        group_of = {node: group for group in loop_groups for node in group}
        solved: set[tuple[str, ...]] = set()
        for index, layer in enumerate(layers):
            for group in loop_groups:
                if group not in solved and max(layer_of[m] for m in group) == index:
                    self._solve_group(group, layer_of)
                    solved.add(group)
            for node in layer:
                if node not in group_of:
                    self.run(node)

    def _recycle_port(self, edge: Edge) -> Port:
        """recycle 边 dst 端口的 manifest 声明（流体类型判据）。"""
        for port in self._unit(edge.dst.unit_id).manifest.ports:
            if port.port_id == edge.dst.port_id:
                return port
        raise InvalidExecutionError(
            f"recycle 边 dst 端口未声明：{edge.dst.unit_id}.{edge.dst.port_id}"
            "（manifest ports 无此 port_id）")

    def _solve_group(self, group: tuple[str, ...], layer_of: Mapping[str, int]) -> None:
        """回路组联立求解：组闭包交 solve_loop，收敛解终跑写回（【回路闭包口径】）。"""
        members = frozenset(group)
        internal = [e for e in self.ctx.edges if e.recycle and e.src.unit_id in members
                    and e.dst.unit_id in members]
        fluid_of = {edge: self._recycle_port(edge).fluid for edge in internal}
        guess: dict[str, dict[str, float]] = {}
        for edge in internal:
            prefix = f"{edge.src.unit_id}.{edge.src.port_id}"
            guess.setdefault(edge.src.unit_id, {}).update(
                {f"{prefix}.{field}": value
                 for field, value in _initial(fluid_of[edge]).items()})
        order = sorted(members, key=lambda node: (layer_of[node], node))

        def compute(flat: dict[str, float]) -> dict[str, float]:
            """组闭包 F：写回估计→按层序重算→读源端口新值（水质尾随更新）。"""
            for edge in internal:
                prefix = f"{edge.src.unit_id}.{edge.src.port_id}"
                self.recycle_flows[edge.src] = _estimate(fluid_of[edge], prefix, flat)
            for node in order:
                self.run(node)
            for edge in internal:
                quality = self.qualities.get(edge.src)
                if quality is not None:
                    self.recycle_qualities[edge.src] = quality
            return {
                f"{edge.src.unit_id}.{edge.src.port_id}.{field}": float(
                    getattr(self.flows[edge.src], field))
                for edge in internal for field in _fields(fluid_of[edge])}

        try:
            solution = solve_loop(list(group), compute, guess, self.ctx.loop_config)
        except LoopDivergence as exc:
            key = ConditionSet.key(self.ctx.condition)
            raise InvalidExecutionError(
                f"回路组 {list(group)} 在工况 {key!r} 不收敛：{exc}") from exc
        compute({k: v for bucket in solution.values() for k, v in bucket.items()})


def execute_graph(
    design: DesignState,
    units: UnitRegistry,
    conditions: ConditionSet,
    env: RunEnv,
) -> PlantResult:
    """唯一执行正门：逐工况整图计算（层-SCC 调度+DSL 映射+UF-42 投影）。

    repro.design_hash 置空串占位（分层契约禁向上依赖）——由 app.run_full_calc
    回填（D3/D5 裁决）；trace=()/summary={} 占位与 R4 的冲突记档 D10。
    """
    edges = _edges_from_design(design.edges)
    sink: TraceSink = env.trace_sink if env.trace_sink is not None else _NullSink()
    loop_config = _loop_config(env)
    result_conditions: dict[str, Mapping[str, UnitResultSnapshot]] = {}
    for condition in conditions.iter_all():
        state = _RunState(_ConditionContext(
            design=design, units=units, condition=condition, env=env,
            edges=edges, sink=sink, loop_config=loop_config))
        state.run_all()
        result_conditions[ConditionSet.key(condition)] = MappingProxyType(
            dict(state.snapshots))
    return PlantResult(
        conditions=MappingProxyType(result_conditions), summary={}, trace=(),
        repro=ReproTriple(design_hash="", engine_version=env.engine_version,
                          data_version=env.data_version))
