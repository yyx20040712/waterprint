"""配水渠单元包根：白名单导出（conveyance_peishuiqu）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "conveyance_peishuiqu"；业务线：集配水线；
#   旧系统对应 mod：peishuiqu（迁移交叉对照，非依据）。
# 【工艺位置】上游：配水井或上游处理单元；下游：并联处理系列
#   （n 路——多出流口为本线特征）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 PQ-F1~PQ-F7 与参数数值真源=docs/norms/conveyance_
#     peishuiqu.md 起草表（2026-08-27，数据策略 v2，待追认）+
#     data/coefficients 0.7.0 数据包（factor.peishuiqu.* 裸短名
#     12 键——removal 零键，穿流单元无水质去除概念；无壁厚概算键
#     ——渠道无井体概算面，渠长归布置面）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.conveyance.peishuiqu.compute import make_unit
from waterprint.units_lib.conveyance.peishuiqu.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
