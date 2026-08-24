"""水量水质沿边传播 + 汇流加权混合（纯函数；工况语义的正确性住所）。

输入:  上游单元结果 + 边（含 recycle 标记）+ 当前工况
输出:  下游单元的输入（flows/qualities 两 Mapping 快照，按 dst PortRef 键化）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T6 实现；镜像测试 tests/graph/test_propagate.py +
# 性质测试 properties_propagate.py）
#
# 【公开接口】
#   mix(qualities: Sequence[WaterQuality], weights: Sequence[float])
#       -> WaterQuality
#       水质汇流加权混合（双参）：逐指标负荷加权 ΣCi·Qi / ΣQi，
#       非浓度简单平均（与 sludge.mix 单参签名区分）
#   propagate(upstream, upstream_qualities, edges, condition)
#       -> tuple[Mapping[PortRef, WaterFlow | SludgeFlow],
#                Mapping[PortRef, WaterQuality]]
#       组装下游输入快照（签名 T6 D4 冻结）
#   InvalidPropagationError(Exception)
#       传播/汇流非法领域异常（GR-11 Invalid* 族：长度不匹配/非法权重/
#       通道类型串混/汇流非有限值）
#
# 【行为规格】
#   R1 汇流加权使用**当前工况流量**：design 工况用 q_design、avg 工况用
#      q_avg_daily——修正旧系统固定按 Q_design 加权的语义错误（§14.2，
#      本条语义写进 propagate docstring 并被测试锁定）。
#   R2 Kz 取 max：多股进水汇流时，下游 WaterFlow 的 Kz 取各股最大值
#      （保守语义，§14.2 明示）。
#   R3 质量守恒（性质测试常驻）：混合后各指标负荷 ΣCi·Qi 守恒
#      （数值容差内）；混合出水各指标浓度必介于各股浓度 min/max 之间。
#   R4 WATER 与 SLUDGE 独立通道：水质混合只作用于 WATER 股；SLUDGE 股
#      走 sludge.mix（DS 求和守恒）。同一 dst 端口类型串混 = 领域异常。
#   R5 recycle 边在迭代期传播"上一次迭代的估计值"（由 loop.py 驱动），
#      本文件不感知迭代状态——纯函数边界：propagate 只沿非 recycle 边。
#
# 【T6 冻结注记】（总控简报 D3/D4/D5，2026-08-24）
#   - mix 守卫（InvalidPropagationError）：len(qualities)==len(weights)；
#     weights 逐项非 bool、有限（GR-02）、>= 0（零权股合法——GR-04 图内
#     传播 Q=0 合法）。GR-18 分界：mix 按传入序求和（浮点加法序敏感），
#     排序义务在调用方——propagate 按 PortRef (unit_id, port_id) 排序后
#     调用（双方 docstring 注记）。
#   - mix 指标三态（逐指标）：全股缺项 → 结果缺项（键不存在）；部分股
#     缺项 → 在场股加权（缺项警告的**记录**归 executor/单元层（有 sink
#     通道时），mix 无 sink 不产警告——分工注记）；在场权合计==0 → 该
#     指标缺项（ΣCi·Qi/ΣQi 无定义，GR-14 显式；全零权即 WaterQuality({})）。
#     空序列 → WaterQuality({})（单位元）。R3 夹逼的数值护栏：结果显式
#     收束回在场股 [min, max]——加权均值数学上恒在该区间（R3 不变量），
#     浮点直除可能越界 1 ULP（锁定性质测试实证），夹逼非语义变更。
#   - propagate 语义（D4 冻结）：(a) 只沿非 recycle 边传播（recycle 边
#     忽略——R5 纯函数边界，迭代期输入由 loop.py 驱动）；(b) 按 dst
#     PortRef 分组，处理序与求和序一律按 (unit_id, port_id) 排序（GR-18）；
#     (c) WATER 股汇流 WaterFlow **直接构造不经 make_flow**（图内传播
#     Q=0 合法 GR-04，make_flow 的 q>0 是厂界口径）：q_avg=Σq_avg、
#     kz=max（R2 保守语义 §14.2），构造前有限性检查 GR-02；水质权重=
#     工况流量（DESIGN→f.q_design、AVG→f.q_avg_daily，R1）经 mix 混合；
#     (d) SLUDGE 股走 sludge.mix（R4，DS 守恒）；(e) 同一 dst 端口收到
#     WATER 与 SLUDGE 混流 → InvalidPropagationError（R4 类型串混）；
#     (f) 单股 dst = 透传再键化（不经混合公式，但走同一分组路径）；
#     (g) 空 edges → 两个空 Mapping（GR-14）；(h) 输出两 Mapping 构造
#     即快照（MappingProxyType）。
#   - 规格沉默处实现期裁定（记档，不扩公开面）：src 端口不在 upstream
#     （或 WATER 股不在 upstream_qualities）→ 原生 KeyError（GR-08 禁
#     静默默认）；非 WaterFlow/SludgeFlow 的股值 → InvalidPropagationError
#     （R4 通道类型守卫族）；同一 (src,dst) 平行重复边按多股计（对账归
#     T7 装配）。
#   - 数值纪律：本文件不在魔法数字白名单——数值字面量仅 0/1（kz=max 与
#     Σ 求和无系数；权重比较无阈值）。
#
# 【测试要求】两档工况加权差异断言（design≠avg 加权结果）、Kz=max、
#   守恒与 min/max 夹逼、通道类型隔离；性质：随机两股混合守恒（hypothesis）。
#
# 【参照】重写计划 §14.2/§14.1；ADR-005/ADR-007；简报 T6 D3/D4/D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from types import MappingProxyType

from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import Edge, PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.sludge import mix as mix_sludge


class InvalidPropagationError(Exception):
    """传播/汇流非法（长度不匹配、非法权重、通道类型串混、非有限值）——领域异常（GR-11 族）。"""


def _require_weight(index: int, weight: float) -> None:
    """股权守卫：非 bool、有限（GR-02）、>= 0（零权股合法——GR-04）。"""
    if isinstance(weight, bool):
        raise InvalidPropagationError(
            f"weights[{index}] 非法：{weight!r}（bool 拒——权为流量数值非开关）"
        )
    if not isfinite(weight):
        raise InvalidPropagationError(
            f"weights[{index}] 非有限值拒绝（GR-02）：得到 {weight!r}"
        )
    if weight < 0:
        raise InvalidPropagationError(
            f"weights[{index}] 必须 >= 0（流量权非负；零权股合法 GR-04）："
            f"得到 {weight!r}"
        )


def mix(
    qualities: Sequence[WaterQuality], weights: Sequence[float]
) -> WaterQuality:
    """水质汇流加权混合：逐指标负荷加权 ΣCi·Qi / ΣQi（非浓度简单平均）。

    GR-18 分界：按传入序求和（浮点加法序敏感），排序义务在调用方——
    propagate 按 PortRef 排序后调用本函数。守卫（InvalidPropagationError）：
    len(qualities)==len(weights)；weights 逐项非 bool、有限、>= 0（零权股
    合法——GR-04 图内传播 Q=0 合法）。缺项三态（逐指标）：全股缺项 →
    结果缺项（键不存在）；部分股缺项 → 在场股加权（缺项警告的**记录**
    归 executor/单元层（有 sink 通道时），mix 无 sink 不产警告）；在场权
    合计==0 → 该指标缺项（GR-14 显式，全零权即 WaterQuality({})）。
    空序列 → WaterQuality({})（单位元）。R3 夹逼：结果显式收束回在场股
    [min, max]——加权均值数学上恒在该区间，浮点直除可能越界 1 ULP，
    夹逼为数值护栏（守恒断言容差 rel 1e-9 内无感）。
    """
    if len(qualities) != len(weights):
        raise InvalidPropagationError(
            f"qualities 与 weights 长度不匹配：{len(qualities)} != "
            f"{len(weights)}（逐股浓度与流量权须一一对应）"
        )
    for index, weight in enumerate(weights):
        _require_weight(index, weight)
    indicators = sorted({key for q in qualities for key in q.concentrations})
    merged: dict[str, float] = {}
    for indicator in indicators:
        stocks = _present_stocks(indicator, qualities, weights)
        load = 0.0
        weight_total = 0.0
        for value, weight in stocks:
            load += value * weight
            weight_total += weight
        if weight_total == 0:
            continue
        low = min(value for value, _ in stocks)
        high = max(value for value, _ in stocks)
        merged[indicator] = min(max(load / weight_total, low), high)
    return WaterQuality(merged)


def _present_stocks(
    indicator: str,
    qualities: Sequence[WaterQuality],
    weights: Sequence[float],
) -> list[tuple[float, float]]:
    """在场股 (浓度, 权) 对——按传入序（GR-18：求和序=传入序）。"""
    return [
        (quality.concentrations[indicator], weight)
        for quality, weight in zip(qualities, weights, strict=True)
        if indicator in quality.concentrations
    ]


def _port_ref_key(ref: PortRef) -> tuple[str, str]:
    """PortRef 排序键 (unit_id, port_id)：处理序与求和序一律按此（GR-18）。"""
    return (ref.unit_id, ref.port_id)


def _condition_flow(flow: WaterFlow, condition: OperatingCondition) -> float:
    """工况流量权（R1 修正语义，ADR-007）：DESIGN→q_design、AVG→q_avg_daily。"""
    if condition.flow_case is FlowCase.DESIGN:
        return flow.q_design
    return flow.q_avg_daily


def _merge_water(
    stocks: Sequence[tuple[PortRef, WaterFlow]],
    upstream_qualities: Mapping[PortRef, WaterQuality],
    condition: OperatingCondition,
) -> tuple[WaterFlow, WaterQuality]:
    """WATER 多股汇流：q_avg=Σ、kz=max（R2 保守）直接构造（GR-04）；水质 mix 工况加权（R1）。

    汇流 WaterFlow 不经 make_flow——make_flow 的 q>0 是厂界口径，图内
    传播 Q=0 合法（GR-04）；求和序=传入序（propagate 已按 PortRef 排序），
    构造前有限性检查（GR-02）。
    """
    q_total = 0.0
    for _, flow in stocks:
        q_total += flow.q_avg_daily
    kz_max = max(flow.kz for _, flow in stocks)
    if not isfinite(q_total) or not isfinite(kz_max):
        raise InvalidPropagationError(
            f"汇流结果非有限值拒绝（GR-02）：q_avg={q_total!r}, kz={kz_max!r}"
        )
    weights = [_condition_flow(flow, condition) for _, flow in stocks]
    qualities = [upstream_qualities[src] for src, _ in stocks]
    return WaterFlow(q_avg_daily=q_total, kz=kz_max), mix(qualities, weights)


def _partition_stocks(
    dst: PortRef,
    stocks: Sequence[tuple[PortRef, WaterFlow | SludgeFlow]],
) -> tuple[list[tuple[PortRef, WaterFlow]], list[tuple[PortRef, SludgeFlow]]]:
    """按值类型分通道：同 dst 混流或非契约类型 → InvalidPropagationError（R4）。"""
    water: list[tuple[PortRef, WaterFlow]] = []
    sludge: list[tuple[PortRef, SludgeFlow]] = []
    for src, flow in stocks:
        if isinstance(flow, WaterFlow):
            water.append((src, flow))
        elif isinstance(flow, SludgeFlow):
            sludge.append((src, flow))
        else:
            raise InvalidPropagationError(
                f"股类型非法：{src.unit_id}.{src.port_id} 的 "
                f"{type(flow).__name__}（WATER/SLUDGE 通道外的值，R4）"
            )
    if water and sludge:
        raise InvalidPropagationError(
            f"通道类型串混：{dst.unit_id}.{dst.port_id} 同时收到 WATER 股 "
            f"{[f'{s.unit_id}.{s.port_id}' for s, _ in water]} 与 SLUDGE 股 "
            f"{[f'{s.unit_id}.{s.port_id}' for s, _ in sludge]}（R4 类型隔离）"
        )
    return water, sludge


def _dispatch_group(
    dst: PortRef,
    stocks: Sequence[tuple[PortRef, WaterFlow | SludgeFlow]],
    upstream_qualities: Mapping[PortRef, WaterQuality],
    condition: OperatingCondition,
) -> tuple[WaterFlow | SludgeFlow, WaterQuality | None]:
    """单 dst 端口的股汇流分派（通道隔离 R4；单股透传再键化不经混合公式）。"""
    water, sludge = _partition_stocks(dst, stocks)
    if water:
        if len(water) == 1:
            src, flow = water[0]
            return flow, upstream_qualities[src]
        return _merge_water(water, upstream_qualities, condition)
    if len(sludge) == 1:
        return sludge[0][1], None
    return mix_sludge([flow for _, flow in sludge]), None


def propagate(
    upstream: Mapping[PortRef, WaterFlow | SludgeFlow],
    upstream_qualities: Mapping[PortRef, WaterQuality],
    edges: Sequence[Edge],
    condition: OperatingCondition,
) -> tuple[
    Mapping[PortRef, WaterFlow | SludgeFlow], Mapping[PortRef, WaterQuality]
]:
    """沿非 recycle 边把上游股传播到下游端口（纯函数，R5：迭代期 recycle 估计值由 loop.py 驱动）。

    语义（D4 冻结）：(a) 只沿非 recycle 边传播；(b) 按 dst PortRef 分组，
    处理序与求和序一律按 (unit_id, port_id) 排序（GR-18——乱序 edges 输入
    同输出）；(c) WATER 股汇流 WaterFlow 直接构造不经 make_flow（图内
    Q=0 合法 GR-04）：q_avg=Σq_avg、kz=max（R2 保守 §14.2），构造前有限性
    检查 GR-02，水质权重=**当前工况流量**（DESIGN→q_design、AVG→
    q_avg_daily——R1 修正语义）经 mix 混合；(d) SLUDGE 股走 sludge.mix
    （R4，DS 守恒）；(e) 同一 dst 收到 WATER 与 SLUDGE 混流 →
    InvalidPropagationError；(f) 单股 dst=透传再键化（不经混合公式，同一
    分组路径）；(g) 空 edges → 两个空 Mapping（GR-14）；(h) 输出构造即
    快照（MappingProxyType）。src 端口不在 upstream（或 WATER 股不在
    upstream_qualities）→ 原生 KeyError（GR-08 禁静默默认）；平行重复边
    按多股计（对账归 T7 装配）。
    """
    groups: dict[PortRef, list[tuple[PortRef, WaterFlow | SludgeFlow]]] = {}
    for edge in edges:
        if not edge.recycle:
            groups.setdefault(edge.dst, []).append((edge.src, upstream[edge.src]))
    flows_out: dict[PortRef, WaterFlow | SludgeFlow] = {}
    qualities_out: dict[PortRef, WaterQuality] = {}
    for dst in sorted(groups, key=_port_ref_key):
        stocks = sorted(groups[dst], key=lambda stock: _port_ref_key(stock[0]))
        flow, quality = _dispatch_group(dst, stocks, upstream_qualities, condition)
        flows_out[dst] = flow
        if quality is not None:
            qualities_out[dst] = quality
    return MappingProxyType(flows_out), MappingProxyType(qualities_out)
