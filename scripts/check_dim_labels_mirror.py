"""dimLabels 镜像门禁：FE DIM_LABELS 键集 ↔ core DimKey 枚举成员对账。

输入:  core/waterprint/contracts/quantity.py（DimKey StrEnum 成员——
       AST 实读）+webapp/src/shared/dimLabels.ts（DIM_LABELS 词典键
       ——正则实读；零依赖门禁不 import core/不跑 node）
输出:  双向差集清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：工况面 UX 反馈批件 4 缺口②（2026-09-12）——FE DIM_LABELS 是
#   core CANONICAL_UNITS/DimKey 的显示层镜像（FIX-ACC1③）；core 新增
#   枚举成员漏同步 FE 词典即静默退化为原样返回（诚实呈现但无单位）。
#   本门禁 CI 一过即拦：双向键集差集非空=FAIL（新增 DimKey 成员必须
#   同步登记 DIM_LABELS；删除成员须同步删词典行）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUANTITY = REPO / "core" / "waterprint" / "contracts" / "quantity.py"
DIM_LABELS = REPO / "webapp" / "src" / "shared" / "dimLabels.ts"


def core_dim_members() -> set[str]:
    """DimKey StrEnum 成员名（class DimKey 体内赋值名——AST 实读）。"""
    tree = ast.parse(QUANTITY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "DimKey":
            members: set[str] = set()
            for stmt in node.body:
                targets: list[ast.expr] = []
                if isinstance(stmt, ast.Assign):
                    targets = stmt.targets
                elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                    targets = [stmt.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        members.add(target.id)
            return members
    raise SystemExit("[FAIL] 未找到 DimKey 枚举定义（core 契约面缺失）")


def fe_dim_labels() -> set[str]:
    """DIM_LABELS 词典键（TS 对象键行——`  FLOW: {` 形态正则实读）。"""
    text = DIM_LABELS.read_text(encoding="utf-8")
    block = re.search(r"const DIM_LABELS[^{]*\{(.*?)\n\};", text, re.DOTALL)
    if block is None:
        raise SystemExit("[FAIL] 未找到 DIM_LABELS 词典（FE 显示层缺失）")
    return set(re.findall(r"^  ([A-Z_]+): \{", block.group(1), re.MULTILINE))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    core = core_dim_members()
    fe = fe_dim_labels()
    core_only = core - fe
    fe_only = fe - core
    if core_only or fe_only:
        if core_only:
            print(f"[FAIL] core DimKey 成员缺 FE 词典登记：{sorted(core_only)}")
        if fe_only:
            print(f"[FAIL] FE DIM_LABELS 键无 core 枚举成员：{sorted(fe_only)}")
        return 1
    print(f"[OK] dimLabels 镜像：FE DIM_LABELS {len(fe)} 键与 core DimKey 成员一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
