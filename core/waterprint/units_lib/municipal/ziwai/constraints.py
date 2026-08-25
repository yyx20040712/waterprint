"""紫外消毒约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  四表校核带（docs/norms/ziwai.md ZW-F2/F3/F9）+ data/coefficients 0.3.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】两条校核带（渠内流速 0.3~0.6 m3/s/有效接触时间 5~10 s）
#   数值真源=factor.ziwai.*（data 包 0.3.0，M2b1 四单元系数批）——
#   本文件零数值字面量，表达式按键引用。ZW-F11 灯管淹没校核
#   （h_submerge ≥ 0）为结果对常数零比较、无 data 包键——仅 compute
#   warnings 承载不在此声明。单渠事故 0.78 m/s 超流速带为四表注记
#   （R1 微修后口径——运行时只校核实际过流态），不构成约束条目。
#   粪大肠出水 ≤1000 个/L 为出水标准数据条目（标准值非系数键），
#   不在本表声明。
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


_HB = (
    "给水排水设计手册（第 5 册 城镇排水）紫外渠道设计；"
    "docs/norms/ziwai.md 起草表 2026-08-25，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="ziwai.velocity_band",
        expression=(
            "v_channel_act >= factor.ziwai.velocity_band.min"
            " and v_channel_act <= factor.ziwai.velocity_band.max"
        ),
        source=(
            f"{_HB}；ZW-F3 带宽（factor.ziwai.velocity_band.*，实际过流态——"
            "单渠事故 0.78 m/s 超带为表内注记非运行时校核）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="ziwai.t_exp_band",
        expression=(
            "t_exp >= factor.ziwai.t_exp_band.min"
            " and t_exp <= factor.ziwai.t_exp_band.max"
        ),
        source=f"{_HB}；ZW-F9 带宽（factor.ziwai.t_exp_band.*，剂量=强度×时间）",
        severity="WARN",
    ),
)
