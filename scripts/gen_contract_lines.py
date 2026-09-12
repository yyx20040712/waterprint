"""file-contracts 行数注记生成器：表中「N 行」数字刷新为实体文件实数。

输入:  docs/file-contracts.md 表格行（首列反引号路径）+ 实体文件行数
输出:  注记数字就地重写（幂等——重跑零 diff）；违规清单（退出码 1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（GOV4 B1-2 / ADR-016，2026-09-12）：file-contracts.md 表内
# 「N 行」注记的数字段是生成物——行数变化后跑本脚本刷新，免手工
# 同步（check_file_budgets 注记一致性面=忘跑检测器，漂移即红）。
# 边界：注记的**在场/缺席仍是人审语义决策**（标记预算压力的行才
# 带）；本脚本只重写既有注记的数字，不给无注记行新增注记、不删
# 既有注记。解析与行数口径单源=check_file_budgets（同目录 import
# 先例=gen_same_layer_edges→check_module_graph，防两套解析漂移）。
# 用法：
#   python scripts/gen_contract_lines.py        刷新全部既有注记数字
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_file_budgets import (  # noqa: E402
    _ANNOTATION_RE,
    _line_count,
    CONTRACTS_DOC,
    REPO,
)


def refresh_line(line: str) -> tuple[str, str | None, str | None]:
    """单表行注记刷新。

    返回（新行, 路径, 违规消息）——路径非 None=该行带注记且已处理；
    违规消息非 None=歧义/指向不存在文件（fail-closed，调用方拒写出）。
    """
    if not line.startswith("| `"):
        return line, None, None
    rel = line.split("`")[1]
    matches = _ANNOTATION_RE.findall(line)
    if not matches:
        return line, None, None
    if len(matches) != 1:
        return line, None, f"{rel}: 行数注记歧义（{matches}）——须恰一，人工消歧"
    target = REPO / rel
    if not target.is_file():
        return line, None, f"{rel}: 注记指向不存在文件"
    actual = _line_count(target)
    new_line = _ANNOTATION_RE.sub(
        lambda m: m.group(0).replace(m.group(1), str(actual), 1), line, count=1
    )
    return new_line, rel, None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    text = CONTRACTS_DOC.read_text(encoding="utf-8")
    problems: list[str] = []
    refreshed = 0
    consistent = 0
    out_lines: list[str] = []
    for line in text.split("\n"):
        new_line, rel, problem = refresh_line(line)
        out_lines.append(new_line)
        if problem is not None:
            problems.append(problem)
        elif rel is not None:
            if new_line != line:
                refreshed += 1
            else:
                consistent += 1
    if problems:
        print(f"[FAIL] 行数注记面违规 {len(problems)} 处（未写出任何变更）：")
        for item in problems:
            print(f"  - {item}")
        return 1
    if refreshed:
        CONTRACTS_DOC.write_text("\n".join(out_lines), encoding="utf-8", newline="\n")
    print(
        f"[OK] 行数注记刷新：改写 {refreshed} 处 / 已吻合 {consistent} 处"
        "（幂等——重跑零 diff；注记在场/缺席仍人审定夺，ADR-016）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
