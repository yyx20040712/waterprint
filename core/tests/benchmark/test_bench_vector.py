"""性能基准：批 13-A 向量化单元万级逐行枚举+apply_batch 万级直连（§18.1）。

输入:  批 A 四单元之三新接线（aao/gaomidu/vxinglvchi——cass 已有
       test_bench_enumerate 13500 先例）+ formulas.apply_batch 直连面
输出:  pytest-benchmark 计时 + 预算断言（探针 §一 场景收编——批 A 面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批 13-A 附带件；task-13-design §一/§三.5、D4）
#
# 【场景】§一 探针六场景收编（批 A 面）：
#   - aao/gaomidu/vxinglvchi 各 2 维 100×100=10000 行逐行枚举
#     （N=1 退化路径——同源向量路径唯一化后的逐行守卫；cass 场景=
#     test_bench_enumerate 既有 13500 先例承载，chuchenchi/bashi_
#     jiliangcao 随批 B/D 补登记）；
#   - apply_batch 直连万级（AO-F1 混合绑定——批量正门本身的吞吐面）。
# 【预算】万级 <5s（§18.1 沿承口径——M2-SOL 起）；apply_batch 直连
#   <1.0s（纯核吞吐——数组语义零逐行 Python 开销的守卫）。
# 【纪律】防退化守卫，不得删除/放宽（test_bench_enumerate 同款注记）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import numpy
import pytest

_mod = importlib.import_module("waterprint.solution.enumerate")
enumerate_solutions = getattr(_mod, "enumerate_solutions", None)
_formulas = importlib.import_module("waterprint.registry.formulas")
apply_batch = getattr(_formulas, "apply_batch", None)

pytestmark = [
    pytest.mark.skipif(
        enumerate_solutions is None,
        reason="实现未就绪：waterprint.solution.enumerate（M1）",
    ),
]

BUDGET_SECONDS = 5.0  # §18.1：万级枚举（单单元，向量化唯一实现前提）
BATCH_BUDGET_SECONDS = 1.0  # apply_batch 万级直连（纯核吞吐面）

_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"


def _wiring(unit_id: str) -> tuple[Any, Any, Any, Any]:
    """单单元接线（inlet → unit——test_bench_enumerate 同款装配正门）。"""
    from waterprint.app import assemble, run_full_calc
    from waterprint.app_enumeration import UpstreamSource, upstream_context
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="b13a",
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
                unit_id: {},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": unit_id, "port_id": "in"},
                }
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="b13a",
            data_version="b13a",
        ),
    )
    assembled = assemble(project, env)
    conditions = build_condition_set([])
    plant = run_full_calc(project, conditions, env).plant
    ctx = upstream_context(
        UpstreamSource(assembled.units, assembled.edges, project.design, plant),
        unit_id,
        next(iter(conditions.iter_all())),
        env,
    )
    return grid_of(unit_id), ctx, assembled.units[unit_id], env


def _span(low: float, high: float, count: int) -> list[float]:
    """闭区间等距取值（100×100 维载体——显式值域零代码注入例外同款）。"""
    return [low + (high - low) * index / (count - 1) for index in range(count)]


def grid_of(unit_id: str) -> Any:
    """§一 场景 2 维 100×100 网格（批 A 三单元敏感对）。

    §12.4 ≤4^k 护栏守 build_grid 声明面（用户网格——2 维上限 16 档）；
    本基准=探针先例直驱（§一 表同款 100×100）：直接构造 Grid 值而非
    声明——护栏语义不涉（非用户声明;探针脚本同款口径）。
    """
    from itertools import product

    from waterprint.solution.grid import Grid

    axes: dict[str, tuple[str, list[float]]] = {
        "municipal_aao": ("ns", [3000.0 + 20.0 * i for i in range(100)]),
        "municipal_gaomidu": ("q_surface", [2.0 + 0.06 * i for i in range(100)]),
        "municipal_vxinglvchi": ("v_filter", [4.0 + 0.08 * i for i in range(100)]),
    }
    first_field, first_values = axes[unit_id]
    second_values = _span(3000.0, 5000.0, 100) if unit_id == "municipal_aao" else _span(
        2.0, 8.0, 100
    ) if unit_id == "municipal_gaomidu" else _span(4.0, 12.0, 100)
    second_field = {"municipal_aao": "x_mlss", "municipal_gaomidu": "n",
                    "municipal_vxinglvchi": "n"}[unit_id]
    fields = (first_field, second_field)
    dtype = numpy.dtype([(field, "<f8") for field in fields])
    array = numpy.empty(10000, dtype=dtype)
    for row, combo in enumerate(product(first_values, second_values)):
        array[row][fields[0]] = combo[0]
        array[row][fields[1]] = combo[1]
    return Grid(fields=fields, array=array, shape=(100, 100), total=10000)


@pytest.mark.parametrize("unit_id", ["municipal_aao", "municipal_gaomidu", "municipal_vxinglvchi"])
def test_vector_unit_10k_rowwise(benchmark, unit_id: str) -> None:
    """批 A 单元万级逐行枚举在预算内（N=1 退化路径守卫——防退化不得放宽）。"""
    grid, ctx, unit, env = _wiring(unit_id)
    benchmark.pedantic(
        enumerate_solutions, args=(grid, ctx, unit, env), rounds=1, iterations=1
    )
    assert benchmark.stats.stats.mean < BUDGET_SECONDS  # §18.1 预算守卫


def test_apply_batch_10k_direct(benchmark) -> None:
    """apply_batch 万级直连吞吐（AO-F1 混合绑定——批量正门纯核面）。"""
    from waterprint.units_lib import discover_units

    discover_units()
    count = 10000
    bindings = {
        "q_avg_daily": numpy.linspace(0.2, 0.9, count),
        "bod5_in": numpy.linspace(80.0, 250.0, count),
        "ns": numpy.linspace(0.05, 0.15, count),
        "x_mlss": numpy.linspace(3000.0, 5000.0, count),
    }
    outcome: Any = benchmark.pedantic(
        apply_batch, args=("AO-F1", bindings, ("b13a_bench", "design")), rounds=1, iterations=1
    )
    assert outcome.shape == (count,)
    assert bool(numpy.isfinite(outcome).all())  # 良批零 NaN
    assert benchmark.stats.stats.mean < BATCH_BUDGET_SECONDS
