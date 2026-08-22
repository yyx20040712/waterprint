"""结构同步门禁：源码文件与 docs/file-contracts.md 职责表双向一致。

输入:  职责表（markdown 表格中反引号包裹的路径）+ 实际目录树
输出:  不同步清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：§13.7"职责漂移"行——新增/改名文件必须同步职责表。
# 规则：
#   a) core/waterprint 与 server/waterprint_server 下每个非 __init__.py
#      必须出现在表中（已登记单元包目录内文件豁免，§3 按包登记）；
#      表中 .py 路径必须存在；
#   b) units_lib 单元包按"包目录（带斜杠）"登记；包内结构按 §13.6 校验
#      （manifest.py/compute.py/constraints.py/README.md/tests/ 两测试）；
#   c) scripts/*.py 必须登记于第 4 节。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTRACTS_MD = REPO / "docs" / "file-contracts.md"
ROW_PATH_RE = re.compile(r"^\|\s*`([^`]+)`")
UNIT_REQUIRED = (
    "manifest.py",
    "compute.py",
    "constraints.py",
    "README.md",
    "tests/test_compute.py",
    "tests/properties.py",
)

def listed_paths() -> tuple[set[str], set[str]]:
    """返回（文件路径集，包目录集）。"""
    files: set[str] = set()
    packages: set[str] = set()
    for line in CONTRACTS_MD.read_text(encoding="utf-8").splitlines():
        match = ROW_PATH_RE.match(line)
        if not match:
            continue
        entry = match.group(1)
        if entry.endswith("/"):
            packages.add(entry.rstrip("/"))
        else:
            files.add(entry)
    return files, packages


def actual_py_files(root: Path, packages: set[str]) -> set[str]:
    """非 __init__ 源文件集合；已登记单元包目录内文件豁免（§3 按包登记）。"""
    found: set[str] = set()
    for path in root.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(REPO).as_posix()
        if any(rel.startswith(pkg + "/") for pkg in packages):
            continue
        found.add(rel)
    return found


def check_unit_package(pkg_rel: str) -> list[str]:
    pkg = REPO / pkg_rel
    if not pkg.is_dir():
        return [f"职责表登记的包不存在: {pkg_rel}"]
    problems = []
    for required in UNIT_REQUIRED:
        if not (pkg / required).is_file():
            problems.append(f"{pkg_rel}: 缺固定结构文件 {required}（§13.6）")
    return problems


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    files, packages = listed_paths()

    actual = actual_py_files(REPO / "core" / "waterprint", packages)
    actual |= actual_py_files(REPO / "server" / "waterprint_server", packages)
    actual |= actual_py_files(REPO / "scripts", packages)

    unlisted = sorted(actual - files)
    for rel in unlisted:
        problems.append(f"文件未登记职责表: {rel}")
    missing = sorted(rel for rel in files if not (REPO / rel).is_file())
    for rel in missing:
        problems.append(f"职责表登记的文件不存在: {rel}")

    for pkg_rel in sorted(packages):
        problems.extend(check_unit_package(pkg_rel))

    if problems:
        print(f"[FAIL] 结构与职责表不同步 {len(problems)} 处：")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"[OK] 结构同步：源文件 {len(files)} 项 + 单元包 {len(packages)} 项与职责表一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
