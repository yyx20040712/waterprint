"""ruff 门禁：本地聚合 CI core-quality 同款检查（T7a C416 教训补齐）。

输入:  core 源码树 + core/.venv 内的 ruff（解释器按 win/posix 双路径定位）
输出:  ruff check 结果透传（退出码透传；venv 双缺失 = FAIL 退出码 1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（出处：CI .github/workflows/ci.yml core-quality job 同款
# 命令 `uv run ruff check .`；T7a 曾因本地门禁不含 ruff 致 C416
# 漏网至 R2——本脚本补齐本地聚合口径，消灭"本地绿、CI 红"盲区）：
#   a) 定位 core 虚拟环境解释器：win=`core/.venv/Scripts/python.exe`、
#      posix=`core/.venv/bin/python`；双双缺失 = FAIL，消息
#      "core/.venv 缺失（宪法环境在册要求）"，退出码 1；
#   b) 以该解释器执行 `-m ruff check .`（cwd=core）：stdout 透传、
#      退出码透传——与 CI 同口径，不截获不改写。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORE = REPO / "core"
VENV_CANDIDATES = (
    CORE / ".venv" / "Scripts" / "python.exe",
    CORE / ".venv" / "bin" / "python",
)


def locate_venv_python() -> Path | None:
    """返回首个存在的 core venv 解释器；win/posix 双路径均缺失返回 None。"""
    for candidate in VENV_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    python = locate_venv_python()
    if python is None:
        print("[FAIL] core/.venv 缺失（宪法环境在册要求）")
        for candidate in VENV_CANDIDATES:
            print(f"  期望之一存在：{candidate.relative_to(REPO).as_posix()}")
        return 1
    print(f"[INFO] 解释器 {python.relative_to(REPO).as_posix()}（透传 ruff）")
    result = subprocess.run(
        [str(python), "-m", "ruff", "check", "."],
        cwd=CORE,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
