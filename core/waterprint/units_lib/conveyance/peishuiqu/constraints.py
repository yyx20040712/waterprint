"""配水渠约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/conveyance_peishuiqu.md 参数档）
       + data/coefficients 0.7.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三条带全经 factor.peishuiqu.*（data 包 0.7.0）——
#   本文件零数值字面量，表达式按键引用；k_uneven+带为数据包自校面
#   （hebing yield.y_band 同口径不在此声明）；m_weir 单值键为堰流
#   系数自校面；elevation_loss 键归高程链子系统（后续批），本文件
#   不声明无依据约束。
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


_GB4 = "GB 50014-2021 §4（渠道设计流速，条号随追认核对）"
_GB4V = "GB 50014-2021 §4（最小流速防淤积，条号随追认核对）"
_HB3 = "《给水排水设计手册（第 3 册 城镇给水）》配水设施章"
_TABLE = (
    "docs/norms/conveyance_peishuiqu.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="conveyance_peishuiqu.v_channel_band",
        expression=(
            "v_channel >= factor.peishuiqu.v_channel_band.min"
            " and v_channel <= factor.peishuiqu.v_channel_band.max"
        ),
        source=f"{_GB4}；{_HB3}（渠内设计流速带 {_TABLE}；越带出 WARN 提示）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_peishuiqu.h_weir_band",
        expression=(
            "h_weir >= factor.peishuiqu.h_weir_band.min"
            " and h_weir <= factor.peishuiqu.h_weir_band.max"
        ),
        source=(
            f"{_HB3}（堰顶水头带 {_TABLE}；水头过小对堰顶施工高差敏感"
            "——配水均匀性不利，越带出 WARN 提示）"
        ),
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_peishuiqu.v_end_band",
        expression=(
            "v_end >= factor.peishuiqu.v_end_band.min"
            " and v_end <= factor.peishuiqu.v_end_band.max"
        ),
        source=f"{_GB4V}（渠末段流速带 {_TABLE}；低于下限=淤积风险，越带出 WARN 提示）",
        severity="WARN",
    ),
)
