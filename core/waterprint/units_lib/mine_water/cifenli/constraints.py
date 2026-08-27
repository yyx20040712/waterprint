"""磁分离约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  手算表校核带（docs/norms/mine_water_cifenli.md KS-F3/KS-F5）
       + data/coefficients 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段与 factor 键限值比较）/
#   source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】两条校核带（表面负荷带 20~40 m³/(m²·h)/盘转速上限
#   3 rpm）数值真源=factor.mine_cifenli.*（data 包 0.5.0）——本文件
#   零数值字面量，表达式按键引用。盘缘线速度 0.3 m/s 为转速键折算
#   口径不另设键；流道停留/流速两选型校核键不在此声明（流道几何
#   归厂商样本——表"其他数据键"原文）；磁种回收率/磁泥含水率/密度
#   带无 data 包键——不造无依据键，仅表内注记（待追认）。
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
    "GB/T 41019-2021（磁加载分离表面负荷/设备构造，条号待核对）；"
    "docs/norms/mine_water_cifenli.md 起草表 2026-08-27，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="mine_water_cifenli.surface_load_band",
        expression=(
            "q_surf >= factor.mine_cifenli.surface_load_band.min"
            " and q_surf <= factor.mine_cifenli.surface_load_band.max"
        ),
        source=f"{_GB}；KS-F3 带宽（factor.mine_cifenli.surface_load_band.*——主控参数）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="mine_water_cifenli.disk_speed",
        expression="omega <= factor.mine_cifenli.disk.speed_max",
        source=(
            f"{_GB}；KS-F5 转速上限（factor.mine_cifenli.disk.speed_max——"
            "盘缘线速度 ≤0.3 m/s 折算口径）"
        ),
        severity="WARN",
    ),
)
