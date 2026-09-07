"""municipal_cass 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(c97bd24ee8)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-A 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


from __future__ import annotations

from typing import Any

from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.units_lib.municipal.cass import make_unit

"""municipal_cass 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(c97bd24ee8)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-A 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


# ── 冻结入参(重写前包内 test_compute 权威夹具的 round-trip 字面量化;
#    变体件与本件同源副本——包内 tests 无包语义,自包含纪律) ──
_UNIT_TEST_ID = 'test_cass'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 123.2996,
    'CODCR': 199.9362,
    'SS': 93.2121,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n_pool': 4.0,
    't_cycle': 4.0,
    't_react': 2.0,
    't_settle': 1.0,
    't_draw': 1.0,
    'ns': 0.1,
    'x_mlss': 4000.0,
    't_selector': 0.75,
    'h2': 5.0,
    'ratio_lb': 2.5,
    'tn_eff': 15.0,
    'side_disc_step': 0.5,
    'factor.cass.ns_band.min': 0.05,
    'factor.cass.ns_band.max': 0.15,
    'factor.cass.mlss_band.min': 3000.0,
    'factor.cass.mlss_band.max': 5000.0,
    'factor.cass.sludge_age_band.min': 15.0,
    'factor.cass.sludge_age_band.max': 25.0,
    'factor.cass.draw_band.min': 1.0,
    'factor.cass.draw_band.max': 2.0,
    'factor.cass.selector_band.min': 0.5,
    'factor.cass.selector_band.max': 1.0,
    'factor.cass.yield.y': 0.5,
    'factor.cass.o2.a_prime': 0.5,
    'factor.cass.o2.b_prime': 0.1,
    'factor.cass.vss_ratio': 0.75,
    'factor.cass.sludge.moisture': 0.994,
    'factor.cass.decant.q_per_unit': 800.0,
    'factor.cass.superheight': 0.5,
    'factor.cass.wall_thickness_coef': 0.4,
    'factor.cass.elevation_loss': 0.5,
    'removal.cass.bod5.mod_default': 0.9,
    'removal.cass.cod.mod_default': 0.85,
    'removal.cass.ss.mod_default': 0.9,
    'removal.cass.nh3n.mod_default': 0.9,
    'removal.cass.tn.mod_default': 0.7,
    'removal.cass.tp.mod_default': 0.93,
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
    'n_pool': 1.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'ns': 0.2,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'ns': 0.05,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'h2': 9.0,
}

