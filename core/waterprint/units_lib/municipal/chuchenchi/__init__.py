"""辐流初沉池单元包根：白名单导出（municipal_chuchenchi）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_chuchenchi"；业务线：市政污水线；
#   旧系统对应 mod：chuchenchi（迁移交叉对照，非依据）。
# 【工艺位置】上游：chenshachi 旋流沉砂池；下游：aao 生物池或
#   cass 生物池（按工艺配置）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 CC-F1~F18 与参数数值真源=docs/norms/chuchenchi.md 起草表
#     （2026-08-25，数据策略 v2，待追认）+ data/coefficients
#     0.2.0/0.2.1 数据包（原表述"随 M2 交付期冻结"刷新——M2 为正式
#     验收批，数值面追认属数据修订批）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.chuchenchi.compute import make_unit
from waterprint.units_lib.municipal.chuchenchi.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
