"""污泥浓缩单元包根：白名单导出（sludge_nongsuo）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "sludge_nongsuo"；业务线：污泥处理线；
#   旧系统对应 mod：wuni_nongsuo（迁移交叉对照，非依据）。
# 【工艺位置】上游：sludge_bengzhan 污泥泵站；下游：sludge_xiaohua
#   污泥消化（主线）或 sludge_tuoshui 污泥脱水（无消化工艺直连——
#   structure-graph 骨架双出路口径）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 NS-F1~NS-F12 与参数数值真源=docs/norms/sludge_nongsuo.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.6.0 数据包（factor.nongsuo.* 裸短名 12 键；removal 零键）；
#   - sup 上清液回流口=端口声明先行（recycle=True，Q1 未裁默认关
#     ——business-logic §6；UF-11 Ruling ②）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.sludge.nongsuo.compute import make_unit
from waterprint.units_lib.sludge.nongsuo.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
