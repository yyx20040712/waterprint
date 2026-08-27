"""结构图谱门禁：docs/structure-graph.md 三表一致性与分层方向校验。

输入:  docs/structure-graph.md + core/pyproject.toml（import-linter 层序）+ 目录树
       + core/waterprint 与 server/waterprint_server 源码（真实 import 面）
输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明：AGENTS.md §13 结构图谱规则。校验六件事：
#   a) §1a 节点表：节点对应路径存在；层归属与 pyproject import-linter
#      第一条 layers 契约双源一致（互相覆盖，漏一边 = 失败）；
#   b) §1b 边表：两端节点已声明；方向沿层序严格向下（同层/向上 = 失败）；
#      依赖图无环（Kahn）；
#   c) §3 单元总表 ↔ file-contracts.md §3 包登记 ↔ units_lib 实际目录
#      三方一致，恰好 32 包；
#   d) §2 调用链中引用的仓库路径真实存在（防"链路指向幽灵文件"）；
#   e) pyproject"工艺单元包互相独立"independence 契约逐包列出实际单元包，
#      模块集合与目录实际单元包集合双向一致（数量与名字；漏列/多列/退回
#      线级粒度 = 失败，DS-01 裁决的机器防线）；
#   f) 真实 import ⊆ §1b 声明边（B3 收口——ENG2 D5/R1-b 裁决 2026-08-27）：
#      stdlib ast 扫描 core/waterprint/** 与 server/waterprint_server/**
#      （排除任意 tests 目录），import 目标解析到 §1a 节点粒度（同节点内
#      import 忽略——跨单元互 import 由 independence 契约另行强制），
#      违者 FAIL 输出 from→to+文件清单。三条硬编码规则：
#      ① `if TYPE_CHECKING:` 块内 import 豁免（类型面依赖——UF-31 口径，
#         contracts/unit_api.py 在册先例）；
#      ② 唯一同层豁免对 `waterprint.app → waterprint.app_enumeration`
#         （SERVER D1 2026-08-26 同层伴生边，§1b 后注记承载不入边表——
#         "严格向下"规则与边表均不为其放开）；
#      ③ stdlib/三方 import 忽略（只认 waterprint*/waterprint_server*
#         且命中 §1a 节点者）。§1a 之外的伴生 .py（ifc_export 占位等）
#      节点粒度不覆盖。零依赖纯标准库（ast），py3.12/3.13 双兼容
#      （gates job 系统 py3.13 消费本脚本）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
import sys
import tomllib
from collections.abc import Iterator
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRAPH_MD = REPO / "docs" / "structure-graph.md"
CONTRACTS_MD = REPO / "docs" / "file-contracts.md"
PYPROJECT = REPO / "core" / "pyproject.toml"
UNITS_ROOT = REPO / "core" / "waterprint" / "units_lib"
SCAN_PY_ROOTS: tuple[Path, ...] = (
    REPO / "core" / "waterprint",
    REPO / "server" / "waterprint_server",
)
# 唯一同层豁免对（规则②：§1b 后注记承载——同层伴生边不入边表）
_SAME_LAYER_EXEMPT: tuple[str, str] = ("waterprint.app", "waterprint.app_enumeration")

# 层序（自上而下）；依赖边只许沿此序前进（to 的序号必须 > from 的序号）
LAYER_ORDER: tuple[str, ...] = (
    "L6", "L5.main", "L5.routers", "L5.services", "L5.jobs", "L5.settings",
    "L4.cli", "L4.app", "L4.project-trace", "L3", "L2", "L1", "L0",
    "DATA", "CONTRACT",
)
# 内核层 token → pyproject import-linter layers 契约（第一条）的层序号
# （L4 为三行子层：cli=0 → app=1 → project|trace=2，与 pyproject 拆分一致）
CORE_LAYER_OF_TOKEN: dict[str, int] = {
    "L4.cli": 0, "L4.app": 1, "L4.project-trace": 2,
    "L3": 3, "L2": 4, "L1": 5, "L0": 6,
}
EXPECTED_UNIT_COUNT = 32
UNIT_LINE_DIRS = ("municipal", "mine_water", "sludge", "conveyance")

NODE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([A-Za-z0-9.\-]+)\s*\|\s*`([^`]+)`")
EDGE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`")
UNIT_ROW = re.compile(r"^\|\s*`([^`]+/)`\s*\|")
TICK = re.compile(r"`([^`]+)`")
HEADING = re.compile(r"^#{2,3}\s+(.*)$")


def sections(text: str) -> dict[str, str]:
    """按 ##/### 标题切块；返回 {标题: 正文}（首个标题之前的内容丢弃）。"""
    chunks: dict[str, str] = {}
    title = ""
    buf: list[str] = []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            if title:
                chunks[title] = "\n".join(buf)
            title = match.group(1).strip()
            buf = []
        elif title:
            buf.append(line)
    if title:
        chunks[title] = "\n".join(buf)
    return chunks


