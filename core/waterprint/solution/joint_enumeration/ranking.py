"""联合枚举排序件：全厂目标函数 + 降权标记制排序（W10/W12/N6 终裁口径）。

输入:  末段复验组合的 design 工况三真键指标（别名键）+ 基线指标 + 权重（registry）
输出:  plant_objective 逐组合标量分（越小越好）+ 降权感知确定性全序
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 定稿件 §一 W10/W12/N6；镜像测试 tests/solution/test_joint_units.py）
#
# 【公开接口】
#   plant_objective(metrics, baseline, weights) -> tuple[float, ...]
#       逐组合标量分：Σ活跃键 w_m×(value_m/baseline_m)（三真键别名
#       opex/energy/carbon——beam 侧经 W12 真键映射 power_total_kwh_d/
#       carbon_intensity_kgco2e_m3/cost_opex_yuan_a 投影后传入；同向
#       越小越好——排序取 design 工况）。
#       N6 除零/缺失面：基准值 0/缺失 → 该键权重重分配至其余键
#       （活跃键权重和归一）；组合缺指标值（sparse）→ 当场重分配；
#       全键缺席 → score=0 恒等（无区分度诚实降级，排序落次序键）。
#   degraded_aware_order(scored) -> tuple[int, ...]
#       降权标记制全序（W10 终裁）：主键=分数升序；同分纯可行
#       （degraded=False）排 sensitivity_degraded=true 之前（不剔除
#       ——sensitivity 失守常因保守工况）；次序键=调用方传入的可比
#       元组（beam=_prefix_key 参数字典序——确定性全序，UI 不抖动）。
#       scored=(score, degraded, key)。
#
# 【行为规格】
#   R1 纯函数：同输入同输出（可复算；排序进 UI 与日志）。
#   R2 无魔法数：权重/基准全由调用方注入（registry 真源）。
#   R3 次序键契约：key 须两两可比（同形元组——str/float 同位不混型；
#      违例 TypeError 直上=程序缺陷口径，GR-08）。
#
# 【测试要求】基线归一方向、零基准重分配、sparse 值重分配、全缺=0、
#   同分降权排后、字典序稳定。
#
# 【参照】.workflow/b4-3/design-final.md §一 W10/W12/N6；ADR-006 决策 5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence

# 组合次序键：((unit_id, ((参数名, 值), ...)), ...)——同形元组两两可比
type OrderKey = tuple[tuple[str, tuple[tuple[str, float], ...]], ...]
# 组合排序载荷：(分数, 降权标记, 确定性次序键)
type ScoredEntry = tuple[float, bool, OrderKey]


def _score_of(
    values: Mapping[str, float], baseline: Mapping[str, float], weights: Mapping[str, float]
) -> float:
    """单组合分：活跃键（值与基准双在场且基准>0）加权比值，权重和归一（N6）。"""
    active = [
        (weights[key], values[key] / baseline[key])
        for key in weights
        if key in values and baseline.get(key, 0.0) > 0.0
    ]
    total_weight = sum(weight for weight, _ in active)
    if total_weight <= 0.0:
        return 0.0  # 全键缺席（N6 终态）：无区分度诚实降级
    return sum(weight * ratio for weight, ratio in active) / total_weight


def plant_objective(
    metrics: Sequence[Mapping[str, float]],
    baseline: Mapping[str, float],
    weights: Mapping[str, float],
) -> tuple[float, ...]:
    """全厂目标函数（纯投影）：逐组合 design 工况指标 → 标量分序列。"""
    return tuple(_score_of(values, baseline, weights) for values in metrics)


def degraded_aware_order(scored: Sequence[ScoredEntry]) -> tuple[int, ...]:
    """降权标记制确定性全序（W10）：分数升序 → 纯可行前 → 次序键字典序。"""
    indexed = sorted(
        enumerate(scored), key=lambda item: (item[1][0], item[1][1], item[1][2])
    )
    return tuple(position for position, _ in indexed)


def prefix_order_key(
    params: Sequence[tuple[str, Mapping[str, float]]]
) -> OrderKey:
    """组合参数确定性次序键（unit_id+参数字典序——同形元组两两可比，R3）。

    beam 传播序与 outcome 排序共用（前缀/整组合同构——(unit_id, 行参数)
    序列 flattening 为可比元组）。"""
    return tuple(
        (unit_id, tuple(sorted(row.items()))) for unit_id, row in params
    )


__all__ = ["ScoredEntry", "degraded_aware_order", "plant_objective", "prefix_order_key"]
