"""municipal_cass 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   时段和=周期长、滗水容积≤池容、需氧量≥0
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_phase_sum_identity：dims 时段和=周期参数（守恒——compute 相位
#     和守卫的读出面回显，t_react+t_settle+t_draw 恒等 t_cycle）；
#   - test_draw_volume_within_pool：单池滗水容积≤池容+滗水深度≤带上限
#     （清单项——CA-F9 max 并集面积的几何推论）；
#   - test_oxygen_nonneg：需氧量 o2_total≥0（清单项）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数）；
#   - test_draw_volume_monotone_in_pools：v_draw 随池数档位单调不增（单调）；
#   - test_boundary_stability：参数域两端点不崩溃、不产 NaN/inf（边界）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】参数从 manifest range/grid 合法域生成；t_cycle 不入随机面
#   （相位和联锁参数——值域合法性由 compute 守卫定义，非法组合归
#   test_compute 拒绝用例）；系数经 load_coefficients 数据包真源+D4
#   前缀投影（units_lib 层禁上行导入 app，包内镜像六行过滤）。
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
from waterprint.units_lib.municipal.cass import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_cass", port_id="in")
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
    for prefix in ("factor.cass.", "removal.cass.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_cass",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    return make_unit().compute(ctx)


def _draws() -> st.SearchStrategy[dict[str, float]]:
    """range 连续 + grid 采样；t_cycle 排除（相位和联锁——见规格头）。"""
    strategy: dict[str, st.SearchStrategy[float]] = {}
    for spec in manifest.params:
        if spec.field_id == "t_cycle":
            continue
        if spec.range is not None:
            lo, hi = spec.range
            strategy[spec.field_id] = st.floats(min_value=lo, max_value=hi)
        elif spec.grid is not None:
            strategy[spec.field_id] = st.sampled_from(spec.grid)
    return st.fixed_dictionaries(strategy)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_phase_sum_identity(draw: dict[str, float]) -> None:
    """守恒：t_phase_sum = t_cycle = t_react+t_settle+t_draw（时段和恒等）。"""
    params = _params(**draw)
    dims = _run(params).dims
    assert isinstance(dims, dict)
    assert dims["t_phase_sum"] == pytest.approx(params["t_cycle"], rel=1e-12)
    phases = params["t_react"] + params["t_settle"] + params["t_draw"]
    assert phases == pytest.approx(params["t_cycle"], rel=1e-12)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_draw_volume_within_pool(draw: dict[str, float]) -> None:
    """清单项：滗水容积≤池容、滗水深度≤滗水深度上限（CA-F9 并集推论）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["v_draw"] <= dims["v_pool"] + 1e-9
    assert dims["h_draw"] <= dims["h_draw_max"] + 1e-9


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（含清单项需氧量 o2_total≥0）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["o2_total"] >= 0.0
    for key, value in dims.items():
        assert value >= 0.0 and math.isfinite(value), (
            f"{key}={value} 非负/有限性破坏"
        )


def test_draw_volume_monotone_in_pools() -> None:
    """单调：单池单周期滗水容积 v_draw 随池数 n_pool 档位单调不增。"""
    grid = next(spec.grid for spec in manifest.params if spec.field_id == "n_pool")
    assert grid is not None and len(grid) >= 2
    previous: float | None = None
    for n_pool in grid:
        dims = _run(_params(n_pool=float(n_pool))).dims
        assert isinstance(dims, dict)
        current = dims["v_draw"]
        if previous is not None:
            assert current <= previous + 1e-9, (
                f"n_pool={n_pool}: v_draw={current} > 前档 {previous}（单调性破坏）"
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
