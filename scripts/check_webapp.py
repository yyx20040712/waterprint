"""webapp 结构门禁：TS 契约头 + feature 切片依赖方向（§13.5）。

输入:  webapp/src 下 .ts/.tsx 源文件 + 路径别名约定（@/ → webapp/src）
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：AGENTS.md §2/§13.5——前端结构从口头约定升级为机器检查：
#   a) 契约头：每个源文件首块 /** … */ 注释必含 "输入:" 与 "输出:"
#      （shared/api/generated 生成物豁免——禁手改区不做要求）；
#   b) 分层：features 之间禁止互相 import（跨 feature 编排只在 app 层）；
#      features 禁止 import app；shared 禁止 import features/app；
#      入口 main.tsx 只允许 import app/**；
#   c) import 解析：./ ../ 相对路径按文件位置归一化；"@/" 别名映射
#      webapp/src；裸模块（react/antd/…）视为外部依赖，不检查。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "webapp" / "src"
EXCLUDED_PARTS = ("shared/api/generated",)
EXCLUDED_NAMES = {"vite-env.d.ts"}
SOURCE_SUFFIXES = {".ts", ".tsx"}
IMPORT_FROM = re.compile(r"""\bfrom\s*["']([^"']+)["']""")
IMPORT_DYNAMIC = re.compile(r"""import\s*\(\s*["']([^"']+)["']""")


def iter_sources() -> list[Path]:
    found: list[Path] = []
    for path in sorted(SRC.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        rel = path.relative_to(SRC).as_posix()
        if path.name in EXCLUDED_NAMES:
            continue
        if any(part in rel for part in EXCLUDED_PARTS):
            continue
        found.append(path)
    return found


def header_problem(path: Path) -> str | None:
    """契约头检查：首个 /** */ 块必含 输入:/输出:；返回违规描述或 None。"""
    text = path.read_text(encoding="utf-8").lstrip("\ufeff \t\n")
    if not text.startswith("/**"):
        return "缺首块 /** … */ 契约头（职责/输入/输出）"
    end = text.find("*/")
    if end == -1:
        return "首块注释未闭合"
    block = text[:end]
    if "输入:" not in block:
        return "契约头缺 '输入:' 段"
    if "输出:" not in block:
        return "契约头缺 '输出:' 段"
    return None


def classify(rel: str) -> tuple[str, str]:
    """源文件归属：(层, feature 名)。rel 相对 webapp/src。"""
    parts = rel.split("/")
    if rel == "main.tsx":
        return ("entry", "")
    if parts[0] == "app":
        return ("app", "")
    if parts[0] == "features" and len(parts) > 1:
        return ("features", parts[1])
    if parts[0] == "shared":
        return ("shared", "")
    return ("other", "")


def resolve(spec: str, from_rel: str) -> str | None:
    """解析 import 说明符 → webapp/src 相对路径；外部模块返回 None。"""
    if spec.startswith("@/"):
        return posixpath.normpath(spec[2:])
    if spec.startswith("."):
        base = posixpath.dirname(from_rel)
        return posixpath.normpath(posixpath.join(base, spec))
    return None


def layer_problem(src_layer: str, src_feature: str, target: str) -> str | None:
    """分层规则（§13.5）；target 为 src 相对路径（不含扩展名）。"""
    dst_layer, dst_feature = classify(target)
    if src_layer == "entry" and dst_layer != "app":
        return f"入口只允许 import app/**（实际 → {target}）"
    if src_layer == "features":
        if dst_layer == "features" and dst_feature != src_feature:
            return f"features 互相 import（{src_feature} → {dst_feature}）"
        if dst_layer == "app":
            return f"feature 禁止 import app 层（→ {target}）"
    if src_layer == "shared" and dst_layer in ("features", "app"):
        return f"shared 禁止 import {dst_layer} 层（→ {target}）"
    return None


def import_problems(path: Path) -> list[str]:
    rel = path.relative_to(SRC).as_posix()
    src_layer, src_feature = classify(rel)
    text = path.read_text(encoding="utf-8")
    specs = IMPORT_FROM.findall(text) + IMPORT_DYNAMIC.findall(text)
    problems = []
    for spec in specs:
        target = resolve(spec, rel)
        if target is None:
            continue
        problem = layer_problem(src_layer, src_feature, target)
        if problem:
            problems.append(f"{rel}: {problem}")
    return problems


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    sources = iter_sources()
    imports_checked = 0
    for path in sources:
        problem = header_problem(path)
        if problem:
            problems.append(f"{path.relative_to(SRC).as_posix()}: {problem}")
        problems.extend(import_problems(path))
        imports_checked += 1
    if problems:
        print(f"[FAIL] webapp 结构违规 {len(problems)} 处：")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(
        f"[OK] webapp 结构：{len(sources)} 个源文件契约头齐全；"
        f"import 分层合规（features 互不依赖/shared 不向上的 §13.5 规则）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
