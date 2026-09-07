"""municipal_chuchenchi 向量化重写前基线锚·参数变体面(批 13-B·件 2/2)。

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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.units_lib.municipal.chuchenchi import make_unit

"""municipal_chuchenchi 向量化重写前基线锚·参数变体面(批 13-B·件 2/2)。

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
_UNIT_TEST_ID = 'test_chuchenchi'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 164.3994,
    'CODCR': 285.6232,
    'SS': 186.4242,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 2.0,
    'q_prime': 2.3,
    't_settle': 1.2,
    't_sludge': 2.0,
    'r1': 1.8,
    'r2': 0.8,
    'h5': 1.5,
    'dia_disc_step': 0.5,
    'length_disc_step': 0.1,
    'factor.chuchenchi.surface_load_band.min': 1.5,
    'factor.chuchenchi.surface_load_band.max': 4.5,
    'factor.chuchenchi.retention_band.min': 1.0,
    'factor.chuchenchi.retention_band.max': 2.5,
    'factor.chuchenchi.depth_band.min': 2.0,
    'factor.chuchenchi.depth_band.max': 4.0,
    'factor.chuchenchi.ratio_dh2_band.min': 6.0,
    'factor.chuchenchi.ratio_dh2_band.max': 12.0,
    'factor.chuchenchi.weir_load.max': 2.9,
    'factor.chuchenchi.superheight': 0.3,
    'factor.chuchenchi.buffer_h3': 0.3,
    'factor.chuchenchi.bottom_slope': 0.05,
    'factor.chuchenchi.center_velocity': 0.3,
    'factor.chuchenchi.sludge.moisture': 0.96,
    'factor.chuchenchi.sludge.vs': 0.6,
    'factor.chuchenchi.wall_thickness_coef': 0.4,
    'factor.chuchenchi.elevation_loss': 0.5,
    'factor.chuchenchi.sludge_cycle_band.min': 1.0,
    'factor.chuchenchi.sludge_cycle_band.max': 2.0,
    'removal.chuchenchi.bod5.mod_default': 0.25,
    'removal.chuchenchi.cod.mod_default': 0.3,
    'removal.chuchenchi.ss.mod_default': 0.5,
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
    'q_prime': 4.8,
}

_VAR2_OVERRIDES: dict[str, float] = {
    't_settle': 2.5,
}

