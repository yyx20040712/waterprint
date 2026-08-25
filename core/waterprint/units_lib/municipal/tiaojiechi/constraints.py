"""调节池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  四表校核带（docs/norms/tiaojiechi.md TJ-F1/F3/F4/F7）+ data/coefficients 0.3.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三条校核带（实际停留时间 6~12 h/有效水深 4.0~6.0 m/
#   长宽比 2.0~3.0）数值真源=factor.tiaojiechi.*（data 包 0.3.0，
#   M2b1 四单元系数批）——本文件零数值字面量，表达式按键引用。
#   TJ-F7 调节容积校核（v_act_total ≥ v_total）为结果对结果比较、
#   无 data 包键——仅 compute warnings 承载不在此声明。溢流管流速与
#   搅拌功率密度为单值设计取值（无带键），不构成校核带。
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


_HB = "给水排水设计手册（第 5 册 城镇排水）；docs/norms/tiaojiechi.md 起草表 2026-08-25，待追认"

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="tiaojiechi.hrt_band",
        expression=(
            "t_reg_act >= factor.tiaojiechi.hrt_band.min"
            " and t_reg_act <= factor.tiaojiechi.hrt_band.max"
        ),
        source=f"{_HB}；TJ-F8 带宽（factor.tiaojiechi.hrt_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="tiaojiechi.depth_band",
        expression=(
            "h2 >= factor.tiaojiechi.depth_band.min"
            " and h2 <= factor.tiaojiechi.depth_band.max"
        ),
        source=f"{_HB}；TJ-F3 带宽（factor.tiaojiechi.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="tiaojiechi.ratio_lb_band",
        expression=(
            "ratio_lb >= factor.tiaojiechi.ratio_lb_band.min"
            " and ratio_lb <= factor.tiaojiechi.ratio_lb_band.max"
        ),
        source=f"{_HB}；TJ-F4 带宽（factor.tiaojiechi.ratio_lb_band.*）",
        severity="WARN",
    ),
)
