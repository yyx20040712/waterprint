"""enumerate 镜像测试：向量化批量计算（N=1 防双轨、非负性、工况标注）。

输入:  waterprint.solution.enumerate 公开符号 + 示范单元（M1 三单元实现后激活）
输出:  单实现双用断言（§3 保证 1 的测试母版）
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

_mod = importlib.import_module("waterprint.solution.enumerate")
enumerate_solutions = getattr(_mod, "enumerate_solutions", None)
build_grid = getattr(importlib.import_module("waterprint.solution.grid"), "build_grid", None)

pytestmark = pytest.mark.skipif(
    None in (enumerate_solutions, build_grid),
    reason="实现未就绪：waterprint.solution.enumerate（M1 三单元切片）",
)


def test_entrypoint_is_callable() -> None:
    """入口冻结：enumerate_solutions(grid, upstream, unit, env)（签名见规格头）。"""
    assert callable(enumerate_solutions)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议）。"""

    def record(self, node: Any) -> None:
        """丢弃记录。"""


class _Coefficients:
    """系数视图占位（enumerate 不消费 env 数值面；结构满足 CoefficientsView）。"""

    data_version = "probe"

    def get(self, key: str) -> None:
        return None

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return ()

    def require_keys(self, keys: Any) -> None:
        return None


def _wiring() -> Any:
    """接线夹具：cugeshan 粗格栅 N=1 网格 + 算例 1 上游快照（M2-SOL D4）。"""
    from waterprint.contracts.condition import FlowCase, OperatingCondition
    from waterprint.contracts.flow import WaterFlow
    from waterprint.contracts.ports import PortRef
    from waterprint.contracts.quality import WaterQuality
    from waterprint.contracts.run_env import RunEnv
    from waterprint.contracts.unit_api import UnitContext
    from waterprint.units_lib.municipal.cugeshan import make_unit

    ref = PortRef(unit_id="test_cugeshan", port_id="in")
    ctx = UnitContext(
        unit_id="test_cugeshan",
        inflows={ref: WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)},
        inqualities={ref: WaterQuality({})},
        params={
            # manifest 默认即三表算例 1（n/b/alpha/h/v/v1/s/bar_shape/
            # g_gravity/length_disc_step）+系数投影键（data/coefficients
            # 0.1.0 逐字——cugeshan 包内测试同源夹具）
            "n": 3.0,
            "b": 0.065,
            "alpha": 75.0,
            "h": 0.6,
            "v": 0.8,
            "v1": 0.7,
            "s": 0.010,
            "bar_shape": 0.0,
            "g_gravity": 9.81,
            "length_disc_step": 0.1,
            "factor.screen.beta.rect": 2.42,
            "factor.screen.beta.semicircle": 1.97,
            "factor.screen.beta.circle": 1.83,
            "factor.screen.headloss.k": 3.0,
            "factor.screen.superheight": 0.3,
            "factor.screen.trough_width_margin": 0.2,
            "factor.screen.trough_length.l3_fixed": 1.0,
            "factor.screen.trough_length.l4_fixed": 0.5,
            "factor.screen.trough_length.drop_constant": 0.2,
            "factor.screen.slag.moisture": 0.80,
            "factor.screen.mech_clean_threshold": 0.2,
            "factor.screen.velocity_band.v.min": 0.6,
            "factor.screen.velocity_band.v.max": 1.0,
            "factor.screen.velocity_band.v1.min": 0.4,
            "factor.screen.velocity_band.v1.max": 0.9,
            "factor.screen.wall_thickness_coef": 0.3,
            "factor.cugeshan.w1_slag": 0.02,
            "removal.cugeshan.bod5.mod_default": 0.05,
            "removal.cugeshan.cod.mod_default": 0.05,
            "removal.cugeshan.ss.mod_default": 0.05,
        },
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    env = RunEnv(
        engine_version="probe",
        data_version="probe",
        assumptions={},
        coefficients=_Coefficients(),  # type: ignore[arg-type]
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    grid = build_grid([{"field_id": "n", "values": [3.0]}])  # type: ignore[misc]
    return grid, ctx, make_unit(), env


def test_n1_grid_matches_single_point_compute() -> None:
    """R1 防双轨铁律：N=1 网格行结果 == 单点 compute 结果。

    接线实质化（M2-SOL D4 总授权）：示范单元=municipal_cugeshan 粗格栅
    （M1 三单元之一）；数值期望锚自 docs/norms/cugeshan.md 手算表
    （n_gap=6/H=1.0/L=1.8/w_slag≈0.6952——算例 1）。放宽/删除 = 评审拒绝。
    """
    grid, ctx, unit, env = _wiring()
    df = enumerate_solutions(grid, ctx, unit, env)
    single = unit.compute(ctx)
    assert len(df) == grid.total
    row = df.iloc[0]
    for key, value in single.dims.items():
        assert row[key] == pytest.approx(value, rel=1e-12, abs=1e-12), key
    assert row["condition_key"] == "design"
    assert not bool(row["nan_flag"])
    assert row["n_gap"] == pytest.approx(6.0)  # 手算表：5.914 → ceil
    assert row["H"] == pytest.approx(1.0)  # 手算表：0.91832 → 1.0
    assert row["L"] == pytest.approx(1.8)  # 手算表：1.75457 → 1.8
    assert row["w_slag"] == pytest.approx(0.6952, abs=1e-4)  # 手算表 0.695214
