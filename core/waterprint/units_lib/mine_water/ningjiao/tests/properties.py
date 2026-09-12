"""mine_water_ningjiao 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   GT 值在设计带内、药剂量≥0
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_gt_band_warning_coupling：四分区总 GT 越带⇒警告在场（清单项
#     ——"在设计带内"域面由警告通道诚实呈现；GT 警告 param_key 与分区
#     停留带共用 t_mix，按消息特征"总 GT"锚定安全关键半边）；
#   - test_dose_nonneg：药剂量 m_pac/m_pam/m_seed≥0（清单项）；
#   - test_flow_conservation：出流水量=入流（穿流守恒）；
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
from waterprint.contracts.unit_api import UnitContext, UnitResult  # noqa: E402
from waterprint.registry.coefficients import load_coefficients  # noqa: E402
from waterprint.units_lib.mine_water.ningjiao import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_mnj", port_id="in")
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)
_GT_BAND = ("factor.mine_ningjiao.gt_band.min", "factor.mine_ningjiao.gt_band.max")


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.mine_ningjiao.", "removal.mine_ningjiao.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_mnj",
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
def test_gt_band_warning_coupling(draw: dict[str, float]) -> None:
    """清单项：总 GT 越带⇒警告在场（消息锚定——param_key 与分区带共用）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    band = tuple(_COEFFS.get(key).value for key in _GT_BAND)
    outside = not band[0] <= dims["gt_total"] <= band[1]
    if outside:
        assert any("总 GT" in w.message for w in result.warnings), (
            f"gt_total={dims['gt_total']} 越带 {band} 而警告缺席（失耦）"
        )


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_dose_nonneg(draw: dict[str, float]) -> None:
    """清单项：药剂量 m_pac/m_pam/m_seed≥0（投加物理域）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    assert dims["m_pac"] >= 0.0
    assert dims["m_pam"] >= 0.0
    assert dims["m_seed"] >= 0.0


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_flow_conservation(draw: dict[str, float]) -> None:
    """守恒：出流水量=入流水量（高密度澄清前置凝聚穿流恒等）。"""
    result = _run(_params(**draw))
    out = result.outflows[PortRef(unit_id="prop_mnj", port_id="out")]
    assert isinstance(out, WaterFlow)
    assert out.q_avg_daily == pytest.approx(_FLOW.q_avg_daily, rel=1e-12)
    assert out.kz == pytest.approx(_FLOW.kz, rel=1e-12)


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（四分区几何/容积/药剂量面）。"""
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
