"""V型滤池单元包根：白名单导出（mine_water_vxinglvchi）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_vxinglvchi"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_vxinglvchi（迁移交叉对照，非依据）。
# 【工艺位置】上游：mine_water_gaomidu 高密沉淀；下游：
#   mine_water_ziwai 紫外消毒（最终把关过滤——回用于消防/洗尘/
#   绿化等 GB/T 31392-2022 回用目标）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 KV-F1~F11 与参数数值真源=docs/norms/mine_water_vxinglvchi.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（removal.mine_vxinglvchi.{ss,cod}——深层过滤段建
#     双指标键；BOD5 全线不建键）；
#   - 导出面=UNIT_ID/make_unit/manifest 三名（终裁 canonical 三名
#     口径，units_lib/__init__ D6 注记）。
# 【物理隔离】与市政同名包 municipal/vxinglvchi（GB 50013-2018
#   §9.5 均质滤料 7~10 m/h 档）零 import 零参数复用——本表低滤速
#   4~6 m/h 精滤档、滤层 0.8~1.2 m（市政 1.2~1.5），键空间经
#   mine_ 限定物理隔离（§14.3）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.vxinglvchi.compute import make_unit
from waterprint.units_lib.mine_water.vxinglvchi.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
