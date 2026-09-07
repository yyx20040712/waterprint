"""municipal_gaomidu 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

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
from waterprint.units_lib.municipal.gaomidu import make_unit

"""municipal_gaomidu 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

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
_UNIT_TEST_ID = 'test_gaomidu'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 9.863964,
    'CODCR': 25.49187,
    'SS': 4.660605,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 2.0,
    'q_surface': 15.0,
    'r_sludge': 0.04,
    't_mix': 1.5,
    't_floc': 12.0,
    'l_tube': 1.0,
    'h_clear': 1.2,
    'h_buffer': 1.2,
    'h_thick': 2.0,
    'side_disc_step': 0.5,
    'length_disc_step': 0.1,
    'factor.gaomidu.surface_load_band.min': 10.0,
    'factor.gaomidu.surface_load_band.max': 20.0,
    'factor.gaomidu.r_sludge_band.min': 0.03,
    'factor.gaomidu.r_sludge_band.max': 0.05,
    'factor.gaomidu.t_mix_band.min': 1.0,
    'factor.gaomidu.t_mix_band.max': 2.0,
    'factor.gaomidu.t_floc_band.min': 8.0,
    'factor.gaomidu.t_floc_band.max': 15.0,
    'factor.gaomidu.g_mix': 500.0,
    'factor.gaomidu.g_floc': 50.0,
    'factor.gaomidu.gt_band.min': 10000.0,
    'factor.gaomidu.gt_band.max': 100000.0,
    'factor.gaomidu.sludge.concentration': 20.0,
    'factor.gaomidu.dose.pac': 30.0,
    'factor.gaomidu.dose.pam': 1.0,
    'factor.gaomidu.superheight': 0.3,
    'factor.gaomidu.wall_thickness_coef': 0.35,
    'factor.gaomidu.elevation_loss': 0.8,
    'removal.gaomidu.bod5.mod_default': 0.4,
    'removal.gaomidu.cod.mod_default': 0.3,
    'removal.gaomidu.ss.mod_default': 0.85,
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
    'q_surface': 25.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'r_sludge': 0.06,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'factor.gaomidu.g_floc': 150.0,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'q_surface': 25.0,
    't_floc': 15.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'q_surface': 25.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q1h': 1013.8537499999998,
        'q_design_h': 2027.7074999999995,
        'a_incl_req': 40.55414999999999,
        'b_raw': 6.368214035347743,
        'b': 6.5,
        'a_act': 42.25,
        'q_surface_act': 23.996538461538456,
        'v_mix': 25.346343749999996,
        'v_floc': 202.77074999999996,
        'p_mix': 6.336585937499999,
        'p_floc': 0.5069268749999999,
        'gt_floc': 36000.0,
        'q_return': 81.10829999999999,
        'ss_out': 0.6990907500000002,
        's_dry': 137.705008389975,
        'q_sludge': 6.8852504194987505,
        'm_pac': 1042.821,
        'm_pam': 34.7607,
        'h_tube_zone': 0.8660254,
        'h_settle': 5.2660254,
        'h_total_raw': 5.5660254,
        'h_total': 5.6000000000000005,
        'h_floc_calc': 4.799307692307692,
        'v_concrete': 165.62,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB/T 50335-2016 §5.4.3（高密斜管清水区液面负荷）；factor.gaomidu.surface_load_band.mi'
            'n~factor.gaomidu.surface_load_band.max',
            '实际液面负荷 = 23.9965 越出建议带 [10.0, 20.0]——调节方向：q_surface（负荷）或 n（池数'
            '）',
            'q_surface',
        ),
    ]
    ports = {
        PortRef(unit_id='test_gaomidu', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_gaomidu', port_id='sludge_out'):
            SludgeFlow(q_wet=7.969039837382812e-05, ds=0.0015938079674765627, moisture=0.98),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_gaomidu', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.918378399999999,
        'CODCR': 17.844309,
        'SS': 0.6990907500000002,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_gaomidu', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'r_sludge': 0.06}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q1h': 1013.8537499999998,
        'q_design_h': 2027.7074999999995,
        'a_incl_req': 67.59024999999998,
        'b_raw': 8.22132896799538,
        'b': 8.5,
        'a_act': 72.25,
        'q_surface_act': 14.032577854671278,
        'v_mix': 25.346343749999996,
        'v_floc': 202.77074999999996,
        'p_mix': 6.336585937499999,
        'p_floc': 0.5069268749999999,
        'gt_floc': 36000.0,
        'q_return': 121.66244999999996,
        'ss_out': 0.6990907500000002,
        's_dry': 137.705008389975,
        'q_sludge': 6.8852504194987505,
        'm_pac': 1042.821,
        'm_pam': 34.7607,
        'h_tube_zone': 0.8660254,
        'h_settle': 5.2660254,
        'h_total_raw': 5.5660254,
        'h_total': 5.6000000000000005,
        'h_floc_calc': 2.8065155709342555,
        'v_concrete': 283.21999999999997,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB/T 50335-2016 §5.4.3（高密斜管清水区液面负荷）；factor.gaomidu.r_sludge_band.min~fa'
            'ctor.gaomidu.r_sludge_band.max',
            '污泥回流比 = 0.0600 越出建议带 [0.03, 0.05]——调节方向：r_sludge（Densadeg 回流档）',
            'r_sludge',
        ),
    ]
    ports = {
        PortRef(unit_id='test_gaomidu', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_gaomidu', port_id='sludge_out'):
            SludgeFlow(q_wet=7.969039837382812e-05, ds=0.0015938079674765627, moisture=0.98),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_gaomidu', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.918378399999999,
        'CODCR': 17.844309,
        'SS': 0.6990907500000002,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_gaomidu', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'factor.gaomidu.g_floc': 150.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q1h': 1013.8537499999998,
        'q_design_h': 2027.7074999999995,
        'a_incl_req': 67.59024999999998,
        'b_raw': 8.22132896799538,
        'b': 8.5,
        'a_act': 72.25,
        'q_surface_act': 14.032577854671278,
        'v_mix': 25.346343749999996,
        'v_floc': 202.77074999999996,
        'p_mix': 6.336585937499999,
        'p_floc': 4.5623418749999995,
        'gt_floc': 108000.0,
        'q_return': 81.10829999999999,
        'ss_out': 0.6990907500000002,
        's_dry': 137.705008389975,
        'q_sludge': 6.8852504194987505,
        'm_pac': 1042.821,
        'm_pam': 34.7607,
        'h_tube_zone': 0.8660254,
        'h_settle': 5.2660254,
        'h_total_raw': 5.5660254,
        'h_total': 5.6000000000000005,
        'h_floc_calc': 2.8065155709342555,
        'v_concrete': 283.21999999999997,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）混合/絮凝 G 值法；factor.gaomidu.gt_band.min~fact'
            'or.gaomidu.gt_band.max',
            '絮凝 GT 值 = 108000 越出建议带 [10000, 100000]——调节方向：t_floc（历时）或 g_floc（系'
            '数键）',
            't_floc',
        ),
    ]
    ports = {
        PortRef(unit_id='test_gaomidu', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_gaomidu', port_id='sludge_out'):
            SludgeFlow(q_wet=7.969039837382812e-05, ds=0.0015938079674765627, moisture=0.98),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_gaomidu', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.918378399999999,
        'CODCR': 17.844309,
        'SS': 0.6990907500000002,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_gaomidu', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'q_surface': 25.0, 't_floc': 15.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'q1h': 1013.8537499999998,
        'q_design_h': 2027.7074999999995,
        'a_incl_req': 40.55414999999999,
        'b_raw': 6.368214035347743,
        'b': 6.5,
        'a_act': 42.25,
        'q_surface_act': 23.996538461538456,
        'v_mix': 25.346343749999996,
        'v_floc': 253.46343749999994,
        'p_mix': 6.336585937499999,
        'p_floc': 0.6336585937499999,
        'gt_floc': 45000.0,
        'q_return': 81.10829999999999,
        'ss_out': 0.6990907500000002,
        's_dry': 137.705008389975,
        'q_sludge': 6.8852504194987505,
        'm_pac': 1042.821,
        'm_pam': 34.7607,
        'h_tube_zone': 0.8660254,
        'h_settle': 5.2660254,
        'h_total_raw': 5.5660254,
        'h_total': 5.6000000000000005,
        'h_floc_calc': 5.999134615384614,
        'v_concrete': 165.62,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB/T 50335-2016 §5.4.3（高密斜管清水区液面负荷）；factor.gaomidu.surface_load_band.mi'
            'n~factor.gaomidu.surface_load_band.max',
            '实际液面负荷 = 23.9965 越出建议带 [10.0, 20.0]——调节方向：q_surface（负荷）或 n（池数'
            '）',
            'q_surface',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）混合/絮凝 G 值法；GM-F19 絮凝区布置校核（h_floc_c'
            'alc < h_settle）',
            '絮凝区计算水深 = 5.9991 m 不低于沉淀区总高 5.2660 m——布置不可行：t_floc（↓）或 q_surf'
            'ace（↑负荷缩面）',
            't_floc',
        ),
    ]
    ports = {
        PortRef(unit_id='test_gaomidu', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_gaomidu', port_id='sludge_out'):
            SludgeFlow(q_wet=7.969039837382812e-05, ds=0.0015938079674765627, moisture=0.98),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_gaomidu', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.918378399999999,
        'CODCR': 17.844309,
        'SS': 0.6990907500000002,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }
    quality_port = PortRef(unit_id='test_gaomidu', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}

