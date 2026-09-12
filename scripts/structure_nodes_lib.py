"""structure-graph §1a 节点表共享库：加载·渲染·标记段单源。

输入:  core/pyproject.toml 与 server/pyproject.toml 的 import-linter
       layers 契约 + 固定三叶节点（webapp/data/api-contracts）
输出:  节点行三元组序列 / §1a 表格文本 / 标记段提取与替换
       （check_module_graph 校验端与 gen_structure_nodes 生成端共用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（GOV4 B1-3 / ADR-017，2026-09-12）：§1a 节点表数据行=自两
# pyproject 的 layers 契约（import-linter 实际消费的机器强制面）+
# 固定三叶节点展开的生成物；docs/structure-graph.md §1a 标记段内
# 禁手编（check_module_graph 比对渲染输出，漂移即红）。单源库防
# 校验端/生成端两套解析漂移（same_layer_lib 先例同型）。层 token
# 映射（组序→token）为库内既定知识：层重构=宪法级事件，须同步
# 本库映射并过评审——fail-closed（组数超映射即拒）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORE_PYPROJECT = REPO / "core" / "pyproject.toml"
SERVER_PYPROJECT = REPO / "server" / "pyproject.toml"

BEGIN_MARK = (
    "<!-- STRUCT-NODES:BEGIN（生成物——gen_structure_nodes.py 自两 pyproject"
    " layers 契约展开，标记段内禁手编；工序=改契约→跑生成器→门禁绿） -->"
)
END_MARK = "<!-- STRUCT-NODES:END -->"

# 层序（自上而下）；依赖边只许沿此序前进（to 的序号必须 > from 的序号）
LAYER_ORDER: tuple[str, ...] = (
    "L6", "L5.main", "L5.routers", "L5.services", "L5.jobs", "L5.settings",
    "L4.cli", "L4.app", "L4.project-trace", "L3", "L2", "L1", "L0",
    "DATA", "CONTRACT",
)
# core layers 契约组序 → 层 token（L4 三行子层：cli=0 → app=1 →
# project|trace=2，与 pyproject 拆分一致——check_module_graph 旧常量迁移）
CORE_TOKEN_OF_GROUP: tuple[str, ...] = (
    "L4.cli", "L4.app", "L4.project-trace", "L3", "L2", "L1", "L0",
)
SERVER_TOKEN_OF_GROUP: tuple[str, ...] = (
    "L5.main", "L5.routers", "L5.services", "L5.jobs", "L5.settings",
)
# 非模块叶节点（不源自任何 pyproject 契约）：webapp 前端 / 数据包 /
# API 契约——固定声明，路径变更=人工同步本表
FIXED_NODES: tuple[tuple[str, str, str], ...] = (
    ("webapp", "L6", "webapp/src"),
    ("data", "DATA", "data"),
    ("api-contracts", "CONTRACT", "api-contracts"),
)

# 内核层 token → pyproject import-linter layers 契约（第一条）的层序号
CORE_LAYER_OF_TOKEN: dict[str, int] = {
    token: idx for idx, token in enumerate(CORE_TOKEN_OF_GROUP)
}


def _pyproject_rows(
    pyproject: Path, prefix: str, token_of_group: tuple[str, ...]
) -> list[tuple[str, str, str]]:
    """单根 pyproject 的 layers 契约 → 节点行（模块→token→仓库相对路径）。

    layers 契约应恰有一份（多契约=人工分诊面）；组序超出 token 映射=
    层重构事件（fail-closed 拒猜）；模块在仓库无目录/文件对应=拒。
    """
    rel_repo = pyproject.relative_to(REPO).as_posix()
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    contracts = [
        c for c in data["tool"]["importlinter"]["contracts"]
        if c.get("type") == "layers"
    ]
    if len(contracts) != 1:
        raise ValueError(
            f"{rel_repo}: layers 契约应恰有一份（实测 {len(contracts)}）"
            "——多契约须人工分诊 structure_nodes_lib 取数面"
        )
    rows: list[tuple[str, str, str]] = []
    groups = contracts[0]["layers"]
    if len(groups) > len(token_of_group):
        raise ValueError(
            f"{rel_repo}: layers 组数 {len(groups)} 超出既定 token 映射"
            f"（{len(token_of_group)}）——层重构须同步 structure_nodes_lib"
        )
    for idx, group in enumerate(groups):
        token = token_of_group[idx]
        for mod in group.split("|"):
            mod = mod.strip()
            rel = f"{prefix}/{mod.replace('.', '/')}"
            if (REPO / rel).is_dir():
                rows.append((mod, token, rel))
            elif (REPO / (rel + ".py")).is_file():
                rows.append((mod, token, rel + ".py"))
            else:
                raise ValueError(f"{rel_repo}: 模块 {mod} 在仓库无对应路径（{rel}）")
    return rows


def load_node_rows() -> list[tuple[str, str, str]]:
    """全部 §1a 节点行（core+server 契约派生 + 固定三叶），按层序稳定排序。

    同层内保持 pyproject 声明序（稳定排序）——渲染输出与手维护时代
    的既有表序逐行一致（首跑零漂移的构造性保证）。
    """
    rows: list[tuple[str, str, str]] = list(FIXED_NODES)
    rows += _pyproject_rows(CORE_PYPROJECT, "core", CORE_TOKEN_OF_GROUP)
    rows += _pyproject_rows(SERVER_PYPROJECT, "server", SERVER_TOKEN_OF_GROUP)
    return sorted(rows, key=lambda r: LAYER_ORDER.index(r[1]))


def render_table(rows: list[tuple[str, str, str]]) -> str:
    """节点行 → §1a 表格文本（表头+分隔行+数据行，全角列名与既有表一致）。"""
    lines = ["| 节点 | 层 | 对应路径 |", "|------|----|----------|"]
    lines += [f"| `{node}` | {token} | `{rel}` |" for node, token, rel in rows]
    return "\n".join(lines)


def extract_segment(text: str) -> str | None:
    """标记段内容（BEGIN/END 之间，去首尾空行）；任一标记缺失=None。"""
    begin = text.find(BEGIN_MARK)
    if begin < 0:
        return None
    end = text.find(END_MARK, begin)
    if end < 0:
        return None
    return text[begin + len(BEGIN_MARK):end].strip("\n")


def replace_segment(text: str, content: str) -> str:
    """标记段内容整体替换（幂等：内容=渲染输出时重跑零 diff）。"""
    begin = text.find(BEGIN_MARK)
    end = text.find(END_MARK, begin)
    return (
        text[:begin + len(BEGIN_MARK)] + "\n" + content + "\n" + text[end:]
    )
