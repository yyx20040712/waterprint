"""紫外消毒单元包根：白名单导出（mine_water_ziwai）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_ziwai"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_ziwai（迁移交叉对照，非依据）。
# 【工艺位置】上游：mine_water_vxinglvchi V 型滤池；下游：回用/外排
#   （全厂末段——消毒对象为回用卫生指标 GB/T 31392-2022）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 KZ-F1~F11 与参数数值真源=docs/norms/mine_water_ziwai.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（removal.mine_ziwai.{ss,cod} 显式 0.0 穿流——
#     物理消毒无去除；BOD5 全线不建键）；
#   - 导出面=UNIT_ID/make_unit/manifest 三名（终裁 canonical 三名
#     口径，units_lib/__init__ D6 注记）。
# 【物理隔离】与市政同名包 municipal/ziwai（单灯处理量概算锚路线，
# 含 q_per_lamp/粪大肠键族）零 import 零参数复用——本表灯管布置
#   实算路线、T254 60~70 高档、含 f_fouling 结垢特征键（市政无），
#   键空间经 mine_ 限定物理隔离（§14.3）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.ziwai.compute import make_unit
from waterprint.units_lib.mine_water.ziwai.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
