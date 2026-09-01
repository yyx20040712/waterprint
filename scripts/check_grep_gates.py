"""grep 门禁：占位/裸异常/乱码三类特征计数必须为 0 + compose 端口直映守卫。

输入:  gate_patterns 定义的扫描范围与特征串；deploy/compose.yml（定点）
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AGENTS.md §3——未完成的功能不写存根；可预期错误用领域异常；
# 中文内容 UTF-8 可读（乱码 = 没验证编码的代价，教训 C4）。
# 本脚本与特征串定义文件本身也在扫描范围内，故特征串一律拼接构造、
# 相关标识符避开特征词。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
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

# WP1 挂账顺收（外审整改#5 同批）：compose 端口直映守卫——server 8000 禁
# 出容器网桥（24 端点零鉴权，暴露即全权；nginx=唯一入口），违规处置见
# docs/deployment.md「安全红线：暴露即全权」节。定点单文件规则，不入
# gate_patterns 扫描面（deploy/ 不属 SCAN_DIRS）。R-1（G1-01 强化）：
# 短格式列表项 `- [IP:]HOSTPORT:8000`（正则匹配任意宿主端口→容器 8000
# 发布形态，非仅字面直映）+ 长格式 `target: 8000`；行内 # 注释先剥离
# （G1-02：文档性提及不误报）。
COMPOSE_GUARD_FILE = "deploy/compose.yml"
COMPOSE_PORT_PUBLISH_RE = re.compile(
    r"""-\s*["']?(\d{1,3}(?:\.\d{1,3}){3}:)?\d+:8000\b|target:\s*["']?8000\b"""
)


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


def check_compose_port_mirror() -> list[str]:
    """compose 端口守卫：deploy/compose.yml 禁现任何到容器 8000 的发布。"""
    path = REPO / COMPOSE_GUARD_FILE
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # fail-closed：文件缺失/不可读时守卫不得静默空转（同 trust-root 口径）
        return [f"{COMPOSE_GUARD_FILE}: 不可读（{exc!r}——端口守卫无从校验）"]
    problems: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]  # 行内注释剥离：文档性提及不误报
        if COMPOSE_PORT_PUBLISH_RE.search(code):
            problems.append(
                f"{COMPOSE_GUARD_FILE}:{lineno}: 发布容器端口 8000"
                "（安全红线：8000 不出容器网桥——处置见 docs/deployment.md"
                "「安全红线」节；WP1 收口回潮防护）"
            )
    return problems


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    violations: list[str] = []
    count = 0
    for path in iter_files():
        count += 1
        violations.extend(check_file(path))
    violations.extend(check_compose_port_mirror())
    if violations:
        print(f"[FAIL] grep 门禁（占位/裸异常/乱码/compose 端口）违规 {len(violations)} 处：")
        for item in violations:
            print(f"  - {item}")
        return 1
    print(
        f"[OK] grep 门禁：占位/裸 except/乱码计数 = 0 + compose 端口守卫通过"
        f"（扫描 {count} 个文件）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
