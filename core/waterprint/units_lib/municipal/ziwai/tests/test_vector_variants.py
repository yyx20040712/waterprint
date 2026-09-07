"""municipal_ziwai 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

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
from waterprint.units_lib.municipal.ziwai import make_unit

"""municipal_ziwai 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

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
_UNIT_TEST_ID = 'test_ziwai'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 5.4745,
    'CODCR': 16.50599,
    'SS': 0.2272045,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n_channel': 2.0,
    'v_channel': 0.4,
    'b_c': 1.2,
    'n_lamp_module': 8.0,
    'l_module': 0.6,
    'l_stab': 1.2,
    'h_module': 0.5,
    'length_disc_step': 0.1,
    'factor.ziwai.dose': 30.0,
    'factor.ziwai.q_per_lamp': 40.0,
    'factor.ziwai.f_aging': 0.8,
    'factor.ziwai.t254_band.min': 0.55,
    'factor.ziwai.t254_band.max': 0.65,
    'factor.ziwai.velocity_band.min': 0.3,
    'factor.ziwai.velocity_band.max': 0.6,
    'factor.ziwai.t_exp_band.min': 5.0,
    'factor.ziwai.t_exp_band.max': 10.0,
    'factor.ziwai.fecal.c_in_design': 100000.0,
    'factor.ziwai.fecal.log_removal': 4.0,
    'factor.ziwai.superheight': 0.5,
    'factor.ziwai.wall_thickness_coef': 0.35,
    'factor.ziwai.elevation_loss': 0.2,
    'removal.ziwai.bod5.mod_default': 0.0,
    'removal.ziwai.cod.mod_default': 0.0,
    'removal.ziwai.ss.mod_default': 0.0,
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
    'v_channel': 0.25,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'n_lamp_module': 4.0,
    'b_c': 2.0,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'h_module': 0.7,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'v_channel': 0.25}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q_c': 0.2816260416666666,
        'h_w_raw': 0.938753472222222,
        'h_w': 1.0,
        'v_channel_act': 0.2346883680555555,
        'n_lamp_raw': 63.365859374999985,
        'n_lamp': 64.0,
        'n_module_raw': 8.0,
        'n_module': 8.0,
        'n_module_series': 4.0,
        'l_lamp_zone': 2.4,
        'l_channel': 4.8,
        't_exp': 10.22632702201871,
        'c_fecal_out': 10.0,
        'h_submerge': 0.5,
        'h_channel': 1.5,
        'v_concrete': 6.048,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）紫外渠道设计；factor.ziwai.velocity_band.min~fact'
            'or.ziwai.velocity_band.max（实际过流态——单渠事故 0.78 m/s 超带为表内注记非运行时）',
            '实际渠内流速 = 0.2347 m/s 越出建议带 [0.3, 0.6]——调节方向：v_channel（↑加深渠）或 b_c'
            '（渠宽）',
            'v_channel',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）紫外渠道设计；factor.ziwai.t_exp_band.min~factor.'
            'ziwai.t_exp_band.max',
            '有效接触时间 = 10.2263 s 越出建议带 [5.0, 10.0]——调节方向：n_lamp_module（↑灯区加长）'
            '或 v_channel/b_c（过流断面）',
            'n_lamp_module',
        ),
    ]
    ports = {
        PortRef(unit_id='test_ziwai', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_ziwai', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'n_lamp_module': 4.0, 'b_c': 2.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q_c': 0.2816260416666666,
        'h_w_raw': 0.35203255208333323,
        'h_w': 0.4,
        'v_channel_act': 0.35203255208333323,
        'n_lamp_raw': 63.365859374999985,
        'n_lamp': 64.0,
        'n_module_raw': 16.0,
        'n_module': 16.0,
        'n_module_series': 8.0,
        'l_lamp_zone': 4.8,
        'l_channel': 7.199999999999999,
        't_exp': 13.635102696024948,
        'c_fecal_out': 10.0,
        'h_submerge': -0.09999999999999998,
        'h_channel': 0.9,
        'v_concrete': 9.072,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）紫外渠道设计；factor.ziwai.t_exp_band.min~factor.'
            'ziwai.t_exp_band.max',
            '有效接触时间 = 13.6351 s 越出建议带 [5.0, 10.0]——调节方向：n_lamp_module（↑灯区加长）'
            '或 v_channel/b_c（过流断面）',
            'n_lamp_module',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）紫外渠道设计；ZW-F11 灯管淹没校核（h_submerge ≥ 0'
            '）',
            '灯管顶淹没裕量 = -0.1000 m < 0（灯管露出水面）——调节方向：v_channel（↓加深渠）或 h_mo'
            'dule（模块高构造）',
            'v_channel',
        ),
    ]
    ports = {
        PortRef(unit_id='test_ziwai', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_ziwai', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'h_module': 0.7}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q_c': 0.2816260416666666,
        'h_w_raw': 0.5867209201388888,
        'h_w': 0.6000000000000001,
        'v_channel_act': 0.3911472800925925,
        'n_lamp_raw': 63.365859374999985,
        'n_lamp': 64.0,
        'n_module_raw': 8.0,
        'n_module': 8.0,
        'n_module_series': 4.0,
        'l_lamp_zone': 2.4,
        'l_channel': 4.8,
        't_exp': 6.135796213211227,
        'c_fecal_out': 10.0,
        'h_submerge': -0.09999999999999987,
        'h_channel': 1.1,
        'v_concrete': 4.4352,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）紫外渠道设计；ZW-F11 灯管淹没校核（h_submerge ≥ 0'
            '）',
            '灯管顶淹没裕量 = -0.1000 m < 0（灯管露出水面）——调节方向：v_channel（↓加深渠）或 h_mo'
            'dule（模块高构造）',
            'v_channel',
        ),
    ]
    ports = {
        PortRef(unit_id='test_ziwai', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_ziwai', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }

