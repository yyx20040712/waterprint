"""门禁聚合入口：一键运行全部架构门禁脚本（CI 与本地同口径）。

输入:  无
输出:  各门禁 PASS/FAIL 汇总（退出码 0=全绿，1=有失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：门禁清单与 AGENTS.md §2/§3、docs/file-contracts.md §4 一致；
# ruff 经 check_ruff.py、mypy 经 check_mypy.py（均逐根各自 venv 依赖、
# 互不代偿）聚合入列——与 CI core/server quality job 对齐（T7a C416
# 教训；mypy=conv-golden 批 2026-10-02 executor.py:280 arg-type 逃逸
# 教训同族第三例）；pytest 仍属 CI/venv 单独跑；其余为零依赖门禁
# （系统 Python 直接可跑）。
# 第十门禁 check_trust_root.py（外审整改#3 H1）：三信任根变更须带
# [HUMAN-LOCK]（AGENTS §7）——门禁数基线 9→10（WP2 台账）。
# 第十一门禁 check_deprecation_gate.py（TD1 2026-09-09）：GR-21
# 弃用到期门禁——门禁数基线 10→11（TD1 台账）。
# 第十二门禁 check_lint_imports.py（GOV2 2026-09-12）：双根
# lint-imports 本地聚合（CI quality job 同款口径——n+42 UF-33 挂账
# 盲区销账，check_ruff 双根三态先例同制）——门禁数基线 11→12
# （GOV2 台账；import-linter 自此本地门禁化，mypy 单独跑）。
# 第十三门禁 check_out_dims_consistency.py（工况面 UX 反馈批件 4
# 2026-09-12）：out_dims.dim 三写面对账——manifest 声明必须=①公式表
# output_dim/②projection dim_of 镜像（真源单归；AST 静态实读零依赖）
# ——门禁数基线 12→13。
# 第十五门禁 check_model_names.py（清洗批 2026-09-16）：源码不得
# 出现 AI 模型代号（与"独立开发"口径冲突的过程痕迹；词表拼接构造防
# 自匹配，scripts/ 不在扫描面）——门禁数基线 14→15。
# 第十四门禁 check_dim_labels_mirror.py（同批件 4 缺口②）：FE
# DIM_LABELS 键集 ↔ core DimKey 枚举成员双向对账（新增枚举漏同步词典
# 即拦）——门禁数基线 13→14。
# 第十六门禁 check_family_parity.py（G-1 治理小批 2026-09-19 用户直排
# 工单①）：aao/cass 同族公式族结构恒等机器断言+显式 delta 清单（需氧量
# /曝气/污泥/能耗+几何/容积平移族——静默分叉变响红；AST 静态实读零依赖）
# ——门禁数基线 15→16。
# 第十七门禁 check_constraint_sync.py（批6h 2026-09-27 AUD-W9 闭项）：
# 约束同源三向对拍——units_lib 各包 ConstraintDecl 声明↔manifest
# constraint_refs↔factors.yaml 数值真源+kb value_basis 数值投影（死
# 声明静默分叉变响红；受限静态求值零依赖——bashi 动态构造面在内）
# ——门禁数基线 16→17。
# 第十八门禁 check_mypy.py（conv-golden 推送批 2026-10-02 用户裁决
# 「授权根治」）：双根（core+server）各自 venv 解释器跑 CI 同款
# mypy strict（conv-golden 批类型面逃逸至 CI 三处红的防线闭口——
# check_ruff/check_lint_imports 同制第三例，三态 SKIP/OSError 兜底
# 逐条同款）——门禁数基线 17→18。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GATES = (
    "check_constraint_sync.py",
    "check_contract_headers.py",
    "check_deprecation_gate.py",
    "check_dim_labels_mirror.py",
    "check_family_parity.py",
    "check_file_budgets.py",
    "check_grep_gates.py",
    "check_lint_imports.py",
    "check_magic_numbers.py",
    "check_module_graph.py",
    "check_model_names.py",
    "check_mypy.py",
    "check_out_dims_consistency.py",
    "check_readonly.py",
    "check_ruff.py",
    "check_structure.py",
    "check_trust_root.py",
    "check_webapp.py",
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failures: list[str] = []
    for gate in GATES:
        print(f"== {gate} " + "=" * max(1, 50 - len(gate)))
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts" / gate)],
            check=False,
            cwd=REPO,
        )
        if result.returncode != 0:
            failures.append(gate)
        print()
    if failures:
        print(f"[FAIL] 门禁未全绿：{', '.join(failures)}")
        return 1
    print("[OK] 全部门禁通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
