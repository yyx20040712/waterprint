"""同层边声明块共享库：§1c 解析+展开+两面校验（check_module_graph 与
gen_same_layer_edges 的单源依赖）。

输入:  structure-graph.md §1c 节正文（toml 围栏块）+ core/pyproject.toml
       + §1a 节点表与节点归一函数（调用方注入——防循环依赖）
输出:  解析结果 [(from, to, independence, glob, note)] 与校验问题清单
"""

# ══════════════════════════════════════════════════════════════════
# 规格：ADR-014（同层边一等公民化）。同层边唯一声明面=structure-graph
# §1c 机器声明块；本库是其全部机器语义的单源——check_module_graph
# （门禁消费：真实 import 豁免面+pyproject 双向对照）与
# gen_same_layer_edges（生成消费：标记段重写）共用，防两套解析漂移。
# glob=True 时 pyproject 展开为 `<from>.* -> <to>`（grimp 精确模块匹配
# 语义——importer 为包子模块的边需要通配，先例 ifc_export.builder）。
# fail-closed：块缺失/空=问题清单非空（防声明面被静默清空后退化为
# 零豁免+全库真实 import 误报）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
import tomllib
from collections.abc import Callable
from pathlib import Path

_SAME_LAYER_FENCE = re.compile(r"^```toml\s*$")
_SAME_LAYER_END = re.compile(r"^```\s*$")


def parse_same_layer_edges(body: str) -> list[tuple[str, str, bool, bool, str]]:
    """§1c 节正文 → [(from, to, independence, glob, note)]。

    围栏 ```toml 块内 tomllib 解析；无围栏块=空列表（空否由
    check_same_layer_block 判 FAIL）。
    """
    lines: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if not in_fence and _SAME_LAYER_FENCE.match(line):
            in_fence = True
            continue
        if in_fence and _SAME_LAYER_END.match(line):
            break
        if in_fence:
            lines.append(line)
    if not lines:
        return []
    data = tomllib.loads("\n".join(lines))
    return [
        (
            edge["from"],
            edge["to"],
            bool(edge.get("independence", False)),
            bool(edge.get("glob", False)),
            str(edge.get("note", "")),
        )
        for edge in data.get("edge", [])
    ]


def expand_ignore_entry(from_mod: str, to_mod: str, glob: bool) -> str:
    """声明边 → pyproject ignore_imports 条目字符串（生成器同款单源）。"""
    importer = f"{from_mod}.*" if glob else from_mod
    return f"{importer} -> {to_mod}"


def check_same_layer_block(
    edges: list[tuple[str, str, bool, bool, str]],
    nodes: dict[str, tuple[str, str]],
    resolve: Callable[[str, dict[str, tuple[str, str]]], str | None],
) -> list[str]:
    """§1c 声明块完整性（ADR-014）：非空、无重复、两端确为同层节点。

    同层性=两端经节点归一（调用方注入的 resolve）到 §1a 后层 token 相等
    ——防把向下边塞进声明块绕过 §1b 边表（fail-closed）。
    """
    if not edges:
        return ["§1c 同层边声明块缺失或为空（唯一声明面不得清空——ADR-014）"]
    problems: list[str] = []
    seen: set[tuple[str, str]] = set()
    for from_mod, to_mod, _, _, _ in edges:
        pair = (from_mod, to_mod)
        if pair in seen:
            problems.append(f"§1c 声明块重复边：{from_mod} → {to_mod}")
        seen.add(pair)
        src = resolve(from_mod, nodes)
        dst = resolve(to_mod, nodes)
        if src is None or dst is None:
            problems.append(
                f"§1c 边端点未归一到 §1a 节点：{from_mod} → {to_mod}"
            )
            continue
        if nodes[src][0] != nodes[dst][0]:
            problems.append(
                f"§1c 非同层边（同层边才可入声明块；向下边走 §1b 边表）："
                f"{from_mod}({nodes[src][0]}) → {to_mod}({nodes[dst][0]})"
            )
    return problems


def check_same_layer_pyproject(
    edges: list[tuple[str, str, bool, bool, str]],
    pyproject: Path,
) -> list[str]:
    """§1c 声明块 ↔ core/pyproject 两契约 ignore_imports 双向对照（ADR-014）。

    layers 契约应恰含全部同层边展开条目；L3 independence 契约应恰含
    independence=true 的边。多/少即 FAIL——忘跑 gen_same_layer_edges.py
    = 门禁红（CI 与本地同拦，pyproject 标记段是生成物禁手编）。
    """
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    layers_contract = next(
        (
            c
            for c in data["tool"]["importlinter"]["contracts"]
            if c.get("type") == "layers"
        ),
        None,
    )
    l3_contract = next(
        (
            c
            for c in data["tool"]["importlinter"]["contracts"]
            if c.get("type") == "independence"
            and any(m == "waterprint.graph" for m in c.get("modules", []))
        ),
        None,
    )
    problems: list[str] = []
    if layers_contract is None or l3_contract is None:
        return ["pyproject 缺 layers 或 L3 independence 契约（结构异常）"]
    expected_layers = {
        expand_ignore_entry(f, t, g) for f, t, _, g, _ in edges
    }
    expected_l3 = {
        expand_ignore_entry(f, t, g) for f, t, ind, g, _ in edges if ind
    }
    actual_layers = set(layers_contract.get("ignore_imports", []))
    actual_l3 = set(l3_contract.get("ignore_imports", []))
    for name, expected, actual in (
        ("layers 契约", expected_layers, actual_layers),
        ("L3 independence 契约", expected_l3, actual_l3),
    ):
        for extra in sorted(actual - expected):
            problems.append(
                f"pyproject {name} ignore_imports 多出（§1c 声明块无此边——"
                f"手编标记段违 ADR-014，请改声明块后跑生成器）：{extra}"
            )
        for missing in sorted(expected - actual):
            problems.append(
                f"pyproject {name} ignore_imports 缺失（声明块已声明——"
                f"跑 scripts/gen_same_layer_edges.py 展开）：{missing}"
            )
    return problems
