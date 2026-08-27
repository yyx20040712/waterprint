"""矿井水输入约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_input.md KI-F7）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】超高校核带（freeboard ≥ 0.3 m）数值真源=
#   factor.mine_input.freeboard.min（data 包 0.5.0）——本文件零数值
#   字面量，表达式按键引用。进水管流速经济流速带（KI-F3 校核）表内
#   未建 data 包键——不造无依据键，仅表内注记不在此声明（待追认）。
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


_NORM = (
    "GB/T 41019-2021（厂区布置一般要求，条号待核对）；"
    "docs/norms/mine_water_input.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_input.freeboard_band",
        expression="freeboard >= factor.mine_input.freeboard.min",
        source=f"{_NORM}；KI-F7 超高校核带（factor.mine_input.freeboard.min）",
        severity="WARN",
    ),
)
