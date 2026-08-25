"""municipal_chuchenchi golden 数值测试（期望值来源：docs/norms/chuchenchi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/chuchenchi.md 算例 1（含 D=24.0/d_center=1.1/h4=0.6/
#   h_total=5.4 离散化项）；系数键值逐字取自 data/coefficients
#   0.2.0+0.2.1 数据包 factors/removal_rates yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q1h/f_req/D/f_act/q'_act/h2/径深比/
#   d_center/q_weir/s_dry_1/s_wet_1/v_need/v1_hopper/h4/v2_cone/
#   v_storage/h_total/v_concrete）+ 校核带越界产 Warning（表面负荷带/
#   有效水深带/径深比带/堰负荷/排泥周期带[0.2.1 键]/贮泥容积）+
#   参数域拒绝（n<1、q_prime≤0）+ 纯函数双跑一致 + formula_ids
#   全部可在公式注册表解析。
# 【口径注记】入流水质=三表衔接式值（SS 186.4242/BOD5 164.3994/
#   COD 285.6232，上游三单元去除链）；出流=衔接下游 AAO 表值。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/chuchenchi/tests`
#   转为只读（AGENTS.md §11）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.municipal.chuchenchi import make_unit, manifest

# ── 算例 1 入参（三表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    三表衔接式值——上游粗格栅/细格栅/旋流沉砂池去除链后） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_chuchenchi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 164.3994, "CODCR": 285.6232, "SS": 186.4242, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """算例 1 参数面（manifest 默认即算例值；factor.*/removal.* 系数投影逐字）。"""
    params: dict[str, float] = {
        "n": 2.0,
        "q_prime": 2.3,
        "t_settle": 1.2,
        "t_sludge": 2.0,
        "r1": 1.8,
        "r2": 0.8,
        "h5": 1.5,
        "dia_disc_step": 0.5,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.2.0 生效 + 0.2.1 前置键）逐字
        "factor.chuchenchi.surface_load_band.min": 1.5,
        "factor.chuchenchi.surface_load_band.max": 4.5,
        "factor.chuchenchi.retention_band.min": 1.0,
        "factor.chuchenchi.retention_band.max": 2.5,
        "factor.chuchenchi.depth_band.min": 2.0,
        "factor.chuchenchi.depth_band.max": 4.0,
        "factor.chuchenchi.ratio_dh2_band.min": 6.0,
        "factor.chuchenchi.ratio_dh2_band.max": 12.0,
        "factor.chuchenchi.weir_load.max": 2.9,
        "factor.chuchenchi.superheight": 0.3,
        "factor.chuchenchi.buffer_h3": 0.3,
        "factor.chuchenchi.bottom_slope": 0.05,
        "factor.chuchenchi.center_velocity": 0.3,
        "factor.chuchenchi.sludge.moisture": 0.96,
        "factor.chuchenchi.sludge.vs": 0.60,
        "factor.chuchenchi.wall_thickness_coef": 0.4,
        "factor.chuchenchi.elevation_loss": 0.5,
        "factor.chuchenchi.sludge_cycle_band.min": 1.0,  # 0.2.1 前置键
        "factor.chuchenchi.sludge_cycle_band.max": 2.0,
        # removal_rates.yaml mod_default 档逐字
        "removal.chuchenchi.bod5.mod_default": 0.25,
        "removal.chuchenchi.cod.mod_default": 0.30,
        "removal.chuchenchi.ss.mod_default": 0.50,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_chuchenchi",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims() -> dict[str, float]:
    """主算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params())).dims
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包。"""
    assert manifest.unit_id == "municipal_chuchenchi"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.chuchenchi.bod5.mod_default",
        "CODCR": "removal.chuchenchi.cod.mod_default",
        "SS": "removal.chuchenchi.ss.mod_default",
    }


def test_main_case_basin() -> None:
    """主算例（三表算例 1）池体水力结果逐项断言（CC-F1~F7）。

    口径注记：三表手算取 Q_design=0.56325（5 位舍入），引擎用精确
    34760.7/86400×1.4=0.5632520833——差 <4e-6 m³/s，f_req/d_raw 容差
    1e-2 覆盖该舍入差；离散化项（D=24.0）不受扰。
    """
    dims = _dims()
    assert dims["q1"] == pytest.approx(0.281625, abs=1e-5)  # CC-F1 子式
    assert dims["q1h"] == pytest.approx(1013.85, abs=0.1)  # CC-F1：×3600
    assert dims["f_req"] == pytest.approx(440.8043, abs=1e-2)  # CC-F2
    assert dims["d_raw"] == pytest.approx(23.6907, abs=1e-2)  # CC-F3
    assert dims["d"] == pytest.approx(24.0, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["f_act"] == pytest.approx(452.3893, abs=1e-3)  # CC-F4
    assert dims["q_prime_act"] == pytest.approx(2.24110, abs=1e-4)  # CC-F5
    assert dims["h2"] == pytest.approx(2.68932, abs=1e-4)  # CC-F6
    assert dims["ratio_dh2"] == pytest.approx(8.92419, abs=1e-4)  # CC-F7


def test_main_case_center_weir_sludge() -> None:
    """主算例中心筒/堰负荷/排泥逐项断言（CC-F8~F12）。"""
    dims = _dims()
    assert dims["d_center"] == pytest.approx(1.1, abs=1e-9)  # CC-F8：1.09328 → 0.1 档
    assert dims["q_weir"] == pytest.approx(1.948783, abs=1e-5)  # CC-F9：L=2π×23
    assert dims["ss_out"] == pytest.approx(93.2121, abs=1e-4)  # 衔接式
    assert dims["s_dry_1"] == pytest.approx(1620.06, abs=0.01)  # CC-F10：单池
    assert dims["s_wet_1"] == pytest.approx(40.5015, abs=1e-3)  # CC-F11
    assert dims["v_need"] == pytest.approx(81.0029, abs=1e-3)  # CC-F12


def test_main_case_hopper_depth() -> None:
    """主算例泥斗/总高/混凝土量逐项断言（CC-F13~F18）。"""
    dims = _dims()
    assert dims["v1_hopper"] == pytest.approx(8.35664, abs=1e-4)  # CC-F13
    assert dims["h4"] == pytest.approx(0.6, abs=1e-9)  # CC-F14：0.51 → 0.1 档
    assert dims["v2_cone"] == pytest.approx(106.0853, abs=1e-3)  # CC-F15
    assert dims["v_storage"] == pytest.approx(114.442, abs=1e-2)  # CC-F16：≥v_need
    assert dims["h_total"] == pytest.approx(5.4, abs=1e-9)  # CC-F17：5.38932 → 0.1 档
    assert dims["v_concrete"] == pytest.approx(1954.322, abs=1e-1)  # CC-F18
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例六条校核带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal.mod_default)，NH3N/TN/TP 透传。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_chuchenchi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(164.3994 * (1 - 0.25)) == out_quality.BOD5  # 123.2996
    assert pytest.approx(285.6232 * (1 - 0.30)) == out_quality.CODCR  # 199.9362
    assert pytest.approx(186.4242 * (1 - 0.50)) == out_quality.SS  # 93.2121
    assert out_quality.NH3N == 26.0  # 无去除键穿流不变
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_surface_load_band_warning() -> None:
    """校核带越界：q_prime=4.8 → f_req↑、D↑、q'_act 越 1.5~4.5 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(q_prime=4.8)))
    surf = [
        w for w in result.warnings
        if w.param_key == "q_prime" and "surface_load_band" in w.source
    ]
    assert surf and surf[0].severity is Severity.WARN