def parse_nodes(body: str) -> dict[str, tuple[str, str]]:
    """节点表 → {节点 id: (层 token, 仓库相对路径)}。"""
    nodes: dict[str, tuple[str, str]] = {}
    for line in body.splitlines():
        match = NODE_ROW.match(line)
        if match:
            nodes[match.group(1)] = (match.group(2), match.group(3))
    return nodes


def parse_edges(body: str) -> list[tuple[str, str]]:
    """边表 → [(from, to)]（每行前两个反引号字段）。"""
    edges: list[tuple[str, str]] = []
    for line in body.splitlines():
        match = EDGE_ROW.match(line)
        if match:
            edges.append((match.group(1), match.group(2)))
    return edges


def parse_unit_rows(body: str) -> set[str]:
    """单元总表 → 包路径集合（首列反引号；去尾部斜杠归一化）。"""
    return {
        match.group(1).rstrip("/")
        for match in (UNIT_ROW.match(line) for line in body.splitlines())
        if match
    }


def parse_chain_paths(body: str) -> list[str]:
    """调用链表 → 其中形如仓库路径的反引号 token（含 / 且无空格）。"""
    tokens = TICK.findall(body)
    return [
        token for token in tokens
        if "/" in token and " " not in token and not token.startswith("http")
    ]


def check_nodes_exist(nodes: dict[str, tuple[str, str]]) -> list[str]:
    problems = []
    for node, (token, rel) in sorted(nodes.items()):
        if token not in LAYER_ORDER:
            problems.append(f"§1a 未知层 token：{node} = {token}")
        if not (REPO / rel).exists():
            problems.append(f"§1a 节点路径不存在：{node} → {rel}")
    return problems


def check_edges(nodes: dict[str, tuple[str, str]],
                edges: list[tuple[str, str]]) -> list[str]:
    problems = []
    for src, dst in edges:
        if src not in nodes or dst not in nodes:
            problems.append(f"§1b 边引用未声明节点：{src} → {dst}")
            continue
        src_token, dst_token = nodes[src][0], nodes[dst][0]
        if src_token not in LAYER_ORDER or dst_token not in LAYER_ORDER:
            continue  # 未知层 token 已由 check_nodes_exist 报告
        if LAYER_ORDER.index(dst_token) <= LAYER_ORDER.index(src_token):
            problems.append(
                f"§1b 依赖方向违规（须沿层序向下）：{src}({src_token}) → "
                f"{dst}({dst_token})"
            )
    return problems


