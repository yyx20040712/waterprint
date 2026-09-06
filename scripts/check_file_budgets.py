"""文件行数预算门禁：任何文件 ≤500 行；units_lib 的 compute.py ≤400 行；
file-contracts.md 行数注记与实体文件一致性（B17 N14-A2 G1-05——手工
注记脱钩防线，fail-closed）。

输入:  仓库内 .py/.ts/.tsx/.md 源文件 + docs/file-contracts.md 注记行
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：见 docs/file-contracts.md §4 与 AGENTS.md §2。
# 无豁免清单（§13.7）：真有理由超标 → 拆文件，不是申请豁免。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GLOBAL_LIMIT = 500
COMPUTE_LIMIT = 400
SCAN_SUFFIXES = {".py", ".ts", ".tsx", ".md"}
CONTRACTS_DOC = REPO / "docs" / "file-contracts.md"
# 行数注记形态：句中「N 行」——「N 行预算」系预算引用非注记，前置排除
# （B17 机器断言——deepseek N14-A2 G1-05：手工行数注记脱钩实测 9 处）
_ANNOTATION_RE = re.compile(r"(\d+)\s*行(?!预算)")
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


def _line_count(path: Path) -> int:
    """行数口径：与预算面同式（wc 形态——尾无换行计一行）。"""
    text = path.read_text(encoding="utf-8")
    return text.count("\n") + (0 if text.endswith("\n") or not text else 1)


def check_contract_annotations() -> list[str]:
    """file-contracts.md 行数注记 ↔ 实体文件一致性（恰一注记即断言；
    多注记=歧义拒；「N 行预算」排除）。"""
    violations: list[str] = []
    checked = 0
    for line in CONTRACTS_DOC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        rel = line.split("`")[1]
        matches = _ANNOTATION_RE.findall(line)
        if not matches:
            continue
        target = REPO / rel
        if len(matches) != 1:
            violations.append(f"{rel}: 行数注记歧义（{matches}）——file-contracts 须恰一")
            continue
        if not target.is_file():
            violations.append(f"{rel}: 注记指向不存在文件")
            continue
        checked += 1
        actual = _line_count(target)
        if actual != int(matches[0]):
            violations.append(f"{rel}: 注记 {matches[0]} 行 ≠ 实体 {actual} 行")
    if not violations:
        print(f"[OK] file-contracts 行数注记一致性：{checked} 处注记全部吻合")
    return violations


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    violations: list[str] = []
    warns: list[str] = []
    count = 0
    for path in iter_files():
        count += 1
        limit = limit_for(path)
        lines = _line_count(path)
        if lines > limit:
            violations.append(f"{path.relative_to(REPO)}: {lines} 行 > {limit}")
        elif lines >= limit * 9 // 10:  # 90% 提前告警（450/400×0.9——ENG8 A 件）
            warns.append(
                f"[WARN] {path.relative_to(REPO)}: {lines} 行"
                f" ≥ {limit * 9 // 10}/{limit}（{lines * 100 // limit}%）——接近预算"
            )
    annotations = check_contract_annotations()
    for item in warns:
        print(item)
    if annotations:
        violations.extend(annotations)
    if violations:
        print(f"[FAIL] 文件行数预算/注记违规 {len(violations)} 处：")
        for item in violations:
            print(f"  - {item}")
        return 1
    near = f"，其中 {len(warns)} 个文件接近预算" if warns else ""
    print(
        f"[OK] 文件行数预算（≤{GLOBAL_LIMIT}，compute.py ≤{COMPUTE_LIMIT}）："
        f"{count} 个文件全部合规{near}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
