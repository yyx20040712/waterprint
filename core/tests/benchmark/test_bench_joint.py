"""性能基准：联合枚举微缩网格（N=3）分钟级主张的微缩锚（B4-3 TDD 序 5）。

输入:  inlet→aao→cass→V 型滤池三目标微缩网格（各 2 档）+真实 coefficients
输出:  pytest-benchmark 计时 + 双轴预算/rows 公式上界断言（不跑 29s 默认
       域全量——W1 换算锚在单测断言，本件锚微缩域实测）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.solution.joint_enumeration")
run_joint_enumerate = getattr(_mod, "run_joint_enumerate", None)
estimate_rows = getattr(_mod, "estimate_rows", None)

pytestmark = [
    pytest.mark.skipif(
        None in (run_joint_enumerate, estimate_rows),
        reason="实现未就绪：solution.joint_enumeration（B4-3）",
    ),
]

BUDGET_SECONDS = 10.0  # 微缩域预算（默认域 29s+末段 ≤25s<120s 看门狗——W6/W7 主张锚单测面）

_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_AAO, _CASS, _VX = "municipal_aao", "municipal_cass", "municipal_vxinglvchi"
_GRIDS = {
    _AAO: ({"field_id": "n", "values": [2.0, 3.0]},),
    _CASS: ({"field_id": "n_pool", "values": [2.0, 3.0]},),
    _VX: ({"field_id": "n", "values": [4.0, 6.0]},),
}


def _wiring() -> tuple[object, object, object, object]:
    """三目标微缩接线：项目/env/工况/选项（beam 测试同源载体扩 V 型滤池）。"""
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
    from waterprint.registry.coefficients import load_coefficients
    from waterprint.solution.joint_enumeration import JointEnumerationOptions

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
                _AAO: {},
                _CASS: {},
                _VX: {},
            },
            edges=[
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": _AAO, "port_id": "in"}},
                {"src": {"unit_id": _AAO, "port_id": "out"},
                 "dst": {"unit_id": _CASS, "port_id": "in"}},
                {"src": {"unit_id": _CASS, "port_id": "out"},
                 "dst": {"unit_id": _VX, "port_id": "in"}},
            ],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="b43", data_version="b43",
        ),
    )
    env = RunEnv(
        engine_version="b43", data_version="b43",
        assumptions={item.key: item.default for item in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_DATA), price_book={},
        trace_sink=None, engine_params={},
    )
    from waterprint.app_assembly import assemble

    options = JointEnumerationOptions(grids=_GRIDS, assemble=assemble)
    return project, env, build_condition_set([]), options


def test_joint_micro_grid_benchmark(benchmark) -> None:  # type: ignore[no-untyped-def]
    """N=3 微缩网格全链实测：行数计费 ≤ rows 公式上界 ≤ max_total_rows。"""
    project, env, conditions, options = _wiring()
    outcome = benchmark.pedantic(
        run_joint_enumeration_face, args=(project, env, conditions, options),
        iterations=1, rounds=1,
    )
    usage = outcome.budget_usage
    # rows 公式上界（g=2,k=5,N=3 → 2·(125−1)/4=62）：实际计费 12（前缀受
    # 网格规模截断——公式=保守上界口径，W7 预检按公式执法即安全侧）
    upper = estimate_rows([2, 2, 2], 5.0, 1)  # type: ignore[misc]
    assert usage["rows_evaluated"] == 2 + 2 * 2 + 4 * 2
    assert usage["rows_evaluated"] <= upper
    assert upper <= 500000.0
    assert usage["full_plant_evals"] == len(outcome.combos) > 0
    assert usage["truncated"] is False
    assert benchmark.stats.stats.mean < BUDGET_SECONDS


def run_joint_enumeration_face(project, env, conditions, options):  # type: ignore[no-untyped-def]
    """基准面薄封装（pedantic 可调用面）。"""
    return run_joint_enumerate(project, [_VX, _AAO, _CASS], conditions, env, options)  # type: ignore[misc]
