"""municipal_wushui_tisheng 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(a684dc1689)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-C 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


from __future__ import annotations

from typing import Any

from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.units_lib.municipal.wushui_tisheng import make_unit

"""municipal_wushui_tisheng 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(a684dc1689)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-C 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


# ── 冻结入参(重写前包内 test_compute 权威夹具的 round-trip 字面量化;
#    变体件与本件同源副本——包内 tests 无包语义,自包含纪律) ──
_UNIT_TEST_ID = 'test_wushui'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 198.0,
    'CODCR': 344.0,
    'SS': 237.0,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'h_static': 10.0,
    'v_pipe': 1.2,
    'l_pipe': 100.0,
    'n_standby': 1.0,
    'h_well': 2.0,
    't_well': 10.0,
    'dia_disc_step': 0.1,
    'g_gravity': 9.81,
    'sec_per_hour': 3600.0,
    'factor.wushui_tisheng.pump.q_per_unit': 1100.0,
    'factor.wushui_tisheng.pump.q_flow_band.min': 400.0,
    'factor.wushui_tisheng.pump.q_flow_band.max': 1500.0,
    'factor.wushui_tisheng.pump.free_head': 1.5,
    'factor.wushui_tisheng.pump.start_band.max': 6.0,
    'factor.wushui_tisheng.pipe.resistance.dn300': 1.025,
    'factor.wushui_tisheng.pipe.resistance.dn350': 0.4529,
    'factor.wushui_tisheng.pipe.resistance.dn400': 0.2232,
    'factor.wushui_tisheng.pipe.resistance.dn450': 0.1195,
    'factor.wushui_tisheng.pipe.resistance.dn500': 0.06839,
    'factor.wushui_tisheng.pipe.resistance.dn600': 0.02602,
    'factor.wushui_tisheng.pipe.resistance.dn700': 0.01149,
    'factor.wushui_tisheng.pipe.resistance.dn800': 0.005665,
    'factor.wushui_tisheng.pipe.velocity_band.min': 0.7,
    'factor.wushui_tisheng.pipe.velocity_band.max': 1.5,
    'factor.wushui_tisheng.pipe.zeta_total': 5.0,
    'factor.wushui_tisheng.well.t_band.min': 5.0,
    'factor.wushui_tisheng.well.t_band.max': 15.0,
    'factor.wushui_tisheng.well.depth_band.min': 1.5,
    'factor.wushui_tisheng.well.depth_band.max': 2.5,
    'factor.wushui_tisheng.superheight': 0.5,
    'factor.wushui_tisheng.wall_thickness_coef': 0.35,
    'factor.wushui_tisheng.elevation_loss': 0.3,
    'removal.wushui_tisheng.bod5.mod_default': 0.0,
    'removal.wushui_tisheng.cod.mod_default': 0.0,
    'removal.wushui_tisheng.ss.mod_default': 0.0,
}


class _Sink:
    """空迹收集器(结构满足 TraceSink 协议)。"""

    def record(self, node: Any) -> None:
        """丢弃记录。"""


