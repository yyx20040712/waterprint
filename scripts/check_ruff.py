"""ruff 门禁：本地聚合 CI core-quality 同款检查（T7a C416 教训补齐）。

输入:  core 源码树 + core/.venv 内的 ruff（解释器按 win/posix 双路径定位）
输出:  ruff check 结果透传；venv 双缺失 = SKIP 退出码 0；ruff 未装或
       检查失败 = FAIL 退出码 1（失败输出前打 [FAIL] 前缀行）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（出处：CI .github/workflows/ci.yml core-quality job 同款
# 命令 `uv run ruff check .`；T7a 曾因本地门禁不含 ruff 致 C416
# 漏网至 R2——本脚本补齐本地聚合口径，消灭"本地绿、CI 红"盲区）。
# 双环境口径（ENG1-R1 裁决：SKIP 语义修复）：
#   a) 定位 core 虚拟环境解释器：win=`core/.venv/Scripts/python.exe`、
#      posix=`core/.venv/bin/python`；双双缺失 = SKIP 退出码 0——
#      CI「架构门禁（零依赖，系统 Python）」job 不装 venv，属预期
#      路径（ruff 由 core-quality job 承担）；本地同样 SKIP 但提示
#      先建 venv（宪法环境在册）——本地全咬、CI 零依赖 job 跳过；
#   b) venv 存在：以该解释器执行 `-m ruff check .`（cwd=core），捕获
#      stdout/stderr 后透传——ruff 未装或退出码非 0 = FAIL，输出前
#      先打 `[FAIL] check_ruff：ruff 检查未通过` 前缀行（可读性），
#      退出码透传（ruff 检查失败即 1）。
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


def emit(text: str) -> None:
    """透传子进程输出（确保按行结尾规整，空串不打）。"""
    if text:
        print(text, end="" if text.endswith("\n") else "\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    python = locate_venv_python()
    if python is None:
        print(
            "[SKIP] check_ruff：core/.venv 缺失——CI 零依赖 job 预期路径"
            "（ruff 由 core-quality job 承担）；本地请先建 venv（宪法环境在册）"
        )
        for candidate in VENV_CANDIDATES:
            print(f"  期望之一存在：{candidate.relative_to(REPO).as_posix()}")
        return 0
    print(f"[INFO] 解释器 {python.relative_to(REPO).as_posix()}（透传 ruff）")
    result = subprocess.run(
        [str(python), "-m", "ruff", "check", "."],
        cwd=CORE,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        print("[FAIL] check_ruff：ruff 检查未通过")
    emit(result.stdout.decode("utf-8", errors="replace"))
    emit(result.stderr.decode("utf-8", errors="replace"))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
