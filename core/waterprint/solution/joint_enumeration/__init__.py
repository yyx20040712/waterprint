"""联合枚举子包聚合正门（B4-3）：分层 beam 全厂联合枚举（ADR-025）。

输入:  beam/stage/ranking/diagnose/final_eval 五部件公开面
输出:  run_joint_enumerate/JointEnumerationOptions/JointOutcome/ComboResult/
       JointEnumerationTooLarge/estimate_rows/terminal_summary（app 再导出=
       server 单入口）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 终裁定稿 .workflow/b4-3/design-final.md——2026-09-20；
#   镜像测试 tests/solution/test_beam.py+test_stage.py）
#
# 【交付方案】分层序列化 beam：拓扑序逐单元枚举（基线上下文冻结——
#   B1 口径：回路反馈边承载值取基线设计快照=已知近似，loop_semantics
#   'frozen'）→top-k 冻结传播→末段 k 组合全厂真值复验（merged 瞬态
#   DesignState→execute_graph 全厂一次含全工况→summary 出水六指标
#   compliant 硬门+W12 三真键排序）。
#
# 【部件分工】beam=主编排/静态预检/双轴预算；stage=冻结前缀+基线上下文
#   +逐级枚举+阶段代理分；ranking=全厂目标函数+降权标记制排序；diagnose
#   =分层最小冲突集（首空级既有 diagnose 委托+末空级一次放宽）；
#   final_eval=末段全厂真值评估面（beam 500 行预算拆件——宪法 §2）。
#
# 【同层边注记】包根=waterprint.solution → waterprint.graph 唯一 import
#   现场（execute_graph 直调——W6 终裁「不新写拓扑序不构成双轨」；子件
#   经包根中继取用，import-linter 单段通配锚定）。经 structure-graph §1c
#   声明块登记（independence=true；ADR-014 唯一声明面）。
# ══════════════════════════════════════════════════════════════════

# W6 直调既有编排：包根单点 import（子件 beam 经本包取用——同层边锚点）
from waterprint.graph import execute_graph
from waterprint.solution.joint_enumeration.beam import (
    JointEnumerationOptions,
    JointEnumerationTooLarge,
    JointOutcome,
    estimate_rows,
    run_joint_enumerate,
)
from waterprint.solution.joint_enumeration.final_eval import (
    ComboResult,
    terminal_summary,
)
from waterprint.solution.joint_enumeration.stage import (
    AssembleFn,
    InvalidJointEnumerationError,
)

__all__ = [
    "AssembleFn",
    "ComboResult",
    "InvalidJointEnumerationError",
    "JointEnumerationOptions",
    "JointEnumerationTooLarge",
    "JointOutcome",
    "estimate_rows",
    "execute_graph",
    "run_joint_enumerate",
    "terminal_summary",
]
