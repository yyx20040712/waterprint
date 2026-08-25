"""辐流初沉池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/chuchenchi.md CC-F2/F5/F6/F7/F9/F12）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】五条校核带（表面负荷 1.5~4.5/有效水深 2.0~4.0/径深比
#   6~12/堰负荷 ≤2.9/排泥周期 1~2[0.2.1 新键]）数值真源=
#   factor.chuchenchi.*（data 包 0.2.0/0.2.1）——本文件零数值字面量，
#   表达式按键引用。CC-F16 贮泥容积校核（v_storage ≥ v_need）为
#   结果对结果比较、无 data 包键——仅 compute warnings 承载不在此声明。
# 【追认口径注记】堰负荷键绑定双圈堰构造（L=2π(D−1)，单侧口径敏感性
#   见三表注记——待领域专家追认）。
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


_NORM = "GB 50014-2021 §6.5（沉淀池；docs/norms/chuchenchi.md 起草表 2026-08-25，待追认）"
_HB = "给水排水设计手册（第 5 册 城镇排水）；docs/norms/chuchenchi.md 起草表 2026-08-25，待追认"

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="chuchenchi.surface_load_band",
        expression=(
            "q_prime_act >= factor.chuchenchi.surface_load_band.min"
            " and q_prime_act <= factor.chuchenchi.surface_load_band.max"
        ),
        source=f"{_NORM}；CC-F5 带宽（factor.chuchenchi.surface_load_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="chuchenchi.depth_band",
        expression=(
            "h2 >= factor.chuchenchi.depth_band.min"
            " and h2 <= factor.chuchenchi.depth_band.max"
        ),
        source=f"{_NORM}；CC-F6 带宽（factor.chuchenchi.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="chuchenchi.ratio_dh2_band",
        expression=(
            "ratio_dh2 >= factor.chuchenchi.ratio_dh2_band.min"
            " and ratio_dh2 <= factor.chuchenchi.ratio_dh2_band.max"
        ),
        source=f"{_HB}；CC-F7 带宽（factor.chuchenchi.ratio_dh2_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="chuchenchi.weir_load",
        expression="q_weir <= factor.chuchenchi.weir_load.max",
        source=(
            f"{_NORM}；CC-F9 堰负荷上限"
            "（factor.chuchenchi.weir_load.max；双圈堰 L=2π(D−1) 口径待追认）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="chuchenchi.sludge_cycle_band",
        expression=(
            "t_sludge >= factor.chuchenchi.sludge_cycle_band.min"
            " and t_sludge <= factor.chuchenchi.sludge_cycle_band.max"
        ),
        source=(
            f"{_NORM}；CC-F12 带宽"
            "（factor.chuchenchi.sludge_cycle_band.*，data 0.2.1 M2a2 前置键）"
        ),
        severity="WARN",
    ),
)
