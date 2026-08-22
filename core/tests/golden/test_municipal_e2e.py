"""市政污水 golden 端到端（34,760 m³/d，一级 A；M2 验收）。

输入:  golden_data/municipal_34760/{input_project.json, expected_summary.json}
输出:  全流程与手算/期望值对照断言（数据未整理时跳过并注明）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M2 验收 = 13 单元全线 + 汇流 + 高程 + 枚举诊断端到端出全套
# 计算书；期望值来源 docs/norms 手算对照与旧系统结果（差异逐条解释，
# 由领域专家签字后录入 golden_data——实现者不得自编）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (Path(__file__).parent / "golden_data" / "municipal_34760" / "expected_summary.json").is_file(),
        reason="golden 数据未整理（M0 §9.4：34,760 m³/d 案例由领域专家录入）",
    ),
]


def test_municipal_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：run_full_calc 结果汇总逐项对照期望值（容差按 expected 内标注）。"""
    input_project = json.loads(
        (golden_data_dir / "municipal_34760" / "input_project.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (golden_data_dir / "municipal_34760" / "expected_summary.json").read_text(encoding="utf-8")
    )
    assert input_project and expected
    raise AssertionError(
        "M2 接线断言：waterprint.app.run_full_calc 跑通 34,760 案例并逐项对照"
        "（含工况集 2+k 索引与计算书导出）——不得删除或放宽"
    )
