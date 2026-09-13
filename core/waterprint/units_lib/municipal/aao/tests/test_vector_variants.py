"""municipal_aao 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.units_lib.municipal.aao import make_unit

"""municipal_aao 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

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
_UNIT_TEST_ID = 'test_aao'
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
    'n': 2.0,
    'ns': 0.1,
    'x_mlss': 4000.0,
    't_p': 1.5,
    'r_external': 1.0,
    'r_internal': 2.0,
    'tn_eff': 15.0,
    'sec_per_hour': 3600.0,
    'h2': 5.0,
    'ratio_lb': 2.5,
    'side_disc_step': 0.5,
    'factor.aao.ns_band.min': 0.05,
    'factor.aao.ns_band.max': 0.15,
    'factor.aao.mlss_band.min': 3500.0,
    'factor.aao.mlss_band.max': 4500.0,
    'factor.aao.sludge_age_band.min': 11.0,
    'factor.aao.sludge_age_band.max': 23.0,
    'factor.aao.hrt_anaerobic_band.min': 1.0,
    'factor.aao.hrt_anaerobic_band.max': 2.0,
    'factor.aao.hrt_anoxic_band.min': 2.0,
    'factor.aao.hrt_anoxic_band.max': 4.0,
    'factor.aao.k_denit': 0.05,
    'factor.aao.o2.a_prime': 0.5,
    'factor.aao.o2.b_prime': 0.1,
    'factor.aao.vss_ratio': 0.75,
    'factor.aao.yield.y': 0.5,
    'factor.aao.r_external_band.min': 0.5,
    'factor.aao.r_external_band.max': 1.0,
    'factor.aao.r_internal_band.min': 1.0,
    'factor.aao.r_internal_band.max': 3.0,
    'factor.aao.sludge.moisture': 0.994,
    'factor.aao.elevation_loss': 0.5,
    'factor.aao.superheight': 0.3,
    'factor.aao.aerator.service_area': 0.5,
    'removal.aao.bod5.mod_default': 0.9,
    'removal.aao.cod.mod_default': 0.85,
    'removal.aao.ss.mod_default': 0.9,
    'removal.aao.nh3n.mod_default': 0.9,
    'removal.aao.tn.mod_default': 0.75,
    'removal.aao.tp.mod_default': 0.93,
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
    'ns': 0.04,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'ns': 0.3,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'x_mlss': 8000.0,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'h2': 6.0,
}

