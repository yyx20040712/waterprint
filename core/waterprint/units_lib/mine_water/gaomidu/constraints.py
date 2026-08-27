"""高密沉淀约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_gaomidu.md KG-F2/F3/F4/F7/F8）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】五条校核带（液面负荷带 5~8 m³/(m²·h) 低负荷保浊度档
#   [参数面+实际面双条]/斜管轴向流速上限 ≤5 mm/s/快混停留 0.5~2.0/
#   絮凝停留 8~15 min）数值真源=factor.mine_gaomidu.*（data 包
#   0.5.0）——本文件零数值字面量，表达式按键引用。无 r_sludge/
#   q_return 回流键族（市政 Densadeg 键族物理隔离，表边界差异节）。
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
    "GB/T 41019-2021（混凝沉淀液面负荷，条号待核对）；"
    "docs/norms/mine_water_gaomidu.md 起草表 2026-08-27，待追认"
)
_HB = (
    "给水排水设计手册（第 3 册 城镇给水）斜管沉淀池轴向流速/混合絮凝"
    "停留常用带；docs/norms/mine_water_gaomidu.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_gaomidu.surface_load_band",
        expression=(
            "q_surf >= factor.mine_gaomidu.surface_load_band.min"
            " and q_surf <= factor.mine_gaomidu.surface_load_band.max"
        ),
        source=(
            f"{_GB}；KG-F4 带宽（factor.mine_gaomidu.surface_load_band.*——"
            "低负荷 5~8 保浊度档，异于市政 10~20）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_gaomidu.surface_load_act",
        expression=(
            "q_surf_act >= factor.mine_gaomidu.surface_load_band.min"
            " and q_surf_act <= factor.mine_gaomidu.surface_load_band.max"
        ),
        source=f"{_GB}；KG-F7 实际负荷带宽（B/L 0.5 m 档离散后校核）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_gaomidu.axial_velocity",
        expression="v_axial <= factor.mine_gaomidu.axial_velocity.max",
        source=f"{_HB}；KG-F8 带宽（factor.mine_gaomidu.axial_velocity.max——≤5 mm/s）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_gaomidu.t_mix_band",
        expression=(
            "t_mix >= factor.mine_gaomidu.t_mix_band.min"
            " and t_mix <= factor.mine_gaomidu.t_mix_band.max"
        ),
        source=f"{_HB}；KG-F2 带宽（factor.mine_gaomidu.t_mix_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_gaomidu.t_floc_band",
        expression=(
            "t_floc >= factor.mine_gaomidu.t_floc_band.min"
            " and t_floc <= factor.mine_gaomidu.t_floc_band.max"
        ),
        source=f"{_HB}；KG-F3 带宽（factor.mine_gaomidu.t_floc_band.*）",
        severity="WARN",
    ),
)
