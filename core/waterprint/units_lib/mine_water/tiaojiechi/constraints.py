"""矿井水调节池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_tiaojiechi.md KT-F1/F3/F4/F8）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三条校核带（实际停留时间 8~12 h 井下脉动/有效水深
#   3.0~5.0 m 半地下·地下式/长宽比 2.0~4.0）数值真源=
#   factor.mine_tiaojiechi.*（data 包 0.5.0）——本文件零数值字面量，
#   表达式按键引用。KT-F7 调节容积校核（v_act_total ≥ v_total）为
#   结果对结果比较、无 data 包键——仅 compute warnings 承载不在此
#   声明。与市政同名包三带限值独立起草（§14.3 物理隔离可审计面）。
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
    "GB/T 41019-2021（矿井水处理工艺——调节构筑物容积口径，条号待核对）；"
    "docs/norms/mine_water_tiaojiechi.md 起草表 2026-08-27，待追认"
)
_HB = (
    "给水排水设计手册（第 5 册 城镇排水）调节池停留时间法/防沉积搅拌"
    "功率密度常用带；docs/norms/mine_water_tiaojiechi.md 起草表"
    " 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_tiaojiechi.hrt_band",
        expression=(
            "t_reg_act >= factor.mine_tiaojiechi.hrt_band.min"
            " and t_reg_act <= factor.mine_tiaojiechi.hrt_band.max"
        ),
        source=f"{_GB}；{_HB}；KT-F8 带宽（factor.mine_tiaojiechi.hrt_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_tiaojiechi.depth_band",
        expression=(
            "h2 >= factor.mine_tiaojiechi.depth_band.min"
            " and h2 <= factor.mine_tiaojiechi.depth_band.max"
        ),
        source=f"{_HB}；KT-F3 带宽（factor.mine_tiaojiechi.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_tiaojiechi.ratio_lb_band",
        expression=(
            "ratio_lb >= factor.mine_tiaojiechi.ratio_lb_band.min"
            " and ratio_lb <= factor.mine_tiaojiechi.ratio_lb_band.max"
        ),
        source=f"{_HB}；KT-F4 带宽（factor.mine_tiaojiechi.ratio_lb_band.*）",
        severity="WARN",
    ),
)
