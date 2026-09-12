"""municipal_cugeshan 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   过栅流速在设计档位内、水头损失≥0、栅渣量≥0
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_velocity_band_warning_coupling：校核流速越带⇔警告在场（清单项
#     ——"在设计档位内"域面由警告通道诚实呈现，param_key=v/v1 双带）；
#   - test_head_loss_nonneg：水头损失 h1≥0（清单项）；
#   - test_slag_nonneg：栅渣量 w_slag/ds_slag≥0（清单项）；
#   - test_slag_monotone_in_flow：栅渣量随流量单调不减（单调——
#     CG-F11 q_design 线性因子，8 点流幅扫描）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数）；
#   - test_boundary_stability：参数域两端点不崩溃、不产 NaN/inf（边界）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】参数从 manifest range/grid 合法域生成；系数经
#   load_coefficients 数据包真源+D4 前缀投影（units_lib 层禁上行
#   导入 app，包内镜像六行过滤——格栅带键 factor.screen.* 共用段）。
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
from waterprint.units_lib.municipal.cugeshan import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_cugeshan", port_id="in")
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)
_V_BAND = ("factor.screen.velocity_band.v.min", "factor.screen.velocity_band.v.max")
_V1_BAND = ("factor.screen.velocity_band.v1.min", "factor.screen.velocity_band.v1.max")


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.cugeshan.", "removal.cugeshan.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float], flow_scale: float = 1.0) -> UnitResult:
    flow = WaterFlow(q_avg_daily=34760.7 / 86400 * flow_scale, kz=1.4)
    ctx = UnitContext(
        unit_id="prop_cugeshan",
        inflows={_IN_REF: flow},
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
def test_velocity_band_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：过栅/栅前流速越带⇔对应警告在场（诚实校核面双向耦合）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    v_band = tuple(_COEFFS.get(key).value for key in _V_BAND)
    v1_band = tuple(_COEFFS.get(key).value for key in _V1_BAND)
    has_v_warning = any(w.param_key == "v" for w in result.warnings)
    has_v1_warning = any(w.param_key == "v1" for w in result.warnings)
    assert has_v_warning == (not v_band[0] <= dims["v_checked"] <= v_band[1]), (
        f"v_checked={dims['v_checked']} 带 {v_band} 与警告在场 {has_v_warning} 失耦"
    )
    assert has_v1_warning == (not v1_band[0] <= dims["v1_checked"] <= v1_band[1]), (
        f"v1_checked={dims['v1_checked']} 带 {v1_band} 与警告在场 {has_v1_warning} 失耦"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_head_loss_nonneg(draw: dict[str, float]) -> None:
    """清单项：水头损失 h1≥0（阻力物理域）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["h1"] >= 0.0


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_slag_nonneg(draw: dict[str, float]) -> None:
    """清单项：栅渣量 w_slag≥0、栅渣浓度 ds_slag≥0。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["w_slag"] >= 0.0
    assert dims["ds_slag"] >= 0.0


def test_slag_monotone_in_flow() -> None:
    """单调：栅渣量随设计流量单调不减（CG-F11 流量线性因子）。"""
    scales = (0.3, 0.5, 0.8, 1.0, 1.3, 1.8, 2.5, 3.0)
    previous: float | None = None
    for scale in scales:
        dims = _run(_params(), flow_scale=scale).dims
        assert isinstance(dims, dict)
        current = dims["w_slag"]
        if previous is not None:
            assert current >= previous - 1e-12, (
                f"scale={scale}: w_slag={current} < 前点 {previous}（单调性破坏）"
            )
        previous = current


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（几何量/阻力量/渣量）。"""
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
