"""municipal_chenshachi 向量化重写前基线锚·参数变体面(批 13-B·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(38fc4b4390)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-B 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


from __future__ import annotations

from typing import Any

from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.units_lib.municipal.chenshachi import make_unit

"""municipal_chenshachi 向量化重写前基线锚·参数变体面(批 13-B·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(38fc4b4390)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-B 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


# ── 冻结入参(重写前包内 test_compute 权威夹具的 round-trip 字面量化;
#    变体件与本件同源副本——包内 tests 无包语义,自包含纪律) ──
_UNIT_TEST_ID = 'test_chenshachi'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 2.0,
    'q_surf': 150.0,
    't_retention': 30.0,
    't_clean': 2.0,
    'theta': 55.0,
    'd_r': 0.5,
    'b_channel': 0.8,
    'v_channel': 1.0,
    'length_disc_step': 0.1,
    'sec_per_hour': 3600.0,
    'factor.chenshachi.sand_yield_x': 30.0,
    'factor.chenshachi.hopper.safety': 1.5,
    'factor.chenshachi.buffer_h3': 0.5,
    'factor.chenshachi.superheight': 0.3,
    'factor.chenshachi.grit.moisture': 0.6,
    'factor.chenshachi.grit.vs': 0.05,
    'factor.chenshachi.grit.density': 1600.0,
    'factor.chenshachi.channel.straight_mult': 7.0,
    'factor.chenshachi.channel.straight_min': 4.5,
    'factor.chenshachi.channel.outlet_mult': 2.0,
    'factor.chenshachi.surface_load_band.min': 150.0,
    'factor.chenshachi.surface_load_band.max': 200.0,
    'factor.chenshachi.retention_band.min': 25.0,
    'factor.chenshachi.retention_band.max': 60.0,
    'factor.chenshachi.h2_band.min': 1.0,
    'factor.chenshachi.h2_band.max': 2.0,
    'factor.chenshachi.ratio_dh2_band.min': 2.0,
    'factor.chenshachi.ratio_dh2_band.max': 2.5,
    'factor.chenshachi.wall_thickness_coef': 0.4,
    'factor.chenshachi.hopper_upper_ratio': 0.5,
    'removal.chenshachi.bod5.mod_default': 0.05,
    'removal.chenshachi.cod.mod_default': 0.05,
    'removal.chenshachi.ss.mod_default': 0.1,
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
    'q_surf': 250.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    't_retention': 90.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'q_surf': 250.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'd': 2.3000000000000003,
        'h2': 2.0833333333333335,
        'ratio_dh2': 1.104,
        'v_eff': 8.655742259109381,
        't_actual': 30.73487880554151,
        'v_sand': 0.5214104999999999,
        'v_hopper': 1.5642314999999996,
        'd_upper': 1.1500000000000001,
        'h4': 0.22756744991815575,
        'v_cone': 0.12794164845623263,
        'h_cyl': 1.4000000000000001,
        'v_storage': 1.5821063479866084,
        'h_total': 4.6000000000000005,
        'a_channel': 0.2816260416666666,
        'h_channel': 0.35203255208333323,
        'ratio_bh': 2.2725171160041584,
        'l_straight': 5.6000000000000005,
        'b_outlet': 1.6,
        'q_wet': 1.0428209999999998,
        'ds_grit': 667.4054399999999,
        'v_concrete': 15.289503126490812,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.4（条文号待核对原文）；factor.chenshachi.surface_load_band.min~facto'
            'r.chenshachi.surface_load_band.max',
            '表面负荷 m3/(m2.h) = 250.0000 越出建议带 [150.0, 200.0]（参数 q_surf——调节表面负荷/停'
            '留时间设计值）',
            'q_surf',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.4（条文号待核对原文）；factor.chenshachi.h2_band.min~factor.chenshac'
            'hi.h2_band.max',
            '有效水深 m = 2.0833 越出建议带 [1.0, 2.0]（参数 t_retention——调节表面负荷/停留时间设'
            '计值）',
            't_retention',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.4（条文号待核对原文）；factor.chenshachi.ratio_dh2_band.min~factor.c'
            'henshachi.ratio_dh2_band.max',
            '径深比 D/h2 = 1.1040 越出建议带 [2.0, 2.5]（参数 q_surf——调节方向：表面负荷 q_surf（'
            '影响 D）或停留时间 t_retention（影响 h2））',
            'q_surf',
        ),
    ]
    ports = {
        PortRef(unit_id='test_chenshachi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chenshachi', port_id='out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'t_retention': 90.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'd': 3.0,
        'h2': 3.75,
        'ratio_dh2': 0.8,
        'v_eff': 26.50718801466388,
        't_actual': 94.1219350944749,
        'v_sand': 0.5214104999999999,
        'v_hopper': 1.5642314999999996,
        'd_upper': 1.5,
        'h4': 0.3501037691048549,
        'v_cone': 0.29788509535793384,
        'h_cyl': 0.8,
        'v_storage': 1.7116017894733409,
        'h_total': 5.800000000000001,
        'a_channel': 0.2816260416666666,
        'h_channel': 0.35203255208333323,
        'ratio_bh': 2.2725171160041584,
        'l_straight': 5.6000000000000005,
        'b_outlet': 1.6,
        'q_wet': 1.0428209999999998,
        'ds_grit': 667.4054399999999,
        'v_concrete': 32.79822730347745,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.4（条文号待核对原文）；factor.chenshachi.h2_band.min~factor.chenshac'
            'hi.h2_band.max',
            '有效水深 m = 3.7500 越出建议带 [1.0, 2.0]（参数 t_retention——调节表面负荷/停留时间设'
            '计值）',
            't_retention',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.4（条文号待核对原文）；factor.chenshachi.ratio_dh2_band.min~factor.c'
            'henshachi.ratio_dh2_band.max',
            '径深比 D/h2 = 0.8000 越出建议带 [2.0, 2.5]（参数 q_surf——调节方向：表面负荷 q_surf（'
            '影响 D）或停留时间 t_retention（影响 h2））',
            'q_surf',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.4（条文号待核对原文）；factor.chenshachi.retention_band.min~factor.c'
            'henshachi.retention_band.max',
            '实际停留时间 s = 94.1219 越出建议带 [25.0, 60.0]（参数 t_retention——调节表面负荷/停留'
            '时间设计值）',
            't_retention',
        ),
    ]
    ports = {
        PortRef(unit_id='test_chenshachi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chenshachi', port_id='out')
    assert result.outqualities[quality_port].concentrations == {}

