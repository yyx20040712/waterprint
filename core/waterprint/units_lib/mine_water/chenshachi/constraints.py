"""平流沉砂池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_chenshachi.md KC-F1/F3/F4/F8）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】五条校核带（实际水平流速 0.15~0.30/停留 30~60/有效
#   水深 0.4~1.2/单格宽下限 ≥0.6/堰负荷 ≤10）数值真源=
#   factor.mine_chenshachi.*（data 包 0.5.0）——本文件零数值字面量，
#   表达式按键引用。与市政同名包（旋流型表面负荷 150~200 口径）
#   带系独立起草——平流型主控参数面（表边界差异节）。
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
    "GB/T 41019-2021（矿井水处理工艺——预处理除砂，条号待核对）；"
    "docs/norms/mine_water_chenshachi.md 起草表 2026-08-27，待追认"
)
_HB = (
    "给水排水设计手册（第 5 册 城镇排水）平流沉砂池水平流速/停留"
    "时间/砂斗常用带；docs/norms/mine_water_chenshachi.md 起草表"
    " 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_chenshachi.velocity_band",
        expression=(
            "v_h_act >= factor.mine_chenshachi.velocity_band.min"
            " and v_h_act <= factor.mine_chenshachi.velocity_band.max"
        ),
        source=f"{_GB}；{_HB}；KC-F4 带宽（factor.mine_chenshachi.velocity_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_chenshachi.retention_band",
        expression=(
            "t_stay >= factor.mine_chenshachi.retention_band.min"
            " and t_stay <= factor.mine_chenshachi.retention_band.max"
        ),
        source=f"{_GB}；{_HB}；KC-F1 带宽（factor.mine_chenshachi.retention_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_chenshachi.depth_band",
        expression=(
            "h2 >= factor.mine_chenshachi.depth_band.min"
            " and h2 <= factor.mine_chenshachi.depth_band.max"
        ),
        source=f"{_HB}；KC-F3 带宽（factor.mine_chenshachi.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_chenshachi.cell_width",
        expression="b_raw >= factor.mine_chenshachi.cell_width.min",
        source=(
            f"{_HB}；KC-F3 单格宽下限"
            "（factor.mine_chenshachi.cell_width.min，0.1 m 档取整前校核）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_chenshachi.weir_load",
        expression="q_weir <= factor.mine_chenshachi.weir_load.max",
        source=f"{_HB}；KC-F8 堰负荷上限（factor.mine_chenshachi.weir_load.max）",
        severity="WARN",
    ),
)