def _compute(overrides: dict[str, float] | None = None) -> UnitResult:
    """冻结入参上下文+主算参数(∪变体覆盖)驱动本包 compute。"""
    params = dict(_MAIN_PARAMS)
    if overrides:
        params.update(overrides)
    in_ref = PortRef(unit_id=_UNIT_TEST_ID, port_id=_IN_PORT)
    ctx = UnitContext(
        unit_id=_UNIT_TEST_ID,
        inflows={in_ref: WaterFlow(**_FLOW_ARGS)},
        inqualities={in_ref: WaterQuality(dict(_QUALITY))},
        params=params,
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    return make_unit().compute(ctx)


_VAR1_OVERRIDES: dict[str, float] = {
    'factor.wushui_tisheng.pump.q_per_unit': 6000.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'v_pipe': 2.3,
}

_VAR3_OVERRIDES: dict[str, float] = {
    't_well': 2.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1(参数面见 OVERRIDES 常量):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q_design_h': 2027.7074999999995,
        'n_pump_raw': 0.3379512499999999,
        'n_pump_duty': 1.0,
        'q_pump': 2027.7074999999995,
        'n_pump_total': 2.0,
        'q_pump_si': 0.5632520833333332,
        'd_pipe_raw': 0.7730646948854141,
        'd_pipe': 0.8,
        'v_pipe_act': 1.1205544171467716,
        'h_friction': 0.1797237731633962,
        'h_local': 0.3199903674279157,
        'h_loss': 0.4997141405913119,
        'h_pump': 11.999714140591312,
        'v_well': 337.9512499999999,
        'a_well': 168.97562499999995,
        'n_start': 1.5,
        'h_well_total': 2.5,
        'v_concrete': 147.85367187499995,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）泵站章；factor.wushui_tisheng.pump.q_flow_band.*',
            '单泵流量 = 2027.71 m3/h 越出建议带 [400.0, 1500.0]——调节方向：factor.wushui_tisheng.p'
            'ump.q_per_unit（概算锚/选泵型号面）',
            'factor.wushui_tisheng.pump.q_per_unit',
        ),
    ]
    ports = {
        PortRef(unit_id='test_wushui', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_wushui', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 198.0,
        'CODCR': 344.0,
        'SS': 237.0,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'v_pipe': 2.3}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q_design_h': 2027.7074999999995,
        'n_pump_raw': 1.8433704545454541,
        'n_pump_duty': 2.0,
        'q_pump': 1013.8537499999998,
        'n_pump_total': 3.0,
        'q_pump_si': 0.2816260416666666,
        'd_pipe_raw': 0.39484582213213687,
        'd_pipe': 0.4,
        'v_pipe_act': 2.2411088342935432,
        'h_friction': 1.770271234336718,
        'h_local': 1.2799614697116628,
        'h_loss': 3.0502327040483808,
        'h_pump': 14.55023270404838,
        'v_well': 168.97562499999995,
        'a_well': 84.48781249999998,
        'n_start': 1.5,
        'h_well_total': 2.5,
        'v_concrete': 73.92683593749997,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）泵站章；factor.wushui_tisheng.pipe.velocity_band.'
            '*',
            '实际流速 = 2.2411 m/s 越出建议带 [0.7, 1.5]——调节方向：v_pipe（名义流速）或泵台数（n_'
            'pump_duty 改变单泵流量）',
            'v_pipe',
        ),
    ]
    ports = {
        PortRef(unit_id='test_wushui', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_wushui', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 198.0,
        'CODCR': 344.0,
        'SS': 237.0,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'t_well': 2.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q_design_h': 2027.7074999999995,
        'n_pump_raw': 1.8433704545454541,
        'n_pump_duty': 2.0,
        'q_pump': 1013.8537499999998,
        'n_pump_total': 3.0,
        'q_pump_si': 0.2816260416666666,
        'd_pipe_raw': 0.5466392880493856,
        'd_pipe': 0.6000000000000001,
        'v_pipe_act': 0.9960483707971302,
        'h_friction': 0.20637301755126078,
        'h_local': 0.25283189525168637,
        'h_loss': 0.4592049128029472,
        'h_pump': 11.959204912802948,
        'v_well': 33.79512499999999,
        'a_well': 16.897562499999996,
        'n_start': 7.5,
        'h_well_total': 2.5,
        'v_concrete': 14.785367187499995,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）泵站章；factor.wushui_tisheng.pump.start_band.max',
            '最大启动次数 = 7.5000 次/h 超上限 6.0（水位启停频繁损泵）——调节方向：t_well（↑集水井'
            '调节容积↑）',
            't_well',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.1；给水排水设计手册（第 5 册 城镇排水）泵站章；factor.wushui_tisheng'
            '.well.t_band.*',
            '集水井调节时间 = 2.00 min 越出建议带 [5.0, 15.0]——调节方向：t_well（带内取值）',
            't_well',
        ),
    ]
    ports = {
        PortRef(unit_id='test_wushui', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_wushui', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 198.0,
        'CODCR': 344.0,
        'SS': 237.0,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }

