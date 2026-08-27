"""矿井水线出图取数表（UF-32 方案②）：矿井单元冻结几何取数声明（分线表②）。

输入:  矿井单元 compute 实跑 dims 键全量（矿井链单点图实跑提取，
       2026-08-27 M3D1 实录 107 键）
输出:  MINE_PROJECTIONS（plan/section/primitive/counts/non_drawn 五类
       取数声明 + 每键量纲列——聚合正门 drawing_projection 消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3D1 D1 新建分线表②——条目面随 M3D1 D2 落表；对账锁定
#   测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   MINE_PROJECTIONS: Final[Mapping[str, UnitProjection]]  矿井水线
#       8 单元逐个声明（unit_id 前缀 mine_water_）
#
# 【行为规格】
#   R1 表覆盖=单元 dims 键全量：plan∪section∪primitive∪counts∪non_drawn
#      == 该单元 compute 实际 dims 输出键集（对账测试以矿井链单点图
#      实跑为证）；non_drawn 与四类取数不相交（校核量不上图）。
#   R2 五类语义不静默：每键归入至少一类（禁遗漏）；plan/primitive
#      重叠合法（取数面非互斥分区）。
#   R3 dim_of 逐键合法：全部 ∈ DimKey 枚举；量纲起草依据=矿井各包
#      manifest FormulaSpec output_dim（KI/KT/KC/KN/KS/KG/KV/KZ 族）
#      与市政线同名键先例——AI 起草待领域专家追认。
#   R5 只读消费 dims 键名（字符串），不 import units_lib、不做任何
#      计算——纯声明面（L0 准入类别①，GR-36）。
#
# 【起草口径】分类原则=几何上图量入取数类（plan/section/primitive/
#   counts），校核/过程/衡算量入 non_drawn；未被 plan_view v1 消费的
#   键亦可入 plan_keys 声明面（approach_width/outlet_width 市政先例）；
#   对账测试是覆盖最终裁决（缺键/多键即红）。
#
# 【禁止事项】不得出现数值字面量（纯键名映射+量纲枚举）；不得
#   import units_lib 或任何 L2+ 层。
#
# 【测试要求】tests/contracts/test_drawing_projection.py：矿井 8 单元
#   链式单点图实跑键集对账 + DimKey 合法性 + 分线键集 disjoint。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；数据策略 v2；
#   M3D1 简报 D1/D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from waterprint.contracts.drawing_projection_types import UnitProjection

__all__ = ["MINE_PROJECTIONS"]

# ── 矿井水线 8 单元取数表（M3D1 D2 本批落表；AI 起草待追认）────
MINE_PROJECTIONS: Final[Mapping[str, UnitProjection]] = MappingProxyType({})