_VAR3_OVERRIDES: dict[str, float] = {
    't_sludge': 3.0,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'q_prime': 5.5,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'q_prime': 4.8}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'f_req': 211.21953124999996,
        'd_raw': 16.39917863211217,
        'd': 16.5,
        'f_act': 213.8246499849553,
        'q_prime_act': 4.741519511765058,
        'h2': 5.689823414118069,
        'ratio_dh2': 2.8999142502487527,
        'd_center': 1.1,
        'q_weir': 2.8917533312680046,
        'ss_out': 93.2121,
        's_dry_1': 1620.058922235,
        's_wet_1': 40.50147305587496,
        'v_need': 81.00294611174992,
        'v1_hopper': 8.35663645854885,
        'h4': 0.4,
        'v2_cone': 36.087474811785945,
        'v_storage': 44.444111270334794,
        'h_total': 8.200000000000001,
        'v_concrete': 1402.689703901307,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.surface_load_band.min~factor.chuchenc'
            'hi.surface_load_band.max',
            '实际表面水力负荷 = 4.7415 越出建议带 [1.5, 4.5]——调节方向：q_prime（负荷）或 n（池数'
            '）',
            'q_prime',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.depth_band.min~factor.chuchenchi.dept'
            'h_band.max',
            '有效水深 h2 = 5.6898 越出建议带 [2.0, 4.0]——调节方向：t_settle（↑加深）或 q_prime（↓'
            '加深）',
            't_settle',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册）；factor.chuchenchi.ratio_dh2_band.min~factor.chuchenchi.r'
            'atio_dh2_band.max',
            '径深比 D/h2 = 2.8999 越出建议带 [6.0, 12.0]——调节方向：q_prime（影响 D）或 t_settle（'
            '影响 h2）',
            'q_prime',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册）；CC-F16 贮泥容积校核（v_storage ≥ v_need）',
            '污泥区容积 = 44.4441 m³ 低于需容积 81.0029 m³——调节方向：t_sludge（↓）或泥斗构造 h5/r'
            '1（↑）',
            't_sludge',
        ),
    ]
    ports = {
        PortRef(unit_id='test_chuchenchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_chuchenchi', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0009375340985156241, ds=0.037501363940625, moisture=0.96),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 123.29955000000001,
        'CODCR': 199.93624,
        'SS': 93.2121,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'t_settle': 2.5}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'f_req': 440.8059782608695,
        'd_raw': 23.690749314392896,
        'd': 24.0,
        'f_act': 452.3893421169302,
        'q_prime_act': 2.2411088317327033,
        'h2': 5.602772079331758,
        'ratio_dh2': 4.283593846077436,
        'd_center': 1.1,
        'q_weir': 1.9487902884632204,
        'ss_out': 93.2121,
        's_dry_1': 1620.058922235,
        's_wet_1': 40.50147305587496,
        'v_need': 81.00294611174992,
        'v1_hopper': 8.35663645854885,
        'h4': 0.6000000000000001,
        'v2_cone': 106.08530072642016,
        'v_storage': 114.441937184969,
        'h_total': 8.4,
        'v_concrete': 3040.056379025771,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.depth_band.min~factor.chuchenchi.dept'
            'h_band.max',
            '有效水深 h2 = 5.6028 越出建议带 [2.0, 4.0]——调节方向：t_settle（↑加深）或 q_prime（↓'
            '加深）',
            't_settle',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册）；factor.chuchenchi.ratio_dh2_band.min~factor.chuchenchi.r'
            'atio_dh2_band.max',
            '径深比 D/h2 = 4.2836 越出建议带 [6.0, 12.0]——调节方向：q_prime（影响 D）或 t_settle（'
            '影响 h2）',
            'q_prime',
        ),
    ]
    ports = {
        PortRef(unit_id='test_chuchenchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_chuchenchi', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0009375340985156241, ds=0.037501363940625, moisture=0.96),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 123.29955000000001,
        'CODCR': 199.93624,
        'SS': 93.2121,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'t_sludge': 3.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'f_req': 440.8059782608695,
        'd_raw': 23.690749314392896,
        'd': 24.0,
        'f_act': 452.3893421169302,
        'q_prime_act': 2.2411088317327033,
        'h2': 2.689330598079244,
        'ratio_dh2': 8.924153845994658,
        'd_center': 1.1,
        'q_weir': 1.9487902884632204,
        'ss_out': 93.2121,
        's_dry_1': 1620.058922235,
        's_wet_1': 40.50147305587496,
        'v_need': 121.50441916762489,
        'v1_hopper': 8.35663645854885,
        'h4': 0.6000000000000001,
        'v2_cone': 106.08530072642016,
        'v_storage': 114.441937184969,
        'h_total': 5.4,
        'v_concrete': 1954.3219579451388,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.sludge_cycle_band.min~factor.chuchenc'
            'hi.sludge_cycle_band.max（0.2.1 键）',
            '排泥周期 = 3.0000 越出建议带 [1.0, 2.0]——调节方向：t_sludge（↑泥量增大/↓贮泥更频）',
            't_sludge',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册）；CC-F16 贮泥容积校核（v_storage ≥ v_need）',
            '污泥区容积 = 114.4419 m³ 低于需容积 121.5044 m³——调节方向：t_sludge（↓）或泥斗构造 h5'
            '/r1（↑）',
            't_sludge',
        ),
    ]
    ports = {
        PortRef(unit_id='test_chuchenchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_chuchenchi', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0009375340985156241, ds=0.037501363940625, moisture=0.96),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 123.29955000000001,
        'CODCR': 199.93624,
        'SS': 93.2121,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'q_prime': 5.5}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'f_req': 184.3370454545454,
        'd_raw': 15.32009190025864,
        'd': 15.5,
        'f_act': 188.69190875623696,
        'q_prime_act': 5.3730642542270015,
        'h2': 6.447677105072402,
        'ratio_dh2': 2.4039665366936744,
        'd_center': 1.1,
        'q_weir': 3.091184595493384,
        'ss_out': 93.2121,
        's_dry_1': 1620.058922235,
        's_wet_1': 40.50147305587496,
        'v_need': 81.00294611174992,
        'v1_hopper': 8.35663645854885,
        'h4': 0.30000000000000004,
        'v2_cone': 24.269588647144552,
        'v_storage': 32.6262251056934,
        'h_total': 8.9,
        'v_concrete': 1343.4863903444073,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.surface_load_band.min~factor.chuchenc'
            'hi.surface_load_band.max',
            '实际表面水力负荷 = 5.3731 越出建议带 [1.5, 4.5]——调节方向：q_prime（负荷）或 n（池数'
            '）',
            'q_prime',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.depth_band.min~factor.chuchenchi.dept'
            'h_band.max',
            '有效水深 h2 = 6.4477 越出建议带 [2.0, 4.0]——调节方向：t_settle（↑加深）或 q_prime（↓'
            '加深）',
            't_settle',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册）；factor.chuchenchi.ratio_dh2_band.min~factor.chuchenchi.r'
            'atio_dh2_band.max',
            '径深比 D/h2 = 2.4040 越出建议带 [6.0, 12.0]——调节方向：q_prime（影响 D）或 t_settle（'
            '影响 h2）',
            'q_prime',
        ),
        (
            "WARN",
            'GB 50014-2021 §6.5（沉淀池）；factor.chuchenchi.weir_load.max',
            '出水堰负荷 = 3.0912 超上限 2.9——堰构造口径注记：默认周边双侧出水堰（L=2π(D−1)），单侧'
            '口径敏感性见 docs/norms/chuchenchi.md（堰构造口径待领域专家追认）',
            None,
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册）；CC-F16 贮泥容积校核（v_storage ≥ v_need）',
            '污泥区容积 = 32.6262 m³ 低于需容积 81.0029 m³——调节方向：t_sludge（↓）或泥斗构造 h5/r'
            '1（↑）',
            't_sludge',
        ),
    ]
    ports = {
        PortRef(unit_id='test_chuchenchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_chuchenchi', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0009375340985156241, ds=0.037501363940625, moisture=0.96),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 123.29955000000001,
        'CODCR': 199.93624,
        'SS': 93.2121,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_chuchenchi', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}

