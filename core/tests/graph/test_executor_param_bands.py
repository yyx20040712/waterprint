"""executor 参数声明带边界测试（FZ-2 补面，R2 d1-W5 回炉批 2026-09-30）。

输入:  waterprint.graph.executor._range_band_warnings（importlib+getattr 取私有
       面）+ chuchenchi 真单元（堰构造守卫恰界形态——core/tests/graph 新文件，
       避 test_executor.py 500 行墙；本文件无「不引 units_lib」铁律）
输出:  声明带判定的边界语义断言（恰界触发/闭区间端点/grid 跳过/非数值与非
       有限跳过/多参数计数/R1 去重回归）
"""

from __future__ import annotations

import importlib

import pytest

from waterprint.contracts.manifest import ParamSpec
from waterprint.contracts.quantity import DimKey

_mod = importlib.import_module("waterprint.graph.executor")
_bands = getattr(_mod, "_range_band_warnings", None)

pytestmark = pytest.mark.skipif(
    _bands is None, reason="实现未就绪：waterprint.graph.executor 声明带面（FZ-2 批）"
)


def _spec(
    field: str, low: float, high: float, grid: tuple[float, ...] | None = None
) -> ParamSpec:
    """构造带 range 声明的 ParamSpec（dataclass 直构——不经 load_manifest）。"""
    return ParamSpec(
        field_id=field, dim=DimKey.DIMENSIONLESS, default=(low + high) / 2,
        grid=grid, range=(low, high),
    )


def test_guard_boundary_exact_diameter() -> None:
    """①恰界形态：q_prime 使池径恰 ceil 到 D=1.0 → 守卫触发（≤ 含等号）；
    D=1.5（>1）→ 不触发照常出结果。直调 chuchenchi 真单元（守卫宿主）。"""
    from waterprint.contracts.manifest import InvalidUnitConfig
    from waterprint.units_lib.municipal.chuchenchi import make_unit
    from waterprint.units_lib.municipal.chuchenchi.tests.test_compute import _ctx, _params

    with pytest.raises(InvalidUnitConfig, match="D=1.0") as excinfo:
        make_unit().compute(_ctx(_params(q_prime=2000.0)))  # d_raw≈0.803 → 0.5 档=1.0
    assert "堰构造" in str(excinfo.value)
    result = make_unit().compute(_ctx(_params(q_prime=1000.0)))  # d_raw≈1.136 → 1.5
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["d"] == pytest.approx(1.5, abs=1e-9)


def test_band_endpoints_inclusive() -> None:
    """②GR-06 闭区间：值==min 与 ==max 均带内零告警。"""
    assert _bands((_spec("q_prime", 1.5, 4.5),), {"q_prime": 1.5}, set()) == ()
    assert _bands((_spec("q_prime", 1.5, 4.5),), {"q_prime": 4.5}, set()) == ()


def test_grid_param_skipped_even_with_range() -> None:
    """③grid 在场即跳过（档位面归 params_guard 档位执法）：值 9.9 越声明带
    [1.5, 4.5] 但命中 grid 档 [9, 10] → 零中央告警。"""
    spec = _spec("q_prime", 1.5, 4.5, grid=(9.0, 10.0))
    assert _bands((spec,), {"q_prime": 9.9}, set()) == ()


def test_non_numeric_and_nonfinite_skipped() -> None:
    """④契约对齐 params_guard 数值防护（R2 d1-W1）：None/bool/非有限（NaN/
    ±Inf）一律跳过不产告警——bool 面（True→1.0 越带）为 W1 红面：旧句
    value is None or not isfinite(value) 把 True 判为有限值产告警。"""
    specs = (
        _spec("a", 1.5, 4.5), _spec("b", 1.5, 4.5),
        _spec("c", 1.5, 4.5), _spec("d", 1.5, 4.5),
    )
    actual = {"a": None, "b": True, "c": float("nan"), "d": float("inf")}
    assert _bands(specs, actual, set()) == ()


def test_multiple_out_of_band_params_count() -> None:
    """⑤多参数同越带：告警条数=越带参数数（2），param_key 集逐键归因。"""
    specs = (
        _spec("q_prime", 1.5, 4.5), _spec("t_settle", 1.0, 2.5), _spec("h5", 0.5, 4.0),
    )
    actual = {"q_prime": 9.9, "t_settle": 1.5, "h5": 1e9}
    extra = _bands(specs, actual, set())
    assert len(extra) == 2
    assert {w.param_key for w in extra} == {"q_prime", "h5"}


def test_reported_keys_dedup() -> None:
    """R1 去重回归：reported 集含 field_id → 跳过（单元级优先，中央兜底）。"""
    spec = _spec("q_prime", 1.5, 4.5)
    assert _bands((spec,), {"q_prime": 9.9}, {"q_prime"}) == ()
    assert len(_bands((spec,), {"q_prime": 9.9}, set())) == 1
