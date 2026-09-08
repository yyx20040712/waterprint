"""GR-21 弃用到期门禁：file-contracts 弃用登记逾期即 FAIL（机制就绪件）。

输入:  docs/file-contracts.md（默认自脚本位置锚定仓库根；可选位置参数
       =镜像测试注入样本面——scripts/lock_tests.py 路径参数先例）
输出:  逾期/格式错逐条 [FAIL]（退出码 1）；无逾期 [OK]（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（TD1 技术债小批 2026-09-09，GR-21 退役机制缺位收口——ARCHDEBT
#   终审「有移除里程碑字段无执行机制，建议加到期门禁」兑现件）：
#
# 【登记语法】（落 file-contracts.md「唯一职责」列尾注，与行数注记并列）
#   (弃用: <旧键> -> <新键>, 移除: YYYY-MM-DD)
#   键名字符集 [A-Za-z0-9_.]+（含连字符键出现时扩正则——TD1 不确定项 1）；
#   逾期判定 = 今日 >= 移除日期（期限语义=当日完成，到期当日即红——
#   TD1 N3 终裁口径）；日期串非法（fromisoformat 解析失败）=格式错 FAIL
#   （防呆：非法登记不得静默通过）。
# 【零登记 = 首检绿】当前登记面零条目（退役流程从未行使）——本门禁落地
#   即绿=机制就绪形态；登记面整体损坏（正则全不命中）残余风险由镜像
#   测试用例②③反向覆盖（TD1 不确定项 6 接受）。
# 【日期轴】today 取 CI 本地日期，不作时区归一（弃用周期月级，日级
#   漂移无碍语义——TD1 不确定项 2 接受）。
# 【参照】briefs/task-TD1-plan.md PD1；engineering-conventions.md GR-21
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACTS = REPO / "docs" / "file-contracts.md"

# 登记串：键名字符集与箭头/日期段不相交，正则无歧义锚定（量词 {4}/{2}
# 属模式语法非数值字面量——注记区）。
_DEPRECATION_RE = re.compile(
    r"\(弃用: (?P<old>[A-Za-z0-9_.]+) -> (?P<new>[A-Za-z0-9_.]+),"
    r" 移除: (?P<date>\d{4}-\d{2}-\d{2})\)"
)


def main(argv: list[str]) -> int:
    """扫描登记真源：逾期/格式错逐条报告，return 1；全合规 return 0。"""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    contracts = Path(argv[0]) if argv else DEFAULT_CONTRACTS
    if not contracts.is_file():
        print(f"[FAIL] 弃用登记真源缺失：{contracts}")
        return 1
    failures: list[str] = []
    today = date.today()
    registered = 0
    for number, line in enumerate(
        contracts.read_text(encoding="utf-8").splitlines(), start=1
    ):
        for match in _DEPRECATION_RE.finditer(line):
            registered += 1
            removal_text = match.group("date")
            try:
                removal = date.fromisoformat(removal_text)
            except ValueError:
                failures.append(
                    f"{contracts.name}:{number} 弃用项 {match.group('old')!r} "
                    f"移除日期非法：{removal_text!r}（须 YYYY-MM-DD）"
                )
                continue
            if today >= removal:
                failures.append(
                    f"{contracts.name}:{number} 弃用项 {match.group('old')!r} "
                    f"已到期（移除: {removal_text}，今日: {today.isoformat()}，"
                    f"替代键: {match.group('new')!r}）——按里程碑执行移除"
                )
    if failures:
        print(f"[FAIL] GR-21 弃用到期门禁违规 {len(failures)} 处：")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    if not registered:
        print("[OK] 无弃用登记（GR-21 退役机制就绪，登记语法见脚本规格头）")
    else:
        print(f"[OK] 弃用登记 {registered} 项，0 逾期")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
