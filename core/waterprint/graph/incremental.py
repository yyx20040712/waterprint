"""脏传播与缓存（仅优化，不参与语义：incremental == 全量重算，字节级）。

输入:  content_hash 变更（旧 design → 新 design 的差集）
输出:  重算范围（受影响单元/工况集合）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B9 实现 2026-09-06；镜像测试 tests/graph/test_incremental.py +
# 性质测试 properties_incremental.py）
#
# 【公开接口】
#   recompute_scope(old_design: DesignState, new_design: DesignState) -> Scope
#       受影响单元集 = 参数变更单元 ∪ 其图上所有下游（含穿越回路的
#       回路组整体）；Scope 含单元集与工况集
#   class CacheKey(不可变)：(unit_id, design_hash, condition_key,
#       engine_version, data_version)——条目不可变，失效=键不再命中，
#       永不原地改写（§17.2 无锁模型）
#   class Scope(不可变) 四栏（B9 D1 实装）：changed_units（参数变更单元
#       frozenset）/ downstream_units（下游闭包+回路不动点扩张后的总下游
#       集）/ loop_groups（命中回路组 frozenset[frozenset[str]]）/
#       full_graph（全图回落标记）；derive 投影：affected_units（False=
#       changed∪downstream∪loop 组成员并集；True=changed_units——全图
#       回落自包含：此时 changed_units 直接装新设计全部 unit_id，
#       downstream/loop 置空[全图语义已含]，调用方无需再持 new_design）、
#       ordered_units（sorted 字典序 tuple——B6 design_digest 确定性先例）
#   class ResultCache：进程内 LRU（默认 512 条）+ 大结果落盘 arrow
#      （按 hash 重载，容量上限可配，默认 512MB，超限逐出最旧）
#
# 【范围判定规则】（B9 实装——D2/D3 定稿的比较基准与保守回落面）
#   ①拓扑比对先行短路：nodes 键集差（增删单元）或规范化边集差 →
#     full_graph=True 全图回落（不做局部扩张；遍历以新拓扑为准）。边规范
#     化=frozenset of (src.unit_id, src.port_id, dst.unit_id, dst.port_id)
#     ——序/键序噪声天然消除（golden municipal_34760 实证边键恰 src/dst
#     两键）；边 dict 若有超 src/dst 的键（recycle 等）或端点形态不合 →
#     整边规范化 JSON 比较兜底（json.dumps sort_keys——io.py/B6
#     design_digest 序列化先例）。**端点 dict 超集键不入比较基准**
#     （B9 R 轮 G1-02 补注：执行面 _to_edges 同款只消费 unit_id/
#     port_id/recycle——端点额外键零语义，不入比较=无漏检方向）。
#   ②其余五键+site（constraint_choices/checked_units/assumption_
#     overrides/influent/standard_binding/site）任一面变更 →
#     full_graph=True 保守回落（总控加裁：不判语义不猜——规格沉默处
#     保守裁决，禁就地自创语义）。
#   ③参数 diff：nodes 共有键逐单元载荷规范化 JSON 比较（键序噪声消除），
#     任一字段不同 → 单元整体入 changed_units（计算相关字段边界=载荷全
#     字段本批口径——领域边界细分留用户承办挂账）。
#   ④下游闭包=全边邻接（含 recycle——脏传播沿一切流股路径）自写 BFS
#     （topo._adjacency 私有件跨包 `_` 前缀禁引——自写合规，D3）；回路
#     不动点扩张（R2）：split_graph 取 loop_groups——变更/下游集命中任
#     一组 → 整组并入 → 新成员再扩下游 → 至集合不再增长。
#   ⑤边结构不合（_to_edges 拒）或图非法（split_graph InvalidConnection
#     ——悬空边/误连环）→ full_graph=True 保守回落：范围判定只优化不引
#     入新失败面（执行期同错仍由 executor 抛出）。
#
# 【行为规格】
#   R1 语义铁律：增量结果必须与全量重算**字节级一致**——随机变更序列下
#      incremental == 全量 是常驻性质测试（违反即 CI 失败，§17.2）；
#      缓存命中只是跳过计算，永不改写结果语义（§3 保证 6）。
#   R2 回路组脏传播：回路组内任一单元变脏 → 整组重算（保守正确性）。
#   R3 缓存键含三元组：engine/data 版本变化自动失配（§16 A8）。
#   R4 方案应用（枚举→写参数）产生新 design_hash → 旧结果自然过期并
#      标 stale，禁止静默覆盖（§17.1 事件矩阵）。
#
# 【B9 实装状态】（2026-09-06，briefs/task-B9-brief.md D7 注记）
#   - 范围判定语义层已落地：参数变更 diff+下游闭包+回路不动点扩张+拓扑
#     变更全图回落+其余键保守回落+CacheKey 键材料（恰五字段 frozen——
#     锁面用例①②翻转面）；
#   - 执行效果待 executor 集成：本批 recompute_scope 不被 executor 消费，
#     集成批接线后增量跳过才生效；
#   - R1 字节级等价不背书：properties_incremental 种子（m3_incremental_
#     seed.json，人类窗口）与断言接线未落地前，R1 是规格承诺非已证性质；
#   - ResultCache 未实装（LRU+落盘面留后续批）；Scope 四栏=单元集面，
#     骨架原文「含单元集与工况集」的工况维度未入本切片（增量按工况逐图
#     口径归 executor 集成批裁决）。
#
# 【测试要求】变更单元下游集正确（含回路组扩张）、缓存键三元组失配、
#   LRU 逐出；性质：随机编辑序列下增量==全量（hypothesis，字节级比较）。
#
# 【参照】重写计划 §3-6/§17.2；病灶"增量 dirty 链路历代 P0"；
#   briefs/task-B9-brief.md（B9 D1~D7 终裁）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, final

from waterprint.contracts.ports import Edge, InvalidConnection, PortRef
from waterprint.contracts.project_schema import DesignState
from waterprint.graph.topo import split_graph

# 规范化 JSON 参数（io.py/B6 design_digest 同款纪律本文件自写——跨模块
# 私有件禁引，B4 双胞胎代价先例）：sort_keys 消键序噪声+紧致分隔符。
_JSON_KWARGS: Final[dict[str, Any]] = {
    "sort_keys": True,
    "ensure_ascii": False,
    "separators": (",", ":"),
}


@dataclass(frozen=True)
@final
class CacheKey:
    """结果缓存键（不可变，恰五字段——锁面用例①②冻结面）。

    engine/data 版本含键内：版本变化自动失配（R3，§16 A8）；条目不可变，
    失效=键不再命中，永不原地改写（§17.2 无锁模型）。本批纯定义件
    （键材料，D4）：零默认值零派生零构造面。
    """

    unit_id: str
    design_hash: str
    condition_key: str
    engine_version: str
    data_version: str


@dataclass(frozen=True)
@final
class Scope:
    """重算范围（不可变四栏，D1 定稿——语义全表见规格头【公开接口】节）。"""

    changed_units: frozenset[str]
    downstream_units: frozenset[str]
    loop_groups: frozenset[frozenset[str]]
    full_graph: bool

    @property
    def affected_units(self) -> frozenset[str]:
        """受影响单元集 derive（不冗余存字段）：full_graph=True=changed_units
        （自包含——此时 changed 装新设计全部单元 id）；False=changed∪
        downstream∪loop 组成员并集。"""
        if self.full_graph:
            return self.changed_units
        members = self.changed_units | self.downstream_units
        for group in self.loop_groups:
            members |= group
        return members

    @property
    def ordered_units(self) -> tuple[str, ...]:
        """确定性有序投影（sorted 字典序——B6 design_digest 确定性先例）。"""
        return tuple(sorted(self.affected_units))


def _canonical_json(value: Any) -> str:
    """确定性 JSON 规范化（sort_keys——键序噪声消除，io.py 同款纪律自写）。"""
    return json.dumps(value, **_JSON_KWARGS)


def _edge_normal_form(edge: Mapping[str, Any]) -> tuple[str, str, str, str] | str:
    """边规范化形态（D2）：恰 {src,dst} 两键且端点含字符串 unit_id/port_id
    → 四元组；否则整边规范化 JSON 兜底（超 src/dst 的键或形态不合）。"""
    if set(edge) == {"src", "dst"}:
        src, dst = edge["src"], edge["dst"]
        if isinstance(src, Mapping) and isinstance(dst, Mapping):
            s_unit, s_port = src.get("unit_id"), src.get("port_id")
            d_unit, d_port = dst.get("unit_id"), dst.get("port_id")
            if (
                isinstance(s_unit, str)
                and isinstance(s_port, str)
                and isinstance(d_unit, str)
                and isinstance(d_port, str)
            ):
                return (s_unit, s_port, d_unit, d_port)
    return _canonical_json(edge)


def _edges_normalized(
    edges: Sequence[Mapping[str, Any]],
) -> frozenset[tuple[str, str, str, str] | str]:
    """规范化边集（frozenset——边序噪声天然消除；D2 比较基准）。"""
    return frozenset(_edge_normal_form(edge) for edge in edges)


def _topology_changed(old_design: DesignState, new_design: DesignState) -> bool:
    """拓扑变更=节点集差（增删单元）或规范化边集差（D2/D3 先行短路面）。"""
    if set(old_design.nodes) != set(new_design.nodes):
        return True
    return _edges_normalized(old_design.edges) != _edges_normalized(new_design.edges)


def _non_graph_keys_changed(old_design: DesignState, new_design: DesignState) -> bool:
    """其余五键+site 任一面变更（总控加裁保守回落面——不判语义不猜）。"""
    return (
        old_design.constraint_choices != new_design.constraint_choices
        or old_design.checked_units != new_design.checked_units
        or old_design.assumption_overrides != new_design.assumption_overrides
        or old_design.influent != new_design.influent
        or old_design.standard_binding != new_design.standard_binding
        or old_design.site != new_design.site
    )


def _params_changed(
    old_nodes: Mapping[str, dict[str, Any]], new_nodes: Mapping[str, dict[str, Any]]
) -> frozenset[str]:
    """参数 diff：共有键逐单元载荷规范化比较——任一字段不同整单元入列（D2）。"""
    return frozenset(
        unit_id
        for unit_id in new_nodes
        if _canonical_json(old_nodes[unit_id]) != _canonical_json(new_nodes[unit_id])
    )


def _to_port_ref(raw: Any) -> PortRef:
    """边端点 dict → PortRef（形态不合=ValueError——调用面保守全图回落）。"""
    if isinstance(raw, Mapping):
        unit_id, port_id = raw.get("unit_id"), raw.get("port_id")
        if isinstance(unit_id, str) and isinstance(port_id, str):
            return PortRef(unit_id=unit_id, port_id=port_id)
    raise ValueError(f"边端点形态非法（须含字符串 unit_id/port_id）：{raw!r}")


def _to_edges(raw_edges: Sequence[Mapping[str, Any]]) -> tuple[Edge, ...]:
    """design.edges dict 面 → Edge 元组（executor._edges_from_design 同款形态
    私有转换——recycle 缺省 False；结构不合=ValueError 供调用面全图回落）。"""
    edges: list[Edge] = []
    for raw in raw_edges:
        recycle = raw.get("recycle", False)
        if not isinstance(recycle, bool):
            raise ValueError(f"边 recycle 标记须为布尔：{recycle!r}")
        edges.append(
            Edge(src=_to_port_ref(raw.get("src")), dst=_to_port_ref(raw.get("dst")),
                 recycle=recycle)
        )
    return tuple(edges)


def _adjacency_of(edges: Sequence[Edge]) -> dict[str, tuple[str, ...]]:
    """全边邻接表（含 recycle——脏传播沿一切流股路径；目标去重升序）。
    topo._adjacency 私有件跨包 `_` 前缀禁引——自写合规（D3）。"""
    targets: dict[str, set[str]] = {}
    for edge in edges:
        targets.setdefault(edge.src.unit_id, set()).add(edge.dst.unit_id)
    return {src: tuple(sorted(dsts)) for src, dsts in targets.items()}


def _downstream_closure(
    seed: frozenset[str], adjacency: Mapping[str, tuple[str, ...]]
) -> set[str]:
    """下游闭包自写 BFS（含种子自身——调用面按需差集扣减）。"""
    reached = set(seed)
    frontier = list(seed)
    while frontier:
        current = frontier.pop()
        for nxt in adjacency.get(current, ()):
            if nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)
    return reached


def _expand_loop_fixpoint(
    changed: frozenset[str],
    adjacency: Mapping[str, tuple[str, ...]],
    loop_groups: Sequence[tuple[str, ...]],
) -> tuple[set[str], set[frozenset[str]]]:
    """回路不动点扩张（R2）：变更/下游集命中任一组 → 整组并入 → 新成员
    再扩下游 → 至集合不再增长。返回 (受影响总集[含变更], 命中回路组集)。"""
    affected = _downstream_closure(changed, adjacency)
    hit: set[frozenset[str]] = set()
    while True:
        newly = {
            frozenset(group)
            for group in loop_groups
            if frozenset(group) & affected and frozenset(group) not in hit
        }
        if not newly:
            return affected, hit
        hit |= newly
        affected |= _downstream_closure(frozenset().union(*newly), adjacency)


def _full_graph_scope(design: DesignState) -> Scope:
    """全图回落 Scope（D1 自包含：changed_units 装新设计全部 unit_id，
    downstream/loop 置空——全图语义已含，调用方无需再持 new_design）。"""
    return Scope(
        changed_units=frozenset(design.nodes),
        downstream_units=frozenset(),
        loop_groups=frozenset(),
        full_graph=True,
    )


def recompute_scope(old_design: DesignState, new_design: DesignState) -> Scope:
    """重算范围判定正门（D3 定稿签名；纯函数——零副作用，遍历以新拓扑为准）。

    判定序（规格头【范围判定规则】）：拓扑比对先行短路 → 其余五键+site
    保守回落 → 参数 diff → 下游闭包 BFS + 回路不动点扩张（R2）。
    """
    if _topology_changed(old_design, new_design):
        return _full_graph_scope(new_design)
    if _non_graph_keys_changed(old_design, new_design):
        return _full_graph_scope(new_design)
    changed = _params_changed(old_design.nodes, new_design.nodes)
    if not changed:
        return Scope(
            changed_units=frozenset(),
            downstream_units=frozenset(),
            loop_groups=frozenset(),
            full_graph=False,
        )
    try:
        edges = _to_edges(new_design.edges)
        adjacency = _adjacency_of(edges)
        _, loop_groups = split_graph(list(new_design.nodes), edges)
    except (ValueError, InvalidConnection):
        return _full_graph_scope(new_design)
    affected, hit = _expand_loop_fixpoint(changed, adjacency, loop_groups)
    return Scope(
        changed_units=changed,
        downstream_units=frozenset(affected - changed),
        loop_groups=frozenset(hit),
        full_graph=False,
    )
