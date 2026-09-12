"""§1a 节点表生成器：两 pyproject layers 契约 → structure-graph §1a 展开。

输入:  core/pyproject.toml 与 server/pyproject.toml 的 import-linter
       layers 契约 + 固定三叶节点（structure_nodes_lib 取数）
输出:  docs/structure-graph.md §1a 的 STRUCT-NODES:BEGIN/END 标记段
       重写（幂等——重跑零 diff）；退出码 0=成功，1=标记缺失/取数失败
"""

# ══════════════════════════════════════════════════════════════════
# 规格（GOV4 B1-3 / ADR-017）：§1a 节点表数据行是生成物——真源=两
# pyproject 的 layers 契约（import-linter 实际消费面）+固定三叶。
# 工序=改 pyproject 契约 → 跑本脚本 → 门禁绿（check_module_graph
# 比对渲染输出，忘跑即红）。标记段外（表头说明/层序注记/§1b/§1c）
# 零触碰；标记段内手编属违规（「与渲染输出不符」面拦截）。取数与
# 渲染单源=structure_nodes_lib（校验端共用，防两套解析漂移）。
# 用法：
#   python scripts/gen_structure_nodes.py        重写 §1a 标记段
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from structure_nodes_lib import (  # noqa: E402
    extract_segment,
    load_node_rows,
    render_table,
    replace_segment,
)

GRAPH_MD = Path(__file__).resolve().parent.parent / "docs" / "structure-graph.md"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        rows = load_node_rows()
    except ValueError as exc:
        print(f"[FAIL] 节点取数失败（fail-closed，未写出任何变更）：{exc}")
        return 1
    content = render_table(rows)
    text = GRAPH_MD.read_text(encoding="utf-8")
    if extract_segment(text) is None:
        print("[FAIL] §1a 缺 STRUCT-NODES:BEGIN/END 标记段"
              "（标记=手工脚手架，一次性插入；内容自本脚本展开）")
        return 1
    if extract_segment(text) == content:
        print(f"[OK] §1a 节点表已是生成物形态：{len(rows)} 节点零 diff"
              "（幂等——重跑零 diff；标记段内禁手编，ADR-017）")
        return 0
    GRAPH_MD.write_text(
        replace_segment(text, content), encoding="utf-8", newline="\n"
    )
    print(f"[OK] §1a 节点表展开：{len(rows)} 节点 → 标记段重写"
          "（git diff 审阅；忘跑检测器=check_module_graph 渲染比对面）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
