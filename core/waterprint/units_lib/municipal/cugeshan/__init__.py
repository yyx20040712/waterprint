"""粗格栅单元包根：白名单导出（municipal_cugeshan）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_cugeshan"；业务线：市政污水线；
#   旧系统对应 mod：cugeshan（迁移交叉对照，非依据）。
# 【工艺位置】上游：市政输入节点或 wushui_tisheng 提升泵房；下游：xigeshan 细格栅。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 CG-F1~F14 与参数数值真源=docs/norms/cugeshan.md 签字表
#     （2026-08-23）+ data/coefficients 0.1.0 数据包（本批 M1a 实装，
#     原表述"随 M2 交付期冻结"刷新——M2 为正式验收批）。
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.cugeshan.compute import make_unit
from waterprint.units_lib.municipal.cugeshan.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
