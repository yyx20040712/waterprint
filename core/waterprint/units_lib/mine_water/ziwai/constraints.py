"""紫外消毒约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_ziwai.md KZ-F3/KZ-F4/KZ-F8）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三条校核带（渠内流速带 0.05~0.7 m/s 宽下限——低流量
#   检修工况可贴限以剂量达标为准/254 nm 穿透率带 60~70 % 百分数口径
#   ——滤后清矿井水高于市政 55~65 档/实算剂量 ≥ 设计剂量——排数
#   ceil 结构保证的合格面声明）数值真源=factor.mine_ziwai.*（data 包
#   0.5.0）——本文件零数值字面量，表达式按键引用。KZ-F10 渠内公式
#   水损与 elevation_loss 经验键双轨语义（公式值走校核面/经验值走
#   高程链——表追认点 14），loss_min 构造下限已内嵌公式不经约束面。
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


_GT = (
    "GB/T 31392-2022（回用消毒剂量，条号待核对）；"
    "docs/norms/mine_water_ziwai.md 起草表 2026-08-27，待追认"
)
_HB = (
    "给水排水设计手册（第 3 册 城镇给水）紫外渠内流速/穿透率常用带；"
    "docs/norms/mine_water_ziwai.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_ziwai.velocity_band",
        expression=(
            "v_ch >= factor.mine_ziwai.velocity_band.min"
            " and v_ch <= factor.mine_ziwai.velocity_band.max"
        ),
        source=(
            f"{_HB}；KZ-F3 带宽（factor.mine_ziwai.velocity_band.*——"
            "宽下限 0.05，低流量检修工况可贴限以剂量达标为准）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ziwai.t254_band",
        expression=(
            "t254 >= factor.mine_ziwai.t254_band.min"
            " and t254 <= factor.mine_ziwai.t254_band.max"
        ),
        source=(
            f"{_HB}；KZ-F4 带宽（factor.mine_ziwai.t254_band.*——百分数"
            "存储口径 60/70，滤后清矿井水高于市政 55~65 档）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_ziwai.dose_check",
        expression="dose_act >= factor.mine_ziwai.dose",
        source=(
            f"{_GT}；KZ-F8 合格面（factor.mine_ziwai.dose——实算剂量"
            "≥设计剂量，排数 ceil 结构保证）"
        ),
        severity="WARN",
    ),
)
