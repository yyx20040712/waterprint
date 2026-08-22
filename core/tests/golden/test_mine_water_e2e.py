"""矿井水 golden 端到端（43,836 m³/d，地表水 III 类；M3 验收）。

输入:  golden_data/mine_43836/{input_project.json, expected_summary.json}
输出:  全流程对照断言（数据未整理时跳过并注明）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (Path(__file__).parent / "golden_data" / "mine_43836" / "expected_summary.json").is_file(),
        reason="golden 数据未整理（M3：43,836 m³/d 案例由领域专家录入）",
    ),
]


def test_mine_water_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：矿井水线 8 单元 + 污泥线全流程对照期望值。"""
    input_project = json.loads(
        (golden_data_dir / "mine_43836" / "input_project.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (golden_data_dir / "mine_43836" / "expected_summary.json").read_text(encoding="utf-8")
    )
    assert input_project and expected
    raise AssertionError(
        "M3 接线断言：run_full_calc 跑通 43,836 案例并逐项对照"
        "（含污泥线回路收敛）——不得删除或放宽"
    )
