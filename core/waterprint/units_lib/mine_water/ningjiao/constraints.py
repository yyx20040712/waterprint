"""混凝反应池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_ningjiao.md KN-F1~F4/F7/F8/F10）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】七条校核带（总 GT 1×10⁴~1×10⁵/四区停留 0.5~2/1~3/
#   2~4/1~2 min/有效水深 2.5~4.0/分区长宽比 0.8~1.5）数值真源=
#   factor.mine_ningjiao.*（data 包 0.5.0）——本文件零数值字面量，
#   表达式按键引用。KN-F5 总停留 ≤12 校核表内无 data 包键——不造
#   无依据键，仅表内注记（待追认）；各 G 值带（500~1000 等）同无键
#   不在此声明（G 值取值键 g_mix 等为计算入参非校核带）。
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
    "GB/T 41019-2021（矿井水处理工艺——混凝路线与药剂，条号待核对）；"
    "docs/norms/mine_water_ningjiao.md 起草表 2026-08-27，待追认"
)
_HB = (
    "给水排水设计手册（第 3 册 城镇给水）混合/絮凝 G 值法与 GT 校核"
    "常用带；docs/norms/mine_water_ningjiao.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_ningjiao.gt_band",
        expression=(
            "gt_total >= factor.mine_ningjiao.gt_band.min"
            " and gt_total <= factor.mine_ningjiao.gt_band.max"
        ),
        source=(
            f"{_HB}；KN-F10 带宽（factor.mine_ningjiao.gt_band.*——ΣG·t 总量口径，"
            "异于旧系统分区独立校核，表内追认点 6）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ningjiao.t_mix_band",
        expression=(
            "t_mix >= factor.mine_ningjiao.t_mix_band.min"
            " and t_mix <= factor.mine_ningjiao.t_mix_band.max"
        ),
        source=f"{_HB}；KN-F1 带宽（factor.mine_ningjiao.t_mix_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ningjiao.t_seed_band",
        expression=(
            "t_seed >= factor.mine_ningjiao.t_seed_band.min"
            " and t_seed <= factor.mine_ningjiao.t_seed_band.max"
        ),
        source=f"{_GB}；{_HB}；KN-F2 带宽（factor.mine_ningjiao.t_seed_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ningjiao.t_floc_band",
        expression=(
            "t_floc >= factor.mine_ningjiao.t_floc_band.min"
            " and t_floc <= factor.mine_ningjiao.t_floc_band.max"
        ),
        source=f"{_HB}；KN-F3 带宽（factor.mine_ningjiao.t_floc_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ningjiao.t_ripen_band",
        expression=(
            "t_ripen >= factor.mine_ningjiao.t_ripen_band.min"
            " and t_ripen <= factor.mine_ningjiao.t_ripen_band.max"
        ),
        source=f"{_HB}；KN-F4 带宽（factor.mine_ningjiao.t_ripen_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ningjiao.depth_band",
        expression=(
            "h2 >= factor.mine_ningjiao.depth_band.min"
            " and h2 <= factor.mine_ningjiao.depth_band.max"
        ),
        source=f"{_HB}；KN-F7 带宽（factor.mine_ningjiao.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ningjiao.cell_ratio_lb_band",
        expression=(
            "ratio_lb >= factor.mine_ningjiao.cell_ratio_lb_band.min"
            " and ratio_lb <= factor.mine_ningjiao.cell_ratio_lb_band.max"
        ),
        source=f"{_HB}；KN-F8 带宽（factor.mine_ningjiao.cell_ratio_lb_band.*——最大分区）",
        severity="WARN",
    ),
)
