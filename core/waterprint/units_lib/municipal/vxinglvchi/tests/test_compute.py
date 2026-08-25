"""municipal_vxinglvchi golden 数值测试（期望值来源：docs/norms/vxinglvchi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=四表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/vxinglvchi.md 算例 1（含 B=4.5/L=10.0 离散化项）；
#   系数键值逐字取自 data/coefficients 0.3.0 数据包 factors/removal_rates
#   yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q_filter/a_total_req/a_cell/b_raw/B/l_raw/
#   L/a_cell_act/a_total_act/v_filter_act/v_forced_act/q_air/q_wash_sim/
#   q_wash/q_sweep/v_air_per/v_wash_per/v_wash_daily/ratio_wash/h_total/
#   v_concrete）+ 校核带越界产 Warning（正常滤速带/强制滤速上限/
#   长宽比带/滤层厚带/砂上水深带/过滤周期带）+ 参数域拒绝（n≤0/
#   n<2 强制滤速分母/v_filter≤0/缺冲洗强度系数）+ 纯函数双跑一致 +
#   formula_ids 全部可在公式注册表解析。
# 【口径注记】入流水质=四表衔接式值（SS 0.6990908/BOD5 5.918378/
#   COD 17.84431，上游高密沉淀池出流）；出流=衔接下游紫外表值=
#   全厂终水（5.474500/16.50599/0.2272045）。
# 【容差注记】四表手算取 Q_design=0.56325（5 位舍入），引擎用精确
#   34760.7/86400×1.4=0.5632520833——差 <4e-6 m³/s，q_filter 面 1e-1
#   容差覆盖该舍入差；离散化项（B=4.5/L=10.0）不受扰。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/vxinglvchi/tests`
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
from waterprint.units_lib.municipal.vxinglvchi import make_unit, manifest

# ── 算例 1 入参（四表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    四表衔接式值——上游高密沉淀池出流链值） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_vxinglvchi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.918378, "CODCR": 17.84431, "SS": 0.6990908, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
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
        "n": 6.0,
        "v_filter": 8.0,
        "ratio_lb": 2.5,
        "h_water_above": 1.3,
        "h_sand": 1.3,
        "h_bottom": 1.0,
        "t_cycle": 24.0,
        "side_disc_step": 0.5,
        # data/coefficients factors.yaml（0.3.0 M2b1 四单元批）逐字
        "factor.vxinglvchi.v_filter_band.min": 7.0,
        "factor.vxinglvchi.v_filter_band.max": 10.0,
        "factor.vxinglvchi.v_forced_band.min": 11.0,
        "factor.vxinglvchi.v_forced_band.max": 13.0,
        "factor.vxinglvchi.selfuse_coef": 1.05,
        "factor.vxinglvchi.cell_ratio_lb_band.min": 2.0,
        "factor.vxinglvchi.cell_ratio_lb_band.max": 3.0,
        "factor.vxinglvchi.media.depth_band.min": 1.2,
        "factor.vxinglvchi.media.depth_band.max": 1.5,
        "factor.vxinglvchi.media.d10_band.min": 0.9,
        "factor.vxinglvchi.media.d10_band.max": 1.2,
        "factor.vxinglvchi.water_above_band.min": 1.2,
        "factor.vxinglvchi.water_above_band.max": 1.5,
        "factor.vxinglvchi.superheight": 0.3,
        "factor.vxinglvchi.wash.air": 15.0,
        "factor.vxinglvchi.wash.water_sim": 2.5,
        "factor.vxinglvchi.wash.water": 5.0,
        "factor.vxinglvchi.wash.sweep": 1.8,
        "factor.vxinglvchi.wash.t_air": 2.0,
        "factor.vxinglvchi.wash.t_sim": 4.0,
        "factor.vxinglvchi.wash.t_water": 4.0,
        "factor.vxinglvchi.cycle_band.min": 24.0,
        "factor.vxinglvchi.cycle_band.max": 48.0,
        "factor.vxinglvchi.wall_thickness_coef": 0.35,
        "factor.vxinglvchi.elevation_loss": 2.5,
        # removal_rates.yaml mod_default 档逐字
        "removal.vxinglvchi.bod5.mod_default": 0.075,
        "removal.vxinglvchi.cod.mod_default": 0.075,
        "removal.vxinglvchi.ss.mod_default": 0.675,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_vxinglvchi",
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
    assert manifest.unit_id == "municipal_vxinglvchi"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.vxinglvchi.bod5.mod_default",
        "CODCR": "removal.vxinglvchi.cod.mod_default",
        "SS": "removal.vxinglvchi.ss.mod_default",
    }


def test_main_case_filter() -> None:
    """主算例（四表算例 1）过滤面积与滤速逐项断言（XL-F1~F9）。"""
    dims = _dims()
    assert dims["q_filter"] == pytest.approx(2129.085, abs=1e-1)  # XL-F1：×1.05 自用水
    assert dims["a_total_req"] == pytest.approx(266.1356, abs=1e-2)  # XL-F2
    assert dims["a_cell"] == pytest.approx(44.35594, abs=1e-2)  # XL-F3
    assert dims["b_raw"] == pytest.approx(4.212170, abs=1e-4)  # XL-F4
    assert dims["b"] == pytest.approx(4.5, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["l_raw"] == pytest.approx(9.856875, abs=1e-4)  # XL-F5
    assert dims["l"] == pytest.approx(10.0, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["a_cell_act"] == pytest.approx(45.0, abs=1e-9)  # XL-F6
    assert dims["a_total_act"] == pytest.approx(270.0, abs=1e-9)  # XL-F7
    assert dims["v_filter_act"] == pytest.approx(7.88550, abs=1e-3)  # XL-F8：带内
    assert dims["v_forced_act"] == pytest.approx(9.46260, abs=1e-3)  # XL-F9：≤11 合格


def test_main_case_wash() -> None:
    """主算例气水反冲洗三阶段逐项断言（XL-F10~F17）。"""
    dims = _dims()
    assert dims["q_air"] == pytest.approx(0.675, abs=1e-9)  # XL-F10：单格
    assert dims["q_wash_sim"] == pytest.approx(0.1125, abs=1e-9)  # XL-F11
    assert dims["q_wash"] == pytest.approx(0.225, abs=1e-9)  # XL-F12
    assert dims["q_sweep"] == pytest.approx(0.081, abs=1e-9)  # XL-F13
    assert dims["v_air_per"] == pytest.approx(243.0, abs=1e-6)  # XL-F14：单格次
    assert dims["v_wash_per"] == pytest.approx(129.6, abs=1e-6)  # XL-F15：单格次
    assert dims["v_wash_daily"] == pytest.approx(777.6, abs=1e-6)  # XL-F16
    assert dims["ratio_wash"] == pytest.approx(0.02237009, abs=1e-7)  # XL-F17：2.24%


def test_main_case_depth() -> None:
    """主算例池深组成与混凝土量逐项断言（XL-F18/F19）。"""
    dims = _dims()
    assert dims["h_total"] == pytest.approx(3.9, abs=1e-9)  # XL-F18：0.3+1.3+1.3+1.0
    assert dims["v_concrete"] == pytest.approx(368.55, abs=1e-6)  # XL-F19：概算口径
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例六条校核带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal.mod_default)=全厂终水。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_vxinglvchi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(5.918378 * (1 - 0.075)) == out_quality.BOD5  # 5.474500
    assert pytest.approx(17.84431 * (1 - 0.075)) == out_quality.CODCR  # 16.50599
    assert pytest.approx(0.6990908 * (1 - 0.675)) == out_quality.SS  # 0.2272045
    assert out_quality.NH3N == 26.0  # 无去除键穿流不变
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_filter_speed_band_warning() -> None:
    """校核带越界：v_filter=12 → 实际滤速≈11.93 越 7~10 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(v_filter=12.0)))
    band = [w for w in result.warnings if "v_filter_band" in w.source]
    assert band and band[0].severity is Severity.WARN
    assert band[0].param_key == "v_filter"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_filter_act"] == pytest.approx(11.9330, abs=1e-2)


