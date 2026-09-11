"""lint-imports 门禁：双根（core+server）本地聚合 CI quality 同款检查。

输入:  core/server 各自 pyproject.toml 的 importlinter 契约 + 各自 .venv
       内的 lint-imports 控制台脚本（win/posix 双路径定位——互不代偿）
输出:  逐根三态单行 [OK]/[FAIL]/[SKIP]（lint-imports 输出透传）；任一根
       FAIL = 退出码 1；venv 缺失根 = SKIP（双根皆缺 = 双 SKIP 退出码 0）；
       venv 在但脚本不可用（OSError 族）= 该根 FAIL 兜底（禁裸抛
       traceback；SKIP 语义红线不破）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：CI .github/workflows/ci.yml core/server 两 quality job 同款命令
# `uv run lint-imports`（内核质量 job=五契约；服务层质量 job=UF-33 单
# 入口契约）。n+42 实录：worker 直连 waterprint.registry 破 UF-33 由
# CI 首抓而本地无门禁=挂账盲区（urgency↑）——本脚本补齐本地聚合口径，
# 消灭"本地绿、CI 红"盲区（check_ruff 双根三态先例同制，GOV2 搭车项）。
# 调用面=lint-imports 控制台脚本（非 python -m：importlinter 包无
# __main__ 入口，venv Scripts/bin 下 shim 直调——实测注记）。
# 门禁数基线 11→12（GOV2 台账）：AGENTS 词汇表/README/file-contracts
# §4/run_gates 头注四处同步义务。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# 双根扫描面（根名, 根路径）——lint-imports 按 cwd 取各自 pyproject 配置。
SCAN_ROOTS: tuple[tuple[str, Path], ...] = (
    ("core", REPO / "core"),
    ("server", REPO / "server"),
)


def locate_lint_imports(root: Path) -> Path | None:
    """返回首个存在的该根 lint-imports 控制台脚本；win/posix 双路径缺失返回 None。"""
    for candidate in (
        root / ".venv" / "Scripts" / "lint-imports.exe",
        root / ".venv" / "bin" / "lint-imports",
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
        runner = locate_lint_imports(root)
        if runner is None:
            print(f"[SKIP] check_lint_imports：{name}（venv 缺失——CI 零依赖"
                  f" job 预期路径；本地运行请在 {name}/ 下 uv sync 安装"
                  " import-linter）")
            continue
        print(f"[INFO] 解释器 {runner.relative_to(REPO).as_posix()}"
              "（透传 lint-imports）")
        # OSError 现实异常族显式枚举兜底（脚本在但不可执行/已损坏——
        # PermissionError/FileNotFoundError 等禁裸抛 traceback；
        # SKIP 语义红线不破：仅 venv 脚本路径缺失才 SKIP，此处=FAIL）。
        try:
            result = subprocess.run(
                [str(runner)],
                cwd=root,
                check=False,
                capture_output=True,
            )
        except (OSError, PermissionError, FileNotFoundError) as exc:
            print(f"[FAIL] check_lint_imports：{name}（子进程不可用：{exc}"
                  "——venv 异常，请重建：uv sync）")
            failed = True
            continue
        emit(result.stdout.decode("utf-8", errors="replace"))
        emit(result.stderr.decode("utf-8", errors="replace"))
        if result.returncode != 0:
            print(f"[FAIL] check_lint_imports：{name}")
            failed = True
        else:
            print(f"[OK] check_lint_imports：{name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
