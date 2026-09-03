"""ruff 门禁：双根（core+server）本地聚合 CI quality 同款检查（T7a C416 教训）。

输入:  core/server 源码树 + 各自 .venv 内的 ruff（解释器逐根按 win/posix
       双路径定位——互不代偿）
输出:  逐根三态单行 [OK]/[FAIL]/[SKIP]（ruff 输出透传）；任一根 FAIL =
       退出码 1；venv 缺失根 = SKIP（双根皆缺 = 双 SKIP 退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（出处：CI .github/workflows/ci.yml core/server quality job
# 同款命令 `uv run ruff check .`；T7a 曾因本地门禁不含 ruff 致 C416
# 漏网至 R2——本脚本补齐本地聚合口径，消灭"本地绿、CI 红"盲区）。
# 双根三态口径（ENG1-R1 SKIP 语义修复 + ENG6 扩面 server——L5 CI 事故
# 后 server 面本地盲区销账）：
#   a) SCAN_ROOTS 双根（core/server）：逐根定位各自虚拟环境解释器
#      （win=`<root>/.venv/Scripts/python.exe`、posix=`<root>/.venv/bin/
#      python`）；缺失根 = 该根单行 [SKIP] 退出码不计失败——CI「架构门禁
#      （零依赖，系统 Python）」job 不装 venv，双 SKIP=退出码 0 属预期
#      路径（ruff 由 core/server quality job 各自承担）；本地同样 SKIP
#      但提示属 CI 预期（宪法环境在册）——逐根独立无跨根耦合；
#   b) 根 venv 存在：以该解释器执行 `-m ruff check .`（cwd=该根——ruff
#      按 cwd 取各自 pyproject.toml 配置，零配置改动），stdout/stderr 捕获
#      后透传；ruff 未装或退出码非 0 = 该根 [FAIL]，任一根 FAIL 即退出
#      码 1（全根 FAIL 汇总——单行 verdict 置于该根输出之后可读性）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# 双根扫描面（根名, 根路径）——ruff 按 cwd 取各自 pyproject 配置。
SCAN_ROOTS: tuple[tuple[str, Path], ...] = (
    ("core", REPO / "core"),
    ("server", REPO / "server"),
)


def locate_venv_python(root: Path) -> Path | None:
    """返回首个存在的该根 venv 解释器；win/posix 双路径均缺失返回 None。"""
    for candidate in (
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return candidate
    return None


def emit(text: str) -> None:
    """透传子进程输出（确保按行结尾规整，空串不打）。"""
    if text:
        print(text, end="" if text.endswith("\n") else "\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failed = False
    for name, root in SCAN_ROOTS:
        python = locate_venv_python(root)
        if python is None:
            print(f"[SKIP] check_ruff：{name}（venv 缺失——CI 零依赖 job 预期路径）")
            continue
        print(f"[INFO] 解释器 {python.relative_to(REPO).as_posix()}（透传 ruff）")
        result = subprocess.run(
            [str(python), "-m", "ruff", "check", "."],
            cwd=root,
            check=False,
            capture_output=True,
        )
        emit(result.stdout.decode("utf-8", errors="replace"))
        emit(result.stderr.decode("utf-8", errors="replace"))
        if result.returncode != 0:
            print(f"[FAIL] check_ruff：{name}")
            failed = True
        else:
            print(f"[OK] check_ruff：{name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
