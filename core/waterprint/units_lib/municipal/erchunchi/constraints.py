"""辐流二沉池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/erchunchi.md EC-F2/F4/F8/F9/F11/F14+参数档+校核 HRT 行）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】六条校核带（清水表面负荷 0.6~1.5/固体面积负荷 ≤150[中心
#   进水档；周进周出 ≤200 键在 data 包备用]/堰负荷 ≤1.7/池边水深 2.5~3.5/
#   Xr 6000~12000[0.2.1 新键]/HRT 1.5~4[0.2.1 新键]）数值真源=
#   factor.erchunchi.*（data 包 0.2.0/0.2.1）——本文件零数值字面量。
# 【追认口径注记】堰负荷键绑定双圈堰构造（L=2πD，堰圈口径与 chuchenchi
#   表不对称系起草取舍——待领域专家追认）。
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


_GB = "GB 50014-2021 表 7.5.1+§7.6.15/§7.6.16（docs/norms/erchunchi.md 起草表 2026-08-25，待追认）"
_HB = "给水排水设计手册（第 5 册 城镇排水）；docs/norms/erchunchi.md 起草表 2026-08-25，待追认"

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="erchunchi.surface_load_band",
        expression=(
            "q_act >= factor.erchunchi.surface_load_band.min"
            " and q_act <= factor.erchunchi.surface_load_band.max"
        ),
        source=f"{_GB}；EC-F8 带宽（factor.erchunchi.surface_load_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="erchunchi.solid_load",
        expression="g_act <= factor.erchunchi.solid_load.center_inlet",
        source=(
            f"{_GB}；EC-F9 上限（factor.erchunchi.solid_load.center_inlet 中心进水档；"
            "周进周出档 .peripheral_inlet 键在 data 包备用）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="erchunchi.weir_load",
        expression="q_weir <= factor.erchunchi.weir_load.max",
        source=(
            "GB 50014-2021（沉淀池堰负荷，二沉档）；EC-F11 上限"
            "（factor.erchunchi.weir_load.max；双圈堰 L=2πD 口径待追认）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="erchunchi.depth_band",
        expression=(
            "h2 >= factor.erchunchi.depth_band.min"
            " and h2 <= factor.erchunchi.depth_band.max"
        ),
        source=f"{_HB}；EC-F14 参数带宽（factor.erchunchi.depth_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="erchunchi.x_r_band",
        expression="x_r >= factor.erchunchi.x_r_band.min and x_r <= factor.erchunchi.x_r_band.max",
        source=(
            f"{_HB}；EC-F10 带宽（factor.erchunchi.x_r_band.*，data 0.2.1 M2a2 前置键）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="erchunchi.hrt_band",
        expression=(
            "t_hrt >= factor.erchunchi.hrt_band.min"
            " and t_hrt <= factor.erchunchi.hrt_band.max"
        ),
        source=(
            f"{_HB}；主算例校核 HRT 行带宽"
            "（factor.erchunchi.hrt_band.*，data 0.2.1 M2a2 前置键）"
        ),
        severity="WARN",
    ),
)