_VAR5_OVERRIDES: dict[str, float] = {
    't_cycle': 8.0,
    't_react': 4.0,
    't_settle': 2.0,
    't_draw': 2.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'n_pool': 1.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'n_cycle': 6.0,
        'v_draw': 5793.45,
        'v_load': 10714.951014299999,
        'v_selector': 1086.271875,
        'v_bio': 11801.2228893,
        'h_draw_max': 1.6666666666666667,
        'a_draw': 3476.0699999999997,
        'a_load': 2360.24457786,
        'a_pool': 3476.0699999999997,
        'h_draw': 1.6666666666666667,
        'v_pool': 17380.35,
        'v_plant': 17380.35,
        't_phase_sum': 4.0,
        'q_decant': 5793.45,
        'n_decant_raw': 7.2418125,
        'n_decant': 8.0,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'ns_act': 0.06789980000000001,
        'h_pool': 5.5,
        'l_pool_raw': 93.22110812471604,
        'l_pool': 93.5,
        'b_pool_raw': 37.28844324988642,
        'b_pool': 37.5,
        'v_concrete': 7647.353999999999,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_cass', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_cass', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 12.900000000000002,
        'TP': 0.4549999999999997,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'ns': 0.2}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'n_cycle': 6.0,
        'v_draw': 1448.3625,
        'v_load': 5357.475507149999,
        'v_selector': 1086.271875,
        'v_bio': 6443.747382149999,
        'h_draw_max': 1.6666666666666667,
        'a_draw': 869.0174999999999,
        'a_load': 322.18736910749993,
        'a_pool': 869.0174999999999,
        'h_draw': 1.6666666666666667,
        'v_pool': 4345.0875,
        'v_plant': 17380.35,
        't_phase_sum': 4.0,
        'q_decant': 1448.3625,
        'n_decant_raw': 1.810453125,
        'n_decant': 2.0,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 11.11111111111111,
        'x_vss': 3000.0,
        'o2_carbon': 3535.9338347189996,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 5200.276150719001,
        'ns_act': 0.0741498,
        'h_pool': 5.5,
        'l_pool_raw': 46.61055406235802,
        'l_pool': 47.0,
        'b_pool_raw': 18.64422162494321,
        'b_pool': 19.0,
        'v_concrete': 7647.353999999999,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §7.6；给水排水设计手册（第 5 册 城镇排水）；factor.cass.ns_band.*',
            'BOD5 污泥负荷 Ns kgBOD5/(kgMLSS·d) = 0.2000 越出建议带 [0.05, 0.15]——调节方向：ns（带'
            '内取值）',
            'ns',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）（CASS 泥龄 15~25d，主反应区口径）；factor.cass.s'
            'ludge_age_band.*',
            '泥龄 theta_c d（主反应区口径） = 11.1111 越出建议带 [15.0, 25.0]——调节方向：ns',
            'ns',
        ),
    ]
    ports = {
        PortRef(unit_id='test_cass', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_cass', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 12.900000000000002,
        'TP': 0.4549999999999997,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'ns': 0.05}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'n_cycle': 6.0,
        'v_draw': 1448.3625,
        'v_load': 21429.902028599998,
        'v_selector': 1086.271875,
        'v_bio': 22516.173903599996,
        'h_draw_max': 1.6666666666666667,
        'a_draw': 869.0174999999999,
        'a_load': 1125.8086951799999,
        'a_pool': 1125.8086951799999,
        'h_draw': 1.2865085393290807,
        'v_pool': 5629.043475899999,
        'v_plant': 22516.173903599996,
        't_phase_sum': 4.0,
        'q_decant': 1448.3625,
        'n_decant_raw': 1.810453125,
        'n_decant': 2.0,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 44.44444444444444,
        'x_vss': 3000.0,
        'o2_carbon': 8357.661791154,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 10022.004107154002,
        'ns_act': 0.05,
        'h_pool': 5.5,
        'l_pool_raw': 53.05206629293528,
        'l_pool': 53.5,
        'b_pool_raw': 21.22082651717411,
        'b_pool': 21.5,
        'v_concrete': 9907.116517584,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）（CASS 泥龄 15~25d，主反应区口径）；factor.cass.s'
            'ludge_age_band.*',
            '泥龄 theta_c d（主反应区口径） = 44.4444 越出建议带 [15.0, 25.0]——调节方向：ns',
            'ns',
        ),
    ]
    ports = {
        PortRef(unit_id='test_cass', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_cass', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 12.900000000000002,
        'TP': 0.4549999999999997,
    }


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'h2': 9.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'n_cycle': 6.0,
        'v_draw': 1448.3625,
        'v_load': 10714.951014299999,
        'v_selector': 1086.271875,
        'v_bio': 11801.2228893,
        'h_draw_max': 3.0,
        'a_draw': 482.78749999999997,
        'a_load': 327.81174692499997,
        'a_pool': 482.78749999999997,
        'h_draw': 3.0,
        'v_pool': 4345.0875,
        'v_plant': 17380.35,
        't_phase_sum': 4.0,
        'q_decant': 1448.3625,
        'n_decant_raw': 1.810453125,
        'n_decant': 2.0,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'ns_act': 0.06789980000000001,
        'h_pool': 9.5,
        'l_pool_raw': 34.741455784120504,
        'l_pool': 35.0,
        'b_pool_raw': 13.896582313648201,
        'b_pool': 14.0,
        'v_concrete': 7338.37,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'business-logic §8 行 8；给水排水设计手册（第 5 册 城镇排水）（滗水器滗水深度）；facto'
            'r.cass.draw_band.*',
            '滗水深度 h_draw m（受 h2/3 上限双控） = 3.0000 越出建议带 [1.0, 2.0]——调节方向：h2',
            'h2',
        ),
    ]
    ports = {
        PortRef(unit_id='test_cass', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_cass', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 12.900000000000002,
        'TP': 0.4549999999999997,
    }


def test_baseline_var5_full_surface() -> None:
    """用例 var5(参数面见 OVERRIDES 常量):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR5_OVERRIDES)
    assert dict(result.dims) == {
        'n_cycle': 3.0,
        'v_draw': 2896.725,
        'v_load': 10714.951014299999,
        'v_selector': 1086.271875,
        'v_bio': 11801.2228893,
        'h_draw_max': 1.6666666666666667,
        'a_draw': 1738.0349999999999,
        'a_load': 590.061144465,
        'a_pool': 1738.0349999999999,
        'h_draw': 1.6666666666666667,
        'v_pool': 8690.175,
        'v_plant': 34760.7,
        't_phase_sum': 8.0,
        'q_decant': 1448.3625,
        'n_decant_raw': 1.810453125,
        'n_decant': 2.0,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'ns_act': 0.033949900000000005,
        'h_pool': 5.5,
        'l_pool_raw': 65.91727770471107,
        'l_pool': 66.0,
        'b_pool_raw': 26.366911081884428,
        'b_pool': 26.5,
        'v_concrete': 15294.707999999999,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §7.6；给水排水设计手册（第 5 册 城镇排水）（滗水控制裕量口径见起草表追'
            '认点 3）；factor.cass.ns_band.*',
            '实际污泥负荷 ns_act（滗水控制裕量） = 0.0339 越出建议带 [0.05, 0.15]——调节方向：ns',
            'ns',
        ),
    ]
    ports = {
        PortRef(unit_id='test_cass', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_cass', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 12.900000000000002,
        'TP': 0.4549999999999997,
    }

