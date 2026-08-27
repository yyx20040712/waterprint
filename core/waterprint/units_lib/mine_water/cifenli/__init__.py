"""磁分离单元包根：白名单导出（mine_water_cifenli）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_cifenli"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_cifenli（迁移交叉对照，非依据）。
# 【工艺位置】上游：mine_water_ningjiao 混凝反应池；下游：
#   mine_water_gaomidu 高密沉淀（磁絮体（煤粉+磁种）磁盘截留；
#   磁种回收循环回流 ningjiao 投加点——净耗衡算见 KS-F8）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 KS-F1~F8 与参数数值真源=docs/norms/mine_water_cifenli.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（removal.mine_cifenli.{ss,cod}——磁絮体分离段建
#     双指标键；BOD5 全线不建键）；
#   - 导出面=UNIT_ID/make_unit/manifest 三名（终裁 canonical 三名
#     口径，units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.cifenli.compute import make_unit
from waterprint.units_lib.mine_water.cifenli.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