def check_acyclic(nodes: dict[str, tuple[str, str]],
                  edges: list[tuple[str, str]]) -> list[str]:
    indegree = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for src, dst in edges:
        if src in outgoing and dst in indegree:
            outgoing[src].append(dst)
            indegree[dst] += 1
    ready = [node for node, deg in indegree.items() if deg == 0]
    seen = 0
    while ready:
        node = ready.pop()
        seen += 1
        for nxt in outgoing[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
    if seen != len(nodes):
        return ["§1b 依赖图存在环（Kahn 拓扑未覆盖全部节点）"]
    return []


def check_pyproject_sync(nodes: dict[str, tuple[str, str]]) -> list[str]:
    problems: list[str] = []
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    contract = data["tool"]["importlinter"]["contracts"][0]
    declared: dict[str, int] = {}
    for idx, group in enumerate(contract["layers"]):
        for mod in group.split("|"):
            declared[mod.strip()] = idx
    for mod, idx in sorted(declared.items()):
        if mod not in nodes:
            problems.append(f"import-linter 模块未入图谱 §1a：{mod}")
            continue
        token = nodes[mod][0]
        if CORE_LAYER_OF_TOKEN.get(token) != idx:
            problems.append(f"§1a 层归属与 import-linter 不一致：{mod}")
    for node, (token, _) in sorted(nodes.items()):
        if token in CORE_LAYER_OF_TOKEN and node not in declared:
            problems.append(f"§1a 内核节点未出现在 import-linter 契约：{node}")
    return problems


def actual_unit_dirs() -> set[str]:
    """实际单元包 = 业务线目录下含 __init__.py 的子目录（排除 __pycache__ 等运行时产物）。"""
    found: set[str] = set()
    for line_dir in UNIT_LINE_DIRS:
        root = UNITS_ROOT / line_dir
        if not root.is_dir():
            continue
        for pkg in sorted(root.iterdir()):
            if pkg.is_dir() and (pkg / "__init__.py").is_file():
                found.add(pkg.relative_to(REPO).as_posix())
    return found


def contracts_packages() -> set[str]:
    text = CONTRACTS_MD.read_text(encoding="utf-8")
    found = {
        match.group(1).rstrip("/")
        for match in (UNIT_ROW.match(line) for line in text.splitlines())
        if match
    }
    return found - {f"core/waterprint/units_lib/_template"}


def check_units(graph_units: set[str]) -> list[str]:
    problems: list[str] = []
    fc = contracts_packages()
    actual = actual_unit_dirs()
    for name, extra in (
        ("职责表 §3", sorted(fc - actual)),
        ("图谱 §3", sorted(graph_units - actual)),
        ("实际目录", sorted(actual - graph_units)),
    ):
        for rel in extra:
            problems.append(f"单元包三方不一致（{name} 多出）：{rel}")
    for rel in sorted(fc - graph_units):
        problems.append(f"职责表 §3 有而图谱 §3 无：{rel}")
    if len(actual) != EXPECTED_UNIT_COUNT:
        problems.append(f"单元包数量为 {len(actual)}，应为 {EXPECTED_UNIT_COUNT}")
    return problems


def check_independence_units() -> list[str]:
    """independence 契约（工艺单元包互相独立）模块集 ↔ 实际单元包集双向一致。

    契约必须逐包列出全部实际单元包（32 个）；漏列一个包或退回线级粒度
    （municipal 等目录模块不是单元包）都视为失败——线级粒度拦不住同线
    单元互 import（DS-01）。
    """
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    declared: set[str] = set()
    for contract in data["tool"]["importlinter"]["contracts"]:
        if contract.get("type") != "independence":
            continue
        declared |= {
            mod
            for mod in contract.get("modules", [])
            if mod.startswith("waterprint.units_lib.")
        }
    actual = {
        rel.removeprefix("core/").replace("/", ".")
        for rel in actual_unit_dirs()
    }
    problems = [
        f"independence 契约列出的不是实际单元包：{mod}"
        for mod in sorted(declared - actual)
    ]
    problems += [
        f"independence 契约漏列单元包：{mod}"
        for mod in sorted(actual - declared)
    ]
    return problems


def check_chains(body: str) -> list[str]:
    problems = []
    for token in parse_chain_paths(body):
        if not (REPO / token).exists():
            problems.append(f"§2 调用链引用的路径不存在：{token}")
    return problems


# ── f) 真实 import 扫描（规则①②③见文件头规格说明）────────────────

def module_of(rel: str) -> tuple[str, bool]:
    """仓库相对路径 → (模块点名, 是否包 __init__)。

    core/、server/ 前缀剥除（§1a 节点即模块名）；__init__.py 归一为包本身
    （相对导入的包基点语义）。
    """
    parts = rel.split("/")
    if parts[0] in {"core", "server"}:
        parts = parts[1:]
    is_package = parts[-1] == "__init__.py"
    if is_package:
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".py")]
    return ".".join(parts), is_package


def resolve_node(module: str, nodes: dict[str, tuple[str, str]]) -> str | None:
    """模块 → §1a 节点（最长前缀且模块边界对齐：==N 或 startswith(N+".")）。

    无命中=None（裸包根/§1a 之外伴生件——节点粒度不覆盖，规则③同面忽略）。
    """
    best = ""
    for node in nodes:
        if (module == node or module.startswith(node + ".")) and len(node) > len(best):
            best = node
    return best or None


