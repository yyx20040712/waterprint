"""V型滤池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  四表校核带（docs/norms/vxinglvchi.md XL-F2/F4/F8/F9/F16/F18）+ data/coefficients 0.3.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段或参数与 factor 键限值
#   比较）/ source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】六条校核带（正常滤速 7~10/强制滤速 11~13[单向上限口径]/
#   单格长宽比 2.0~3.0/滤层厚 1.2~1.5/砂上水深 1.2~1.5/过滤周期
#   24~48）数值真源=factor.vxinglvchi.*（data 包 0.3.0，M2b1 四单元
#   系数批）——本文件零数值字面量，表达式按键引用。强制滤速带
#   11~13 为典型带——校核按单向上限（≤max；四表算例 9.4626<11 注
#   "合格"：低于带下限=保守合格非越界）。XL-F17 反冲耗水率≤5% 无
#   data 包键且被 selfuse_coef 覆盖（四表注记）——dims 承载不在此
#   声明（追认点）。media.d10_band 为滤料选型注记（无计算面）不声明。
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
    "GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速）；"
    "docs/norms/vxinglvchi.md 起草表 2026-08-25，待追认"
)
_HB = (
    "给水排水设计手册（第 5 册 城镇排水）V 型滤池构造常用值；"
    "docs/norms/vxinglvchi.md 起草表 2026-08-25，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="vxinglvchi.v_filter_band",
        expression=(
            "v_filter_act >= factor.vxinglvchi.v_filter_band.min"
            " and v_filter_act <= factor.vxinglvchi.v_filter_band.max"
        ),
        source=f"{_GB}；XL-F8 带宽（factor.vxinglvchi.v_filter_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="vxinglvchi.v_forced_band",
        expression="v_forced_act <= factor.vxinglvchi.v_forced_band.max",
        source=(
            f"{_GB}；XL-F9 强制滤速单向上限（factor.vxinglvchi.v_forced_band.max；"
            "带 11~13 为典型带，低于下限=保守合格非越界）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="vxinglvchi.cell_ratio_lb_band",
        expression=(
            "ratio_lb >= factor.vxinglvchi.cell_ratio_lb_band.min"
            " and ratio_lb <= factor.vxinglvchi.cell_ratio_lb_band.max"
        ),
        source=f"{_HB}；XL-F4 带宽（factor.vxinglvchi.cell_ratio_lb_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="vxinglvchi.media.depth_band",
        expression=(
            "h_sand >= factor.vxinglvchi.media.depth_band.min"
            " and h_sand <= factor.vxinglvchi.media.depth_band.max"
        ),
        source=f"{_GB}；XL-F18 滤层厚带宽（factor.vxinglvchi.media.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="vxinglvchi.water_above_band",
        expression=(
            "h_water_above >= factor.vxinglvchi.water_above_band.min"
            " and h_water_above <= factor.vxinglvchi.water_above_band.max"
        ),
        source=f"{_HB}；XL-F18 砂上水深带宽（factor.vxinglvchi.water_above_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="vxinglvchi.cycle_band",
        expression=(
            "t_cycle >= factor.vxinglvchi.cycle_band.min"
            " and t_cycle <= factor.vxinglvchi.cycle_band.max"
        ),
        source=f"{_HB}；XL-F16 带宽（factor.vxinglvchi.cycle_band.*）",
        severity="WARN",
    ),
)
