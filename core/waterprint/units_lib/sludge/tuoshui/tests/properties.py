"""sludge_tuoshui 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（SLUDGE 入流）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言。
#   contracts/properties_sludge.py 锁定 mix 代数面（contracts 层），
#   本件锁定本包 compute 脱水分流全链（单元层——两层互补非重复））
#
# 【本单元性质清单（旧系统物理测试映射）】
#   DS 守恒（泥饼+滤液）、泥饼含水率∈档位
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_ds_conservation：入流 DS=泥饼口 DS+滤液口 DS（清单项
#     ——TU-F8 分流恒等，随机参数）；
#   - test_cake_moisture_grade：泥饼含水率=p_cake（清单项——目标
#     含水率档回显恒等）；
#   - test_machine_count_integer：脱水机台数=正整数且≥未取整原值
#     （ceil 整台化恒等——含备用 n+1 面）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数）；
#   - test_boundary_stability：参数域两端点+档位端点不崩溃、不产
#     NaN/inf（边界）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】参数从 manifest range/grid 合法域生成；系数经
#   load_coefficients 数据包真源+D4 前缀投影（units_lib 层禁上行
#   导入 app，包内镜像六行过滤）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from waterprint.contracts.condition import FlowCase, OperatingCondition  # noqa: E402
from waterprint.contracts.ports import PortRef  # noqa: E402
from waterprint.contracts.sludge import SludgeFlow  # noqa: E402
from waterprint.contracts.unit_api import UnitContext, UnitResult  # noqa: E402
from waterprint.registry.coefficients import load_coefficients  # noqa: E402
from waterprint.units_lib.sludge.tuoshui import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_tu", port_id="in")
_IN_FLOW = SludgeFlow(q_wet=0.05, ds=0.012, moisture=0.99)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.tuoshui.", "removal.tuoshui.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_tu",
        inflows={_IN_REF: _IN_FLOW},
        inqualities={},
        params=params,
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    return make_unit().compute(ctx)


def _draws() -> st.SearchStrategy[dict[str, float]]:
    """range 参数连续生成 + grid 参数档位采样（合法域策略）。"""
    strategy: dict[str, st.SearchStrategy[float]] = {}
    for spec in manifest.params:
        if spec.range is not None:
            lo, hi = spec.range
            strategy[spec.field_id] = st.floats(min_value=lo, max_value=hi)
        elif spec.grid is not None:
            strategy[spec.field_id] = st.sampled_from(spec.grid)
    return st.fixed_dictionaries(strategy)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_ds_conservation(draw: dict[str, float]) -> None:
    """清单项守恒：入流 DS=泥饼口 DS+滤液口 DS（TU-F8 分流恒等）。"""
    result = _run(_params(**draw))
    cake = result.outflows[PortRef(unit_id="prop_tu", port_id="out")]
    filtrate = result.outflows[PortRef(unit_id="prop_tu", port_id="filtrate")]
    assert isinstance(cake, SludgeFlow)
    assert isinstance(filtrate, SludgeFlow)
    assert cake.ds + filtrate.ds == pytest.approx(
        _IN_FLOW.ds, rel=1e-9, abs=1e-15
    ), f"DS 分流 {cake.ds}+{filtrate.ds} ≠ 入流 {_IN_FLOW.ds}（守恒破坏）"


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_cake_moisture_grade(draw: dict[str, float]) -> None:
    """清单项：泥饼含水率=p_cake（目标含水率档回显恒等）。"""
    params = _params(**draw)
    cake = _run(params).outflows[PortRef(unit_id="prop_tu", port_id="out")]
    assert isinstance(cake, SludgeFlow)
    assert cake.moisture == pytest.approx(params["p_cake"], rel=1e-9)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_machine_count_integer(draw: dict[str, float]) -> None:
    """整台化：工作台数=正整数且≥原值、总台数=工作+备用（n+1 面）。"""
    params = _params(**draw)
    dims = _run(params).dims
    assert isinstance(dims, dict)
    duty = dims["n_machine_duty"]
    assert duty == int(duty) and duty >= 1.0
    assert dims["n_machine_duty"] >= dims["n_machine_raw"] - 1e-12
    assert dims["n_machine_total"] == pytest.approx(
        duty + params["n_standby"], rel=1e-12
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（泥饼/滤液/药耗面）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        assert value >= 0.0 and math.isfinite(value), (
            f"{key}={value} 非负/有限性破坏"
        )


def test_boundary_stability() -> None:
    """边界：range 两端点+grid 档位端点实跑不崩溃、不产 NaN/inf。"""
    edges: list[tuple[str, float]] = []
    for spec in manifest.params:
        if spec.range is not None:
            edges.extend((spec.field_id, edge) for edge in spec.range)
        elif spec.grid is not None:
            edges.extend((spec.field_id, float(g)) for g in (spec.grid[0], spec.grid[-1]))
    for field_id, edge in edges:
        dims = _run(_params(**{field_id: edge})).dims
        assert isinstance(dims, dict)
        for value in dims.values():
            assert math.isfinite(value), (
                f"{field_id}={edge} 边界产 NaN/inf"
            )


@given(draw=_draws())
@settings(max_examples=20, deadline=None, derandomize=True)
def test_purity(draw: dict[str, float]) -> None:
    """纯函数：同 ctx 双跑同果（R1——可复算基石）。"""
    first = _run(_params(**draw))
    second = _run(_params(**draw))
    assert dict(first.dims) == dict(second.dims)
    assert first.formula_ids == second.formula_ids
