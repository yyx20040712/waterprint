"""性能基准：万级方案枚举 <5s（§18.1；CI 手动触发）。

输入:  示范单元万级网格（CASS 七维 13500 行——M2-SOL 探针②载体）
输出:  pytest-benchmark 计时 + 预算断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.solution.enumerate")
enumerate_solutions = getattr(_mod, "enumerate_solutions", None)

pytestmark = [
    pytest.mark.skipif(
        enumerate_solutions is None,
        reason="实现未就绪：waterprint.solution.enumerate（M1）",
    ),
]

BUDGET_SECONDS = 5.0  # §18.1：万级枚举（单单元，向量化唯一实现前提）

_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"


def _wiring() -> tuple[object, object, object, object]:
    """万级网格接线（M2-SOL R1 总授权实质化，2026-08-26）：CASS 七维。

    上游上下文经 app 正门（assemble+run_full_calc 取上游链值）；网格
    total=13500（n_pool 5 × t_cycle 3 × ns 5 × x_mlss 5 × t_selector 4 ×
    h2 3 × ratio_lb 3，护栏 4^7=16384 内）——探针②同源载体。
    """
    from waterprint.app import assemble, run_full_calc
    from waterprint.app_enumeration import UpstreamSource, upstream_context
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.solution.grid import build_grid

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="m2sol",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "NH3N": 26.0,
                    "TN": 43.0,
                    "TP": 6.5,
                },
                "municipal_cass": {},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                }
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="m2sol",
            data_version="m2sol",
        ),
    )
    assembled = assemble(project, env)
    conditions = build_condition_set([])
    plant = run_full_calc(project, conditions, env).plant
    ctx = upstream_context(
        UpstreamSource(assembled.units, assembled.edges, project.design, plant),
        "municipal_cass",
        next(iter(conditions.iter_all())),
        env,
    )
    grid = build_grid(
        [
            {"field_id": "n_pool", "values": [2.0, 3.0, 4.0, 5.0, 6.0]},
            {"field_id": "t_cycle", "values": [4.0, 6.0, 8.0]},
            {"field_id": "ns", "range": {"min": 0.05, "max": 0.13}, "step": 0.02},
            {
                "field_id": "x_mlss",
                "range": {"min": 3000.0, "max": 5000.0},
                "step": 500.0,
            },
            {"field_id": "t_selector", "range": {"min": 0.5, "max": 0.8}, "step": 0.1},
            {"field_id": "h2", "values": [4.0, 5.0, 6.0]},
            {"field_id": "ratio_lb", "values": [2.0, 2.5, 3.0]},
        ]
    )
    return grid, ctx, assembled.units["municipal_cass"], env


def test_enumerate_10k_benchmark(benchmark) -> None:
    """万级枚举在预算内（CASS 13500 行——防退化守卫，不得删除/放宽）。

    接线实质化（M2-SOL R1 总授权"休眠骨架补齐"先例，2026-08-26）：
    原占位 raise AssertionError 由真实 benchmark 替代；实测参考 2.17s
    （逐行驱动同一 compute 现实口径——apply 向量化增强挂账 UF-36，
    余量收窄时此守卫先红）。
    """
    grid, ctx, unit, env = _wiring()
    assert grid.total >= 10000  # 万级前提（13500）
    benchmark.pedantic(
        enumerate_solutions, args=(grid, ctx, unit, env), rounds=1, iterations=1
    )
    assert benchmark.stats.stats.mean < BUDGET_SECONDS  # §18.1 预算守卫
