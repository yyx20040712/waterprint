"""文件行数预算门禁：任何文件 ≤500 行；units_lib 的 compute.py ≤400 行。

输入:  仓库内 .py/.ts/.tsx/.md 源文件
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：见 docs/file-contracts.md §4 与 AGENTS.md §2。
# 无豁免清单（§13.7）：真有理由超标 → 拆文件，不是申请豁免。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GLOBAL_LIMIT = 500
COMPUTE_LIMIT = 400
SCAN_SUFFIXES = {".py", ".ts", ".tsx", ".md"}
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis",
    "__snapshots__", "dist", "build", "generated", ".mimosa",
}


def limit_for(path: Path) -> int:
    """按路径决定预算：units_lib 下的 compute.py 用更严的 400 行。"""
    parts = path.relative_to(REPO).parts
    if path.name == "compute.py" and "units_lib" in parts:
        return COMPUTE_LIMIT
    return GLOBAL_LIMIT


def iter_files() -> list[Path]:
    found: list[Path] = []
    for path in sorted(REPO.rglob("*")):
        if not path.is_file():
            continue
        if EXCLUDED_DIRS.intersection(path.relative_to(REPO).parts):
            continue
        if path.suffix in SCAN_SUFFIXES:
            found.append(path)
    return found


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    violations: list[str] = []
    count = 0
    for path in iter_files():
        count += 1
        limit = limit_for(path)
        text = path.read_text(encoding="utf-8")
        lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
        if lines > limit:
            violations.append(f"{path.relative_to(REPO)}: {lines} 行 > {limit}")
    if violations:
        print(f"[FAIL] 文件行数预算违规 {len(violations)} 处：")
        for item in violations:
            print(f"  - {item}")
        return 1
    print(f"[OK] 文件行数预算（≤{GLOBAL_LIMIT}，compute.py ≤{COMPUTE_LIMIT}）：{count} 个文件全部合规")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
