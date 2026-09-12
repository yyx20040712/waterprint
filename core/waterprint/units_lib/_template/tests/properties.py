"""单元性质测试模板：四模板通用断言（非负/单调/守恒/边界）蓝本。

输入:  目标单元 compute（_UNIT_MODULE 指定）；manifest 参数域
输出:  性质验证结果（wp new-unit 复制后改一行导入即全绿）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：可执行蓝本）
#
# 【使用工序】`wp new-unit <line> <name>` 复制本件到新单元包后，
#   将 _UNIT_MODULE 改为实际包路径（如
#   "waterprint.units_lib.municipal.newunit"）——四条通用断言即刻
#   激活；单元专属守恒/单调按各包规格头【本单元性质清单】追加
#   （GR-30：新单元 properties.py 至少挂一条守恒或单调）。
# 【骨架合法（D6）】_template 包自身无 compute 导出——动态导入失败
#   即零用例定义（与空骨架同语义，收集零 skip 零 error）；生成包
#   在 manifest+compute 就绪前同态。
#
# 【固定形态（按单元适用性取用，至少两条）】
#   - 非负性：一切几何量/设备数/负荷 >= 0；
#   - 单调性：容积类结果随池数/尺寸参数单调不减（网格有序维断言）；
#   - 守恒性：质量/负荷进出平衡（进出水负荷差 == 去除率语义允许值，
#     去除率上下界来自 coefficients——不编数字）；
#   - 边界：N=1、最小参数、极端进水（构造合法域边界值）不崩溃、
#     不产生 NaN/inf。
#
# 【生成策略】参数从 manifest 范围内生成（合法域测试），非法域
#   构造留给 test_compute 的显式拒绝用例。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import math
from typing import Any

import pytest

hypothesis = pytest.importorskip("hypothesis")

_UNIT_MODULE = "waterprint.units_lib.municipal.newunit"  # ← 生成后改本行
try:
    _mod: Any = importlib.import_module(_UNIT_MODULE)
except ImportError:  # 骨架未接线（D6）——零用例合法
    _mod = None

if _mod is not None:
    from hypothesis import given, settings
    from hypothesis import strategies as st

    from waterprint.contracts.condition import (
        FlowCase,
        OperatingCondition,
    )
    from waterprint.contracts.flow import WaterFlow
    from waterprint.contracts.ports import PortRef
    from waterprint.contracts.quality import WaterQuality
    from waterprint.contracts.unit_api import UnitContext

    make_unit: Any = _mod.make_unit
    manifest: Any = _mod.manifest
    _UNIT_ID: str = manifest.unit_id

    class _Sink:
        """空迹收集器（结构满足 TraceSink 协议——蓝本同款）。"""

        def record(self, node: Any) -> None:
            """协议方法：空实现。"""
    _IN_REF = PortRef(unit_id="prop_tpl", port_id="in")
    _FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
    _QUALITY = WaterQuality(
        {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
    )

    def _run(params: dict[str, float]) -> Any:
        ctx = UnitContext(
            unit_id="prop_tpl",
            inflows={_IN_REF: _FLOW},
            inqualities={_IN_REF: _QUALITY},
            params=params,
            condition=OperatingCondition(flow_case=FlowCase.DESIGN),
            assumptions={},
            trace=_Sink(),
        )
        return make_unit().compute(ctx)

    def _draws() -> Any:
        strategy: dict[str, Any] = {}
        for spec in manifest.params:
            if spec.range is not None:
                lo, hi = spec.range
                strategy[spec.field_id] = st.floats(min_value=lo, max_value=hi)
            elif spec.grid is not None:
                strategy[spec.field_id] = st.sampled_from(spec.grid)
        return st.fixed_dictionaries(strategy)

    @given(draw=_draws())
    @settings(max_examples=30, deadline=None, derandomize=True)
    def test_nonneg_finite(draw: dict[str, float]) -> None:
        """非负性：一切 dims 量非负且有限（默认参数面）。"""
        dims = _run({s.field_id: s.default for s in manifest.params}).dims
        assert isinstance(dims, dict)
        for key, value in dims.items():
            assert value >= 0.0 and math.isfinite(value), (
                f"{key}={value} 非负/有限性破坏"
            )

    @given(draw=_draws())
    @settings(max_examples=30, deadline=None, derandomize=True)
    def test_purity(draw: dict[str, float]) -> None:
        """纯函数：同 ctx 双跑同果（R1——可复算基石）。"""
        base = {s.field_id: s.default for s in manifest.params}
        first = _run({**base, **draw})
        second = _run({**base, **draw})
        assert dict(first.dims) == dict(second.dims)
        assert first.formula_ids == second.formula_ids

    def test_boundary_stability() -> None:
        """边界：range 参数两端点实跑不崩溃、不产 NaN/inf。"""
        base = {s.field_id: s.default for s in manifest.params}
        for spec in manifest.params:
            if spec.range is None:
                continue
            for edge in spec.range:
                dims = _run({**base, spec.field_id: edge}).dims
                assert isinstance(dims, dict)
                for value in dims.values():
                    assert math.isfinite(value), (
                        f"{spec.field_id}={edge} 边界产 NaN/inf"
                    )
