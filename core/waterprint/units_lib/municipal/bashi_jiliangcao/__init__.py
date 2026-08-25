"""巴歇尔计量槽单元包根：白名单导出（municipal_bashi_jiliangcao）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_bashi_jiliangcao"；业务线：市政污水线；
#   旧系统对应 mod：bashi_jiliangcao（社区）（迁移交叉对照，非依据）。
# 【工艺位置】上游：ziwai 紫外消毒（全厂终水）；下游：排放口。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 BL-F1~F9 与参数数值真源=docs/norms/bashi_jiliangcao.md 起草表
#     （2026-08-26，数据策略 v2，待追认）+ data/coefficients 0.4.0 数据包
#     （M2c 三单元系数批——B7 七档 C/n/scrit/hmin/hmax 全档录入，
#     "CJ/T 3008.3-1993 正式文本核对"降级为追认点注记）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.bashi_jiliangcao.compute import make_unit
from waterprint.units_lib.municipal.bashi_jiliangcao.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
