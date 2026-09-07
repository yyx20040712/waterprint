"""municipal_erchunchi 向量化重写前基线锚·参数变体面(批 13-B·件 2/2)。

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
from waterprint.units_lib.municipal.erchunchi import make_unit

"""municipal_erchunchi 向量化重写前基线锚·参数变体面(批 13-B·件 2/2)。

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
_UNIT_TEST_ID = 'test_erchunchi'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 12.32996,
    'CODCR': 29.99043,
    'SS': 9.32121,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 2.0,
    'q_nom': 1.2,
    'x_mlss': 4000.0,
    'r_external': 1.0,
    'h2': 3.0,
    'r_pit': 1.0,
    'dia_disc_step': 0.5,
    'length_disc_step': 0.1,
    'factor.erchunchi.surface_load_band.min': 0.6,
    'factor.erchunchi.surface_load_band.max': 1.5,
    'factor.erchunchi.solid_load.center_inlet': 150.0,
    'factor.erchunchi.solid_load.peripheral_inlet': 200.0,
    'factor.erchunchi.weir_load.max': 1.7,
    'factor.erchunchi.depth_band.min': 2.5,
    'factor.erchunchi.depth_band.max': 3.5,
    'factor.erchunchi.superheight': 0.3,
    'factor.erchunchi.buffer_h3': 0.3,
    'factor.erchunchi.bottom_slope': 0.05,
    'factor.erchunchi.center_velocity': 0.3,
    'factor.erchunchi.wall_thickness_coef': 0.4,
    'factor.erchunchi.elevation_loss': 0.6,
    'factor.erchunchi.x_r_band.min': 6000.0,
    'factor.erchunchi.x_r_band.max': 12000.0,
    'factor.erchunchi.hrt_band.min': 1.5,
    'factor.erchunchi.hrt_band.max': 4.0,
    'removal.erchunchi.bod5.mod_default': 0.2,
    'removal.erchunchi.cod.mod_default': 0.15,
    'removal.erchunchi.ss.mod_default': 0.5,
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
    'q_nom': 2.0,
    'factor.erchunchi.solid_load.center_inlet': 10000.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'r_external': 0.4,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'h2': 2.0,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'h2': 2.0,
    'q_nom': 1.5,
    'factor.erchunchi.solid_load.center_inlet': 10000.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1(参数面见 OVERRIDES 常量):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'a_q': 506.9268749999999,
        'm_solid': 194659.91999999995,
        'a_solid': 19.465991999999996,
        'a_tank': 506.9268749999999,
        'd_raw': 25.405498293460386,
        'd': 25.5,
        'a_act': 510.70515574919074,
        'q_act': 1.9852036710158203,
        'g_act': 381.1591048350375,
        'x_r': 8000.0,
        'v_check': 1532.1154672475723,
        't_hrt': 1.5111799579057361,
        'q_return_sludge': 1013.8537499999998,
        'q_weir': 1.7577324170452575,
        'd_center': 1.6,
        'h4': 0.6000000000000001,
        'h_total': 4.2,
        'v_concrete': 1715.9693233172811,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 表 7.5.1+§7.6.15/§7.6.16；factor.erchunchi.surface_load_band.min~factor'
            '.erchunchi.surface_load_band.max',
            '实际清水表面负荷 = 1.9852 越出建议带 [0.6, 1.5]——调节方向：q_nom（负荷）或 n（池数）',
            'q_nom',
        ),
        (
            "WARN",
            'GB 50014-2021（沉淀池堰负荷，二沉档）；factor.erchunchi.weir_load.max',
            '出水堰负荷 = 1.7577 超上限 1.7——堰构造口径注记：默认周边双侧出水堰（L=2πD），单侧口径'
            '敏感性见 docs/norms/erchunchi.md（堰构造口径待领域专家追认）',
            None,
        ),
    ]
    ports = {
        PortRef(unit_id='test_erchunchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_erchunchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 9.863968,
        'CODCR': 25.4918655,
        'SS': 4.660605,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'r_external': 0.4}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'a_q': 844.8781249999998,
        'm_solid': 136261.94399999996,
        'a_solid': 908.4129599999998,
        'a_tank': 908.4129599999998,
        'd_raw': 34.009223802108764,
        'd': 34.5,
        'a_act': 934.8201639838128,
        'q_act': 1.084544160536053,
        'g_act': 145.76273517604554,
        'x_r': 14000.0,
        'v_check': 2804.4604919514386,
        't_hrt': 2.766139092498735,
        'q_return_sludge': 405.5414999999999,
        'q_weir': 1.299193525642147,
        'd_center': 1.3,
        'h4': 0.9,
        'h_total': 4.5,
        'v_concrete': 3365.3525903417267,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）；factor.erchunchi.x_r_band.min~factor.erchunchi.'
            'x_r_band.max（0.2.1 键）',
            '回流污泥浓度 Xr = 14000.0000 mg/L 越出建议带 [6000.0, 12000.0]——调节方向：r_external'
            '（↑Xr↓，与 AAO 表联动）',
            'r_external',
        ),
    ]
    ports = {
        PortRef(unit_id='test_erchunchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_erchunchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 9.863968,
        'CODCR': 25.4918655,
        'SS': 4.660605,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'h2': 2.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'a_q': 844.8781249999998,
        'm_solid': 194659.91999999995,
        'a_solid': 1297.7327999999998,
        'a_tank': 1297.7327999999998,
        'd_raw': 40.64879726953662,
        'd': 41.0,
        'a_act': 1320.2543126711105,
        'q_act': 0.7679230738120388,
        'g_act': 147.44123017191146,
        'x_r': 8000.0,
        'v_check': 2640.508625342221,
        't_hrt': 2.6044275373467047,
        'q_return_sludge': 1013.8537499999998,
        'q_weir': 1.0932238203574165,
        'd_center': 1.6,
        'h4': 1.0,
        'h_total': 3.6,
        'v_concrete': 3802.332420492798,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）；factor.erchunchi.depth_band.min~factor.erchunch'
            'i.depth_band.max',
            '池边有效水深 h2 = 2.0000 越出建议带 [2.5, 3.5]——调节方向：h2（带内取值）',
            'h2',
        ),
    ]
    ports = {
        PortRef(unit_id='test_erchunchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_erchunchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 9.863968,
        'CODCR': 25.4918655,
        'SS': 4.660605,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var4_full_surface() -> None:
    """用例 var4(参数面见 OVERRIDES 常量):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'q1': 0.2816260416666666,
        'q1h': 1013.8537499999998,
        'a_q': 675.9024999999998,
        'm_solid': 194659.91999999995,
        'a_solid': 19.465991999999996,
        'a_tank': 675.9024999999998,
        'd_raw': 29.335742557251862,
        'd': 29.5,
        'a_act': 683.4927516966294,
        'q_act': 1.4833423580327918,
        'g_act': 284.80173274229605,
        'x_r': 8000.0,
        'v_check': 1366.9855033932588,
        't_hrt': 1.348306403555009,
        'q_return_sludge': 1013.8537499999998,
        'q_weir': 1.5193958181238667,
        'd_center': 1.6,
        'h4': 0.7000000000000001,
        'h_total': 3.3000000000000003,
        'v_concrete': 1804.420864479102,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）；factor.erchunchi.depth_band.min~factor.erchunch'
            'i.depth_band.max',
            '池边有效水深 h2 = 2.0000 越出建议带 [2.5, 3.5]——调节方向：h2（带内取值）',
            'h2',
        ),
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）；factor.erchunchi.hrt_band.min~factor.erchunchi.'
            'hrt_band.max（0.2.1 键）',
            '校核 HRT = 1.3483 h 越出建议带 [1.5, 4.0]——调节方向：q_nom（↓池径↑t↑）或 h2（↑t↑）',
            'q_nom',
        ),
    ]
    ports = {
        PortRef(unit_id='test_erchunchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_erchunchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 9.863968,
        'CODCR': 25.4918655,
        'SS': 4.660605,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }

