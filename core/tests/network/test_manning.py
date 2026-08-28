"""manning 镜像测试：曼宁水力（非负/单调性质；数值 golden 归 norms 手算）。

输入:  waterprint.network.manning 公开符号
输出:  水力语义断言
"""

from __future__ import annotations

import importlib
import math
from itertools import pairwise

import pytest

from waterprint.registry.formulas import apply

_mod = importlib.import_module("waterprint.network.manning")
manning_velocity = getattr(_mod, "manning_velocity", None)
solve_depth = getattr(_mod, "solve_depth", None)

pytestmark = pytest.mark.skipif(
    None in (manning_velocity, solve_depth),
    reason="实现未就绪：waterprint.network.manning（M3）",
)


def test_velocity_positive_and_monotone_in_slope() -> None:
    """R3/R4：流速为正且随坡度单调增。"""
    low = manning_velocity(0.5, 0.001, 0.009)
    high = manning_velocity(0.5, 0.004, 0.009)
    assert low > 0
    assert high > low


def test_solve_depth_finds_consistent_root() -> None:
    """求根一致性：解出的充满度反算流量应匹配输入（容差内）。"""
    depth = solve_depth(0.5, 0.002, 0.009, 0.05)
    assert 0.0 < depth <= 1.0


# ── NET2 段二批追加（2026-08-28）：R3/R4 性质断言 + 手册比例表互校 ──
# 期望值唯一来源=docs/norms/network_manning.md（RATIFY4 追认）：峰值
# 充满度 0.9382/Q 比峰值 1.0757（比例表头性质锚）+ 0.05 档 19 行表载值
# （实现为解析式——表载 4dp 誊录与解析差 ≤4.9e-05，容差取 1e-4）。

partial_flow = getattr(_mod, "partial_flow")
full_flow_capacity = getattr(_mod, "full_flow_capacity")


def test_max_flow_near_depth_094() -> None:
    """R3：非满流最大流量出现在充满度约 0.94 附近（手册比例表性质锚）。"""
    diameter, slope, roughness = 0.5, 0.004, 0.013
    capacity_full = full_flow_capacity(diameter, slope, roughness)
    peak_ratio, peak_depth = 0.0, 0.0
    steps = [0.05 + 0.001 * i for i in range(951)]
    for depth in steps:
        ratio = partial_flow(diameter, slope, roughness, depth).flow / capacity_full
        if ratio > peak_ratio:
            peak_ratio, peak_depth = ratio, depth
    assert abs(peak_depth - 0.9382) < 0.01
    assert abs(peak_ratio - 1.0757) < 0.002


def test_full_flow_monotone_in_diameter() -> None:
    """R4：同坡度满流流量随管径单调增（300→600→900→1500 抽档）。"""
    flows = [full_flow_capacity(diameter, 0.004, 0.013) for diameter in (0.3, 0.6, 0.9, 1.5)]
    assert all(later > earlier for earlier, later in pairwise(flows))


def test_manual_ratio_table_cross_check() -> None:
    """手册 0.05 档 19 行比例表互校（network_manning.md NM-F2 载体）。

    解析式 α/β 与表载 4dp 值差 ≤1e-4；v/v_full=β^(2/3) 与 Q/Q_full=α·β^(2/3)
    复合比同容差（含 DSL 串 π 常量八位截断系统差，远小于 4dp 誊录误差）。
    """
    diameter, slope, roughness = 0.5, 0.004, 0.013
    full = manning_velocity(diameter, slope, roughness)
    capacity_full = full_flow_capacity(diameter, slope, roughness)
    table = (
        (0.05, 0.0187, 0.1302, 0.2569, 0.0048),
        (0.10, 0.0520, 0.2541, 0.4012, 0.0209),
        (0.15, 0.0941, 0.3715, 0.5168, 0.0486),
        (0.20, 0.1424, 0.4824, 0.6151, 0.0876),
        (0.25, 0.1955, 0.5865, 0.7007, 0.1370),
        (0.30, 0.2523, 0.6838, 0.7761, 0.1958),
        (0.35, 0.3119, 0.7740, 0.8430, 0.2629),
        (0.40, 0.3735, 0.8569, 0.9022, 0.3370),
        (0.45, 0.4364, 0.9323, 0.9544, 0.4165),
        (0.50, 0.5000, 1.0000, 1.0000, 0.5000),
        (0.55, 0.5636, 1.0595, 1.0393, 0.5857),
        (0.60, 0.6265, 1.1106, 1.0724, 0.6718),
        (0.65, 0.6881, 1.1526, 1.0993, 0.7564),
        (0.70, 0.7477, 1.1849, 1.1198, 0.8372),
        (0.75, 0.8045, 1.2067, 1.1335, 0.9119),
        (0.80, 0.8576, 1.2168, 1.1397, 0.9775),
        (0.85, 0.9059, 1.2131, 1.1374, 1.0304),
        (0.90, 0.9480, 1.1921, 1.1243, 1.0658),
        (0.95, 0.9813, 1.1458, 1.0950, 1.0745),
    )
    for row in table:
        depth, alpha_t, beta_t, velocity_t, flow_t = row
        result = partial_flow(diameter, slope, roughness, depth)
        assert abs(result.velocity / full - velocity_t) < 1e-4
        assert abs(result.flow / capacity_full - flow_t) < 1e-4
        theta_volume = result.area / (3.14159265 * diameter**2 / 4)
        assert abs(theta_volume - alpha_t) < 1e-4
        assert abs(result.hydraulic_radius / (diameter / 4) - beta_t) < 1e-4
        # NM-F3 定义式（A/P，partial_flow 出值）与 NM-F2-R 比例式（β·d/4）
        # 注册表互校闭合（手算表口径；rel_tol=1e-8 含 DSL 串 π 常量八位
        # 截断 vs math.pi 的 ~1e-9 级系统差——运行时抛障版 NET2 审裁撤，
        # 照 R4"一致性由测试背书"移此）。
        theta = 2.0 * math.acos(1.0 - 2.0 * depth)
        beta_analytic = (theta - math.sin(theta)) / theta
        radius_ratio = apply("NM-F2-R", {"beta": beta_analytic, "d": diameter}, ("network", "test"))
        assert math.isclose(result.hydraulic_radius, radius_ratio, rel_tol=1e-8)
