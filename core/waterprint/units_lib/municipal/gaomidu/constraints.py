"""高密沉淀池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  四表校核带（docs/norms/gaomidu.md GM-F2/F5/F6/F7/F10/F11）+ data/coefficients 0.3.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段或参数与 factor 键限值
#   比较）/ source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】五条校核带（液面负荷 10~20/回流比 0.03~0.05/快混停留
#   1~2 min/絮凝停留 8~15 min/GT 1e4~1e5）数值真源=factor.gaomidu.*
#   （data 包 0.3.0，M2b1 四单元系数批）——本文件零数值字面量，
#   表达式按键引用。GM-F19 絮凝区布置校核（h_floc_calc < h_settle）
#   为结果对结果比较、无 data 包键——仅 compute warnings 承载不在此
#   声明。
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


_GT = (
    "GB/T 50335-2016 §5.4.3；GB 50013-2018 §9.4.24（ADR-008 双源）；"
    "docs/norms/gaomidu.md 起草表 2026-08-25，待追认"
)
_HB = (
    "给水排水设计手册（第 5 册 城镇排水）；"
    "docs/norms/gaomidu.md 起草表 2026-08-25，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="gaomidu.surface_load_band",
        expression=(
            "q_surface_act >= factor.gaomidu.surface_load_band.min"
            " and q_surface_act <= factor.gaomidu.surface_load_band.max"
        ),
        source=f"{_GT}；GM-F5 带宽（factor.gaomidu.surface_load_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="gaomidu.r_sludge_band",
        expression=(
            "r_sludge >= factor.gaomidu.r_sludge_band.min"
            " and r_sludge <= factor.gaomidu.r_sludge_band.max"
        ),
        source=f"{_GT}；GM-F11 带宽（factor.gaomidu.r_sludge_band.*，Densadeg 回流档）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="gaomidu.t_mix_band",
        expression=(
            "t_mix >= factor.gaomidu.t_mix_band.min"
            " and t_mix <= factor.gaomidu.t_mix_band.max"
        ),
        source=f"{_HB}；GM-F6 带宽（factor.gaomidu.t_mix_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="gaomidu.t_floc_band",
        expression=(
            "t_floc >= factor.gaomidu.t_floc_band.min"
            " and t_floc <= factor.gaomidu.t_floc_band.max"
        ),
        source=f"{_HB}；GM-F7 带宽（factor.gaomidu.t_floc_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="gaomidu.gt_band",
        expression=(
            "gt_floc >= factor.gaomidu.gt_band.min"
            " and gt_floc <= factor.gaomidu.gt_band.max"
        ),
        source=f"{_HB}；GM-F10 带宽（factor.gaomidu.gt_band.*）",
        severity="WARN",
    ),
)
