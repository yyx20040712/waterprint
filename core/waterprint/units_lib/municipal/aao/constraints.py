"""AAO 生物池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/aao.md AO-F1/F3/F5/F8/F13/F14+参数档）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】七条校核带（Ns 0.05~0.15/MLSS 3500~4500/厌氧 HRT 1~2/
#   缺氧 HRT 2~4/好氧泥龄 11~23/外回流 0.5~1.0/内回流 1.0~3.0）数值
#   真源=factor.aao.*（data 包 0.2.0）——本文件零数值字面量，表达式
#   按键引用。泥龄带绑定好氧泥龄判断口径（全池口径备考注记见三表
#   参数档——待领域专家追认）。
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


_GB = "GB 50014-2021 §7.6（docs/norms/aao.md 起草表 2026-08-25，待追认）"
_HB = "给水排水设计手册（第 5 册 城镇排水）；docs/norms/aao.md 起草表 2026-08-25，待追认"

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="aao.ns_band",
        expression="ns >= factor.aao.ns_band.min and ns <= factor.aao.ns_band.max",
        source=f"{_GB}；{_HB}；AO-F1 参数带宽（factor.aao.ns_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="aao.mlss_band",
        expression="x_mlss >= factor.aao.mlss_band.min and x_mlss <= factor.aao.mlss_band.max",
        source=f"{_GB}；AO-F1 参数带宽（factor.aao.mlss_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="aao.hrt_anaerobic_band",
        expression=(
            "t_p >= factor.aao.hrt_anaerobic_band.min"
            " and t_p <= factor.aao.hrt_anaerobic_band.max"
        ),
        source="GB 50014-2021 §7.6.39（厌氧区 HRT 1~2h）；AO-F3 参数带宽"
        "（factor.aao.hrt_anaerobic_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="aao.hrt_anoxic_band",
        expression=(
            "t_n >= factor.aao.hrt_anoxic_band.min"
            " and t_n <= factor.aao.hrt_anoxic_band.max"
        ),
        source=f"{_HB}；AO-F5 带宽（factor.aao.hrt_anoxic_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="aao.sludge_age_band",
        expression=(
            "theta_c >= factor.aao.sludge_age_band.min"
            " and theta_c <= factor.aao.sludge_age_band.max"
        ),
        source=(
            f"{_GB}（AAO 泥龄 11~23d）；AO-F8 带宽（factor.aao.sludge_age_band.*；"
            "好氧泥龄判断口径，全池口径备考注记待领域专家追认）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="aao.r_external_band",
        expression=(
            "r_external >= factor.aao.r_external_band.min"
            " and r_external <= factor.aao.r_external_band.max"
        ),
        source=f"{_HB}；AO-F13 参数带宽（factor.aao.r_external_band.*；与二沉池联动）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="aao.r_internal_band",
        expression=(
            "r_internal >= factor.aao.r_internal_band.min"
            " and r_internal <= factor.aao.r_internal_band.max"
        ),
        source=f"{_HB}；AO-F14 参数带宽（factor.aao.r_internal_band.*）",
        severity="WARN",
    ),
)
