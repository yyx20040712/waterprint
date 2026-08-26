"""性能基准：全流程计算 <5s（§18.1；M1 起接线，CI 手动触发）。

输入:  golden 市政案例（十二节点主线三件套，GOLDEN 批 2026-08-26 激活）
输出:  pytest-benchmark 计时（超预算由 CI 基准门禁判失败）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_SEED = Path(__file__).resolve().parents[1] / "golden" / "golden_data" / "municipal_34760" / "input_project.json"
_EXPECTED = _SEED.parent / "expected_summary.json"
_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"

pytestmark = [
    pytest.mark.skipif(
        not _SEED.is_file(),
        reason="基准数据未就绪（M1/M2：golden 案例录入后激活）",
    ),
]

BUDGET_SECONDS = 5.0  # §18.1：全流程（32 单元 × 2+k 工况，含回路）


def _wiring() -> tuple[object, object, object]:
    """golden 接线束：正门载项目 + build_condition_set 勾选 3 单元（5 工况）。

    checked_units 取自 expected_summary.json（单一数据源——与 e2e 同源勾选）；
    env 口径=expected.generated 实录（server 正门版本串）。
    """
    from waterprint.app import load_project
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    expected = json.loads(_EXPECTED.read_text(encoding="utf-8"))
    lib = load_coefficients(_REPO_DATA)
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    return load_project(_SEED), build_condition_set(expected["checked_units"]), env


def test_full_calc_benchmark(benchmark) -> None:
    """全流程计算在预算内（劣化即 CI 失败）。

    占位实质化（GOLDEN 批总授权"占位实质化"先例，2026-08-26）：原占位
    raise 由真实 benchmark(waterprint.app.run_full_calc, golden 项目,
    build_condition_set 勾选 3 单元) 替代——pedantic rounds=1 形态照
    test_bench_enumerate 先例；BUDGET_SECONDS=5.0 保持 §18.1 32 单元口径
    （当前 13 单元为子集）。实测余量见 notes.md/golden 实现报告。
    """
    from waterprint.app import run_full_calc

    project, conditions, env = _wiring()
    benchmark.pedantic(run_full_calc, args=(project, conditions, env), rounds=1, iterations=1)
    assert benchmark.stats.stats.mean < BUDGET_SECONDS  # §18.1 预算守卫
