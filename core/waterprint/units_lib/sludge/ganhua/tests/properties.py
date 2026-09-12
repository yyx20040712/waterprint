"""sludge_ganhua 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（SLUDGE 入流）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言。
#   contracts/properties_sludge.py 锁定 mix 代数面（contracts 层），
#   本件锁定本包 compute 全链守恒（单元层——两层互补非重复））
#
# 【本单元性质清单（旧系统物理测试映射）】
#   DS 守恒、含水率单调下降、热耗≥理论蒸发能耗
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_ds_conservation：出流 DS=入流 DS（清单项——干化不减固体，
#     仅蒸发水分）；
#   - test_moisture_decreasing：出流含水率<入流含水率=p_out（清单项
#     ——单调下降且落目标含水率档）；
#   - test_heat_above_theoretical：热耗≥理论蒸发能耗（清单项——
#     GH-F6 q_heat=w_evap×h_evap/eta≥w_evap×h_evap，eta∈(0,1)）；
#   - test_mass_check_identity：m_check=m_in−w_evap（GH-F5 蒸发衡算）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数）；
#   - test_boundary_stability：参数域两端点不崩溃、不产 NaN/inf（边界）；
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
from waterprint.units_lib.sludge.ganhua import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_gh", port_id="in")
_IN_FLOW = SludgeFlow(q_wet=0.05, ds=0.012, moisture=0.99)
_H_EVAP = "factor.ganhua.h_evap"
_ETA_THERMAL = "factor.ganhua.eta_thermal"


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.ganhua.", "removal.ganhua.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_gh",
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
    """清单项守恒：出流 DS=入流 DS（干化蒸发水分不减固体）。"""
    out = _run(_params(**draw)).outflows[PortRef(unit_id="prop_gh", port_id="out")]
    assert isinstance(out, SludgeFlow)
    assert out.ds == pytest.approx(_IN_FLOW.ds, rel=1e-12)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_moisture_decreasing(draw: dict[str, float]) -> None:
    """清单项：出流含水率<入流含水率（=p_out 目标含水率档回显）。"""
    params = _params(**draw)
    out = _run(params).outflows[PortRef(unit_id="prop_gh", port_id="out")]
    assert isinstance(out, SludgeFlow)
    assert out.moisture < _IN_FLOW.moisture
    assert out.moisture == pytest.approx(params["p_out"], rel=1e-9)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_heat_above_theoretical(draw: dict[str, float]) -> None:
    """清单项：热耗≥理论蒸发能耗（GH-F6——eta_thermal∈(0,1) 推论）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    eta = _COEFFS.get(_ETA_THERMAL).value
    h_evap = _COEFFS.get(_H_EVAP).value
    assert 0.0 < eta < 1.0
    theoretical = dims["w_evap"] * h_evap
    assert dims["q_heat"] >= theoretical - 1e-9, (
        f"q_heat={dims['q_heat']} < 理论蒸发能耗 {theoretical}（热力学下限破坏）"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_mass_check_identity(draw: dict[str, float]) -> None:
    """守恒：m_check=m_in−w_evap（GH-F5 蒸发衡算恒等）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["m_check"] == pytest.approx(
        dims["m_in"] - dims["w_evap"], rel=1e-9, abs=1e-12
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（蒸发/热耗/干化面积面）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        assert value >= 0.0 and math.isfinite(value), (
            f"{key}={value} 非负/有限性破坏"
        )


def test_boundary_stability() -> None:
    """边界：range 参数两端点实跑不崩溃、不产 NaN/inf。"""
    for spec in manifest.params:
        if spec.range is None:
            continue
        for edge in spec.range:
            dims = _run(_params(**{spec.field_id: edge})).dims
            assert isinstance(dims, dict)
            for value in dims.values():
                assert math.isfinite(value), (
                    f"{spec.field_id}={edge} 边界产 NaN/inf"
                )


@given(draw=_draws())
@settings(max_examples=20, deadline=None, derandomize=True)
def test_purity(draw: dict[str, float]) -> None:
    """纯函数：同 ctx 双跑同果（R1——可复算基石）。"""
    first = _run(_params(**draw))
    second = _run(_params(**draw))
    assert dict(first.dims) == dict(second.dims)
    assert first.formula_ids == second.formula_ids
