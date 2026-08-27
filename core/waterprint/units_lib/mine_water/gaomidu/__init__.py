"""高密沉淀单元包根：白名单导出（mine_water_gaomidu）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_gaomidu"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_gaomidu（迁移交叉对照，非依据）。
# 【工艺位置】上游：mine_water_cifenli 磁分离；下游：
#   mine_water_vxinglvchi V 型滤池（保安沉淀段——磁分离段已载大部分
#   SS，快混（PAC）+机械絮凝（PAM 磁絮体熟化延续）+斜管沉淀/清水区
#   +泥渣浓缩区直接外排）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 KG-F1~F10 与参数数值真源=docs/norms/mine_water_gaomidu.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（removal.mine_gaomidu.{ss,cod}——保安沉淀段建双
#     指标键；BOD5 全线不建键）；
#   - 导出面=UNIT_ID/make_unit/manifest 三名（终裁 canonical 三名
#     口径，units_lib/__init__ D6 注记）。
# 【物理隔离】与市政同名包 municipal/gaomidu（ADR-008 ③ Densadeg
#   污泥回流型）零 import 零参数复用（§14.3）：本表无污泥回流键族、
#   低负荷 5~8 档（市政 10~20）——同 ID 不同型构筑物，键空间经
#   mine_ 限定物理隔离。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.gaomidu.compute import make_unit
from waterprint.units_lib.mine_water.gaomidu.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
