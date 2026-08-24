"""拓扑排序 + 强连通分量（SCC）划分（纯函数，回路一等公民的第一步）。

输入:  节点列表 + 边列表（含 recycle 标记）
输出:  执行分层（DAG 部分按层排序）+ 回路组（SCC 列表，供 loop.py 迭代）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T6 实现；镜像测试 tests/graph/test_topo.py + properties_topo.py）
#
# 【公开接口】
#   topological_layers(nodes: Sequence[str], edges: Sequence[Edge])
#       -> tuple[tuple[str, ...], ...]
#       DAG 骨架的分层执行序（同层可并行；同层按 unit_id 字典序）
#   strongly_connected_components(nodes: Sequence[str], edges: Sequence[Edge])
#       -> tuple[tuple[str, ...], ...]
#       全边 Tarjan SCC（返回全部分量含单点；序确定性）
#   split_graph(nodes: Sequence[str], edges: Sequence[Edge])
#       -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]
#       总入口：一次划分出"无环分层 + 回路组"（(layers, loop_groups)）
#
# 【行为规格】
#   R1 环不是错误（§3 保证 3，病灶"DAG 环路直接异常、污泥回流绕行"）：
#      recycle 边构成的环被划入 SCC 组交给 loop.py；只有"非 recycle 边
#      构成的环"（用户误连）才抛 InvalidConnection（附环上的节点路径，
#      形态"a → b → a"——按环序）。
#   R2 纯函数：无副作用、无内部可变状态泄漏；同输入同输出（可复算前提）。
#   R3 层序确定性：同层节点按 unit_id 字典序——结果与保存/加载顺序无关；
#      Tarjan 按排序后节点起 DFS、邻接按 (unit_id, port_id) 排序后去重
#      升序——乱序输入同输出。
#   R4 孤立节点/悬空边：孤立节点进第 0 层；悬空边（端点 unit_id 不在
#      nodes）抛 InvalidConnection（消息含边两端 ref）。
#
# 【T6 冻结注记】（总控简报 D2/D5，2026-08-24）
#   - 输入守卫（InvalidConnection，消息含节点/边 ref——GR-09）：nodes
#     元素非空 str 且无重复；悬空边（src/dst unit_id 不在 nodes）拒。
#   - 环两分法：topological_layers 先对非 recycle 边子图做 SCC——多节点
#     分量或自环 = 误连环 → InvalidConnection（消息含环节点路径，按环序，
#     锁定测试 match 依赖此序）；再忽略 recycle 边按最长路径分层（Kahn
#     波序）；recycle 环节点照常进分层（DAG 骨架分层——SCC 节点与层的
#     调度关系归 executor T7 裁决，本函数不排除）；空图 → ()（GR-14）。
#   - strongly_connected_components：先跑同款非 recycle 环拒，再对全边
#     Tarjan；返回全部 SCC（含单点——前向 DAG 的 SCC 全单点）。
#   - split_graph：回路组 = 全边 SCC 中"多节点分量 或 含自环边的单点
#     分量"（单点无自环不进回路组——前向 DAG 场景 loop_groups=()）；
#     非 recycle 自环已在环两分法前哨被拒，故回路组的自环边恒为 recycle。
#   - 拒绝异常一律复用 ports.InvalidConnection（D5：graph→contracts 为
#     合法依赖边，不新建异常）。
#   - 数值纪律：本文件不在魔法数字白名单——数值字面量仅 0/1。
#
# 【测试要求】已知图分层正确、recycle 环进 SCC 而非异常、误连环异常
#   （消息含路径）、确定性（节点乱序输入同层序）；性质：任意 DAG 分层后
#   每条边都从低层指向高层、SCC 内任意两点互达（hypothesis）。
#
# 【参照】重写计划 §3-3/§14.2；ADR-003；简报 T6 D1/D2/D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence

from waterprint.contracts.ports import Edge, InvalidConnection


def _validated_nodes(nodes: Sequence[str]) -> tuple[str, ...]:
    """节点守卫（R3 前提）：元素非空 str 且无重复；返回排序视图。"""
    seen: set[str] = set()
    for node in nodes:
        if not isinstance(node, str) or not node:
            raise InvalidConnection(
                f"节点非法：{node!r}（须为非空 str——节点=单元 unit_id）"
            )
        if node in seen:
            raise InvalidConnection(
                f"节点重复：{node!r}（nodes 须无重复——R3 确定性前提）"
            )
        seen.add(node)
    return tuple(sorted(seen))


def _validated_edges(
    edges: Sequence[Edge], node_set: frozenset[str]
) -> tuple[Edge, ...]:
    """悬空边守卫（R4，消息含两端 ref）+ 边序列确定性排序（R2 注记的落点）。"""
    checked: list[Edge] = []
    for edge in edges:
        for ref in (edge.src, edge.dst):
            if ref.unit_id not in node_set:
                raise InvalidConnection(
                    f"悬空边：{edge.src.unit_id}.{edge.src.port_id} → "
                    f"{edge.dst.unit_id}.{edge.dst.port_id}"
                    f"（{ref.unit_id!r} 不在节点集——R4）"
                )
        checked.append(edge)
    return tuple(
        sorted(
            checked,
            key=lambda e: (
                e.src.unit_id,
                e.src.port_id,
                e.dst.unit_id,
                e.dst.port_id,
            ),
        )
    )


def _adjacency(
    edges: Sequence[Edge], *, include_recycle: bool
) -> dict[str, tuple[str, ...]]:
    """邻接表：每源节点的目标 unit_id 去重升序（(unit_id, port_id) 序的投影）。"""
    targets: dict[str, set[str]] = {}
    for edge in edges:
        if edge.recycle and not include_recycle:
            continue
        targets.setdefault(edge.src.unit_id, set()).add(edge.dst.unit_id)
    return {src: tuple(sorted(dsts)) for src, dsts in targets.items()}


def _self_loops(edges: Sequence[Edge], *, include_recycle: bool) -> frozenset[str]:
    """自环节点集（src.unit_id == dst.unit_id）；include_recycle 口径与邻接一致。"""
    return frozenset(
        edge.src.unit_id
        for edge in edges
        if edge.src.unit_id == edge.dst.unit_id
        and (include_recycle or not edge.recycle)
    )


def _tarjan_sccs(
    nodes: Sequence[str], adjacency: Mapping[str, Sequence[str]]
) -> tuple[tuple[str, ...], ...]:
    """Tarjan SCC：根按节点升序起 DFS、邻接升序遍历——同输入同输出（R3）。"""
    index_of: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        """单节点 DFS（递归深度 ≤ 节点数——厂区图规模内安全）。"""
        index_of[node] = len(index_of)
        low[node] = index_of[node]
        stack.append(node)
        on_stack.add(node)
        for succ in adjacency.get(node, ()):
            if succ not in index_of:
                visit(succ)
                low[node] = min(low[node], low[succ])
            elif succ in on_stack:
                low[node] = min(low[node], index_of[succ])
        if low[node] == index_of[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.append(member)
                if member == node:
                    break
            components.append(tuple(sorted(component)))

    for node in nodes:
        if node not in index_of:
            visit(node)
    return tuple(components)


def _cycle_path(
    component: Sequence[str], adjacency: Mapping[str, Sequence[str]]
) -> str:
    """环上节点路径（按环序，形态"a → b → a"）：自分分量最小节点沿最小后继走。"""
    members = frozenset(component)
    start = min(members)
    path = [start]
    position = {start: 0}
    current = start
    while True:
        current = min(dst for dst in adjacency[current] if dst in members)
        if current in position:
            return " → ".join([*path[position[current] :], current])
        position[current] = len(path)
        path.append(current)


def _reject_user_cycles(
    nodes: Sequence[str],
    forward: Mapping[str, Sequence[str]],
    forward_self_loops: frozenset[str],
) -> None:
    """环两分法前哨：非 recycle 子图多节点分量或自环 = 用户误连环（R1）。"""
    for component in _tarjan_sccs(nodes, forward):
        if len(component) > 1:
            raise InvalidConnection(
                "误连环（非 recycle 边构成环，用户误连——R1）："
                f"{_cycle_path(component, forward)}"
            )
    for node in nodes:
        if node in forward_self_loops:
            raise InvalidConnection(
                f"误连环（非 recycle 自环边，用户误连——R1）：{node} → {node}"
            )


def _kahn_layers(
    nodes: Sequence[str], forward: Mapping[str, Sequence[str]]
) -> tuple[tuple[str, ...], ...]:
    """最长路径分层（Kahn 波序：level(v)=1+max(level(u))）；同层字典序（R3）。"""
    indegree: dict[str, int] = dict.fromkeys(nodes, 0)
    for targets in forward.values():
        for dst in targets:
            indegree[dst] += 1
    layers: list[tuple[str, ...]] = []
    frontier = sorted(node for node in nodes if indegree[node] == 0)
    while frontier:
        layers.append(tuple(frontier))
        reached: list[str] = []
        for node in frontier:
            for dst in forward.get(node, ()):
                indegree[dst] -= 1
                if indegree[dst] == 0:
                    reached.append(dst)
        frontier = sorted(reached)
    return tuple(layers)


def _prepared(
    nodes: Sequence[str], edges: Sequence[Edge]
) -> tuple[tuple[str, ...], tuple[Edge, ...], dict[str, tuple[str, ...]]]:
    """三公开函数的共享前置：节点/边守卫 + 排序视图 + 非 recycle 环拒。"""
    validated = _validated_nodes(nodes)
    ordered = _validated_edges(edges, frozenset(validated))
    forward = _adjacency(ordered, include_recycle=False)
    _reject_user_cycles(
        validated, forward, _self_loops(ordered, include_recycle=False)
    )
    return validated, ordered, forward


def topological_layers(
    nodes: Sequence[str], edges: Sequence[Edge]
) -> tuple[tuple[str, ...], ...]:
    """DAG 骨架分层执行序（环两分法：非 recycle 环拒 → 忽略 recycle 边分层）。

    输入守卫（InvalidConnection，消息含节点/边 ref）：nodes 元素非空 str
    且无重复；悬空边（端点 unit_id 不在 nodes）拒。非 recycle 边构成环
    （多节点分量或自环）= 用户误连环 → InvalidConnection（消息含按环序
    的节点路径，形态"a → b → a"）。分层忽略 recycle 边按最长路径（Kahn
    波序），同层按 unit_id 字典序；recycle 环节点照常进分层（SCC 节点
    与层的调度关系归 executor T7 裁决）；孤立节点进第 0 层（R4）；
    空图 → ()（GR-14 合法）。
    """
    validated, _, forward = _prepared(nodes, edges)
    return _kahn_layers(validated, forward)


def strongly_connected_components(
    nodes: Sequence[str], edges: Sequence[Edge]
) -> tuple[tuple[str, ...], ...]:
    """全边 Tarjan SCC（含单点分量）：先跑非 recycle 环拒，再对全边划分。

    输入守卫与误连环拒绝口径同 topological_layers（recycle 环是可解对象
    不拒——R1）；随后对含 recycle 边的全图 Tarjan（按排序后节点起 DFS、
    邻接升序遍历——确定性，R3），返回全部 SCC（含单点——前向 DAG 的
    SCC 全单点），组内节点升序。
    """
    validated, ordered, _ = _prepared(nodes, edges)
    return _tarjan_sccs(validated, _adjacency(ordered, include_recycle=True))


def split_graph(
    nodes: Sequence[str], edges: Sequence[Edge]
) -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]:
    """总入口：一次划分出"无环分层 + 回路组"。

    layers = topological_layers(nodes, edges)（守卫/环拒/分层口径同彼）；
    loop_groups = 全边 SCC 中"多节点分量 或 含自环边的单点分量"（单点
    无自环不进回路组——前向 DAG 场景 loop_groups=()；非 recycle 自环
    已被前哨拒绝，回路组的自环边恒为 recycle）。
    """
    validated, ordered, forward = _prepared(nodes, edges)
    layers = _kahn_layers(validated, forward)
    components = _tarjan_sccs(validated, _adjacency(ordered, include_recycle=True))
    looped = _self_loops(ordered, include_recycle=True)
    loop_groups = tuple(
        component
        for component in components
        if len(component) > 1 or component[0] in looped
    )
    return layers, loop_groups
