"""grep 门禁：占位/裸异常/乱码三类特征计数必须为 0。

输入:  gate_patterns 定义的扫描范围与特征串
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AGENTS.md §3——未完成的功能不写存根；可预期错误用领域异常；
# 中文内容 UTF-8 可读（乱码 = 没验证编码的代价，教训 C4）。
# 本脚本与特征串定义文件本身也在扫描范围内，故特征串一律拼接构造、
# 相关标识符避开特征词。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

from gate_patterns import (
    BARE_EXCEPT_RE,
    DOC_SUFFIXES,
    EXCLUDED_DIR_NAMES,
    MOJIBAKE_TOKENS,
    SCAN_DIRS,
    SOURCE_SUFFIXES,
    UNFINISHED_MARKERS,
)

REPO = Path(__file__).resolve().parent.parent


def iter_files() -> list[Path]:
    found: list[Path] = []
    for rel in SCAN_DIRS:
        root = REPO / rel
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if EXCLUDED_DIR_NAMES.intersection(path.relative_to(REPO).parts):
                continue
            if path.suffix in SOURCE_SUFFIXES or path.suffix in DOC_SUFFIXES:
                found.append(path)
    return found


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    rel = path.relative_to(REPO).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{rel}: 不是合法 UTF-8"]
    if path.suffix in SOURCE_SUFFIXES:
        lowered = text.lower()
        for token in UNFINISHED_MARKERS:
            if token.lower() in lowered:
                problems.append(f"{rel}: 含未完成标记（grep 门禁特征）")
        if path.suffix == ".py":
            for match in BARE_EXCEPT_RE.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{rel}:{line}: 裸/过宽 except（用领域异常）")
    for token in MOJIBAKE_TOKENS:
        if token in text:
            problems.append(f"{rel}: 含乱码特征串")
    return problems


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    violations: list[str] = []
    count = 0
    for path in iter_files():
        count += 1
        violations.extend(check_file(path))
    if violations:
        print(f"[FAIL] grep 门禁（占位/裸异常/乱码）违规 {len(violations)} 处：")
        for item in violations:
            print(f"  - {item}")
        return 1
    print(f"[OK] grep 门禁：占位/裸 except/乱码计数 = 0（扫描 {count} 个文件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
