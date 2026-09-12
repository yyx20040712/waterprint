"""sludge_nongsuo 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（SLUDGE 入流）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言。
#   contracts/properties_sludge.py 锁定 mix 代数面（contracts 层），
#   本件锁定本包 compute 浓缩分流全链（单元层——两层互补非重复））
#
# 【本单元性质清单（旧系统物理测试映射）】
#   DS 守恒（浓缩污泥+上清液）、含水率单调下降
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_ds_conservation：入流 DS=浓缩口 DS+上清液口 DS（清单项
#     ——NS-F7/F10 分流恒等，随机参数）；
#   - test_flow_conservation：入流湿泥量=浓缩口+上清液口（守恒——
#     质量分流对偶面）；
#   - test_moisture_decreasing：浓缩口含水率<入流含水率=p_out
#     （清单项——增稠单调下降且落目标含水率档）；
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
from waterprint.units_lib.sludge.nongsuo import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_ns", port_id="in")
_IN_FLOW = SludgeFlow(q_wet=0.05, ds=0.012, moisture=0.99)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.nongsuo.", "removal.nongsuo.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_ns",
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
    """清单项守恒：入流 DS=浓缩口 DS+上清液口 DS（分流恒等）。"""
    result = _run(_params(**draw))
    thick = result.outflows[PortRef(unit_id="prop_ns", port_id="out")]
    sup = result.outflows[PortRef(unit_id="prop_ns", port_id="sup")]
    assert isinstance(thick, SludgeFlow)
    assert isinstance(sup, SludgeFlow)
    assert thick.ds + sup.ds == pytest.approx(_IN_FLOW.ds, rel=1e-9, abs=1e-15), (
        f"DS 分流 {thick.ds}+{sup.ds} ≠ 入流 {_IN_FLOW.ds}（守恒破坏）"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_flow_conservation(draw: dict[str, float]) -> None:
    """守恒：入流湿泥量=浓缩口+上清液口（质量分流对偶面）。"""
    result = _run(_params(**draw))
    thick = result.outflows[PortRef(unit_id="prop_ns", port_id="out")]
    sup = result.outflows[PortRef(unit_id="prop_ns", port_id="sup")]
    assert isinstance(thick, SludgeFlow)
    assert isinstance(sup, SludgeFlow)
    assert thick.q_wet + sup.q_wet == pytest.approx(
        _IN_FLOW.q_wet, rel=1e-9, abs=1e-15
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_moisture_decreasing(draw: dict[str, float]) -> None:
    """清单项：浓缩口含水率<入流含水率（=p_out 目标含水率档回显）。"""
    params = _params(**draw)
    thick = _run(params).outflows[PortRef(unit_id="prop_ns", port_id="out")]
    assert isinstance(thick, SludgeFlow)
    assert thick.moisture < _IN_FLOW.moisture
    assert thick.moisture == pytest.approx(params["p_out"], rel=1e-9)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（池径/面积/固通量面）。"""
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
