"""municipal_bashi_jiliangcao 物理不变性测试（hypothesis 性质）。

输入:  本包 compute + manifest 参数域
输出:  性质验证结果（违反物理不变性即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（GOV3 2026-09-12 语义覆盖批转实：性质清单全量断言）
#
# 【本单元性质清单（旧系统物理测试映射）】
#   流量-水头关系单调、喉宽取标准档位
# 【通用性质】非负性/单调性/守恒（按单元适用）/边界稳定。
#
# 【实装面】
#   - test_head_monotone_in_flow：量水堰水头 ha_design/h_loss 随设计流量
#     单调不减（清单项——流量-水头关系单调，8 点流幅扫描）；
#   - test_throat_grade_grid：B7 七档喉宽全档位实跑合法（清单项——
#     非档位值由 compute 选档守卫拒绝，档位面全绿即"取标准档位"）；
#   - test_nonneg_finite：全 dims 非负+有限（非负性，档位随机）；
#   - test_purity：同 ctx 双跑同果（R1 纯函数）。
# 【策略纪律】参数从 manifest grid 合法域采样（range 面为空——
#   本单元仅喉宽一参带域）；系数经 load_coefficients 数据包真源
#   +D4 前缀投影（与 app_assembly _unit_params 同式——units_lib
#   层禁上行导入 app，包内镜像六行过滤）。
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
from waterprint.units_lib.municipal.bashi_jiliangcao import (  # noqa: E402
    make_unit,
    manifest,
)

_REPO_ROOT = Path(__file__).resolve().parents[6]
_COEFFS = load_coefficients(_REPO_ROOT / "data" / "coefficients")
_IN_REF = PortRef(unit_id="prop_bashi", port_id="in")
_QUALITY = WaterQuality(
    {"BOD5": 123.3, "CODCR": 199.9, "SS": 93.2, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议——test_compute.py 同款）。"""

    def record(self, node: Any) -> None:
        """协议方法：空实现。"""


def _params(**overrides: float) -> dict[str, float]:
    """manifest 默认 + 系数投影（D4 同式三前缀过滤，数据包真源）。"""
    params = {spec.field_id: spec.default for spec in manifest.params}
    for prefix in (
        "factor.bashi_jiliangcao.",
        "removal.bashi_jiliangcao.",
        "factor.screen.",
    ):
        for key in _COEFFS.keys(prefix):
            params[key] = _COEFFS.get(key).value
    params.update(overrides)
    return params


def _run(params: dict[str, float], flow_scale: float = 1.0) -> UnitResult:
    flow = WaterFlow(q_avg_daily=34760.7 / 86400 * flow_scale, kz=1.4)
    ctx = UnitContext(
        unit_id="prop_bashi",
        inflows={_IN_REF: flow},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    return make_unit().compute(ctx)


def _draws() -> st.SearchStrategy[dict[str, float]]:
    """grid 参数档位采样（本单元 range 面为空——唯一带域参数=喉宽档）。"""
    strategy: dict[str, st.SearchStrategy[float]] = {}
    for spec in manifest.params:
        if spec.grid is not None:
            strategy[spec.field_id] = st.sampled_from(spec.grid)
    return st.fixed_dictionaries(strategy)


def test_head_monotone_in_flow() -> None:
    """单调：堰上水头 ha_design 与水头损失 h_loss 随流量单调不减。"""
    scales = (0.3, 0.5, 0.8, 1.0, 1.3, 1.8, 2.5, 3.0)
    previous: tuple[float, float] | None = None
    for scale in scales:
        dims = _run(_params(), flow_scale=scale).dims
        assert isinstance(dims, dict)
        current = (dims["ha_design"], dims["h_loss"])
        if previous is not None:
            assert current[0] >= previous[0] - 1e-12, (
                f"scale={scale}: ha_design={current[0]} < 前点 {previous[0]}"
            )
            assert current[1] >= previous[1] - 1e-12, (
                f"scale={scale}: h_loss={current[1]} < 前点 {previous[1]}"
            )
        previous = current


def test_throat_grade_grid() -> None:
    """边界：B7 七档喉宽全档位实跑合法、不产 NaN/inf（档位即合法域）。"""
    grid = next(spec.grid for spec in manifest.params if spec.field_id == "b_throat")
    assert grid is not None and len(grid) >= 2
    for b_throat in grid:
        dims = _run(_params(b_throat=float(b_throat))).dims
        assert isinstance(dims, dict)
        for value in dims.values():
            assert math.isfinite(value), f"b_throat={b_throat} 产 NaN/inf"


@given(draw=_draws())
@settings(max_examples=40, deadline=None, derandomize=True)
def test_nonneg_finite(draw: dict[str, float]) -> None:
    """非负性：一切 dims 量非负且有限（几何量/量测水力量）。"""
    dims = _run(_params(**draw)).dims
    assert isinstance(dims, dict)
    for key, value in dims.items():
        assert value >= 0.0 and math.isfinite(value), (
            f"{key}={value} 非负/有限性破坏"
        )


@given(draw=_draws())
@settings(max_examples=20, deadline=None, derandomize=True)
def test_purity(draw: dict[str, float]) -> None:
    """纯函数：同 ctx 双跑同果（R1——可复算基石）。"""
    first = _run(_params(**draw))
    second = _run(_params(**draw))
    assert dict(first.dims) == dict(second.dims)
    assert first.formula_ids == second.formula_ids
