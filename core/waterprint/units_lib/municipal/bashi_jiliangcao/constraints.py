"""巴歇尔计量槽约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/bashi_jiliangcao.md BL-F2/F8）+ data/coefficients 0.4.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】两条校核带（选档水头适用带 hmin/hmax + 淹没度 ≤ scrit）
#   数值真源=factor.bashi_jiliangcao.flume.<档>.*（data 包 0.4.0，M2c
#   三单元系数批——B7 七档逐档录入）——本文件零数值字面量，表达式按
#   档引用；档位切换时各档表达式独立成立（选档档名=b075 主算例档）。
#   构造尺寸回归式（BL-F4~F6）与槽总长（BL-F7）为构造面非校核带，
#   不在此声明。
# ══════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from typing import final

from waterprint.units_lib.municipal.bashi_jiliangcao.manifest import GRADES


@dataclass(frozen=True)
@final
class ConstraintDecl:
    """单条约束声明：键 + 受限比较式 + 出处 + 级别（声明式，无数值）。"""

    key: str
    expression: str
    source: str
    severity: str


_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》量水堰槽章；"
    "docs/norms/bashi_jiliangcao.md 起草表 2026-08-26，待追认"
    "（CJ/T 3008.3-1993 正式文本核对归追认点——business-logic §10 Q3）"
)

_CONSTRAINTS: list[ConstraintDecl] = []
for _grade in GRADES:
    _CONSTRAINTS.append(
        ConstraintDecl(
            key=f"bashi_jiliangcao.ha_band.{_grade}",
            expression=(
                f"ha_design >= factor.bashi_jiliangcao.flume.{_grade}.hmin"
                f" and ha_design <= factor.bashi_jiliangcao.flume.{_grade}.hmax"
            ),
            source=f"{_HB}；BL-F2 本档水头适用带（flume.{_grade}.hmin/hmax）",
            severity="WARN",
        )
    )
    _CONSTRAINTS.append(
        ConstraintDecl(
            key=f"bashi_jiliangcao.submergence.{_grade}",
            expression=f"sigma <= factor.bashi_jiliangcao.flume.{_grade}.scrit",
            source=f"{_HB}；BL-F8 自由流判别（σ=Hb/Ha ≤ scrit，flume.{_grade}.scrit）",
            severity="WARN",
        )
    )

CONSTRAINTS: tuple[ConstraintDecl, ...] = tuple(_CONSTRAINTS)
