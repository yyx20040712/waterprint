"""架构门禁：文件行数预算（≤500；units_lib compute.py ≤400）（永续激活）。

输入:  仓库源文件树 + scripts/check_file_budgets.py
输出:  预算断言结果（超标即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AGENTS §2 / §13.7——AI 上下文能否完整覆盖一个单元的命门。
# 无豁免清单；超标拆文件。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.arch

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_file_budget_gate() -> None:
    """行数门禁脚本全绿（含 AGENTS.md ≤500 与 compute.py ≤400 特判）。"""
    env = dict(os.environ, PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_file_budgets.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
