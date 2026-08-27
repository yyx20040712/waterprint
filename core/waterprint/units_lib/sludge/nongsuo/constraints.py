"""污泥浓缩约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_nongsuo.md NS-F1/F2/F6/F8）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】四条校核带（固体负荷带 30~60 kgDS/(m²·d)——实际负荷
#   校核 NS-F6、参数带同名；浓缩时间带 12~24 h；有效水深带 3.0~5.0
#   m；底流含水率带 0.95~0.98）数值真源=factor.nongsuo.*（data 包
#   0.6.0）——本文件零数值字面量，表达式按键引用。截留率/超高/
#   壁厚系数为计算入参键非校核带。
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
    "GB 50014-2021 §8（污泥章——重力浓缩，条号待核对）；"
    "docs/norms/sludge_nongsuo.md 起草表 2026-08-27，待追认"
)
_HB5 = (
    "给水排水设计手册（第 5 册 城镇排水）污泥浓缩章；"
    "docs/norms/sludge_nongsuo.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_nongsuo.solid_load_band",
        expression=(
            "q_solid_act >= factor.nongsuo.solid_load_band.min"
            " and q_solid_act <= factor.nongsuo.solid_load_band.max"
        ),
        source=(
            f"{_GB}；NS-F6 带宽（factor.nongsuo.solid_load_band.*——"
            "实际固体负荷校核；参数 q_solid 同带）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_nongsuo.time_band",
        expression=(
            "t_thicken >= factor.nongsuo.time_band.min"
            " and t_thicken <= factor.nongsuo.time_band.max"
        ),
        source=f"{_GB}；NS-F2 带宽（factor.nongsuo.time_band.*——浓缩时间参数带）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_nongsuo.depth_band",
        expression=(
            "h_eff >= factor.nongsuo.depth_band.min"
            " and h_eff <= factor.nongsuo.depth_band.max"
        ),
        source=f"{_GB}；NS-F2 带宽（factor.nongsuo.depth_band.*——有效水深参数带）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_nongsuo.moisture_out_band",
        expression=(
            "p_out >= factor.nongsuo.moisture_out_band.min"
            " and p_out <= factor.nongsuo.moisture_out_band.max"
        ),
        source=(
            f"{_HB5}；NS-F8 带宽（factor.nongsuo.moisture_out_band.*——"
            "底流含水率参数带；引文 97~98% 档归追认裁定）"
        ),
        severity="WARN",
    ),
)
