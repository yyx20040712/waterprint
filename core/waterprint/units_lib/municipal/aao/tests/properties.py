"""municipal_aao 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   分区容积和=总容积、需氧量≥0、回流比>0、剩余污泥≥0
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_zone_volume_conservation：三区容积和=总容积（守恒，随机参数）；
#   - test_nonneg_finite：全 dims 非负+有限+出流水质非负（非负性）；
#   - test_spec_list_positive：清单显式项——需氧量/回流/剩余污泥量>0；
#   - test_volume_monotone_in_pools：单系列容积随池数 n 网格单调不增（单调）；
#   - test_boundary_stability：参数域两端点不崩溃、不产 NaN/inf（边界）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】参数从 manifest range/grid 合法域生成（模板规格）；
#   系数经 load_coefficients 数据包真源+D4 前缀投影（与 app_assembly
#   _unit_params 同式——units_lib 层禁上行导入 app，包内镜像六行过滤）。
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
from waterprint.contracts.flow import WaterFlow  # noqa: E402
from waterprint.contracts.ports import PortRef  # noqa: E402
from waterprint.contracts.quality import WaterQuality  # noqa: E402
from waterprint.contracts.sludge import SludgeFlow  # noqa: E402
from waterprint.contracts.unit_api import UnitContext, UnitResult  # noqa: E402
from waterprint.registry.coefficients import load_coefficients  # noqa: E402
from waterprint.units_lib.municipal.aao import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_aao", port_id="in")
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.aao.", "removal.aao.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_aao",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
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
def test_zone_volume_conservation(draw: dict[str, float]) -> None:
    """守恒：v_anaerobic + v_anoxic + v_o = v_total（AO 三区分解恒等）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    total = dims["v_anaerobic"] + dims["v_anoxic"] + dims["v_o"]
    assert total == pytest.approx(dims["v_total"], rel=1e-9, abs=1e-9)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限，出流六指标非负。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        assert value >= 0.0 and math.isfinite(value), (
            f"{key}={value} 非负/有限性破坏"
        )
    out_quality = result.outqualities[PortRef(unit_id="prop_aao", port_id="out")]
    for indicator in ("BOD5", "CODCR", "SS", "NH3N", "TN", "TP"):
        assert float(getattr(out_quality, indicator)) >= 0.0


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_spec_list_positive(draw: dict[str, float]) -> None:
    """清单显式项：需氧量≥0、回流比>0（q_return/q_internal）、剩余污泥≥0。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["o2_total"] >= 0.0
    assert dims["q_return"] > 0.0
    assert dims["q_internal"] > 0.0
    assert dims["s_y"] >= 0.0
    sludge = result.outflows[PortRef(unit_id="prop_aao", port_id="sludge_out")]
    assert isinstance(sludge, SludgeFlow)
    assert sludge.q_wet >= 0.0 and sludge.ds >= 0.0


def test_volume_monotone_in_pools() -> None:
    """单调：单系列容积 v_o_series 随池数 n 档位单调不增（网格有序维）。"""
    grid = next(spec.grid for spec in manifest.params if spec.field_id == "n")
    assert grid is not None and len(grid) >= 2
    previous: float | None = None
    for n in grid:
        dims = _run(_params(n=float(n))).dims
        assert isinstance(dims, dict)
        current = dims["v_o_series"]
        if previous is not None:
            assert current <= previous + 1e-9, (
                f"n={n}: v_o_series={current} > 前档 {previous}（单调性破坏）"
            )
        previous = current


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
