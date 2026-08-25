"""CASS 生物池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/cass.md CA-F3/F10/F18/F4）+ data/coefficients 0.4.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段或参数与 factor 键限值
#   比较）/ source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】五条校核带（污泥负荷 0.05~0.15/MLSS 3000~5000[SBR 变体
#   档]/泥龄 15~25 d/滗水深度 1.0~2.0 m/选择区 HRT 0.5~1.0 h）数值真源=
#   factor.cass.*（data 包 0.4.0，M2c 三单元系数批）——本文件零数值
#   字面量，表达式按键引用。时段和=周期不变性（CA-F13）为 compute 域拒
#   （business-logic §8 不变性，非建议带）不在此声明；滗水深度 ≤h2/3
#   上限由 CA-F6~F9 双控构造保证（max 取大后 h_draw≤h_draw_max 恒成立）
#   ——draw_band 仅承载滗水器能力带 1.0~2.0 m。
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
    "GB 50014-2021 §7.6（docs/norms/cass.md 起草表 2026-08-26，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》SBR/CASS 章常用带；"
    "docs/norms/cass.md 起草表 2026-08-26，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="cass.ns_band",
        expression="ns >= factor.cass.ns_band.min and ns <= factor.cass.ns_band.max",
        source=f"{_GB}；{_HB}；CA-F3 参数带（factor.cass.ns_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="cass.mlss_band",
        expression=(
            "x_mlss >= factor.cass.mlss_band.min"
            " and x_mlss <= factor.cass.mlss_band.max"
        ),
        source=f"{_HB}；CA-F3 参数带（factor.cass.mlss_band.*，SBR 变体档）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="cass.sludge_age_band",
        expression=(
            "theta_c >= factor.cass.sludge_age_band.min"
            " and theta_c <= factor.cass.sludge_age_band.max"
        ),
        source=f"{_HB}；CA-F18 带宽（factor.cass.sludge_age_band.*，主反应区口径）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="cass.draw_band",
        expression=(
            "h_draw >= factor.cass.draw_band.min"
            " and h_draw <= factor.cass.draw_band.max"
        ),
        source=(
            "business-logic §8 行 8；"
            f"{_HB}；CA-F10 带宽（factor.cass.draw_band.*，滗水器能力带——"
            "≤h2/3 上限由 CA-F6~F9 双控构造保证）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="cass.selector_band",
        expression=(
            "t_selector >= factor.cass.selector_band.min"
            " and t_selector <= factor.cass.selector_band.max"
        ),
        source=f"{_HB}；CA-F4 参数带（factor.cass.selector_band.*，生物选择区）",
        severity="WARN",
    ),
)
