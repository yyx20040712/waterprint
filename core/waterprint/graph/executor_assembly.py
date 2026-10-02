"""execute_graph 输入装配域：端点解析/边推导/回路配置/单元参数装配。

输入:  DesignState 图数据（edges/nodes 原始映射）+ RunEnv.engine_params + Unit manifest
输出:  PortRef/Edge 元组/LoopConfig/params 装配中间结构（executor.py 消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（TD1 技术债小批 2026-09-09；镜像测试 tests/graph/test_executor_assembly.py）：
#   自 executor.py 缝 A（输入装配域）拆出六件：_LOOP_KEYS/_NullSink/
#   _endpoint/_edges_from_design/_loop_config/_unit_params——行为零变更
#   纯搬迁（B3 R2 executor_dsl/executor_projection 拆分同构第三例）；
#   _LOOP_KEYS 随唯一消费方 _loop_config 同迁。
#   两件引用面=跨件私有引用沿 executor_dsl 先例（executor 消费
#   executor_dsl._apply_mappings 同款），非包外公开契约；executor.py
#   顶部同名导入保引用连续（消费面零改动）。
#   InvalidExecutionError 定义面在 executor_dsl（B3 R2 修正①），本件经
#   import 消费——同向无环。
#   _LoopProbe（P2 次批 2026-09-12，ADR-012 D2）：回路统计包装器——
#   forward_stocks（conv-golden 批缝 B 2026-10-02）：前向边源股装配
#   （在场股直取+offline 检修饥饿边零股承接——口径全文见该函数
#   docstring；executor._inflows 唯一消费方）。
#   UnitRegistry 协议（CI-fix 批缝 C 2026-10-02）：自 executor.py 下移
#   ——forward_stocks 第 4 参实参=该协议实例（原签名 Mapping[str, Unit]
#   与 UnitRegistry 结构不兼容，mypy strict arg-type 红；定义面下移
#   单源化+executor.py 同名再导入保引用连续——TD1/B3 同构第四例，
#   行为零变更纯搬迁，恒等钉第七符号）。
#   solve_loop 四参锁零触碰，executor 消费（跨件私有引用同先例）。
#   B3-c 批 2c 收敛（2026-09-19）：_endpoint/_edges_from_design 校验/
#   消息逻辑单源化至 contracts.edge_parsing（endpoint_from/edges_from，
#   error=InvalidExecutionError 绑定件——定案 docs/design/2026-09-19_
#   b4-twins-convergence-design.md）；私有名与定义位不动=镜像恒等钉
#   零扰动；executor 侧 _endpoint 消息两处补「得到」分隔词（app 版
#   对齐，J3 呈案 A——状态码契约面经类型注入恒等）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Final, Protocol, final

from waterprint.contracts.condition import OperatingCondition
from waterprint.contracts.edge_parsing import edges_from, endpoint_from
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import Edge, FluidKind, PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.trace_api import TraceNodeSpec
from waterprint.contracts.unit_api import Unit
from waterprint.graph.executor_dsl import InvalidExecutionError
from waterprint.graph.loop import LoopConfig

_LOOP_KEYS: Final[tuple[str, ...]] = (
    "loop.tolerance", "loop.max_iterations", "loop.damping"
)


@final
class _NullSink:
    """空迹收集器（env.trace_sink 缺省占位；trace 结果面归 M1——D10 记档）。"""

    def record(self, node: TraceNodeSpec) -> None:
        """丢弃记录（结构满足 TraceSink 协议）。"""


@final
class _LoopProbe:
    """回路统计包装器（ADR-012 D2——solve_loop 四参锁零触碰）。

    计数=iterations（compute 被调次数，收敛首步即 1）；末步残差=末次
    入参 state × 返回 evaluated 按 loop._step 同款公式复算（阻尼更新+
    全变量相对残差取 max——确定性计算，复算值与 solve_loop 内部恒等）。"""

    __slots__ = ("_inner", "_last_evaluated", "_last_state", "iterations")

    def __init__(
        self, inner: Callable[[dict[str, float]], dict[str, float]]
    ) -> None:
        self._inner = inner
        self.iterations = 0
        self._last_state: dict[str, float] | None = None
        self._last_evaluated: dict[str, float] | None = None

    def compute(self, flat: dict[str, float]) -> dict[str, float]:
        """包装回调：计数+末步入/出快照（值透传零修改——数值行为不变）。"""
        self.iterations += 1
        evaluated = self._inner(flat)
        self._last_state = dict(flat)
        self._last_evaluated = dict(evaluated)
        return evaluated

    def final_residual(self, config: LoopConfig) -> float:
        """末步全变量相对残差复算（loop._step 同式 R1 口径；未驱动即取=装配缺陷）。"""
        if self._last_state is None or self._last_evaluated is None:
            raise InvalidExecutionError(
                "LoopProbe.final_residual 在 compute 未被调用时即取"
                "（装配缺陷——probe 必须先经 solve_loop 驱动）"
            )
        residual_max = 0.0
        for name, old in self._last_state.items():
            fresh = self._last_evaluated[name]
            new = old + config.damping * (fresh - old)
            residual = abs(new - old) / max(abs(old), 1.0)
            residual_max = max(residual_max, residual)
        return residual_max


def _endpoint(raw: object, side: str, index: int) -> PortRef:
    """边端点转换绑定件：内核 endpoint_from + 本域拒绝载体（B3-c 收敛）。

    逻辑/消息单源=contracts.edge_parsing；本定义仅为 InvalidExecutionError
    类型绑定（批 3a not_found 注入同型）。**镜像钉兼容壳（生产零消费——
    门一 W1 处置）**：生产路径的端点解析经内核 edges_from→endpoint_from
    直达，本私有名仅由 tests/graph/test_executor_assembly.py 恒等钉与
    executor.py 再导出面持有——改本函数 error 类不改变运行时行为，
    契约载体改动须改 _edges_from_design（热路径绑定）。
    """
    return endpoint_from(raw, side, index, error=InvalidExecutionError)


def _edges_from_design(raw_edges: Sequence[object]) -> tuple[Edge, ...]:
    """design.edges（D3 冻结元素形态）→ contracts.ports.Edge 元组（绑定件）。"""
    return edges_from(raw_edges, error=InvalidExecutionError)


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


def _starved_stock(edge: Edge, units: UnitRegistry) -> tuple[
    WaterFlow | SludgeFlow, WaterQuality | None]:
    """检修饥饿边零股（流体取 dst 端口 manifest 声明——_recycle_port 同判据）。

    WATER=WaterFlow(0, kz=1) 直接构造+空水质 WaterQuality({})（GR-04
    图内 Q=0 合法——make_flow 的 q>0 是厂界口径，propagate 同款 idiom；
    propagate WATER 股恒需成对〔_merge_water 取 upstream_qualities[src]〕，
    空水质零指标=零权股不稀释下游浓度）；SLUDGE=SludgeFlow(0,0,0)
    单位元（contracts/sludge P4 全零股单位元同款），无水质。"""
    for port in units[edge.dst.unit_id].manifest.ports:
        if port.port_id == edge.dst.port_id:
            if port.fluid is FluidKind.SLUDGE:
                return SludgeFlow(q_wet=0.0, ds=0.0, moisture=0.0), None
            return WaterFlow(q_avg_daily=0.0, kz=1.0), WaterQuality({})
    raise InvalidExecutionError(
        f"饥饿边 dst 端口未声明：{edge.dst.unit_id}.{edge.dst.port_id}"
        "（manifest ports 无此 port_id——零股流体判据无源，GR-09）")


class UnitRegistry(Protocol):
    """单元注册表协议：unit_id → Unit 实例（app.py 装配，R2 装配边界）。

    CI-fix 批缝 C（2026-10-02）自 executor.py 下移单源化（行为零变更
    纯搬迁）；executor.py 同名再导入保引用连续——恒等钉第七符号。"""

    def __getitem__(self, unit_id: str) -> Unit: ...


def forward_stocks(
    flows: Mapping[PortRef, WaterFlow | SludgeFlow],
    qualities: Mapping[PortRef, WaterQuality],
    forward: Sequence[Edge],
    units: UnitRegistry,
    condition: OperatingCondition,
) -> tuple[
    dict[PortRef, WaterFlow | SludgeFlow], dict[PortRef, WaterQuality]]:
    """前向边源股装配（conv-golden 批 2026-10-02 缝 B，executor._inflows 迁入）。

    【检修饥饿边口径】ADR-007 offline 语义=「该单元 n−1、其余全池」；
    动态多口单元（conveyance peishuijing/peishuiqu/jipeishuijing 形态
    ——manifest ports 声明单 out 口、compute 按参数 n 动态产 out_1~
    out_n）在 offline 帧参数 n 降为 n−1 后只产 out_1~out_{n−1}，设计期
    布线的 out_n 边失去源股=「检修饥饿边」。承接语义：offline 帧
    （condition.offline_unit 非 None）内前向边源端口不在 flows 池**且
    缺股源单元==offline 目标单元**（edge.src.unit_id==offline_unit——
    承接仅限目标单元检修降级所产生的饥饿边）→ 该边承载零股
    （_starved_stock）——物理口径：检修停运口零出流，在运口承载
    全流量（compute 按 n−1 均分）→ Σ边股==入流守恒成立。基线帧
    （design/avg）与 offline 帧内**非目标单元**缺股均不适用：源端口
    缺股=装配/单元缺陷，维持原生 KeyError 裸逃逸（GR-08 禁静默默认
    ——本口径仅「offline 帧×目标单元源」生效，基线与非目标缺股行为
    位串级零变）。行为锚=tests/graph/test_executor_starved_edge.py
    镜像四用例+golden municipal_34760_conveyance e2e。"""
    upstream: dict[PortRef, WaterFlow | SludgeFlow] = {}
    upstream_qualities: dict[PortRef, WaterQuality] = {}
    for edge in forward:
        stock = flows.get(edge.src)
        if (stock is None and condition.offline_unit is not None
                and edge.src.unit_id == condition.offline_unit):
            stock, quality = _starved_stock(edge, units)
            upstream[edge.src] = stock
            if quality is not None:
                upstream_qualities[edge.src] = quality
            continue
        upstream[edge.src] = flows[edge.src]  # 缺股=原生 KeyError（GR-08）
        upstream_qualities[edge.src] = qualities[edge.src]
    return upstream, upstream_qualities
