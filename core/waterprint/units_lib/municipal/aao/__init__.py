"""AAO 生物池单元包根：白名单导出（municipal_aao）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_aao"；业务线：市政污水线；
#   旧系统对应 mod：aao（迁移交叉对照，非依据）。
# 【工艺位置】上游：chuchenchi 初沉池或 tiaojiechi 调节池；下游：
#   erchunchi 辐流二沉池（回流比/MLSS 联动——各包独立声明同值参数）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 AO-F1~F14 与参数数值真源=docs/norms/aao.md 起草表
#     （2026-08-25，数据策略 v2，待追认；公式路线 ADR-008 ①负荷法
#     主线+泥龄校核带）+ data/coefficients 0.2.0 数据包（原表述
#     "随 M2 交付期冻结"刷新——M2 为正式验收批）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.aao.compute import make_unit
from waterprint.units_lib.municipal.aao.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
