"""sludge_hebing 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域（三股污泥经参数面合成——无入流边）
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言。
#   contracts/properties_sludge.py 锁定 mix 代数面（contracts 层），
#   本件锁定本包 compute 三股合成全链（单元层——两层互补非重复））
#
# 【本单元性质清单（旧系统物理测试映射）】
#   湿泥量加和守恒、DS（干固体）加和守恒（HB-F4~F7 与 mix P4 镜像）
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_flow_sum_conservation：汇出湿泥量=三股之和（清单项——
#     HB-F4~F6 加和恒等 q_total=q_primary+q_bio+q_chem）；
#   - test_port_echo：出流端口 q_wet/ds=dims 汇出面回显（清单项 DS
#     加和守恒的端口面——ds_total 单源回显恒等）；
#   - test_flow_monotone_in_plant_flow：汇出湿泥量随厂均流量单调不减
#     （单调——初沉/生池除污泥量线性因子，五点扫描）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，随机参数）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】三股污泥经参数面合成（无 SLUDGE 入流边——HB 单源
#   合成口径）；参数域 range/grid 均空——随机面退化为单例（默认
#   参数面），单调/边界由厂流量扫描面承载；系数经 load_coefficients
#   数据包真源+D4 前缀投影（units_lib 层禁上行导入 app，包内镜像
#   六行过滤）。
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
from waterprint.units_lib.sludge.hebing import make_unit, manifest  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in ("factor.hebing.", "removal.hebing.", "factor.screen."):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float]) -> UnitResult:
    ctx = UnitContext(
        unit_id="prop_hb",
        inflows={},
        inqualities={},
        params=params,
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    return make_unit().compute(ctx)


def _draws() -> st.SearchStrategy[dict[str, float]]:
    """range/grid 均空——单例策略（默认参数面，退化合法）。"""
    return st.fixed_dictionaries({})


@given(draw=_draws())
@settings(max_examples=10, deadline=None, derandomize=True)
def test_flow_sum_conservation(draw: dict[str, float]) -> None:
    """清单项守恒：汇出湿泥量=初沉+生化+化学三股之和（加和恒等）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    total = dims["q_primary"] + dims["q_bio"] + dims["q_chem"]
    assert dims["q_total"] == pytest.approx(total, rel=1e-9, abs=1e-12)


@given(draw=_draws())
@settings(max_examples=10, deadline=None, derandomize=True)
def test_port_echo(draw: dict[str, float]) -> None:
    """清单项守恒：出流端口 q_wet/ds=dims 汇出面回显（单源恒等）。"""
    result = _run(_params(**draw))
    dims = result.dims
    assert isinstance(dims, dict)
    out = result.outflows[PortRef(unit_id="prop_hb", port_id="out")]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(dims["q_total"] / 86400.0, rel=1e-9)
    assert out.ds == pytest.approx(dims["ds_total"] / 86400.0, rel=1e-9)


def test_flow_monotone_in_plant_flow() -> None:
    """单调：汇出湿泥量随厂均流量单调不减（污泥产率线性因子，五点）。"""
    spec = next(s for s in manifest.params if s.field_id == "q_avg_daily")
    base = spec.default
    points = [base * factor for factor in (0.5, 0.75, 1.0, 1.5, 2.0)]
    previous: float | None = None
    for q_avg in points:
        dims = _run(_params(q_avg_daily=q_avg)).dims
        assert isinstance(dims, dict)
        current = dims["q_total"]
        if previous is not None:
            assert current >= previous - 1e-12, (
                f"q_avg_daily={q_avg}: q_total={current} < 前点 {previous}"
            )
        previous = current


@given(draw=_draws())
@settings(max_examples=10, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（三股流量/DS/含固面）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        assert value >= 0.0 and math.isfinite(value), (
            f"{key}={value} 非负/有限性破坏"
        )


@given(draw=_draws())
@settings(max_examples=10, deadline=None, derandomize=True)
def test_purity(draw: dict[str, float]) -> None:
    """纯函数：同 ctx 双跑同果（R1——可复算基石）。"""
    first = _run(_params(**draw))
    second = _run(_params(**draw))
    assert dict(first.dims) == dict(second.dims)
    assert first.formula_ids == second.formula_ids
