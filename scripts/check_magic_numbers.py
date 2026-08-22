"""魔法数字门禁：内核与服务代码数值字面量仅限真源区（ADR-009 附则）。

输入:  core/waterprint 与 server/waterprint_server 源码的 AST
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（docs/business-logic.md §9 / AGENTS.md §3 / ADR-009）：
#   a) 代码中的数值字面量（int/float）只允许 0/1/2/10（索引/计数/幂底）；
#      其余数值（24、0.5632、3000、0.85…）一律来自 registry 真源或
#      assumptions/coefficients 注入——工程默认值带出处是可复算前提；
#   b) 白名单区（数值允许出现）：core/waterprint/registry/**
#      （注册表真源）、core/waterprint/contracts/quantity.py（单位定义）、
#      core/waterprint/units_lib/**/manifest.py（单元默认值=带出处的
#      声明式真源，B-3 裁决方案①——按"前缀+文件名"双条件精确命中，
#      同前缀下 compute.py 等其余文件继续严管）；
#   c) 豁免路径：任意层级 tests/ 目录（golden 期望值走 norms 手算表，
#      由测试只读锁承担纪律）；
#   d) server 层同规：配置数值属 settings/env/数据包，不内联代码；
#   e) 骨架期文件为纯注释 = 零命中空转；M1 实现起即咬人（负向测试已证）。
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
ALLOWED_VALUES = {0, 1, 2, 10}
WHITELIST_PREFIXES = (
    "core/waterprint/registry/",
)
WHITELIST_EXACT = ("core/waterprint/contracts/quantity.py",)
# units_lib 真源区只放行 manifest.py：前缀 + 文件名双条件，
# 直接加前缀会连带放行同目录 compute.py（B-3 裁决方案①明令禁止）。
WHITELIST_MANIFEST = ("core/waterprint/units_lib/", "/manifest.py")
EXCLUDED_PARTS = {"tests", "__pycache__"}


def is_whitelisted(rel: str) -> bool:
    prefix, suffix = WHITELIST_MANIFEST
    return (
        rel.startswith(WHITELIST_PREFIXES)
        or rel in WHITELIST_EXACT
        or (rel.startswith(prefix) and rel.endswith(suffix))
    )


def is_excluded(path: Path) -> bool:
    return EXCLUDED_PARTS.intersection(path.relative_to(REPO).parts) != set()


def numeric_violations(path: Path) -> list[tuple[int, object]]:
    """返回 [(行号, 字面量值)]；仅统计代码 AST 常量（注释/文档串天然排除）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[int, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        value = node.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if value in ALLOWED_VALUES:
            continue
        found.append((getattr(node, "lineno", 0), value))
    return found


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    scanned = 0
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if is_excluded(path):
                continue
            scanned += 1
            rel = path.relative_to(REPO).as_posix()
            if is_whitelisted(rel):
                continue
            for lineno, value in numeric_violations(path):
                problems.append(f"{rel}:{lineno} 魔法数字 {value}（真源区外）")
    if problems:
        print(f"[FAIL] 魔法数字违规 {len(problems)} 处（数值只许来自 registry/单元 manifest/假设清单/系数库）：")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(
        f"[OK] 魔法数字：{scanned} 个源文件字面量合规"
        f"（白名单区 registry/quantity/units_lib manifest.py 之外"
        f"仅允许 {sorted(ALLOWED_VALUES)}）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
