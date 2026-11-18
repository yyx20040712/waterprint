"""grep 门禁：占位（英文四词+中文硬封族）/裸异常/乱码三类特征计数必须为 0
+ compose 端口直映守卫。

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

import ast
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
    WIDE_EXCEPT_WAIVERS,
)

REPO = Path(__file__).resolve().parent.parent

# WP1 挂账顺收（外审整改#5 同批）：compose 端口直映守卫——server 8000 禁
# 出容器网桥（token 空=鉴权关，暴露即全权；nginx=唯一入口），违规处置见
# docs/architecture.md §4.1 安全红线。定点单文件规则，不入
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


# AUDIT-#20（b30，D7）：宽族 except 豁免键形态（与 gate_patterns
# WIDE_EXCEPT_WAIVERS 登记一致）；族名取值见该文件注释。
VALID_FAMILIES = ("Exception", "bare")
WaiverKey = tuple[str, str, str]


def validate_waivers() -> tuple[list[str], set[WaiverKey]]:
    """豁免登记面自身校验：四字段非空（reason 空理由=无审查依据）+ 族合法 + 键唯一。

    返回（问题清单, 登记键集）。
    """
    problems: list[str] = []
    keys: set[WaiverKey] = set()
    for idx, entry in enumerate(WIDE_EXCEPT_WAIVERS):
        tag = f"WIDE_EXCEPT_WAIVERS[{idx}]（{entry.file}）"
        for field in ("file", "symbol", "family", "reason"):
            if not getattr(entry, field).strip():
                problems.append(f"{tag}: 字段 {field} 为空（豁免登记不完整——reason 非空强制）")
        if entry.family not in VALID_FAMILIES:
            problems.append(f"{tag}: 异常族 {entry.family!r} 非法（合法={VALID_FAMILIES}）")
        key = (entry.file, entry.symbol, entry.family)
        if key in keys:
            problems.append(f"{tag}: 键重复 {key[0]}#{key[1]}[{key[2]}]")
        keys.add(key)
    return problems, keys


def parse_code_map(text: str) -> tuple[dict[int, str], dict[int, str]]:
    """AST 解析 →（行号→限定名, 行号→except 处理器族名）。

    豁免键定位专用（AUDIT-#20；b30 回炉 blocker/major 两收）：
    - 限定名含类链（Class.method——不同类同名方法不得共享豁免键），
      嵌套取最内层链；模块级无键——按“<module>”处理；
    - 族名=处理器异常类型精确名（ast.Name 之 id；无类型=“bare”）——
      前缀形态（如 ExceptionGroup）不得冒充 Exception 族消费豁免。
    SyntaxError → 两空映射（该文件另由 ruff/mypy 门禁兜底；此处无
    AST 信息时族判定走行文本完整 token 回退）。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}, {}
    symbols: dict[int, str] = {}
    families: dict[int, str] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}.{child.name}" if prefix else child.name
                for line in range(child.lineno, (child.end_lineno or child.lineno) + 1):
                    symbols[line] = name  # 后写覆盖=最内层
                visit(child, name)
            elif isinstance(child, ast.ExceptHandler):
                t = child.type
                if t is None:
                    families[child.lineno] = "bare"
                elif isinstance(t, ast.Name):
                    families[child.lineno] = t.id
                else:  # Tuple/Attribute 复合形态：主正则不产生候选，防御归宽族
                    families[child.lineno] = "Exception"
                visit(child, prefix)
            else:
                visit(child, prefix)

    visit(tree, "")
    return symbols, families


def check_file(path: Path, waiver_keys: set[WaiverKey], used: set[WaiverKey]) -> list[str]:
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
            symbols: dict[int, str] | None = None  # 懒建：仅有命中时才解析 AST
            families: dict[int, str] = {}
            lines: list[str] = []
            for match in BARE_EXCEPT_RE.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                if symbols is None:
                    symbols, families = parse_code_map(text)
                    lines = text.splitlines()
                # 族判定（b30 回炉 major）：AST 处理器精确类型名优先——
                # Exception 前缀连写形态（ExceptionGroup 类）不得冒充
                # Exception 族消费豁免；无处理器（注释/字符串内文本命中）
                # 走行文本完整 token 回退，无类型捕获形态=bare
                family = families.get(line)
                if family is None:
                    token = re.match(r"\s*except\s+([A-Za-z_]\w*)", lines[line - 1])
                    family = token.group(1) if token else "bare"
                symbol = (symbols or {}).get(line, "<module>")
                key = (rel, symbol, family)
                if key in waiver_keys:
                    # b30 回炉 blocker：一条豁免至多消费一个处理器——
                    # 同键第二处必红（豁免不得批量放行同函数多处宽族）
                    if key in used:
                        problems.append(
                            f"{rel}:{line}: 裸/过宽 except（豁免键 {rel}#{symbol}"
                            f"[{family}] 已被消费——同键第二处宽族未登记，"
                            "须逐处审查登记或收窄）"
                        )
                    else:
                        used.add(key)
                    continue
                problems.append(
                    f"{rel}:{line}: 裸/过宽 except（用领域异常；豁免面"
                    f" gate_patterns.WIDE_EXCEPT_WAIVERS 键 {rel}#{symbol}"
                    f"[{family}] 未登记）"
                )
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
                "（安全红线：8000 不出容器网桥——处置见 docs/architecture.md"
                " §4.1 安全红线；WP1 收口回潮防护）"
            )
    return problems


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # AUDIT-#20：登记面校验先行（fail-fast——豁免表自身残缺时先红登记面）
    violations, waiver_keys = validate_waivers()
    used: set[WaiverKey] = set()
    count = 0
    for path in iter_files():
        count += 1
        violations.extend(check_file(path, waiver_keys, used))
    violations.extend(check_compose_port_mirror())
    for key in sorted(waiver_keys - used):
        # 豁免腐烂检测：登记未被任何违规消费=兜底已删除/函数改名/异常族
        # 变化——登记失效（键不是摆设），审查后清理或重登记。
        violations.append(
            f"宽族 except 豁免未消费：{key[0]}#{key[1]}[{key[2]}]"
            "（兜底已删除/函数改名/异常族变化——登记失效，审查后清理或重登记）"
        )
    if violations:
        print(f"[FAIL] grep 门禁（占位/裸异常/乱码/compose 端口）违规 {len(violations)} 处：")
        for item in violations:
            print(f"  - {item}")
        return 1
    print(
        f"[OK] grep 门禁：占位/裸 except/乱码计数 = 0 + compose 端口守卫通过"
        f"（扫描 {count} 个文件；宽族豁免消费 {len(used)}/{len(waiver_keys)}"
        "——登记面 gate_patterns.WIDE_EXCEPT_WAIVERS）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
