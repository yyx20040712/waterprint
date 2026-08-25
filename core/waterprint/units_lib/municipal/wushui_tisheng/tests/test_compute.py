"""municipal_wushui_tisheng golden 数值测试（期望值来源：docs/norms/wushui_tisheng.md）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-26 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/wushui_tisheng.md 算例 1（含 n_pump_duty=2/DN600 离散化
#   项）；系数键值逐字取自 data/coefficients 0.4.0 数据包 factors/
#   removal_rates yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q_design_h/n_pump_raw/n_pump_duty/n_pump_
#   total/q_pump/d_pipe_raw/d_pipe[DN600]/v_pipe_act/h_friction/h_local/
#   h_loss/h_pump[扬程三分量]/v_well/a_well/n_start/h_well_total/
#   v_concrete）+ 泵台数 ceil 离散（概算锚 6000→n_raw=0.34→1 用）+
#   校核带越界产 Warning（流速带 v_pipe=2.0→act≈1.77/启停带 t_well=2→
#   7.5>6/调节时间带同源）+ 参数域拒（h_static=0/v_pipe=0/t_well=0/
#   sec_per_hour=0）+ DN 档越比阻表域拒（v_pipe=10→DN200 越表）+
#   出流=原水零去除穿流 + 纯函数双跑一致 + formula_ids 全部可在公式
#   注册表解析。
# 【口径注记】入流水质=三表衔接式值（**市政输入原水链值**：BOD5 198/
#   COD 344/SS 237——M2a1 衔接链头值逐字引用，泵房位于粗格栅前）；
#   出流=零去除键透传（全指标原样穿流不经 apply，衔接 cugeshan 表）。
# 【容差注记】三表手算取 Q_design=0.56325（5 位舍入，q_design_h=
#   2027.70），引擎用精确 0.5632520833（2027.7075）——差 <8e-3 m³/h，
#   泵流量/水损/扬程面 1e-3~1e-4 容差覆盖；离散化项（2 台/DN600）
#   不受扰；v_well/n_start 按引擎精确值断言（168.9756/1.500000）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/wushui_tisheng/tests`
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
from waterprint.units_lib.municipal.wushui_tisheng import make_unit, manifest

# ── 算例 1 入参（三表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    三表衔接式值——市政输入原水链值，M2a1 衔接链头值逐字引用） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_wushui", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 198.0, "CODCR": 344.0, "SS": 237.0, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
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
        "h_static": 10.0,
        "v_pipe": 1.2,
        "l_pipe": 100.0,
        "n_standby": 1.0,
        "h_well": 2.0,
        "t_well": 10.0,
        "dia_disc_step": 0.1,
        "g_gravity": 9.81,
        "sec_per_hour": 3600.0,
        # data/coefficients factors.yaml（0.4.0 M2c 三单元批）逐字
        "factor.wushui_tisheng.pump.q_per_unit": 1100.0,
        "factor.wushui_tisheng.pump.q_flow_band.min": 400.0,
        "factor.wushui_tisheng.pump.q_flow_band.max": 1500.0,
        "factor.wushui_tisheng.pump.free_head": 1.5,
        "factor.wushui_tisheng.pump.start_band.max": 6.0,
        "factor.wushui_tisheng.pipe.resistance.dn300": 1.025,
        "factor.wushui_tisheng.pipe.resistance.dn350": 0.4529,
        "factor.wushui_tisheng.pipe.resistance.dn400": 0.2232,
        "factor.wushui_tisheng.pipe.resistance.dn450": 0.1195,
        "factor.wushui_tisheng.pipe.resistance.dn500": 0.06839,
        "factor.wushui_tisheng.pipe.resistance.dn600": 0.02602,
        "factor.wushui_tisheng.pipe.resistance.dn700": 0.01149,
        "factor.wushui_tisheng.pipe.resistance.dn800": 0.005665,
        "factor.wushui_tisheng.pipe.velocity_band.min": 0.7,
        "factor.wushui_tisheng.pipe.velocity_band.max": 1.5,
        "factor.wushui_tisheng.pipe.zeta_total": 5.0,
        "factor.wushui_tisheng.well.t_band.min": 5.0,
        "factor.wushui_tisheng.well.t_band.max": 15.0,
        "factor.wushui_tisheng.well.depth_band.min": 1.5,
        "factor.wushui_tisheng.well.depth_band.max": 2.5,
        "factor.wushui_tisheng.superheight": 0.5,
        "factor.wushui_tisheng.wall_thickness_coef": 0.35,
        "factor.wushui_tisheng.elevation_loss": 0.3,
        # removal_rates.yaml mod_default 档逐字（提升单元零去除）
        "removal.wushui_tisheng.bod5.mod_default": 0.0,
        "removal.wushui_tisheng.cod.mod_default": 0.0,
        "removal.wushui_tisheng.ss.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_wushui",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims(**overrides: float) -> dict[str, float]:
    """主算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params(**overrides))).dims
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包（全 0.0）。"""
    assert manifest.unit_id == "municipal_wushui_tisheng"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.wushui_tisheng.bod5.mod_default",
        "CODCR": "removal.wushui_tisheng.cod.mod_default",
        "SS": "removal.wushui_tisheng.ss.mod_default",
    }


def test_main_case_pumps() -> None:
    """主算例选泵逐项断言（TS-F1~F3）——2 用 1 备（整台 ceil 收口）。"""
    dims = _dims()
    assert dims["q_design_h"] == pytest.approx(2027.7075, abs=1e-3)  # 精确引擎值
    assert dims["n_pump_raw"] == pytest.approx(1.843370, abs=1e-4)  # TS-F1：2027.7/1100
    assert dims["n_pump_duty"] == pytest.approx(2.0, abs=1e-9)  # 整台向上取整
    assert dims["n_pump_total"] == pytest.approx(3.0, abs=1e-9)  # TS-F3：2+1 备
    assert dims["q_pump"] == pytest.approx(1013.85375, abs=1e-3)  # TS-F2（带内）


def test_main_case_pipe() -> None:
    """主算例压力管水力逐项断言（TS-F4~F8）——DN600 档比阻法。"""
    dims = _dims()
    assert dims["q_pump_si"] == pytest.approx(0.281626, abs=1e-6)
    assert dims["d_pipe_raw"] == pytest.approx(0.546639, abs=1e-5)  # TS-F4
    assert dims["d_pipe"] == pytest.approx(0.6, abs=1e-9)  # 0.1 m 档=DN600
    assert dims["v_pipe_act"] == pytest.approx(0.996048, abs=1e-5)  # TS-F5：带内
    assert dims["h_friction"] == pytest.approx(0.206373, abs=1e-5)  # TS-F6：0.02602×100×q²
    assert dims["h_local"] == pytest.approx(0.252832, abs=1e-5)  # TS-F7：ζv²/2g
    assert dims["h_loss"] == pytest.approx(0.459205, abs=1e-5)  # TS-F8


def test_main_case_head_well() -> None:
    """主算例扬程三分量（TS-F9，追认点 14 承接）与集水井/启停（TS-F10~F14）。"""
    dims = _dims()
    assert dims["h_pump"] == pytest.approx(11.959205, abs=1e-4)  # TS-F9：10+0.459+1.5
    assert dims["v_well"] == pytest.approx(168.975625, abs=1e-3)  # TS-F10
    assert dims["a_well"] == pytest.approx(84.487812, abs=1e-3)  # TS-F11
    assert dims["n_start"] == pytest.approx(1.5, abs=1e-4)  # TS-F12：≤6 合格
    assert dims["h_well_total"] == pytest.approx(2.5, abs=1e-9)  # TS-F13
    assert dims["v_concrete"] == pytest.approx(73.926836, abs=1e-3)  # TS-F14
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例四条校核带均合格


def test_pump_count_ceil_discretization() -> None:
    """泵台数整台 ceil 离散：概算锚 6000 → n_raw=0.338 → 1 用（单泵流量
    2027.7 越单泵流量带上限产 WARN——ceil 离散与选泵面校核联动；归因
    param_key=概算锚系数键[M2c R1-b：n_standby 只进 TS-F3 与 q_pump 零耦合]）。"""
    result = make_unit().compute(_ctx(_params(**{"factor.wushui_tisheng.pump.q_per_unit": 6000.0})))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["n_pump_raw"] == pytest.approx(0.337951, abs=1e-5)
    assert dims["n_pump_duty"] == pytest.approx(1.0, abs=1e-9)
    assert dims["n_pump_total"] == pytest.approx(2.0, abs=1e-9)
    qflow = [w for w in result.warnings if "q_flow_band" in w.source]
    assert qflow and qflow[0].severity is Severity.WARN
    assert qflow[0].param_key == "factor.wushui_tisheng.pump.q_per_unit"


def test_band_warnings() -> None:
    """校核带越界产 WARN：v_pipe=2.3→DN400 实际流速≈2.24 越 0.7~1.5 带；
    t_well=2→启停 7.5 次/h 超 6 上限（调节时间带同源越界）。"""
    result = make_unit().compute(_ctx(_params(v_pipe=2.3)))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["d_pipe"] == pytest.approx(0.4, abs=1e-9)  # DN400 档
    assert dims["v_pipe_act"] == pytest.approx(2.241109, abs=1e-4)
    vel = [w for w in result.warnings if "velocity_band" in w.source]
    assert vel and vel[0].severity is Severity.WARN
    assert vel[0].param_key == "v_pipe"
    result = make_unit().compute(_ctx(_params(t_well=2.0)))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["n_start"] == pytest.approx(7.5, abs=1e-4)  # 900×q/v=15/t
    start = [w for w in result.warnings if "start_band" in w.source]
    assert start and start[0].severity is Severity.WARN
    assert start[0].param_key == "t_well"


def test_param_domain_rejected() -> None:
    """参数域拒：h_static=0/v_pipe=0/t_well=0/sec_per_hour=0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(h_static=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_pipe=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_well=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(sec_per_hour=0.0)))


def test_dn_out_of_resistance_table_rejected() -> None:
    """DN 档越比阻表域拒：v_pipe=10 → d_raw≈0.19 → DN200 越表（录入面
    DN300~DN800，越表显式拒——起草表追认点 4）。"""
    with pytest.raises(InvalidUnitConfig, match="越比阻表覆盖面"):
        make_unit().compute(_ctx(_params(v_pipe=10.0)))


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=零去除键透传（原水六指标原样穿流）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_wushui", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert out_quality.BOD5 == 198.0  # 透传（removal 全 0.0，不经 apply）
    assert out_quality.CODCR == 344.0
    assert out_quality.SS == 237.0
    assert out_quality.NH3N == 26.0
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings
    assert first.formula_ids == second.formula_ids


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"TS-F{index}" for index in range(1, 15))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
