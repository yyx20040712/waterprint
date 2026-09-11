"""通用语义门禁：声明 removal_refs 的单元出流指标 = 入流×(1−r)（代数不变式）。

输入:  units_lib.discover_units() 全部声明 removal_refs 的单元（正门发现）
       + data/coefficients 数据包真源去除率（registry 装载+app._unit_params 投影）
输出:  参数化断言结果（任何"声明去除而透传/率用错/漏键"即失败——UF-51 类防线）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV1 2026-09-12 深度审计裁决 C1 通用件；ADR-013）：
#   不变式：DESIGN 工况默认参数实跑，对每个 K ∈ removal_refs：
#     out[K] ≈ in[K] × (1 − r[K])，r 自数据包真源（GR-15 出处纪律）。
#   实测基线（2026-09-12 入库日）：20 单元 × 全指标零偏差。
#   语义防线（与逐单元精确值断言互补——NP1/NP2 锁数值，本件锁语义存在性）：
#   UF-51 型缺陷（声明 removal_refs 却零去除透传，如 M2 期 N/P 穿流）在本面
#   即刻红；透传单元合法（数据包显式 r=0.0 带出处注记——诚实穿流 ≠ 空实现）。
#   正门纪律（宪法 §1）：单元发现经 units_lib.discover_units（装配点唯一），
#   系数投影经 app._unit_params（D4 投影正门），禁本件自建投影。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path

import pytest

from waterprint.app import _unit_params
from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import UnitContext
from waterprint.registry.coefficients import load_coefficients
from waterprint.units_lib import discover_units

REPO_ROOT = Path(__file__).resolve().parents[3]
_COEFFS = load_coefficients(REPO_ROOT / "data" / "coefficients")
# 规范入流/入质（六指标全给——覆盖全部 removal_refs 键名族；量级取
# docs/norms 市政算例衔接式值，任何物理合理量级不影响代数式断言）
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)
# 声明 removal_refs 的单元（快照参数化面——新单元入册即自动纳入防线）
_REMOVAL_UNITS = sorted(
    unit_id
    for unit_id, (manifest, _factory) in discover_units().items()
    if manifest.removal_refs
)


def _water_out_port(unit_id: str, manifest: object) -> PortRef:
    """取唯一 WATER OUT 端口（多出水口=结构歧义，显式红）。"""
    ports = [
        p for p in manifest.ports
        if p.direction.name == "OUT" and p.fluid.name == "WATER"
    ]
    assert len(ports) == 1, f"{unit_id}: WATER OUT 端口数 {len(ports)} ≠ 1"
    return PortRef(unit_id=unit_id, port_id=ports[0].port_id)


@pytest.mark.parametrize("unit_id", _REMOVAL_UNITS)
def test_removal_algebraic_invariant(unit_id: str) -> None:
    """出流 = 入流×(1−r) 全指标代数断言（r 自数据包真源）。"""
    manifest, factory = discover_units()[unit_id]
    params = {spec.field_id: spec.default for spec in manifest.params}
    params.update(_unit_params(unit_id, _COEFFS))
    in_ref = PortRef(unit_id=unit_id, port_id="in")
    ctx = UnitContext(
        unit_id=unit_id,
        inflows={in_ref: _FLOW},
        inqualities={in_ref: _QUALITY},
        params=params,
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=None,
    )
    result = factory().compute(ctx)
    out_ref = _water_out_port(unit_id, manifest)
    out_quality = result.outqualities[out_ref]
    for indicator, coeff_key in manifest.removal_refs.items():
        rate = _COEFFS.get(coeff_key).value
        assert 0.0 <= rate <= 1.0, (
            f"{unit_id}.{indicator}: 去除率 {rate} 越域 [0,1]（{coeff_key}）"
        )
        inflow = float(getattr(_QUALITY, indicator))
        outflow = float(getattr(out_quality, indicator))
        expected = inflow * (1.0 - rate)
        assert outflow == pytest.approx(expected, rel=1e-9, abs=1e-12), (
            f"{unit_id}.{indicator}: 出流 {outflow} ≠ 入流×(1−r)"
            f"={expected}（r={rate}，{coeff_key}——声明去除未兑现或率用错，"
            "UF-51 类语义缺陷）"
        )
