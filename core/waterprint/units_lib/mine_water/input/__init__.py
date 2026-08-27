"""矿井水输入单元包根：白名单导出（mine_water_input）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_input"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_input（迁移交叉对照，非依据）。
# 【工艺位置】上游：线起点（executor 源节点，零入边注入点）；下游：
#   mine_water_tiaojiechi 调节池。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 KI-F1~F7 与参数数值真源=docs/norms/mine_water_input.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（factor.mine_input.*；去除率零键——输入源单元
#     不建 removal.mine_input.*，与市政线内置输入节点镜像口径）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.input.compute import make_unit
from waterprint.units_lib.mine_water.input.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
