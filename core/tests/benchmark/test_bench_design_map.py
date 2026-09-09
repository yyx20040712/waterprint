"""性能基准：FD 可行域引导（design_map）单单元 50×50 稠密扫描（PD5/U2）。

输入:  app.run_design_map 正门（aao 双轴 50×50=2500 点——满配护栏场景）
输出:  pytest-benchmark 计时 + 预算断言（2.0s——U2 推断值，实测校准口径）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FD 批 PD5 基准件）
#
# 【场景】aao（批 13 实测最重单元）双轴 ns×x_mlss 各 50 点=2500
#   （solution.design_map.max_points 满配——护栏上界的耗时面）；
#   经 app.run_design_map 全链（装配→execute_graph→逐行 compute→
#   apply_constraints→产物装配）——真实同步端点的耗时上界口径。
#
# 【预算】<2.0s（U2：批 13 全枚举 aao 3.83s/万级点外推 2500 点 ~1s
#   级，2.0s 留 ~2× 余量防机器抖动；实测超限须回查 PD4 的 2500 上限
#   是否仍成立——设计腿校准条款）。
#
# 【纪律】防退化守卫，不得删除/放宽（test_bench_vector 同款注记）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_app = importlib.import_module("waterprint.app")
run_design_map = getattr(_app, "run_design_map", None)

pytestmark = [
    pytest.mark.skipif(
        run_design_map is None,
        reason="实现未就绪：waterprint.app.run_design_map（FD 批）",
    ),
]

BUDGET_SECONDS = 2.0  # FD PD5：2500 点满配同步直返预算（U2 校准口径）

_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"


def _fd_case() -> tuple[object, str, object, object]:
    """aao 满配场景（50×50——test_bench_vector 同款装配正门）。"""
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="fd",
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
                    "CODCR": 400.0, "BOD5": 200.0, "SS": 250.0,
                    "NH3N": 26.0, "TN": 43.0, "TP": 6.5,
                },
                "municipal_aao": {},
            },
            edges=[{
                "src": {"unit_id": "inlet", "port_id": "out"},
                "dst": {"unit_id": "municipal_aao", "port_id": "in"},
            }],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="fd", data_version="fd",
        ),
    )
    return project, "municipal_aao", build_condition_set([]), env


def test_bench_design_map_aao_50x50(benchmark: object) -> None:
    """aao 50×50=2500 点可行域扫描（满配护栏——同步端点耗时上界）。"""

    from waterprint.solution.design_map import DesignMapOptions

    def _run() -> object:
        project, unit_id, conditions, env = _fd_case()
        return run_design_map(  # type: ignore[misc]
            project, unit_id, conditions, env,
            DesignMapOptions(axes=[
                {"field_id": "ns", "step": 0.0020408163265306123},
                {"field_id": "x_mlss", "step": 20.408163265306122},
            ], fixed_params={}),
        )

    product = benchmark(_run)
    payload = product.payload()  # type: ignore[attr-defined]
    assert payload["stats"]["total"] == 2500  # 满配护栏（50×50）
    assert benchmark.stats["mean"] < BUDGET_SECONDS  # type: ignore[attr-defined]
