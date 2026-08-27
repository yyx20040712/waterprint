"""污泥干化约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_ganhua.md GH-F2/GH-F8）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】两条校核带（干化后含水率带 0.20~0.40——半干化档、
#   全干化 <0.20 归设备批；传热面积蒸发强度带 4~15 kg/(m²·h)）数值
#   真源=factor.ganhua.*（data 包 0.6.0）——本文件零数值字面量，
#   表达式按键引用。蒸发潜热/热效率/天然气热值为计算入参键非
#   校核带；GH-F5 质量守恒=代数恒等校核（差 0）无键不声明。
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
    "GB 50014-2021 §8（污泥章——干化后含水率档，条号待核对）；"
    "docs/norms/sludge_ganhua.md 起草表 2026-08-27，待追认"
)
_HB5 = (
    "给水排水设计手册（第 5 册 城镇排水）污泥干化章（间接式干化传热面"
    "蒸发强度带）；docs/norms/sludge_ganhua.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_ganhua.moisture_out_band",
        expression=(
            "p_out >= factor.ganhua.moisture_out_band.min"
            " and p_out <= factor.ganhua.moisture_out_band.max"
        ),
        source=(
            f"{_GB}；GH-F2~F4 带宽（factor.ganhua.moisture_out_band.*——"
            "半干化档 0.20~0.40，全干化 <0.20 归设备批）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_ganhua.evap_rate_band",
        expression=(
            "r_evap >= factor.ganhua.evap_rate_band.min"
            " and r_evap <= factor.ganhua.evap_rate_band.max"
        ),
        source=(
            f"{_HB5}；GH-F8 带宽（factor.ganhua.evap_rate_band.*——"
            "传热面积蒸发强度参数带）"
        ),
        severity="WARN",
    ),
)
