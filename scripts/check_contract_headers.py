"""模块契约头门禁：每个 .py 首个 docstring 必含 职责/输入/输出 三段。

输入:  core/waterprint 与 server/waterprint_server 全部 .py 文件
输出:  缺失清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：§13.2/§13.7——docstring 存在、首行非空（一句话职责）、
# 含 "输入:" 与 "输出:" 标记段。__init__.py 同样受检（正门规格载体）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAN_ROOTS = (
    REPO / "core" / "waterprint",
    REPO / "server" / "waterprint_server",
)


def check_file(path: Path) -> str | None:
    """返回违规描述；合规返回 None。"""
    source = path.read_text(encoding="utf-8")
    try:
        doc = ast.get_docstring(ast.parse(source))
    except SyntaxError as exc:
        return f"{path}: 语法错误 {exc}"
    if not doc:
        return f"{path}: 缺首个 docstring（职责/输入/输出三段）"
    first_line = doc.strip().splitlines()[0] if doc.strip() else ""
    if not first_line:
        return f"{path}: docstring 首行为空（缺一句话职责）"
    if "输入:" not in doc:
        return f"{path}: docstring 缺 '输入:' 段"
    if "输出:" not in doc:
        return f"{path}: docstring 缺 '输出:' 段"
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    violations: list[str] = []
    count = 0
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            count += 1
            problem = check_file(path)
            if problem:
                violations.append(problem)
    if violations:
        print(f"[FAIL] 模块契约头缺失 {len(violations)} 处：")
        for item in violations:
            print(f"  - {item}")
        return 1
    print(f"[OK] 模块契约头（职责/输入/输出）：{count} 个文件全部合规")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
