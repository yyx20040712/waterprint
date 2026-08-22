"""propagate 镜像测试：汇流加权混合（工况流量加权、负荷守恒、夹逼）。

输入:  waterprint.graph.propagate.mix + contracts 类型
输出:  混合语义断言（§14.2 修正语义的锁定测试）
"""

from __future__ import annotations

import importlib

import pytest

_flow = importlib.import_module("waterprint.contracts.flow")
make_flow = getattr(_flow, "make_flow", None)
_qty = importlib.import_module("waterprint.contracts.quantity")
Quantity = getattr(_qty, "Quantity", None)
_q = importlib.import_module("waterprint.contracts.quality")
WaterQuality = getattr(_q, "WaterQuality", None)

_mod = importlib.import_module("waterprint.graph.propagate")
mix = getattr(_mod, "mix", None)

pytestmark = pytest.mark.skipif(
    None in (make_flow, Quantity, WaterQuality, mix),
    reason="实现未就绪：waterprint.graph.propagate.mix（M1）",
)


def _flow(q_avg: float, kz: float):
    return make_flow(Quantity(q_avg, "m3/s"), kz)


def test_mix_is_load_weighted_not_average() -> None:
    """R1：负荷加权 ΣCi·Qi/ΣQi——两股不同浓度结果 ≠ 简单平均。"""
    q1, q2 = 3.0, 1.0
    c1, c2 = 100.0, 20.0
    mixed = mix(
        [WaterQuality({"BOD5": c1}), WaterQuality({"BOD5": c2})],
        [q1, q2],
    )
    expected = (c1 * q1 + c2 * q2) / (q1 + q2)
    assert getattr(mixed, "BOD5") == pytest.approx(expected)
    assert expected != pytest.approx((c1 + c2) / 2)


def test_mix_conserves_load() -> None:
    """R3：混合负荷守恒 ΣCi·Qi = C_mix × ΣQi。"""
    flows = [(2.0, 50.0), (3.0, 120.0)]
    mixed = mix(
        [WaterQuality({"BOD5": c}) for (_, c) in flows],
        [q for (q, _) in flows],
    )
    total_load = sum(q * c for (q, c) in flows)
    assert getattr(mixed, "BOD5") * sum(q for (q, _) in flows) == pytest.approx(total_load)


def test_mixed_concentration_between_min_max() -> None:
    """R3：混合浓度必介于各股 min/max 之间（夹逼）。"""
    mixed = mix(
        [WaterQuality({"BOD5": 10.0}), WaterQuality({"BOD5": 300.0})],
        [1.0, 4.0],
    )
    assert 10.0 < getattr(mixed, "BOD5") < 300.0


def test_design_weighting_differs_from_avg_weighting() -> None:
    """R1（工况语义）：q_design 与 q_avg_daily 加权在 Kz 不对称时必须不同。

    两股 Kz 不同 → design 档权重比 ≠ avg 档权重比 → 混合结果不同。
    （此测试锁定"汇流加权随工况"的语义，防回退旧系统固定 Q_design。）
    """
    f1, f2 = _flow(2.0, 1.5), _flow(3.0, 1.0)
    qualities = [WaterQuality({"BOD5": 60.0}), WaterQuality({"BOD5": 90.0})]
    by_design = mix(qualities, [f.q_design for f in (f1, f2)])
    by_avg = mix(qualities, [f.q_avg_daily for f in (f1, f2)])
    assert getattr(by_design, "BOD5") != pytest.approx(getattr(by_avg, "BOD5"))
