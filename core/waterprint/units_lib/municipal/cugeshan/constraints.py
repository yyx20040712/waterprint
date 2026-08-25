"""粗格栅约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/cugeshan.md CG-F5/F6）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三表校核带 0.6~1.0（v）/0.4~0.9（v₁）数值真源=
#   factor.screen.velocity_band.*（data 包 0.1.0）——本文件零数值字面量，
#   表达式按键引用（solution/constraints DSL 就绪后按 field_id 消费）。
# 【R1 限值有出处】source 逐条带 data 包键+三表注记（条文级核对挂账）。
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


_NORM = "GB 50014-2021 §6.3（条文号待核对原文；docs/norms/cugeshan.md 签字表）"

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="cugeshan.velocity_band.v",
        expression=(
            "v_checked >= factor.screen.velocity_band.v.min"
            " and v_checked <= factor.screen.velocity_band.v.max"
        ),
        source=f"{_NORM}；CG-F5 校核带（factor.screen.velocity_band.v.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="cugeshan.velocity_band.v1",
        expression=(
            "v1_checked >= factor.screen.velocity_band.v1.min"
            " and v1_checked <= factor.screen.velocity_band.v1.max"
        ),
        source=f"{_NORM}；CG-F6 校核带（factor.screen.velocity_band.v1.*）",
        severity="WARN",
    ),
)
