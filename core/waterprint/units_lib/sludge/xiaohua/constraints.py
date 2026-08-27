"""污泥消化约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_xiaohua.md XH-F2/F4/F5/F6）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】四条校核带（消化时间带 15~30 d、VS 降解率带 0.30~0.60、
#   产气率带 0.8~1.1 m³/kgVS——参数带；VS 容积负荷带 0.5~1.5
#   kgVS/(m³·d)——结果字段校核）数值真源=factor.xiaohua.*（data 包
#   0.6.0）——本文件零数值字面量，表达式按键引用。temp/f_vs/ratio_dh/
#   壁厚系数为计算入参键非校核带（temp 本批不消费——UF-09 注记）。
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
    "GB 50014-2021 §8（污泥章——消化时间/挥发分降解率/产气率，条号待"
    "核对）；docs/norms/sludge_xiaohua.md 起草表 2026-08-27，待追认"
)
_HB5 = (
    "给水排水设计手册（第 5 册 城镇排水）污泥消化章；"
    "docs/norms/sludge_xiaohua.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_xiaohua.time_band",
        expression=(
            "t_digest >= factor.xiaohua.time_band.min"
            " and t_digest <= factor.xiaohua.time_band.max"
        ),
        source=(
            f"{_GB}；XH-F2 带宽（factor.xiaohua.time_band.*——中温消化"
            "时间参数带，GB 中温 20~30 档注记归追认）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_xiaohua.eta_vs_band",
        expression=(
            "eta_vs >= factor.xiaohua.eta_vs_band.min"
            " and eta_vs <= factor.xiaohua.eta_vs_band.max"
        ),
        source=f"{_GB}；XH-F4 带宽（factor.xiaohua.eta_vs_band.*——VS 降解率参数带）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_xiaohua.biogas_rate_band",
        expression=(
            "r_biogas >= factor.xiaohua.biogas_rate_band.min"
            " and r_biogas <= factor.xiaohua.biogas_rate_band.max"
        ),
        source=f"{_GB}；XH-F5 带宽（factor.xiaohua.biogas_rate_band.*——产气率参数带）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="sludge_xiaohua.vs_load_band",
        expression=(
            "l_vs >= factor.xiaohua.vs_load_band.min"
            " and l_vs <= factor.xiaohua.vs_load_band.max"
        ),
        source=(
            f"{_HB5}；XH-F6 带宽（factor.xiaohua.vs_load_band.*——VS 容积"
            "负荷结果校核带）"
        ),
        severity="WARN",
    ),
)
