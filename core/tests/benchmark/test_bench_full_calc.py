"""性能基准：全流程计算 <5s（§18.1；M1 起接线，CI 手动触发）。

输入:  golden 市政案例（或 M1 三单元切片）
输出:  pytest-benchmark 计时（超预算由 CI 基准门禁判失败）
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SEED = Path(__file__).resolve().parents[1] / "golden" / "golden_data" / "municipal_34760" / "input_project.json"

pytestmark = [
    pytest.mark.skipif(
        not _SEED.is_file(),
        reason="基准数据未就绪（M1/M2：golden 案例录入后激活）",
    ),
]

BUDGET_SECONDS = 5.0  # §18.1：全流程（32 单元 × 2+k 工况，含回路）


def test_full_calc_benchmark(benchmark) -> None:
    """全流程计算在预算内（劣化即 CI 失败）。"""
    raise AssertionError(
        "M1 接线：benchmark(waterprint.app.run_full_calc, golden 项目)——不得删除"
    )
