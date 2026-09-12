"""mine_water_gaomidu 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   上升流速≤限值、参数域与市政线互不引用
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_surface_load_band_warning_coupling：液面负荷（上升流速当量）
#     越带⇔警告在场（清单项——参数面+实际面双检查共用 param_key=q_surf，
#     按双面并集耦合）；
#   - test_axial_velocity_warning_coupling：轴向流速超上限⇔警告在场
#     （清单项同构面——单向上限）；
#   - test_municipal_keyspace_isolation：参数面与市政高密键空间零交
#     （清单项——§14.3 物理隔离在数据键面的镜像，随机参数投影面）；
#   - test_sludge_ds_conservation：排泥 DS=SS 去除量×平均流量（守恒
#     ——固流恒等）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数）；
#   - test_boundary_stability：参数域两端点不崩溃、不产 NaN/inf（边界）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】参数从 manifest range/grid 合法域生成；系数经
#   load_coefficients 数据包真源+D4 前缀投影（units_lib 层禁上行
#   导入 app，包内镜像六行过滤——矿井水线键名带 mine_ 限定）。
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
from waterprint.units_lib.mine_water.gaomidu import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_mgm", port_id="in")
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)
_LOAD_BAND = (
    "factor.mine_gaomidu.surface_load_band.min",
    "factor.mine_gaomidu.surface_load_band.max",
)
_AXIAL_MAX = "factor.mine_gaomidu.axial_velocity.max"


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.mine_gaomidu.", "removal.mine_gaomidu.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_mgm",
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
def test_surface_load_band_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：液面负荷越带⇔警告在场（参数面+实际面双检查共用
    param_key=q_surf——按双面并集耦合）。"""
    params = _params(**draw)
    result = _run(params)
    dims = result.dims
    assert isinstance(dims, dict)
    band = tuple(_COEFFS.get(key).value for key in _LOAD_BAND)
    has_warning = any(w.param_key == "q_surf" for w in result.warnings)
    expect = (
        not band[0] <= params["q_surf"] <= band[1]
    ) or (
        not band[0] <= dims["q_surf_act"] <= band[1]
    )
    assert has_warning == expect, (
        f"q_surf={params['q_surf']}/act={dims['q_surf_act']} 带 {band}"
        f" 与警告在场 {has_warning} 失耦（双面并集）"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_axial_velocity_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：轴向流速超上限⇔警告在场（单向上限双向耦合）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    upper = _COEFFS.get(_AXIAL_MAX).value
    has_warning = any(w.param_key == "n" for w in result.warnings)
    assert has_warning == (dims["v_axial"] > upper), (
        f"v_axial={dims['v_axial']} 上限 {upper} 与警告在场 {has_warning} 失耦"
    )


def test_municipal_keyspace_isolation() -> None:
    """清单项：参数面与市政高密键空间零交（§14.3 物理隔离镜像）。"""
    params = _params()
    municipal_keys = set(_COEFFS.keys("factor.gaomidu.")) | set(
        _COEFFS.keys("removal.gaomidu.")
    )
    leaked = municipal_keys & set(params)
    assert not leaked, f"矿井水高密参数面泄漏市政键：{sorted(leaked)}"


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_sludge_ds_conservation(draw: dict[str, float]) -> None:
    """守恒：排泥 DS=SS 去除量（(SS_in−SS_out)×q_avg 恒等）。"""
    result = _run(_params(**draw))
    out_quality = result.outqualities[PortRef(unit_id="prop_mgm", port_id="out")]
    sludge = result.outflows[PortRef(unit_id="prop_mgm", port_id="sludge_out")]
    assert isinstance(sludge, SludgeFlow)
    ss_in = _QUALITY.SS
    ss_out = out_quality.SS
    assert ss_in is not None and ss_out is not None
    removed_load = (ss_in - ss_out) * 1e-3 * _FLOW.q_avg_daily
    assert sludge.ds == pytest.approx(removed_load, rel=1e-9, abs=1e-12), (
        f"排泥 DS={sludge.ds} ≠ SS 去除负荷 {removed_load}（固流守恒破坏）"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（几何/容积/药剂量面）。"""
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