def is_type_checking_test(test: ast.expr) -> bool:
    """规则①判定面：`if TYPE_CHECKING:`（Name）或 `if typing.TYPE_CHECKING:`（Attribute）。"""
    return (
        isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"
    ) or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def iter_import_targets(
    tree: ast.Module, module: str, is_package: bool
) -> Iterator[tuple[str, int]]:
    """AST 内全部 import 目标（模块名+行号）；TYPE_CHECKING 体豁免（规则①）。

    `from waterprint import app` 一并归入 waterprint.app（包级别名=子模块
    依赖，候选=module 与 module.别名，命中 §1a 节点者生效——规则③天然
    滤掉 stdlib/三方与属性符号）。相对导入按源文件包基点解析。
    """
    package_parts = module.split(".")
    if not is_package:
        package_parts = package_parts[:-1]
    pending: list[tuple[ast.AST, bool]] = [(tree, False)]
    while pending:
        node, skip = pending.pop()
        if isinstance(node, ast.If) and is_type_checking_test(node.test):
            pending.extend((child, True) for child in ast.iter_child_nodes(node))
            continue
        if not skip and isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif not skip and isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    yield node.module, node.lineno
                    for alias in node.names:
                        yield f"{node.module}.{alias.name}", node.lineno
            elif node.level <= len(package_parts):
                base = package_parts[: len(package_parts) - (node.level - 1)]
                prefix = ".".join(base)
                head = f"{prefix}.{node.module}" if node.module else prefix
                yield head, node.lineno
                for alias in node.names:
                    yield f"{head}.{alias.name}", node.lineno
        pending.extend((child, skip) for child in ast.iter_child_nodes(node))


def check_real_imports(
    nodes: dict[str, tuple[str, str]], edges: list[tuple[str, str]]
) -> list[str]:
    """f) 跨节点真实 import ⊆ §1b 声明边（违者中文清单：from→to+现场）。"""
    declared = {(src, dst) for src, dst in edges if src in nodes and dst in nodes}
    declared.add(_SAME_LAYER_EXEMPT)
    violations: dict[tuple[str, str], list[str]] = {}
    for root in SCAN_PY_ROOTS:
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if "tests" in path.relative_to(REPO).parts:
                continue
            module, is_package = module_of(rel)
            source = resolve_node(module, nodes)
            if source is None:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError) as exc:
                violations.setdefault(("-", "-"), []).append(f"{rel}: 解析失败 {exc}")
                continue
            for target, lineno in iter_import_targets(tree, module, is_package):
                dst = resolve_node(target, nodes)
                if dst is None or dst == source:  # 规则③滤面/同节点忽略
                    continue
                if (source, dst) in declared:
                    continue
                violations.setdefault((source, dst), []).append(f"{rel}:{lineno}")
    return [
        f"未声明依赖边（真实 import 越 §1b 声明面）：{src} → {dst}"
        f"（{len(sites)} 处，如 {sites[0]}）"
        for (src, dst), sites in sorted(violations.items())
    ]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    parts = sections(GRAPH_MD.read_text(encoding="utf-8"))
    node_sec = next((v for k, v in parts.items() if k.startswith("1a.")), "")
    edge_sec = next((v for k, v in parts.items() if k.startswith("1b.")), "")
    chain_sec = next((v for k, v in parts.items() if k.startswith("2.")), "")
    unit_sec = next((v for k, v in parts.items() if k.startswith("3.")), "")

    nodes = parse_nodes(node_sec)
    edges = parse_edges(edge_sec)
    problems += check_nodes_exist(nodes)
    problems += check_edges(nodes, edges)
    problems += check_acyclic(nodes, edges)
    problems += check_pyproject_sync(nodes)
    problems += check_units(parse_unit_rows(unit_sec))
    problems += check_independence_units()
    problems += check_chains(chain_sec)
    problems += check_real_imports(nodes, edges)

    if problems:
        print(f"[FAIL] 结构图谱违规 {len(problems)} 处：")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(
        f"[OK] 结构图谱：{len(nodes)} 节点 / {len(edges)} 依赖边全部沿层序向下、"
        f"无环、与 import-linter 一致；单元包三方一致（{EXPECTED_UNIT_COUNT} 包）"
        f"且 independence 契约逐包吻合；调用链路径全部存在；"
        f"真实 import 全库扫描 ⊆ §1b 声明边（含同层豁免对）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
