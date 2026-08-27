"""矿井水调节池单元包根：白名单导出（mine_water_tiaojiechi）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_tiaojiechi"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_tiaojiechi（迁移交叉对照，非依据）。
# 【工艺位置】上游：mine_water_input 矿井水输入；下游：
#   mine_water_chenshachi 平流沉砂池。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 与市政同名包 municipal/tiaojiechi 零 import 零参数复用
#     （§14.3 物理隔离：hrt/depth/搅拌三带独立起草，键空间
#     factor.mine_tiaojiechi.* 经 mine_ 限定）；
#   - 公式 KT-F1~F12 与参数数值真源=docs/norms/mine_water_tiaojiechi.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（removal.mine_tiaojiechi.{ss,cod} 显式 0.0 穿流
#     ——纯均化主线，旧预沉 0.30 口径归追认点 1）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.tiaojiechi.compute import make_unit
from waterprint.units_lib.mine_water.tiaojiechi.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
