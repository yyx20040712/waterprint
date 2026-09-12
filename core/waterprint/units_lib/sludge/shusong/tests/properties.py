"""sludge_shusong 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（SLUDGE 入流）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言。
#   contracts/properties_sludge.py 锁定 mix 代数面（contracts 层），
#   本件锁定本包 compute 全链穿流（单元层——两层互补非重复））
#
# 【本单元性质清单（旧系统物理测试映射）】
#   流速在防淤积带内、损失≥0（ST-F8~F9 穿流守恒=contracts.sludge R1）
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_passthrough_conservation：出流 DS/湿泥量/含水率=入流（清单项
#     ——ST-F8~F9 穿流守恒，随机参数）；
#   - test_velocity_band_warning_coupling：压力段流速越带⇔警告在场
#     （清单项——"防淤积带内"域面由警告通道诚实呈现）；
#   - test_gravity_velocity_warning_coupling：重力段流速低于最小流速
#     ⇒警告在场（清单项同构面——防淤积下限）；
#   - test_pressure_loss_nonneg：沿程压降≥0（清单项——p_in≥p_out）；
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
from waterprint.units_lib.sludge.shusong import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_st", port_id="in")
_IN_FLOW = SludgeFlow(q_wet=0.05, ds=0.012, moisture=0.99)
_V_BAND = ("factor.shusong.velocity_band.min", "factor.shusong.velocity_band.max")
_GRAVITY_V_MIN = "factor.shusong.gravity_v_min"


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.shusong.", "removal.shusong.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_st",
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
def test_passthrough_conservation(draw: dict[str, float]) -> None:
    """清单项守恒：出流 DS/湿泥量/含水率=入流（压力输送穿流恒等）。"""
    out = _run(_params(**draw)).outflows[PortRef(unit_id="prop_st", port_id="out")]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(_IN_FLOW.q_wet, rel=1e-12)
    assert out.ds == pytest.approx(_IN_FLOW.ds, rel=1e-12)
    assert out.moisture == pytest.approx(_IN_FLOW.moisture, rel=1e-12)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_velocity_band_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：压力段实际流速越带⇔警告在场（双向耦合）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    band = tuple(_COEFFS.get(key).value for key in _V_BAND)
    has_warning = any(w.param_key == "v_press" for w in result.warnings)
    assert has_warning == (not band[0] <= dims["v_act"] <= band[1]), (
        f"v_act={dims['v_act']} 带 {band} 与警告在场 {has_warning} 失耦"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_gravity_velocity_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：重力段流速低于最小流速⇒警告在场（防淤积下限单向）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    v_min = _COEFFS.get(_GRAVITY_V_MIN).value
    if dims["v_grav"] < v_min:
        assert any(
            w.param_key == "d_grav" and "重力段流速" in w.message
            for w in result.warnings
        ), f"v_grav={dims['v_grav']} < 最小 {v_min} 而警告缺席（失耦）"


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_pressure_loss_nonneg(draw: dict[str, float]) -> None:
    """清单项：沿程压降≥0（p_in≥p_out——输送阻力方向性）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["p_in"] >= dims["p_out"] - 1e-12


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（管径/流速/坡度面）。"""
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
