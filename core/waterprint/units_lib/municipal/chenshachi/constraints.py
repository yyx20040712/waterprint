"""旋流沉砂池约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/chenshachi.md CS-F2/F3/F4/F6）+ data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】四条校核带（表面负荷 150~200/有效水深 1.0~2.0/径深比
#   2.0~2.5/停留时间 25~60）数值真源=factor.chenshachi.*_band（data 包
#   0.1.0）——本文件零数值字面量，表达式按键引用。三表另两条校核
#   （h渠≥0.2 m、B渠/h渠 带 1.0~3.0）无 data 包键——挂账不声明。
# 【矛盾 3 挂账】mod.json 参数 t min=30 与停留时间校核带 25~60 不一致
#   ——"待领域专家裁定"（三表 CS-F6 行注记逐字保留）。
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


_NORM = "GB 50014-2021 §6.4（条文号待核对原文；docs/norms/chenshachi.md 签字表）"

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="chenshachi.surface_load_band",
        expression=(
            "q_surf >= factor.chenshachi.surface_load_band.min"
            " and q_surf <= factor.chenshachi.surface_load_band.max"
        ),
        source=f"{_NORM}；CS-F2 带宽（factor.chenshachi.surface_load_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="chenshachi.h2_band",
        expression=("h2 >= factor.chenshachi.h2_band.min and h2 <= factor.chenshachi.h2_band.max"),
        source=f"{_NORM}；CS-F3 带宽（factor.chenshachi.h2_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="chenshachi.ratio_dh2_band",
        expression=(
            "ratio_dh2 >= factor.chenshachi.ratio_dh2_band.min"
            " and ratio_dh2 <= factor.chenshachi.ratio_dh2_band.max"
        ),
        source=f"{_NORM}；CS-F4 带宽（factor.chenshachi.ratio_dh2_band.*）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="chenshachi.retention_band",
        expression=(
            "t_actual >= factor.chenshachi.retention_band.min"
            " and t_actual <= factor.chenshachi.retention_band.max"
        ),
        source=(
            f"{_NORM}；CS-F6 带宽（factor.chenshachi.retention_band.*；"
            "mod.json t min=30 与带 25~60 不一致——待领域专家裁定）"
        ),
        severity="WARN",
    ),
)
