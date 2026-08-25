"""调节池单元包根：白名单导出（municipal_tiaojiechi）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_tiaojiechi"；业务线：市政污水线；
#   旧系统对应 mod：tiaojiechi（迁移交叉对照，非依据）。
# 【工艺位置】上游：chenshachi 旋流沉砂池（沉砂后位置口径，与
#   chuchenchi 表同源——两单元并列替代关系按工艺配置）；下游：
#   aao 生物池或 cass 生物池（替代配置）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 TJ-F1~F13 与参数数值真源=docs/norms/tiaojiechi.md 起草表
#     （2026-08-25，数据策略 v2，待追认）+ data/coefficients 0.3.0
#     数据包（M2b1 四单元系数批）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.tiaojiechi.compute import make_unit
from waterprint.units_lib.municipal.tiaojiechi.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