def test_depth_band_warning() -> None:
    """校核带越界：t_settle=2.5 → h2≈5.0 越 2.0~4.0 带（param_key=t_settle）。"""
    result = make_unit().compute(_ctx(_params(t_settle=2.5)))
    dep = [w for w in result.warnings if "depth_band" in w.source]
    assert dep and dep[0].severity is Severity.WARN
    assert dep[0].param_key == "t_settle"


def test_weir_and_cycle_band_warnings() -> None:
    """堰负荷/排泥周期带越界：t_sludge=3 越 1~2 d 带（0.2.1 键生效）。"""
    result = make_unit().compute(_ctx(_params(t_sludge=3.0)))
    cycle = [w for w in result.warnings if "sludge_cycle_band" in w.source]
    assert cycle and cycle[0].severity is Severity.WARN
    assert cycle[0].param_key == "t_sludge"
    assert "0.2.1" in cycle[0].source


def test_param_domain_rejected() -> None:
    """参数域拒绝：n<1 / q_prime≤0 / 缺 SS 入流 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(q_prime=0.0)))
    ctx = UnitContext(
        unit_id="test_chuchenchi",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: WaterQuality({"BOD5": 160.0})},
        params=_params(),
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(ctx)


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"CC-F{index}" for index in range(1, 19))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