def test_forced_speed_upper_warning() -> None:
    """强制滤速单向上限：v_filter=10/n=4/ratio_lb=3.0 → v_forced≈13.14>13
    产 WARN（v_filter_act≈9.86 仍在 7~10 带内——单越界归因）。"""
    result = make_unit().compute(_ctx(_params(v_filter=10.0, n=4.0, ratio_lb=3.0)))
    forced = [w for w in result.warnings if "v_forced_band" in w.source]
    assert forced and forced[0].severity is Severity.WARN
    assert forced[0].param_key == "n"
    assert not [w for w in result.warnings if "v_filter_band" in w.source]
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_forced_act"] == pytest.approx(13.1419, abs=1e-2)


def test_geometry_band_warnings() -> None:
    """校核带越界：ratio_lb=3.5 越长宽比带；h_sand=1.6 越滤层带；h_water_above=1.6 越水深带。"""
    ratio = [
        w for w in make_unit().compute(_ctx(_params(ratio_lb=3.5))).warnings
        if "cell_ratio_lb_band" in w.source
    ]
    assert ratio and ratio[0].severity is Severity.WARN
    assert ratio[0].param_key == "ratio_lb"
    sand = [
        w for w in make_unit().compute(_ctx(_params(h_sand=1.6))).warnings
        if "media.depth_band" in w.source
    ]
    assert sand and sand[0].severity is Severity.WARN
    assert sand[0].param_key == "h_sand"
    above = [
        w for w in make_unit().compute(_ctx(_params(h_water_above=1.6))).warnings
        if "water_above_band" in w.source
    ]
    assert above and above[0].severity is Severity.WARN
    assert above[0].param_key == "h_water_above"


def test_cycle_band_warning() -> None:
    """校核带越界：t_cycle=20 越过滤周期带下限 24 产 WARN。"""
    result = make_unit().compute(_ctx(_params(t_cycle=20.0)))
    cyc = [w for w in result.warnings if "cycle_band" in w.source]
    assert cyc and cyc[0].severity is Severity.WARN
    assert cyc[0].param_key == "t_cycle"


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0/n<2（强制滤速分母）/v_filter≤0/缺冲洗强度系数
    → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=1.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_filter=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(**{"factor.vxinglvchi.wash.air": 0.0})))


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
    assert result.formula_ids == tuple(f"XL-F{index}" for index in range(1, 20))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
