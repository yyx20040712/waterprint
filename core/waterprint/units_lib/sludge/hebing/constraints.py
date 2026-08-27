"""污泥合并约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/sludge_hebing.md HB-F11）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】一条互校偏差上限（≤20 %）数值真源=factor.hebing.dev_band.max
#   （data 包 0.6.0，source=ADR-008 ④ 拍板值）——本文件零数值字面量，
#   表达式按键引用。产率 y/合成产率 Y/Kd 三带键为系数自校面（无 dims/
#   参数消费位——y_yield 经 factor.hebing.yield.y 单值键投影入算，带越
#   界归数据包追认批，不在此声明无依据约束）；dev_close 闭合差表载
#   "≈0 闭合（源表末位舍入）"无 data 包键——不造无依据键，仅表内注记。
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


_ADR = (
    "ADR-008（工艺计算方法路线④——经验产率法主线+机理互校已拍板，"
    "2026-08-22）；docs/norms/sludge_hebing.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="sludge_hebing.dev_band",
        expression="dev_pct <= factor.hebing.dev_band.max",
        source=(
            f"{_ADR}；HB-F11 互校偏差上限（factor.hebing.dev_band.max——"
            ">20% 出 WARN 提示核对 SS/BOD 比，出警告不阻断）"
        ),
        severity="WARN",
    ),
)
