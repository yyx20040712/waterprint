"""污泥泵站约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_bengzhan.md BZ-F3/F7/F14 + 集泥井双带）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】五条校核带（单泵流量带 5~50 m³/h、出泥管流速带
#   1.0~2.0 m/s、启停频率上限 ≤6 次/h、集泥井调节时间带 5~15 min、
#   集泥井有效水深带 1.5~2.5 m）数值真源=factor.bengzhan.*（data 包
#   0.6.0）——本文件零数值字面量，表达式按键引用。泵组锚/自由水头/
#   沿程 λ/局部 ζ/污泥粘度修正/超高/壁厚系数为计算入参键非校核带。
# ══════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from typing import final


@dataclass(frozen=True)
@final
class ConstraintDecl:
    """单条约束声明：键 + 受限比较式 + 出处 + 级别（声明式，无数值）。"""

    key: str
    expression: str
    source: str
    severity: str


_GB = (
    "GB 50014-2021 §6.1（集水池容积/备用泵，条号随追认核对）与 §8"
    "（污泥章，条号待核对）；docs/norms/sludge_bengzhan.md 起草表"
    " 2026-08-27，待追认"
)
_HB5 = (
    "给水排水设计手册（第 5 册 城镇排水）污泥泵站章；"
    "docs/norms/sludge_bengzhan.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_bengzhan.pump_q_flow_band",
        expression=(
            "q_pump_h >= factor.bengzhan.pump.q_flow_band.min"
            " and q_pump_h <= factor.bengzhan.pump.q_flow_band.max"
        ),
        source=f"{_HB5}；BZ-F3 带宽（factor.bengzhan.pump.q_flow_band.*——均分反算单泵流量）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_bengzhan.pipe_velocity_band",
        expression=(
            "v_act >= factor.bengzhan.pipe.velocity_band.min"
            " and v_act <= factor.bengzhan.pipe.velocity_band.max"
        ),
        source=f"{_GB}；BZ-F7 带宽（factor.bengzhan.pipe.velocity_band.*——取整后实流速）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_bengzhan.pump_start_band",
        expression="n_start <= factor.bengzhan.pump.start_band.max",
        source=f"{_HB5}；BZ-F14 启停频率上限（factor.bengzhan.pump.start_band.max）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_bengzhan.well_t_band",
        expression=(
            "t_well >= factor.bengzhan.well.t_band.min"
            " and t_well <= factor.bengzhan.well.t_band.max"
        ),
        source=f"{_GB}；BZ-F12 带宽（factor.bengzhan.well.t_band.*——调节时间参数带）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_bengzhan.well_depth_band",
        expression=(
            "h_well >= factor.bengzhan.well.depth_band.min"
            " and h_well <= factor.bengzhan.well.depth_band.max"
        ),
        source=f"{_HB5}；BZ-F13 带宽（factor.bengzhan.well.depth_band.*——有效水深参数带）",
        severity="WARN",
    ),
)
