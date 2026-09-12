"""mine_water_input 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（注入点——零入流，水量水质经参数面）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   流量>0、各浓度非负
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_design_flow_identity：设计流量=平均日流量×变化系数（守恒
#     ——KI-F1 恒等，dims 规范单位 m3/s 经 /86400 换算，随机参数）；
#   - test_flow_positive：注入流量>0（清单项——q_design/q_avg_h/出流）；
#   - test_quality_injection_echo：出流水质=参数注入五指标（清单项
#     ——各浓度非负回显恒等）；
#   - test_freeboard_warning_coupling：地面高出进水水面低于下限⇔警告
#     在场（KI 超高校核诚实面）；
#   - test_nonneg_finite：dims 流量/流速/浓度面非负+有限（标高族除外
#     ——高程为坐标量非物理量，随机参数）；
#   - test_boundary_stability：参数域两端点不崩溃、不产 NaN/inf（边界）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】注入点零入流构造（_no_inflow 守卫的镜像面）；参数从
#   manifest range/grid 合法域生成；系数经 load_coefficients 数据包
#   真源+D4 前缀投影（units_lib 层禁上行导入 app，包内镜像六行过滤）。
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
from waterprint.contracts.unit_api import UnitContext, UnitResult  # noqa: E402
from waterprint.registry.coefficients import load_coefficients  # noqa: E402
from waterprint.units_lib.mine_water.input import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_OUT_REF = PortRef(unit_id="prop_ki", port_id="out")
_QUALITY_PARAMS = ("ss_in", "cod_in", "nh3n_in", "tn_in", "tp_in")
_QUALITY_INDICATORS = ("SS", "CODCR", "NH3N", "TN", "TP")
_FREEBOARD_MIN = "factor.mine_input.freeboard.min"
# 标高族=坐标量（可负域），非物理量面——非负断言豁免键
_ELEVATION_KEYS = frozenset({"z_pipe_bottom", "z_water", "z_bottom", "freeboard"})


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.mine_input.", "removal.mine_input.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_ki",
        inflows={},
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
def test_design_flow_identity(draw: dict[str, float]) -> None:
    """守恒：q_design = q_avg_daily×kz（KI-F1 恒等——dims 规范单位
    m3/s，参数面 m3/d 经 /86400 换算）。"""
    params = _params(**draw)
    dims = _run(params).dims
    assert isinstance(dims, dict)
    assert dims["q_design"] == pytest.approx(
        params["q_avg_daily"] * params["kz"] / 86400.0, rel=1e-9
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_flow_positive(draw: dict[str, float]) -> None:
    """清单项：注入流量>0（设计流量/平均时流量/出流端口）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["q_design"] > 0.0
    assert dims["q_avg_h"] > 0.0
    out = result.outflows[_OUT_REF]
    assert isinstance(out, WaterFlow)
    assert out.q_avg_daily > 0.0


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_quality_injection_echo(draw: dict[str, float]) -> None:
    """清单项：出流水质=参数注入五指标（浓度非负回显恒等）。"""
    params = _params(**draw)
    result = _run(params)
    out_quality = result.outqualities[_OUT_REF]
    for indicator, param in zip(
        _QUALITY_INDICATORS, _QUALITY_PARAMS, strict=True
    ):
        value = float(getattr(out_quality, indicator))
        assert value == pytest.approx(params[param], rel=1e-12)
        assert value >= 0.0, f"{indicator} 注入浓度 {value} 为负"


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_freeboard_warning_coupling(draw: dict[str, float]) -> None:
    """超高校核：地面高出进水水面低于下限⇔警告在场（诚实面耦合）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    floor = _COEFFS.get(_FREEBOARD_MIN).value
    has_warning = any(w.param_key == "z_ground" for w in result.warnings)
    assert has_warning == (dims["freeboard"] < floor), (
        f"freeboard={dims['freeboard']} 下限 {floor} 与警告在场 {has_warning} 失耦"
    )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：流量/流速面非负且有限（标高族除外——坐标量）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        if key in _ELEVATION_KEYS:
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
