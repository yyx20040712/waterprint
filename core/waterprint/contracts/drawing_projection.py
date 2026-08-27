"""出图取数对照契约聚合正门（UF-32 方案②）：分线表聚合——市政 13+矿井 8（M3D1）+污泥/输送后续批。

输入:  分线表（drawing_projection_municipal 13 条目 + drawing_projection_mine
       矿井条目）+ drawing_projection_types 类型面
输出:  PROJECTION_TABLE（全单元聚合只读映射——geometry/drafting/elevation/
       app_enumeration 消费方 import 路径不变）+ UnitProjection /
       ProfileStation / ElevationProfile 再导出
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3D1 D1 重写为聚合正门——原 13 条目与三类型已分线迁出，
#   语义零变更；对账锁定测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   PROJECTION_TABLE: Final[Mapping[str, UnitProjection]] =
#       MappingProxyType({**MUNICIPAL_PROJECTIONS, **MINE_PROJECTIONS})
#       ——32 单元分线聚合：市政 13+矿井 8（本批）+污泥/输送随对应批次
#       扩入各自分线文件，本正门公式不动。
#   UnitProjection / ProfileStation / ElevationProfile：类型面再导出
#       （__all__ 四符号不变——消费方零改动，宪法 §2 拆分正解=伴生件
#       先例 app.py→app_enumeration.py：经正门保持单入口）。
#
# 【行为规格】
#   R1 聚合无静默覆盖：分线键集两两不相交 + 并集==PROJECTION_TABLE
#      键集（test_line_sets_disjoint 机器守卫——后批扩线越线即红）。
#   R2 分线职责（一文件一主概念）：表条目随业务线归分线文件；类型
#      独占 types 文件；本文件只做聚合与再导出，零表内容。
#   R3~R5 表覆盖/五类不静默/量纲列/纯声明面等规则随分线表文件规格
#      （municipal/mine 各自头注承载——对账测试按本正门全量断言）。
#
# 【禁止事项】本文件不得新增表条目或类型定义（聚合面专用）；不得
#   import units_lib 或任何 L2+ 层（L0 准入类别①，GR-36）。
#
# 【测试要求】tests/contracts/test_drawing_projection.py：21 单元
#   golden 实跑键集对账 + DimKey 合法性 + 分线键集 disjoint。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；重写计划 §10.2/
#   §10.5/§12.5/§13.6；M3D1 简报 D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from waterprint.contracts.drawing_projection_mine import MINE_PROJECTIONS
from waterprint.contracts.drawing_projection_municipal import (
    MUNICIPAL_PROJECTIONS,
)
from waterprint.contracts.drawing_projection_types import (
    ElevationProfile,
    ProfileStation,
    UnitProjection,
)

__all__ = [
    "PROJECTION_TABLE",
    "ElevationProfile",
    "ProfileStation",
    "UnitProjection",
]

PROJECTION_TABLE: Final[Mapping[str, UnitProjection]] = MappingProxyType({
    **MUNICIPAL_PROJECTIONS,
    **MINE_PROJECTIONS,
})
