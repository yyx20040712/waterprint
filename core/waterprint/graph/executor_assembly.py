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
#   solve_loop 四参锁零触碰，executor 消费（跨件私有引用同先例）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Final, final

from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.run_env import RunEnv
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
