"""同层边生成器：structure-graph.md §1c 声明块 → core/pyproject.toml 展开。

输入:  docs/structure-graph.md §1c toml 围栏块（唯一声明面，ADR-014）
输出:  core/pyproject.toml 两契约 ignore_imports 的
       `SAME-LAYER-EDGES:BEGIN/END` 标记段重写（幂等——重跑零 diff）；
       退出码 0=成功，1=声明块缺失/标记段缺失/写入失败
"""

# ══════════════════════════════════════════════════════════════════
# 规格：GOV2 ADR-014（同层边一等公民化）。同层边唯一声明面=structure-
# graph.md §1c 机器声明块；本脚本把声明展开为 import-linter 两契约的
# ignore_imports 生成段（layers 契约=全部边；L3 independence 契约=
# independence=true 的边），条目注释行由 note 字段生成。新增同层边
# 工序=编辑 §1c 块 → 跑本脚本 → 门禁绿（check_module_graph 双向对照
# pyproject，忘跑=门禁红）。标记段外的一切 pyproject 内容零触碰；
# 标记段内手编属违规（门禁「多出」面拦截）。
# 解析单源=check_module_graph.parse_same_layer_edges/expand_ignore_entry
# （同目录 import 先例=check_grep_gates→gate_patterns）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_module_graph import GRAPH_MD, PYPROJECT, sections  # noqa: E402
from same_layer_lib import expand_ignore_entry, parse_same_layer_edges  # noqa: E402

BEGIN_MARK = "# SAME-LAYER-EDGES:BEGIN（生成物——gen_same_layer_edges.py 自 §1c 声明块展开，标记段内禁手编）"
END_MARK = "# SAME-LAYER-EDGES:END"


def render_block(
    edges: list[tuple[str, str, bool, bool, str]], independence_only: bool
) -> list[str]:
    """声明边 → 标记段内容行（条目+note 注释行；independence_only 分契约）。

    注释行=# <from> → <to>：note（声明块 note 即 pyproject 先例注记真源）。
    BEGIN/END 标记行零缩进（重写锚以行首为界——幂等保证）。
    """
    lines: list[str] = [BEGIN_MARK]
    for from_mod, to_mod, ind, glob, note in edges:
        if independence_only and not ind:
            continue
        lines.append(f"    # {from_mod} → {to_mod}：{note}")
        lines.append(f'    "{expand_ignore_entry(from_mod, to_mod, glob)}",')
    lines.append(END_MARK)
    return lines


def _line_start(text: str, pos: int) -> int:
    """标记位置回退到所在行行首（含缩进一并重写——幂等：不残留旧缩进）。"""
    while pos > 0 and text[pos - 1] in " \t":
        pos -= 1
    return pos


def rewrite_section(
    text: str, edges: list[tuple[str, str, bool, bool, str]]
) -> str | None:
    """重写 pyproject 中一处标记段（按 contracts 出现序：先 layers 后 L3）。

    返回新文本；找不到成对标记= None（调用方 FAIL——fail-closed）。
    """
    begin = text.find(BEGIN_MARK)
    if begin < 0:
        return None
    begin = _line_start(text, begin)
    end = text.find(END_MARK, begin)
    if end < 0:
        return None
    end += len(END_MARK)
    return text[:begin] + "\n".join(render_block(edges, False)) + text[end:]


def rewrite_l3_section(
    text: str, edges: list[tuple[str, str, bool, bool, str]]
) -> str | None:
    """重写第二处标记段（L3 independence 契约内——independence=true 边）。"""
    first = text.find(BEGIN_MARK)
    if first < 0:
        return None
    begin = text.find(BEGIN_MARK, first + len(BEGIN_MARK))
    if begin < 0:
        return None
    begin = _line_start(text, begin)
    end = text.find(END_MARK, begin)
    if end < 0:
        return None
    end += len(END_MARK)
    return text[:begin] + "\n".join(render_block(edges, True)) + text[end:]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parts = sections(GRAPH_MD.read_text(encoding="utf-8"))
    same_layer_sec = next(
        (v for k, v in parts.items() if k.startswith("1c.")), ""
    )
    edges = parse_same_layer_edges(same_layer_sec)
    if not edges:
        print("[FAIL] §1c 同层边声明块缺失或为空（唯一声明面不得清空）")
        return 1
    text = PYPROJECT.read_text(encoding="utf-8")
    text = rewrite_section(text, edges)
    if text is None:
        print("[FAIL] core/pyproject.toml 缺第一处 SAME-LAYER-EDGES 标记段"
              "（layers 契约 ignore_imports 内）")
        return 1
    text = rewrite_l3_section(text, edges)
    if text is None:
        print("[FAIL] core/pyproject.toml 缺第二处 SAME-LAYER-EDGES 标记段"
              "（L3 independence 契约 ignore_imports 内）")
        return 1
    PYPROJECT.write_text(text, encoding="utf-8", newline="\n")
    ind_count = sum(1 for _, _, ind, _, _ in edges if ind)
    print(f"[OK] 同层边展开：{len(edges)} 条边 → pyproject 两契约标记段"
          f"（layers 全量 / L3 independence {ind_count} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
