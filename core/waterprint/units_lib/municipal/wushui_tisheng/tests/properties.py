"""municipal_wushui_tisheng 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   扬程≥0、备用满足 n+1 规则
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_head_positive：泵扬程 h_pump≥0（清单项——静扬程+损失合成）；
#   - test_standby_rule：总台数=工作+备用且工作台数为正整数（清单项
#     ——n+1 规则恒等式 TS-F3+ceil 整台化）；
#   - test_head_monotone_in_static：扬程随静扬程单调不减（单调——
#     h_static 线性因子，range 五点扫描）；
#   - test_flow_conservation：出流水量=入流（穿流守恒——泵站不存水）；
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
from waterprint.contracts.flow import WaterFlow  # noqa: E402
from waterprint.contracts.ports import PortRef  # noqa: E402
from waterprint.contracts.quality import WaterQuality  # noqa: E402
from waterprint.contracts.unit_api import UnitContext, UnitResult  # noqa: E402
from waterprint.registry.coefficients import load_coefficients  # noqa: E402
from waterprint.units_lib.municipal.wushui_tisheng import (  # noqa: E402
    make_unit,
    manifest,
)

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_wst", port_id="in")
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in (
        "factor.wushui_tisheng.",
        "removal.wushui_tisheng.",
        "factor.screen.",
    ):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_wst",
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
def test_head_positive(draw: dict[str, float]) -> None:
    """清单项：泵扬程 h_pump≥0（静扬程+沿程+局部损失合成域）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["h_pump"] >= 0.0


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_standby_rule(draw: dict[str, float]) -> None:
    """清单项：n+1 备用规则——总台数=工作+备用、工作台数为正整数。"""
    params = _params(**draw)
    dims = _run(params).dims
    assert isinstance(dims, dict)
    duty = dims["n_pump_duty"]
    assert duty == int(duty) and duty >= 1.0
    assert dims["n_pump_total"] == pytest.approx(
        duty + params["n_standby"], rel=1e-12
    )
    assert dims["n_pump_duty"] >= dims["n_pump_raw"] - 1e-12


def test_head_monotone_in_static() -> None:
    """单调：扬程随静扬程单调不减（h_static 线性因子，五点扫描）。"""
    spec = next(s for s in manifest.params if s.field_id == "h_static")
    assert spec.range is not None
    lo, hi = spec.range
    points = [lo + (hi - lo) * i / 4 for i in range(5)]
    previous: float | None = None
    for h_static in points:
        dims = _run(_params(h_static=h_static)).dims
        assert isinstance(dims, dict)
        current = dims["h_pump"]
        if previous is not None:
            assert current >= previous - 1e-9, (
                f"h_static={h_static}: h_pump={current} < 前点 {previous}（单调性破坏）"
            )
        previous = current


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_flow_conservation(draw: dict[str, float]) -> None:
    """守恒：出流水量=入流水量（泵站穿流恒等——提升不存水）。"""
    result = _run(_params(**draw))
    out = result.outflows[PortRef(unit_id="prop_wst", port_id="out")]
    assert isinstance(out, WaterFlow)
    assert out.q_avg_daily == pytest.approx(_FLOW.q_avg_daily, rel=1e-12)
    assert out.kz == pytest.approx(_FLOW.kz, rel=1e-12)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（管径/扬程/台数/井容面）。"""
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
