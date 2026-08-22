"""门禁聚合入口：一键运行全部架构门禁脚本（CI 与本地同口径）。

输入:  无
输出:  各门禁 PASS/FAIL 汇总（退出码 0=全绿，1=有失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：门禁清单与 AGENTS.md §2/§3、docs/file-contracts.md §4 一致；
# ruff/mypy/import-linter/pytest 属于各项目 venv 内工具（CI 单独跑），
# 本脚本只聚合零依赖门禁（系统 Python 直接可跑）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GATES = (
    "check_file_budgets.py",
    "check_contract_headers.py",
    "check_grep_gates.py",
    "check_structure.py",
    "check_readonly.py",
    "check_module_graph.py",
    "check_webapp.py",
    "check_magic_numbers.py",
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failures: list[str] = []
    for gate in GATES:
        print(f"== {gate} " + "=" * max(1, 50 - len(gate)))
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts" / gate)],
            check=False,
            cwd=REPO,
        )
        if result.returncode != 0:
            failures.append(gate)
        print()
    if failures:
        print(f"[FAIL] 门禁未全绿：{', '.join(failures)}")
        return 1
    print("[OK] 全部门禁通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
