"""配水井约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/conveyance_peishuijing.md 参数档）
       + data/coefficients 0.7.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】四条带全经 factor.peishuijing.*（data 包 0.7.0）——
#   本文件零数值字面量，表达式按键引用；k_uneven+带为数据包自校面
#   （无 dims/参数消费位，hebing yield.y_band 同口径不在此声明）；
#   elevation_loss 键归高程链子系统（后续批），本文件不声明无依据约束。
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


_HB3 = "《给水排水设计手册（第 3 册 城镇给水）》配水设施章"
_HB5 = "《给水排水设计手册（第 5 册 城镇排水）》泵站章"
_TABLE = (
    "docs/norms/conveyance_peishuijing.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="conveyance_peishuijing.v_band",
        expression=(
            "v_act >= factor.peishuijing.v_band.min"
            " and v_act <= factor.peishuijing.v_band.max"
        ),
        source=f"{_HB3}（出流口实际流速带 {_TABLE}；越带出 WARN 提示）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_peishuijing.head_band",
        expression=(
            "h_head >= factor.peishuijing.head_band.min"
            " and h_head <= factor.peishuijing.head_band.max"
        ),
        source=(
            f"{_HB3}（配水孔口作用水头带 {_TABLE}；水头过小对施工高差"
            "敏感——配水均匀性不利，越带出 WARN 提示）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_peishuijing.v_channel_band",
        expression=(
            "v_channel >= factor.peishuijing.v_channel_band.min"
            " and v_channel <= factor.peishuijing.v_channel_band.max"
        ),
        source=f"{_HB5}（井室断面流速带 {_TABLE}；越带出 WARN 提示）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_peishuijing.depth_band",
        expression=(
            "h_well >= factor.peishuijing.depth_band.min"
            " and h_well <= factor.peishuijing.depth_band.max"
        ),
        source=f"{_HB5}（集水设施有效水深带 {_TABLE}；越带出 WARN 提示）",
        severity="WARN",
    ),
)
