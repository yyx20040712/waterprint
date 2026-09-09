"""FD 可行域护栏假设伴生件（PD4）：solution.design_map.max_points 单键声明。

输入:  类注入（Assumption/TuningImpact——assumptions 主件装配点传入）
输出:  design_map_entries(…) → FD 假设条目元组（主件 DEFAULT_ASSUMPTIONS 解包）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FD 批 PD4 落位 2026-09-09 会话 n+28 终裁；U1 亲核闭合）
#
# 【定位】assumptions.py 恰 500 行余量 0（E 冻结结论4）——FD 新键落
#   主件即破行数硬门禁（check_file_budgets 无豁免清单 §13.7：真有
#   理由超标→拆文件）。本件=伴生件（app_assembly 先例第二例的 registry
#   同构）：持有 FD 键的 Assumption 声明，主件 +import +解包两行装配。
#
# 【防环形态】依赖单向 assumptions→本件（import-linter 同层内边，
#   Kahn 无环门禁约束）；本件**零 waterprint import**——Assumption/
#   TuningImpact 经 design_map_entries 参数注入（类注入防环；TypeVar
#   类型面，mypy 零 Any 逃逸）。伴生件零反向依赖=app_assembly 规格
#   头【依赖足迹】同款纪律。
#
# 【键语义】solution.design_map.max_points：可行域引导稠密扫描总点数
#   上限（各轴 points 之积；解析期拦截——先于 build_grid，P1-5）。
#   与 solution.grid.base_per_dim（枚举护栏）独立不共用（PD4）。
#   2500=50×50——依据=批 13 实测最重单元全枚举 3.83s<5s 预算，2500
#   点体量小一个数量级以上；50×50 对 2D 热力图视觉分辨率足够。
#   default 待专家追认（.workflow/pending-domain-expert.md §31.4）。
#
# 【测试要求】主件 DEFAULT_ASSUMPTIONS 含本键（键数 21→22）；覆盖值
#   经 assumption() 正门生效；0/负覆盖值由 solution/design_map.py 消费
#   侧域守卫拒（max_points>=1——挂账硬化裁量，本批兑现）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from typing import Final

_SOURCE: Final[str] = (
    "FD 终裁 PD4（总控 GLM-5.3 会话 n+28，2026-09-09）——2500=50×50；"
    "待专家追认（.workflow/pending-domain-expert.md §31.4）"
)
_NOTE: Final[str] = (
    "可行域引导（design_map）稠密扫描总点数上限——各轴 points 之积，"
    "解析期拦截（先于 build_grid 生成，P1-5）；与 solution.grid."
    "base_per_dim 枚举护栏独立不共用；solution/design_map.py 消费"
    "（含 >=1 域守卫），数值真源唯一在此（GR-15）"
)
_TUNING: Final[str] = "增大上限→扫描更密但同步耗时上升，减小→护栏更严"


def design_map_entries[T](
    assumption: Callable[..., T], tuning_impact: Callable[..., object]
) -> tuple[T, ...]:
    """FD 假设条目（类注入防环——主件装配点传 Assumption/TuningImpact）。"""
    return (
        assumption(
            "solution.design_map.max_points",
            2500.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE,
            tuning_impact(_TUNING, ()),
        ),
    )
