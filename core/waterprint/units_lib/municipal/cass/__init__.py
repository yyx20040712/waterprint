"""CASS 生物池单元包根：白名单导出（municipal_cass）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_cass"；业务线：市政污水线；
#   旧系统对应 mod：cass（迁移交叉对照，非依据）。
# 【工艺位置】上游：chuchenchi 初沉池或 tiaojiechi 调节池；下游：
#   erchunchi 辐流二沉池（与 aao 互为备选生物工艺——同入流对比记档
#   见 docs/norms/cass.md 衔接式）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 CA-F1~F27 与参数数值真源=docs/norms/cass.md 起草表
#     （2026-08-26，数据策略 v2，待追认）+ data/coefficients 0.4.0
#     数据包（M2c 三单元系数批）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.cass.compute import make_unit
from waterprint.units_lib.municipal.cass.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
