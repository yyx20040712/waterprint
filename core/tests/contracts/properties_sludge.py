"""sludge 性质测试：DS 守恒的随机化验证（混合/多股）。

输入:  hypothesis 随机 SludgeFlow 组
输出:  Σds 守恒断言（含水率变化不守恒即失败——§14.2）
"""

from __future__ import annotations

import importlib

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

_mod = importlib.import_module("waterprint.contracts.sludge")
make_sludge = getattr(_mod, "make_sludge", None)
mix = getattr(_mod, "mix", None)

pytestmark = [
    pytest.mark.skipif(
        None in (make_sludge, mix),
        reason="实现未就绪：waterprint.contracts.sludge（M1）",
    ),
]

q_wet = st.floats(min_value=1e-9, max_value=1.0, allow_nan=False)
ds = st.floats(min_value=1e-9, max_value=100.0, allow_nan=False)
moisture = st.floats(min_value=0.0, max_value=0.999, allow_nan=False)


@given(flows=st.lists(
    st.tuples(q_wet, ds, moisture), min_size=2, max_size=5
))
def test_mix_conserves_ds_random(flows: list[tuple[float, float, float]]) -> None:
    """随机 2~5 股混合：Σds 与 Σq_wet 守恒（相对容差内）。"""
    sludges = [make_sludge(q, d, m) for (q, d, m) in flows]
    merged = mix(sludges)
    total_ds = sum(d for (_, d, _) in flows)
    assert merged.ds == pytest.approx(total_ds, rel=1e-9)
    assert merged.q_wet == pytest.approx(sum(q for (q, _, _) in flows), rel=1e-9)
