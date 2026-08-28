"""曼宁水力计算（充满度分档）：圆管非满流的速度/坡度/充满度关系。

输入:  管断面（管径/粗糙系数）+ 设计流量
输出:  流速/水力坡度/充满度（全部经公式注册表求值，挂条文溯源）

NET2 实装注记（2026-08-28，段二批——数据基线 RATIFY4 已追认）：
- 公式载体=docs/norms/network_manning.md 公式表 NM-F1~F5（DSL 串逐字）；
  中心角 θ 解析式（cos(θ/2)=1−2h/d、A=(d²/8)(θ−sinθ)、P=dθ/2）含
  arccos/sin 不入 DSL 白名单——照 NS-F5"离散化后的产出符号作下游公式
  输入"先例，α/β 在本模块 python 侧收口后作 NM-F2 消费串的输入符号
  （注册形态=每条 DSL 串一条 FormulaSpec，id 族 NM-F1/NM-F2-*/NM-F3/
  NM-F5-*，记档 task-NET2-impl-report.md）。
- 比例表载体裁决（简报 D1"载体实现者定"）：取**解析式实现**——手册
  0.05 档 19 行比例表（手算表 NM-F2 载体）作测试互校锚（tests/network/
  test_manning.py 表载断言，tests 区数值合法），不进模块常量表；golden
  容差口径随之取 1e-4（4dp 誊录 vs 解析真值——冻结 §三 D 条）。
- 粗糙系数为实参非键查询（R2：调用方从 coefficients network.roughness.*
  取值传入）；solve 容差/轮数/区间端点经 assumptions network.solve.*
  四键（registry/assumptions.py NET2 批登记）。
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/network/test_manning.py）
#
# 【公开接口】
#   manning_velocity(diameter, slope, roughness) -> float   满流流速
#   partial_flow(diameter, slope, roughness,
#                depth_ratio) -> PartialFlowResult          非满流分档
#   class PartialFlowResult：velocity、flow、depth_ratio、area、
#       wetted_perimeter、hydraulic_radius
#   solve_depth(diameter, slope, roughness, flow) -> float
#       已知流量反解充满度（数值求根，容差来自 assumptions）
#
# 【行为规格】
#   R1 充满度分档：圆管非满流水力特性按充满度表/公式分档计算
#      （分档数据与公式条文出处由实现期领域专家核定后登记公式
#      注册表——禁止无出处公式）。
#   R2 粗糙系数（塑料管/混凝土管等）来自 coefficients 数据包
#      （带出处），零代码常量。
#   R3 物理不变量（性质测试）：充满度 ∈ (0,1]、流速 > 0、
#      非满流最大流量出现在充满度约 0.94 附近（教科书结论作为
#      性质断言的容差带，出处入 assumptions/coefficients）。
#   R4 单调性（性质测试）：同断面流速随坡度单调增；
#      同坡度流量随管径单调增。
#   R5 迭代求根（solve_depth）：容差/最大迭代来自 assumptions；
#      不收敛抛领域异常（复用 loop 思想但不 import graph——独立域）。
#
# 【测试要求】满流基准数值（golden，来源 docs/norms 手算对照）、
#   非满流分档查表正确、性质四条、求根收敛与不收敛路径。
#
# 【参照】重写计划 §13.3 管网行/§14.3 独立域
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from math import acos, pi, sin
from typing import Final, final

from waterprint.contracts.quantity import DimKey
from waterprint.registry.assumptions import assumption
from waterprint.registry.formulas import FormulaSpec, apply, register

__all__ = [
    "NetworkHydraulicsError",
    "PartialFlowResult",
    "full_flow_capacity",
    "manning_velocity",
    "partial_flow",
    "solve_depth",
]


class NetworkHydraulicsError(Exception):
    """管网水力计算非法/不收敛（GR-11 族领域异常——禁静默截断）。"""


# 求值上下文（trace 留空：本域独立无 collector，formula_id 已入注册表
# 可溯源——结构图谱 §2:107 network→contracts 边注记口径）。
_CTX: Final[tuple[str, str]] = ("network", "manning")

_NM_REF: Final[str] = (
    "GB 50014-2021 §5 排水管渠水力计算（条号随追认核对）；"
    "docs/norms/network_manning.md NM-F1~F5（RATIFY4 追认 2026-08-28）"
)
_HB_REF: Final[str] = (
    "《给水排水设计手册（第 5 册 城镇排水）》管渠水力计算章（非满流"
    "比例表标准形式）；docs/norms/network_manning.md（RATIFY4 追认）"
)

# 量纲短名（符号表构造用）
_D = DimKey.LENGTH
_V = DimKey.VELOCITY
_Q = DimKey.FLOW
_A = DimKey.AREA
_Z = DimKey.DIMENSIONLESS


@dataclass(frozen=True)
@final
class PartialFlowResult:
    """非满流分档结果六字段（NM-F2/F3 产出符号直供）。"""

    velocity: float  # v_part m/s（NM-F2 消费串①）
    flow: float  # q_part m³/s（NM-F2 消费串②）
    depth_ratio: float  # h/D 充满度
    area: float  # a_part m²（NM-F2-A）
    wetted_perimeter: float  # p_part m（解析 θ·d/2）
    hydraulic_radius: float  # r_part m（NM-F3 定义式，与 NM-F2-R 互校）


# ── NM-F* 公式族登记（DSL 串逐字照手算表公式表；α/β/θ 为 python 侧
#    收口的输入符号——acos/sin 不入 DSL 白名单，照 NS-F5 先例）──
_FORMULAS: Final[tuple[FormulaSpec, ...]] = (
    FormulaSpec(
        "NM-F1",
        "v_full = (1/n) * (d/4)**(2/3) * s**0.5",
        {
            "n": (_Z, "曼宁粗糙系数（coefficients network.roughness.*）"),
            "d": (_D, "管径 m"),
            "s": (_Z, "水力坡度 m/m（设计取管道坡度）"),
        },
        _V,
        _NM_REF,
    ),
    FormulaSpec(
        "NM-F2-V",
        "v_part = (1/n) * (beta * d / 4)**(2/3) * s**0.5",
        {
            "n": (_Z, "粗糙系数"),
            "beta": (_Z, "水力半径比 R/R_full（python 侧收口）"),
            "d": (_D, "管径 m"),
            "s": (_Z, "水力坡度 m/m"),
        },
        _V,
        _HB_REF + "；NM-F2 消费串①（β 作输入符号）",
    ),
    FormulaSpec(
        "NM-F2-Q",
        "q_part = alpha * 3.14159265 * d**2 / 4 * v_part",
        {
            "alpha": (_Z, "面积比 A/A_full（python 侧收口）"),
            "d": (_D, "管径 m"),
            "v_part": (_V, "非满流流速 m/s（NM-F2-V 产出）"),
        },
        _Q,
        _HB_REF + "；NM-F2 消费串②（alpha=1 退化即满流 Q_full）",
    ),
    FormulaSpec(
        "NM-F2-A",
        "a_part = alpha * 3.14159265 * d**2 / 4",
        {"alpha": (_Z, "面积比 A/A_full"), "d": (_D, "管径 m")},
        _A,
        _HB_REF + "；NM-F2 断面式（A=α·A_full）",
    ),
    FormulaSpec(
        "NM-F2-R",
        "r_part = beta * d / 4",
        {"beta": (_Z, "水力半径比 R/R_full"), "d": (_D, "管径 m")},
        _D,
        _HB_REF + "；NM-F2 比例式（R=β·D/4，与 NM-F3 定义式互校）",
    ),
    FormulaSpec(
        "NM-F3",
        "r_part = a_part / p_part",
        {"a_part": (_A, "过水断面积 m²"), "p_part": (_D, "湿周 m")},
        _D,
        "《给水排水设计手册（第 5 册）》水力半径定义；"
        "docs/norms/network_manning.md NM-F3（RATIFY4 追认）",
    ),
    FormulaSpec(
        "NM-F5-V",
        "margin_v = min(v_part - v_band_min, v_band_max - v_part)",
        {
            "v_part": (_V, "非满流流速 m/s"),
            "v_band_min": (_V, "最小设计流速 m/s"),
            "v_band_max": (_V, "最大设计流速 m/s"),
        },
        _V,
        "GB 50014-2021 §5 设计流速带（条号随追认核对）；"
        "docs/norms/network_manning.md NM-F5 裕度式①（≥0 合格）",
    ),
    FormulaSpec(
        "NM-F5-FILL",
        "margin_fill = fill_limit - h_d",
        {
            "fill_limit": (_Z, "最大设计充满度（coefficients network.max_fill_ratio.dn*）"),
            "h_d": (_Z, "充满度 h/D"),
        },
        _Z,
        "GB 50014-2021 §5 最大设计充满度表（条号随追认核对）；"
        "docs/norms/network_manning.md NM-F5 裕度式②",
    ),
    FormulaSpec(
        "NM-F5-DEPTH",
        "margin_depth = depth_max - (ground - invert)",
        {
            "depth_max": (_D, "最大埋深 m（coefficients network.max_depth）"),
            "ground": (_D, "地面标高 m"),
            "invert": (_D, "管底标高 m"),
        },
        _D,
        "《给水排水设计手册（第 5 册 城镇排水）》管道最大埋深；"
        "docs/norms/network_manning.md NM-F5 裕度式③",
    ),
)

for _spec in _FORMULAS:
    register(_spec)


def _central_angle(depth_ratio: float) -> float:
    """θ=2·arccos(1−2h/d)（手算表 NM-F2 解析式——acos 不入 DSL，python 收口）。"""
    return 2.0 * acos(1.0 - 2.0 * depth_ratio)


def _ratio_factors(depth_ratio: float) -> tuple[float, float]:
    """(α, β)：α=(θ−sinθ)/(2π)、β=(θ−sinθ)/θ（手册比例表解析式）。"""
    theta = _central_angle(depth_ratio)
    chord = theta - sin(theta)
    return chord / (2.0 * pi), chord / theta


def _checked_positive(value: float, name: str) -> None:
    """正数守卫：管径/坡度/糙率/流量非正=领域异常（GR-02 输入即拒）。"""
    if value <= 0.0:
        raise NetworkHydraulicsError(
            f"{name} 必须为正数：得到 {value!r}（管径/坡度/糙率/流量物理域）"
        )


def manning_velocity(diameter: float, slope: float, roughness: float) -> float:
    """满流流速（NM-F1 经注册表 apply——R3 唯一求值路径）。"""
    for value, name in ((diameter, "管径"), (slope, "坡度"), (roughness, "粗糙系数")):
        _checked_positive(value, name)
    return apply("NM-F1", {"n": roughness, "d": diameter, "s": slope}, _CTX)


def full_flow_capacity(diameter: float, slope: float, roughness: float) -> float:
    """满流流量 Q_full（NM-F2-Q alpha=1 退化形态；NM-F1 v_full 链式）。"""
    velocity = manning_velocity(diameter, slope, roughness)
    return apply("NM-F2-Q", {"alpha": 1.0, "d": diameter, "v_part": velocity}, _CTX)


def partial_flow(
    diameter: float, slope: float, roughness: float, depth_ratio: float
) -> PartialFlowResult:
    """非满流分档（NM-F2 消费串×3 + NM-F3 定义式出 R）。

    NM-F2-R 比例式（R=β·d/4）与 NM-F3 定义式（A/P）的互校闭合不在此
    运行时抛障（DSL 串 π 常量八位截断 vs math.pi 存在 ~1e-9 级系统差，
    抛障需引入容差键）——照 R4"实现与注册表一致性由测试背书"口径移
    tests/network/test_manning.py 互校断言（rel_tol=1e-8 含截断差带）。
    """
    for value, name in ((diameter, "管径"), (slope, "坡度"), (roughness, "粗糙系数")):
        _checked_positive(value, name)
    if not 0.0 < depth_ratio <= 1.0:
        raise NetworkHydraulicsError(
            f"充满度必须在 (0, 1] 区间：得到 {depth_ratio!r}（R3 物理不变量）"
        )
    alpha, beta = _ratio_factors(depth_ratio)
    velocity = apply("NM-F2-V", {"n": roughness, "beta": beta, "d": diameter, "s": slope}, _CTX)
    flow = apply("NM-F2-Q", {"alpha": alpha, "d": diameter, "v_part": velocity}, _CTX)
    area = apply("NM-F2-A", {"alpha": alpha, "d": diameter}, _CTX)
    wetted_perimeter = _central_angle(depth_ratio) * diameter / 2.0
    radius = apply("NM-F3", {"a_part": area, "p_part": wetted_perimeter}, _CTX)
    return PartialFlowResult(
        velocity=velocity,
        flow=flow,
        depth_ratio=depth_ratio,
        area=area,
        wetted_perimeter=wetted_perimeter,
        hydraulic_radius=radius,
    )


def solve_depth(diameter: float, slope: float, roughness: float, flow: float) -> float:
    """已知流量反解充满度（NM-F4 二分求根：容差/轮数/区间经 assumptions）。

    Q/Q_full 随 h/D 在 [0.02, 0.9382] 单调增（手册比例表性质）；流量
    超过区间上端输水能力时不收敛→抛 NetworkHydraulicsError（R5 禁静默）。
    """
    for value, name in (
        (diameter, "管径"),
        (slope, "坡度"),
        (roughness, "粗糙系数"),
        (flow, "流量"),
    ):
        _checked_positive(value, name)
    tolerance = assumption("network.solve.tolerance", {})
    max_iterations = int(assumption("network.solve.max_iterations", {}))
    low = assumption("network.solve.depth_min", {})
    high = assumption("network.solve.depth_max", {})
    ceiling = partial_flow(diameter, slope, roughness, high).flow
    if flow > ceiling:
        raise NetworkHydraulicsError(
            f"流量超过断面最大输水能力：Q={flow!r} > "
            f"Q(h/D={high!r})={ceiling!r}（DN/坡度组合过小——NM-F4 无根）"
        )
    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        capacity = partial_flow(diameter, slope, roughness, mid).flow
        if abs(capacity - flow) <= tolerance:
            return mid
        if capacity < flow:
            low = mid
        else:
            high = mid
    raise NetworkHydraulicsError(
        f"solve_depth 二分求根不收敛：d={diameter!r} s={slope!r} n={roughness!r} "
        f"Q={flow!r}（{max_iterations} 轮后残差仍超容差 {tolerance!r}——R5）"
    )
