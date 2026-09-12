"""municipal_ziwai 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   剂量≥设计最小值、灯管数为正整数
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_lamp_count_integer：灯管/模块数=正整数且≥其未取整原值
#     （清单项——ceil 整台化恒等，随机参数）；
#   - test_dose_band_warning_coupling：有效接触时间（剂量当量）越带⇔
#     警告在场（清单项——"剂量≥设计最小值"域面由警告通道诚实呈现）；
#   - test_submerge_warning_coupling：灯管淹没裕量<0⇔警告在场（ZW-F11
#     诚实校核面——h_submerge 为差值校核量，可负域由警告承载）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数；
#     h_submerge 除外——首跑实录抓出其可负域=淹没校核差值非几何量）；
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
from waterprint.units_lib.municipal.ziwai import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_zw", port_id="in")
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)
_TEXP_BAND = ("factor.ziwai.t_exp_band.min", "factor.ziwai.t_exp_band.max")


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.ziwai.", "removal.ziwai.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_zw",
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
def test_lamp_count_integer(draw: dict[str, float]) -> None:
    """清单项：灯管/模块数为正整数且≥未取整原值（ceil 整台化恒等）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for field in ("n_lamp", "n_module", "n_module_series"):
        value = dims[field]
        assert value == int(value) and value >= 1.0, (
            f"{field}={value} 非正整数（灯管数清单项）"
        )
    assert dims["n_lamp"] >= dims["n_lamp_raw"] - 1e-12
    assert dims["n_module"] >= dims["n_module_raw"] - 1e-12


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_dose_band_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：有效接触时间（剂量当量）越带⇔警告在场（双向耦合）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    band = tuple(_COEFFS.get(key).value for key in _TEXP_BAND)
    has_warning = any(w.param_key == "n_lamp_module" for w in result.warnings)
    assert has_warning == (not band[0] <= dims["t_exp"] <= band[1]), (
        f"t_exp={dims['t_exp']} 带 {band} 与警告在场 {has_warning} 失耦"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_submerge_warning_coupling(draw: dict[str, float]) -> None:
    """ZW-F11：灯管淹没裕量<0⇒淹没警告在场（单向——param_key 与渠流速
    带共用 v_channel，按消息特征"灯管露出水面"锚定安全关键半边）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    if dims["h_submerge"] < 0.0:
        assert any("灯管露出水面" in w.message for w in result.warnings), (
            f"h_submerge={dims['h_submerge']} 而淹没警告缺席（ZW-F11 失耦）"
        )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（h_submerge 除外——校核差值量）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        if key == "h_submerge":
            assert math.isfinite(value)
            continue
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
