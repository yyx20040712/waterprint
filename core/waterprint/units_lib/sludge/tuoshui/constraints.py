"""污泥脱水约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_tuoshui.md TU-F1/TU-F6）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】两条校核带（PAM 投加量带 2~8 g/kgDS、泥饼含水率带
#   0.75~0.80）数值真源=factor.tuoshui.*（data 包 0.6.0）——本文件
#   零数值字面量，表达式按键引用。回收率/带式·离心单机容量为计算
#   入参键非校核带（机型档选择面经 machine_type grid 承载）。
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
    "GB 50014-2021 §8（污泥章——机械脱水，条号待核对）；"
    "docs/norms/sludge_tuoshui.md 起草表 2026-08-27，待追认"
)
_HB5 = (
    "给水排水设计手册（第 5 册 城镇排水）污泥脱水章（阳离子 PAM 常用带）；"
    "docs/norms/sludge_tuoshui.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_tuoshui.dose_pam_band",
        expression=(
            "dose_pam >= factor.tuoshui.dose_pam_band.min"
            " and dose_pam <= factor.tuoshui.dose_pam_band.max"
        ),
        source=f"{_HB5}；TU-F1 带宽（factor.tuoshui.dose_pam_band.*——带式取 4/离心档取 3）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_tuoshui.cake_moisture_band",
        expression=(
            "p_cake >= factor.tuoshui.cake_moisture_band.min"
            " and p_cake <= factor.tuoshui.cake_moisture_band.max"
        ),
        source=(
            f"{_GB}；TU-F6 带宽（factor.tuoshui.cake_moisture_band.*——"
            "机械脱水常用带 75~80%，过深脱水非机械档）"
        ),
        severity="WARN",
    ),
)
