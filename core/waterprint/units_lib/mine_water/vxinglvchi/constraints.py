"""V型滤池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_vxinglvchi.md KV-F3/F5/F6/F9/F10）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】六条校核带（正常滤速带 4~6 m/h 低滤速精滤档——异于
#   市政 7~10/强制滤速上限 ≤10 m/h/滤层厚带 0.8~1.2 m 偏薄档——异于
#   市政 1.2~1.5/砂上水深带 1.0~1.5 m/过滤周期带 24~48 h/反冲耗水率
#   上限 ≤5%）数值真源=factor.mine_vxinglvchi.*（data 包 0.5.0）——
#   本文件零数值字面量，表达式按键引用。反冲三阶段强度/历时键为
#   计算入参非校核带，不在此声明。
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
    "GB/T 41019-2021（过滤段滤速/滤料层厚，条号待核对）；"
    "docs/norms/mine_water_vxinglvchi.md 起草表 2026-08-27，待追认"
)
_HB = (
    "给水排水设计手册（第 3 册 城镇给水）V 型滤池滤料/气水反冲/反冲"
    "耗水常用带；docs/norms/mine_water_vxinglvchi.md 起草表 2026-08-27，"
    "待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_vxinglvchi.v_filter_band",
        expression=(
            "v_filter >= factor.mine_vxinglvchi.v_filter_band.min"
            " and v_filter <= factor.mine_vxinglvchi.v_filter_band.max"
        ),
        source=(
            f"{_GB}；KV-F3 带宽（factor.mine_vxinglvchi.v_filter_band.*——"
            "低滤速精滤档 4~6，异于市政 7~10）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_vxinglvchi.forced_velocity",
        expression="v_force_act <= factor.mine_vxinglvchi.v_forced.max",
        source=f"{_GB}；KV-F5 上限（factor.mine_vxinglvchi.v_forced.max——一格冲洗时余格承载）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_vxinglvchi.media_depth_band",
        expression=(
            "h_media >= factor.mine_vxinglvchi.media.depth_band.min"
            " and h_media <= factor.mine_vxinglvchi.media.depth_band.max"
        ),
        source=(
            f"{_GB}；KV-F10 带宽（factor.mine_vxinglvchi.media.depth_band.*——"
            "细砂精滤偏薄档，异于市政 1.2~1.5）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_vxinglvchi.water_above_band",
        expression=(
            "h_water >= factor.mine_vxinglvchi.water_above_band.min"
            " and h_water <= factor.mine_vxinglvchi.water_above_band.max"
        ),
        source=f"{_HB}；KV-F10 带宽（factor.mine_vxinglvchi.water_above_band.*——恒水位过滤）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_vxinglvchi.cycle_band",
        expression=(
            "t_filter >= factor.mine_vxinglvchi.cycle_band.min"
            " and t_filter <= factor.mine_vxinglvchi.cycle_band.max"
        ),
        source=f"{_HB}；KV-F2 带宽（factor.mine_vxinglvchi.cycle_band.*——低浊进水可短周期）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_vxinglvchi.wash_ratio",
        expression="eta_wash <= factor.mine_vxinglvchi.wash.ratio_max",
        source=(
            f"{_HB}；KV-F9 上限（factor.mine_vxinglvchi.wash.ratio_max——"
            "单格日冲一次口径）"
        ),
        severity="WARN",
    ),
)
