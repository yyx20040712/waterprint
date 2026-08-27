"""集水井约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/conveyance_jishuijing.md 参数档）
       + data/coefficients 0.7.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三条带全经 factor.jishuijing.*（data 包 0.7.0）——
#   本文件零数值字面量，表达式按键引用；elevation_loss 键归高程链
#   子系统（后续批），本文件不声明无依据约束。
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


_GB61 = (
    "GB 50014-2021 §6.1（集水池容积参照口径，条号随追认核对）；"
    "给水排水设计手册（第 5 册 城镇排水）泵站章"
)
_HB = "给水排水设计手册（第 5 册 城镇排水）"
_TABLE = (
    "docs/norms/conveyance_jishuijing.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="conveyance_jishuijing.t_band",
        expression=(
            "t_well >= factor.jishuijing.t_band.min"
            " and t_well <= factor.jishuijing.t_band.max"
        ),
        source=f"{_GB61}（汇流停留带 {_TABLE}；越带出 WARN 提示——出警告不阻断）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_jishuijing.depth_band",
        expression=(
            "h_well >= factor.jishuijing.depth_band.min"
            " and h_well <= factor.jishuijing.depth_band.max"
        ),
        source=f"{_HB}泵站章（集水设施有效水深带 {_TABLE}；越带出 WARN 提示）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="conveyance_jishuijing.d_band",
        expression=(
            "d >= factor.jishuijing.d_band.min"
            " and d <= factor.jishuijing.d_band.max"
        ),
        source=(
            f"{_HB}圆形集水井构造常用档（井径校核带 {_TABLE}；越带出 WARN"
            " 提示——超上限宜分座或改矩形）"
        ),
        severity="WARN",
    ),
)
