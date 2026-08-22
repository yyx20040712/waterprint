"""架构门禁：测试只读校验（manifest 哈希 + 只读属性 + 无未登记文件）。

输入:  test-lock.manifest.json + core/tests、server/tests 文件状态
输出:  锁定断言结果（改动测试/绕过锁定 = 失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AGENTS §7——本测试保护其余全部测试的不可变性：
#   改内容（哈希变）、去只读（属性在）、偷加文件（无登记）三种
#   投机路径全部失败。这是"AI 不能改测试让自己通过"的执行体。
#   属性检查只在 Windows 本地生效（git clone 会丢失只读位，
#   CI/Linux 侧由 manifest 哈希门禁承担内容完整性）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.arch

REPO_ROOT = Path(__file__).resolve().parents[3]

ATTR_BARRIER_ACTIVE = sys.platform == "win32" and os.environ.get("CI") != "true"


def test_readonly_gate() -> None:
    """只读门禁脚本全绿（哈希/属性/登记三重校验）。"""
    env = dict(os.environ, PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_readonly.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    not ATTR_BARRIER_ACTIVE,
    reason="只读属性是 Windows 本地写屏障；CI/Linux 由 manifest 哈希门禁覆盖",
)
def test_this_file_is_readonly() -> None:
    """自证：本文件自身处于只读状态（写权限已除）。"""
    assert not os.access(Path(__file__), os.W_OK), "测试文件必须只读（AGENTS §7）"
