"""污泥输送约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_shusong.md ST-F4/ST-F6）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】两条校核带（压力段实际流速带 1.0~2.0 m/s——取整后实
#   流速校核；重力段最小流速 0.7 m/s——整定坡度下实流速校核）数值
#   真源=factor.shusong.velocity_band.*/factor.shusong.gravity_v_min
#   （data 包 0.6.0）——本文件零数值字面量，表达式按键引用。最小
#   坡度 slope_min 为 ST-F7 整定下限非校核带不在此声明；曼宁糙率
#   为计算入参键非校核带。
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
    "GB 50014-2021 §8（污泥章——污泥管道压力流速，条号待核对）；"
    "docs/norms/sludge_shusong.md 起草表 2026-08-27，待追认"
)
_HB5 = (
    "给水排水设计手册（第 5 册 城镇排水）污泥管道章（重力输泥最小流速）；"
    "docs/norms/sludge_shusong.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_shusong.velocity_band",
        expression=(
            "v_act >= factor.shusong.velocity_band.min"
            " and v_act <= factor.shusong.velocity_band.max"
        ),
        source=f"{_GB}；ST-F4 带宽（factor.shusong.velocity_band.*——取整后实流速校核）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_shusong.gravity_v_min",
        expression="v_grav >= factor.shusong.gravity_v_min",
        source=f"{_HB5}；ST-F6 最小流速（factor.shusong.gravity_v_min——整定坡度下校核）",
        severity="WARN",
    ),
)
