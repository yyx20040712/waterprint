"""propagate 性质测试：随机两股混合的守恒与夹逼。

输入:  hypothesis 随机流量/浓度对
输出:  负荷守恒 + min/max 夹逼性质
"""

from __future__ import annotations

import importlib

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

_mod = importlib.import_module("waterprint.graph.propagate")
mix = getattr(_mod, "mix", None)
_quality = importlib.import_module("waterprint.contracts.quality")
WaterQuality = getattr(_quality, "WaterQuality", None)

pytestmark = [
    pytest.mark.skipif(
        None in (mix, WaterQuality),
        reason="实现未就绪：waterprint.graph.propagate.mix（M1）",
    ),
]

flows = st.floats(min_value=1e-6, max_value=1e3, allow_nan=False)
concs = st.floats(min_value=1e-6, max_value=1e4, allow_nan=False)


@given(data=st.data())
def test_random_mix_conserves_and_clamps(data) -> None:
    """随机两股：负荷守恒且混合浓度 ∈ (min, max)。"""
    (q1, c1) = (data.draw(flows), data.draw(concs))
    (q2, c2) = (data.draw(flows), data.draw(concs))
    mixed = mix([WaterQuality({"BOD5": c1}), WaterQuality({"BOD5": c2})], [q1, q2])
    value = getattr(mixed, "BOD5")
    assert value * (q1 + q2) == pytest.approx(c1 * q1 + c2 * q2, rel=1e-9)
    assert min(c1, c2) <= value <= max(c1, c2)
