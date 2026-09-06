"""units_lib 共享常量件：SECS_PER_DAY 单源真源（B8 R3——13 份 manifest 重复收敛）。

输入:  无（纯常量声明）
输出:  SECS_PER_DAY（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s 的时间换算因子）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B8 R3 收敛；参照 .workflow/briefs/task-B8-brief.md D2）
#
# 【消费面】13 处原 manifest 消费点（chuchenchi/aao/gaomidu×2/
#   chenshachi/cifenli/hebing/shusong/bengzhan/nongsuo/xiaohua/
#   tuoshui/ganhua）：笔②起各 manifest.py 删重复定义行，对应
#   compute.py 的 import 改自本件（manifest 纯度零破——compute 直改源
#   形态，总控改裁②）。
# 【B8 R3 收敛注记】本件=WHITELIST_DECLARATION 声明面白名单在册
#   （check_magic_numbers.py）——常量带出处注记，与 manifest.py
#   "带出处的声明式真源"同款；其余 units_lib 文件继续严管。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Final

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）——时间量纲
# 换算 1 d = 24×3600 s = 86400 s（各 manifest 定义处先例注释同款：nongsuo/
# ganhua 等「单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）
# ——由 compute 消费」；B8 R3 迁此单源）。
SECS_PER_DAY: Final[float] = 86400.0
