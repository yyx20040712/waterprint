"""结果缓存件：进程内 LRU+命中重放（仅优化——冷/暖结果含 trace 字节级等价）。

输入:  CacheKey（incremental 五字段键）+ UnitResult+TraceNodeSpec 节点（冷跑捕获）
输出:  命中条目（原引用返回——消费面禁改写）/未命中 None（调用方计算后 put）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B12 实现 2026-09-06——briefs/task-B12-brief.md 终裁；
#   镜像测试 tests/graph/test_cache.py）
#
# 【公开接口】
#   class ResultCache：进程内 LRU（容量默认 512 条，构造可配；get/put/
#       __len__/clear）；条目不可变——失效=键不再命中，永不原地改写
#   class CachedUnitRun(不可变)：缓存值载体=(UnitResult,
#       tuple[TraceNodeSpec,...])——trace 节点冷跑捕获、命中重放
#   class CaptureSink：冷跑捕获腔（转发真实 sink 并累积节点）
#   design_fingerprint(design: DesignState) -> str：缓存键 design_hash
#       分量（sha256 of 规范化 JSON of model_dump 全字段——graph 内自算）
#   default_cache() -> ResultCache：进程级惰性单例（executor 消费面）
#
# 【行为规格】
#   R1 命中=跳过 compute 后与未命中路径同码落账（池 update+快照投影），
#      并先向真实 sink 逐节点重放 trace——冷/暖 PlantResult 含 trace
#      字节级相同（锁定测试 test_app.py:187 双跑字节同的承载前提；
#      重放次序=调度序内单元位置恒定→全 tree 次序恒定）。
#   R2 回路组旁路：_solve_group 组内迭代中间值不入缓存（get 命中首
#      迭代值=假收敛——正确性必需）；executor 侧 use_cache=False 显式
#      旁路，组内成员 get/put 双面排除。
#   R3 键=CacheKey 五字段（unit_id/design_hash[=design_fingerprint]/
#      condition_key/engine_version/data_version）——engine/data 版本
#      变化自动失配（§16 A8）；「永不原地改写」指条目对象值面不可变
#      （命中返回同对象零变异）——同键 put=槽位替换（新条目对象），
#      旧条目对象永不改写，与无锁模型一致（executor 流程先 get 命中
#      即返回，同键 put 不可达）。
#   R4 design_fingerprint 与 ReproTriple.design_hash（L4 content_hash
#       ——io.dumps_design+format_version 头）数值不同源：仅缓存键内部
#       用，不进 ReproTriple（分层契约：L3 禁向上依赖 L4）。
#
# 【部署与并发前提】
#   - 进程级单例：每 worker 进程各一份、无跨进程共享（§17.3 api 单进程
#     +calc 进程池 N worker 直配——跨 worker 不共享命中属规格内行为）；
#   - 进程内单线程消费前提：部署形态=ProcessPoolExecutor 每 worker 同时
#     单任务（manager.py 实测）；条目不可变仅覆盖值面，LRU 顺序态的
#     线程安全由此前提担保——进程内多线程化须先加锁；
#   - get 返回条目原引用：消费面禁止改写（executor 侧只读已实证；
#     防御拷贝否弃=热路径成本+Mapping 深拷贝语义含糊）。
#
# 【落盘面挂账（后续批）】
#   - 内存治理=本批 LRU 按条数（512 条）；512MB=落盘 arrow 字节预算
#     （§17.2「大结果落盘 arrow…容量上限 512MB 超限逐出」主语=落盘面）
#     ——本批落盘不实装，无内存字节治理义务；
#   - 落盘实装须预记跨重启纪律：键健全性前提=env.assumptions≡
#     DEFAULT_ASSUMPTIONS（进程内恒定）∪design.assumption_overrides
#     （在指纹参与面）——落盘携带跨重启后须引擎版本纪律或 assumptions
#     摘要入键；
#   - 批 11 性质测试的全量 oracle 跑须 cache-cold（clear 后跑）。
#
# 【数值纪律】容量常量 512/512MB 居本件声明式真源区（带规格出处——
#   check_magic_numbers 白名单登记，B8 _constants.py 同款先例）。
#
# 【测试要求】LRU 逐出/五分量逐项失配/指纹全字段覆盖/命中跳过+重放/
#   R4 整 design 失配+旧键保留/回路组旁路/单例 clear 隔离。
#
# 【参照】重写计划 §17.2/§17.3；briefs/task-B12-brief.md（裁定1~4）；
#   reports/task-B12-DESIGN-kimi-design.md + task-B12-deepseek-review.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from typing import Final, final

from waterprint.contracts.project_schema import DesignState
from waterprint.contracts.trace_api import TraceNodeSpec, TraceSink
from waterprint.contracts.unit_api import UnitResult
from waterprint.graph.incremental import CacheKey, _canonical_json

_DEFAULT_CAPACITY: Final[int] = 512  # 内存条目数上限（§17.2 LRU 默认）


@dataclass(frozen=True)
@final
class CachedUnitRun:
    """缓存值载体：compute 产物+其执行期记录的 trace 节点（重放材料）。"""

    result: UnitResult
    trace_nodes: tuple[TraceNodeSpec, ...]


def design_fingerprint(design: DesignState) -> str:
    """缓存键 design_hash 分量：sha256(model_dump 规范化 JSON)。

    model_dump 全字段（DesignState 现八字段）自动覆盖（与 L4 content_hash
    参与面同集——R4 注记：数值不同源，仅缓存内部用）。"""
    payload = _canonical_json(design.model_dump())
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@final
class CaptureSink:
    """冷跑捕获腔：转发真实 sink 并累积节点（缓存值 trace 重放材料）。"""

    def __init__(self, inner: TraceSink) -> None:
        self._inner = inner
        self.nodes: list[TraceNodeSpec] = []

    def record(self, node: TraceNodeSpec) -> None:
        """转发+累积（到达序——重放次序的确定性来源）。"""
        self._inner.record(node)
        self.nodes.append(node)


@final
class ResultCache:
    """进程内 LRU 结果缓存（条目不可变——失效=键不再命中）。"""

    def __init__(self, capacity: int = _DEFAULT_CAPACITY) -> None:
        if capacity < 1:
            raise ValueError(f"缓存容量须为正整数：得到 {capacity!r}")
        self._capacity = capacity
        self._entries: OrderedDict[CacheKey, CachedUnitRun] = OrderedDict()

    def get(self, key: CacheKey) -> CachedUnitRun | None:
        """命中=条目原引用+LRU 位次刷新；未命中=None。"""
        entry = self._entries.get(key)
        if entry is not None:
            self._entries.move_to_end(key)
        return entry

    def put(self, key: CacheKey, value: CachedUnitRun) -> None:
        """入缓+超容逐出最旧（同键再 put=覆盖本键位次——条目面永不改写）。"""
        self._entries[key] = value
        self._entries.move_to_end(key)
        while len(self._entries) > self._capacity:
            self._entries.popitem(last=False)

    def __len__(self) -> int:
        """条目数（测试与运维面）。"""
        return len(self._entries)

    def clear(self) -> None:
        """清空（测试隔离+批 11 oracle 冷跑纪律）。"""
        self._entries.clear()


@lru_cache(maxsize=1)
def default_cache() -> ResultCache:
    """进程级惰性单例（executor 消费面——部署前提见规格头）。"""
    return ResultCache()