_VAR5_OVERRIDES: dict[str, float] = {
    'ratio_lb': 3.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'ns': 0.04}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'v_o': 26787.377535749994,
        't_o': 18.494939999999996,
        'v_anaerobic': 2172.54375,
        'delta_n': 28.0,
        'v_anoxic': 4866.498,
        't_n': 3.36,
        'v_total': 33826.419285749995,
        't_total': 23.354939999999996,
        'v_o_series': 13393.688767874997,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 55.55555555555555,
        'x_vss': 3000.0,
        'o2_carbon': 9964.904443298998,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 11629.246759298998,
        'q_return': 2027.7074999999995,
        'q_internal': 2896.725,
        'h2': 5.0,
        'a_pool': 6765.283857149999,
        'h_pool': 5.3,
        'l_pool_raw': 130.05079639462036,
        'b_pool_raw': 52.02031855784814,
        'l_pool': 130.5,
        'b_pool': 52.5,
        'v_pool': 34256.25,
        'n_aerator_raw': 5357.4755071499985,
        'n_aerator': 5358.0,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §7.6；给水排水设计手册（第 5 册 城镇排水）；factor.aao.ns_band.*',
            'BOD5 污泥负荷 Ns kgBOD5/(kgMLSS·d) = 0.0400 越出建议带 [0.05, 0.15]——调节方向：ns（带'
            '内取值）',
            'ns',
        ),
        (
            "WARN",
            'GB 50014-2021 §7.6（AAO 泥龄 11~23d，好氧泥龄判断口径）；factor.aao.sludge_age_band.*',
            '好氧泥龄 theta_c = 55.5556 d 越出建议带 [11.0, 23.0]——调节方向：ns（↓泥龄↑）或 x_mlss'
            '（↑泥龄↑）；全池口径备考注记见 docs/norms/aao.md（口径待领域专家追认）',
            'ns',
        ),
    ]
    ports = {
        PortRef(unit_id='test_aao', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_aao', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0037204691021874964, ds=0.022322814613124995, moisture=0.994),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_aao', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 10.75,
        'TP': 0.4549999999999997,
    }
    quality_port = PortRef(unit_id='test_aao', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'ns': 0.3}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'v_o': 3571.6503380999993,
        't_o': 2.4659919999999995,
        'v_anaerobic': 2172.54375,
        'delta_n': 28.0,
        'v_anoxic': 4866.498,
        't_n': 3.36,
        'v_total': 10610.692088099999,
        't_total': 7.325991999999999,
        'v_o_series': 1785.8251690499997,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 7.407407407407407,
        'x_vss': 3000.0,
        'o2_carbon': 3000.1862840039994,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 4664.528600004,
        'q_return': 2027.7074999999995,
        'q_internal': 2896.725,
        'h2': 5.0,
        'a_pool': 2122.13841762,
        'h_pool': 5.3,
        'l_pool_raw': 72.83780641981195,
        'b_pool_raw': 29.135122567924782,
        'l_pool': 73.0,
        'b_pool': 29.5,
        'v_pool': 10767.5,
        'n_aerator_raw': 714.3300676199999,
        'n_aerator': 715.0,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §7.6；给水排水设计手册（第 5 册 城镇排水）；factor.aao.ns_band.*',
            'BOD5 污泥负荷 Ns kgBOD5/(kgMLSS·d) = 0.3000 越出建议带 [0.05, 0.15]——调节方向：ns（带'
            '内取值）',
            'ns',
        ),
        (
            "WARN",
            'GB 50014-2021 §7.6（AAO 泥龄 11~23d，好氧泥龄判断口径）；factor.aao.sludge_age_band.*',
            '好氧泥龄 theta_c = 7.4074 d 越出建议带 [11.0, 23.0]——调节方向：ns（↓泥龄↑）或 x_mlss'
            '（↑泥龄↑）；全池口径备考注记见 docs/norms/aao.md（口径待领域专家追认）',
            'ns',
        ),
    ]
    ports = {
        PortRef(unit_id='test_aao', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_aao', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0037204691021874964, ds=0.022322814613124995, moisture=0.994),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_aao', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 10.75,
        'TP': 0.4549999999999997,
    }
    quality_port = PortRef(unit_id='test_aao', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'x_mlss': 8000.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'v_o': 5357.475507149999,
        't_o': 3.6989879999999995,
        'v_anaerobic': 2172.54375,
        'delta_n': 28.0,
        'v_anoxic': 2433.249,
        't_n': 1.68,
        'v_total': 9963.268257149999,
        't_total': 6.878988,
        'v_o_series': 2678.7377535749997,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 6000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'q_return': 2027.7074999999995,
        'q_internal': 2896.725,
        'h2': 5.0,
        'a_pool': 1992.6536514299999,
        'h_pool': 5.3,
        'l_pool_raw': 70.58069232144864,
        'b_pool_raw': 28.23227692857946,
        'l_pool': 71.0,
        'b_pool': 28.5,
        'v_pool': 10117.5,
        'n_aerator_raw': 1071.49510143,
        'n_aerator': 1072.0,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §7.6；给水排水设计手册（第 5 册 城镇排水）；factor.aao.mlss_band.*',
            '设计 MLSS mg/L = 8000.0000 越出建议带 [3500.0, 4500.0]——调节方向：x_mlss（带内取值）',
            'x_mlss',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）；factor.aao.hrt_anoxic_band.*',
            '缺氧区 HRT t_n = 1.6800 h 越出建议带 [2.0, 4.0]——调节方向：x_mlss（↑t_n↓）或反硝化速'
            '率 Kde（factor.aao.k_denit，↑t_n↓）',
            'x_mlss',
        ),
    ]
    ports = {
        PortRef(unit_id='test_aao', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_aao', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0037204691021874964, ds=0.022322814613124995, moisture=0.994),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_aao', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 10.75,
        'TP': 0.4549999999999997,
    }
    quality_port = PortRef(unit_id='test_aao', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'h2': 6.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'v_o': 10714.951014299999,
        't_o': 7.397975999999999,
        'v_anaerobic': 2172.54375,
        'delta_n': 28.0,
        'v_anoxic': 4866.498,
        't_n': 3.36,
        'v_total': 17753.992764299997,
        't_total': 12.257976,
        'v_o_series': 5357.475507149999,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'q_return': 2027.7074999999995,
        'q_internal': 2896.725,
        'h2': 6.0,
        'a_pool': 2958.9987940499996,
        'h_pool': 6.3,
        'l_pool_raw': 86.00870296153174,
        'b_pool_raw': 34.4034811846127,
        'l_pool': 86.5,
        'b_pool': 34.5,
        'v_pool': 17905.5,
        'n_aerator_raw': 1785.8251690499999,
        'n_aerator': 1786.0,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_aao', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_aao', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0037204691021874964, ds=0.022322814613124995, moisture=0.994),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_aao', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 10.75,
        'TP': 0.4549999999999997,
    }
    quality_port = PortRef(unit_id='test_aao', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var5_full_surface() -> None:
    """用例 var5({'ratio_lb': 3.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR5_OVERRIDES)
    assert dict(result.dims) == {
        'v_o': 10714.951014299999,
        't_o': 7.397975999999999,
        'v_anaerobic': 2172.54375,
        'delta_n': 28.0,
        'v_anoxic': 4866.498,
        't_n': 3.36,
        'v_total': 17753.992764299997,
        't_total': 12.257976,
        'v_o_series': 5357.475507149999,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'q_return': 2027.7074999999995,
        'q_internal': 2896.725,
        'h2': 5.0,
        'a_pool': 3550.7985528599993,
        'h_pool': 5.3,
        'l_pool_raw': 103.21044355383808,
        'b_pool_raw': 34.403481184612694,
        'l_pool': 103.5,
        'b_pool': 34.5,
        'v_pool': 17853.75,
        'n_aerator_raw': 2142.99020286,
        'n_aerator': 2143.0,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_aao', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_aao', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0037204691021874964, ds=0.022322814613124995, moisture=0.994),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_aao', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 10.75,
        'TP': 0.4549999999999997,
    }
    quality_port = PortRef(unit_id='test_aao', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}

