"""sludge_xiaohua 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（SLUDGE 入流）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言。
#   contracts/properties_sludge.py 锁定 mix 代数面（contracts 层），
#   本件锁定本包 compute 消化减量全链（单元层——两层互补非重复））
#
# 【本单元性质清单（旧系统物理测试映射）】
#   DS 守恒（进=出+沼气带走 VS）、产气量≥0
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_ds_digestion_conservation：入流 DS−VS 消解量=出流 DS（清单项
#     ——XH-F7 消化减量恒等 ds_in−w_vs_deg=ds_out，随机参数）；
#   - test_port_echo：出流端口 ds=dims ds_out（单源回显恒等）；
#   - test_biogas_nonneg：产气量 v_biogas≥0（清单项）；
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
from waterprint.units_lib.sludge.xiaohua import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_xh", port_id="in")
_IN_FLOW = SludgeFlow(q_wet=0.05, ds=0.012, moisture=0.99)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.xiaohua.", "removal.xiaohua.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_xh",
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
def test_ds_digestion_conservation(draw: dict[str, float]) -> None:
    """清单项守恒：入流 DS−VS 消解量=出流 DS（XH-F7 减量恒等）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["ds_in"] - dims["w_vs_deg"] == pytest.approx(
        dims["ds_out"], rel=1e-9, abs=1e-15
    ), (
        f"ds_in−w_vs_deg={dims['ds_in'] - dims['w_vs_deg']} ≠ ds_out="
        f"{dims['ds_out']}（消化守恒破坏）"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_port_echo(draw: dict[str, float]) -> None:
    """守恒：出流端口 ds/q_wet=dims 单源回显（与入流 ds_in 恒等）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    out = result.outflows[PortRef(unit_id="prop_xh", port_id="out")]
    assert isinstance(out, SludgeFlow)
    assert out.ds == pytest.approx(dims["ds_out"] / 86400.0, rel=1e-9)
    assert dims["ds_in"] == pytest.approx(_IN_FLOW.ds * 86400.0, rel=1e-9)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_biogas_nonneg(draw: dict[str, float]) -> None:
    """清单项：产气量 v_biogas≥0（厌氧产气物理域）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["v_biogas"] >= 0.0


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（池容/产气/VS 消解面）。"""
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
