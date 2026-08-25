"""污水提升泵房单元包根：白名单导出（municipal_wushui_tisheng）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  仅暴露 manifest 与 make_unit 两个名字（units_lib 白名单铁律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【身份】UNIT_ID = "municipal_wushui_tisheng"；业务线：市政污水线；
#   旧系统对应 mod：wushui_tisheng（社区）（迁移交叉对照，非依据）。
# 【工艺位置】上游：市政输入节点（入流=原水链值）；下游：cugeshan
#   粗格栅（全厂首端提升单元）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 公式 TS-F1~F14 与参数数值真源=docs/norms/wushui_tisheng.md 起草表
#     （2026-08-26，数据策略 v2，待追认）+ data/coefficients 0.4.0
#     数据包（M2c 三单元系数批——含舍维列夫比阻 DN300~DN800 八档）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.municipal.wushui_tisheng.compute import make_unit
from waterprint.units_lib.municipal.wushui_tisheng.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
