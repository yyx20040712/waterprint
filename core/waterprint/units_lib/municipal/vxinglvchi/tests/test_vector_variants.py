"""municipal_vxinglvchi 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

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
from waterprint.units_lib.municipal.vxinglvchi import make_unit

"""municipal_vxinglvchi 向量化重写前基线锚·参数变体面(批 13-A·件 2/2)。

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
_UNIT_TEST_ID = 'test_vxinglvchi'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 5.918378,
    'CODCR': 17.84431,
    'SS': 0.6990908,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 6.0,
    'v_filter': 8.0,
    'ratio_lb': 2.5,
    'h_water_above': 1.3,
    'h_sand': 1.3,
    'h_bottom': 1.0,
    't_cycle': 24.0,
    'side_disc_step': 0.5,
    'factor.vxinglvchi.v_filter_band.min': 7.0,
    'factor.vxinglvchi.v_filter_band.max': 10.0,
    'factor.vxinglvchi.v_forced_band.min': 11.0,
    'factor.vxinglvchi.v_forced_band.max': 13.0,
    'factor.vxinglvchi.selfuse_coef': 1.05,
    'factor.vxinglvchi.cell_ratio_lb_band.min': 2.0,
    'factor.vxinglvchi.cell_ratio_lb_band.max': 3.0,
    'factor.vxinglvchi.media.depth_band.min': 1.2,
    'factor.vxinglvchi.media.depth_band.max': 1.5,
    'factor.vxinglvchi.media.d10_band.min': 0.9,
    'factor.vxinglvchi.media.d10_band.max': 1.2,
    'factor.vxinglvchi.water_above_band.min': 1.2,
    'factor.vxinglvchi.water_above_band.max': 1.5,
    'factor.vxinglvchi.superheight': 0.3,
    'factor.vxinglvchi.wash.air': 15.0,
    'factor.vxinglvchi.wash.water_sim': 2.5,
    'factor.vxinglvchi.wash.water': 5.0,
    'factor.vxinglvchi.wash.sweep': 1.8,
    'factor.vxinglvchi.wash.t_air': 2.0,
    'factor.vxinglvchi.wash.t_sim': 4.0,
    'factor.vxinglvchi.wash.t_water': 4.0,
    'factor.vxinglvchi.cycle_band.min': 24.0,
    'factor.vxinglvchi.cycle_band.max': 48.0,
    'factor.vxinglvchi.wall_thickness_coef': 0.35,
    'factor.vxinglvchi.elevation_loss': 2.5,
    'removal.vxinglvchi.bod5.mod_default': 0.075,
    'removal.vxinglvchi.cod.mod_default': 0.075,
    'removal.vxinglvchi.ss.mod_default': 0.675,
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
    'v_filter': 12.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'v_filter': 10.0,
    'n': 4.0,
    'ratio_lb': 3.0,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'ratio_lb': 3.5,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'h_sand': 1.6,
}

_VAR5_OVERRIDES: dict[str, float] = {
    'h_water_above': 1.6,
}

_VAR6_OVERRIDES: dict[str, float] = {
    't_cycle': 20.0,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'v_filter': 12.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q_filter': 2129.0928749999994,
        'a_total_req': 177.42440624999995,
        'a_cell': 29.57073437499999,
        'b_raw': 3.439228656254189,
        'b': 3.5,
        'l_raw': 8.448781249999998,
        'l': 8.5,
        'a_cell_act': 29.75,
        'a_total_act': 178.5,
        'v_filter_act': 11.927691176470585,
        'v_forced_act': 14.313229411764702,
        'q_air': 0.44625,
        'q_wash_sim': 0.074375,
        'q_wash': 0.14875,
        'q_sweep': 0.05355000000000001,
        'v_air_per': 160.64999999999998,
        'v_wash_per': 85.67999999999999,
        'v_wash_daily': 514.0799999999999,
        'ratio_wash': 0.014789115293995805,
        'h_total': 3.9000000000000004,
        'v_concrete': 243.6525,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速）；factor.vxinglvchi.v_filter_band.mi'
            'n~factor.vxinglvchi.v_filter_band.max',
            '实际正常滤速 = 11.9277 越出建议带 [7.0, 10.0]——调节方向：v_filter（滤速）或 n（分格数'
            '）',
            'v_filter',
        ),
        (
            "WARN",
            'GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速）；factor.vxinglvchi.v_forced_band.ma'
            'x（单向上限——带 11~13 为典型带，低于下限=保守合格）',
            '一格冲洗时强制滤速 = 14.3132 超上限 13.0——调节方向：n（↑加格）或 v_filter（↓滤速）',
            'n',
        ),
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'v_filter': 10.0, 'n': 4.0, 'ratio_lb': 3.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q_filter': 2129.0928749999994,
        'a_total_req': 212.90928749999995,
        'a_cell': 53.22732187499999,
        'b_raw': 4.2121776582903045,
        'b': 4.5,
        'l_raw': 11.828293749999997,
        'l': 12.0,
        'a_cell_act': 54.0,
        'a_total_act': 216.0,
        'v_filter_act': 9.85691145833333,
        'v_forced_act': 13.142548611111108,
        'q_air': 0.81,
        'q_wash_sim': 0.135,
        'q_wash': 0.27,
        'q_sweep': 0.09720000000000001,
        'v_air_per': 291.6,
        'v_wash_per': 155.52,
        'v_wash_daily': 622.08,
        'ratio_wash': 0.017896072288532742,
        'h_total': 3.9000000000000004,
        'v_concrete': 294.84000000000003,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速）；factor.vxinglvchi.v_forced_band.ma'
            'x（单向上限——带 11~13 为典型带，低于下限=保守合格）',
            '一格冲洗时强制滤速 = 13.1425 超上限 13.0——调节方向：n（↑加格）或 v_filter（↓滤速）',
            'n',
        ),
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'ratio_lb': 3.5}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q_filter': 2129.0928749999994,
        'a_total_req': 266.1366093749999,
        'a_cell': 44.35610156249999,
        'b_raw': 3.5599398695764504,
        'b': 4.0,
        'l_raw': 11.089025390624997,
        'l': 11.5,
        'a_cell_act': 46.0,
        'a_total_act': 276.0,
        'v_filter_act': 7.714104619565215,
        'v_forced_act': 9.256925543478259,
        'q_air': 0.69,
        'q_wash_sim': 0.115,
        'q_wash': 0.23,
        'q_sweep': 0.0828,
        'v_air_per': 248.39999999999998,
        'v_wash_per': 132.48000000000002,
        'v_wash_daily': 794.8800000000001,
        'ratio_wash': 0.022867203479791837,
        'h_total': 3.9000000000000004,
        'v_concrete': 376.74,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）V 型滤池构造；factor.vxinglvchi.cell_ratio_lb_ban'
            'd.min~factor.vxinglvchi.cell_ratio_lb_band.max',
            '单格长宽比 L/B = 3.5000 越出建议带 [2.0, 3.0]——调节方向：ratio_lb（V 滤单格工程常用）',
            'ratio_lb',
        ),
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'h_sand': 1.6}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'q_filter': 2129.0928749999994,
        'a_total_req': 266.1366093749999,
        'a_cell': 44.35610156249999,
        'b_raw': 4.2121776582903045,
        'b': 4.5,
        'l_raw': 9.85691145833333,
        'l': 10.0,
        'a_cell_act': 45.0,
        'a_total_act': 270.0,
        'v_filter_act': 7.8855291666666645,
        'v_forced_act': 9.462634999999997,
        'q_air': 0.675,
        'q_wash_sim': 0.1125,
        'q_wash': 0.225,
        'q_sweep': 0.081,
        'v_air_per': 243.00000000000006,
        'v_wash_per': 129.60000000000002,
        'v_wash_daily': 777.6,
        'ratio_wash': 0.022370090360665926,
        'h_total': 4.2,
        'v_concrete': 396.9,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速）；factor.vxinglvchi.media.depth_band'
            '.min~factor.vxinglvchi.media.depth_band.max',
            '均质滤料层厚 = 1.6000 m 越出建议带 [1.2, 1.5]——调节方向：h_sand（GB 50013-2018 §9.5 '
            '均质滤料）',
            'h_sand',
        ),
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var5_full_surface() -> None:
    """用例 var5({'h_water_above': 1.6}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR5_OVERRIDES)
    assert dict(result.dims) == {
        'q_filter': 2129.0928749999994,
        'a_total_req': 266.1366093749999,
        'a_cell': 44.35610156249999,
        'b_raw': 4.2121776582903045,
        'b': 4.5,
        'l_raw': 9.85691145833333,
        'l': 10.0,
        'a_cell_act': 45.0,
        'a_total_act': 270.0,
        'v_filter_act': 7.8855291666666645,
        'v_forced_act': 9.462634999999997,
        'q_air': 0.675,
        'q_wash_sim': 0.1125,
        'q_wash': 0.225,
        'q_sweep': 0.081,
        'v_air_per': 243.00000000000006,
        'v_wash_per': 129.60000000000002,
        'v_wash_daily': 777.6,
        'ratio_wash': 0.022370090360665926,
        'h_total': 4.2,
        'v_concrete': 396.9,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）V 型滤池构造；factor.vxinglvchi.water_above_band.'
            'min~factor.vxinglvchi.water_above_band.max',
            '砂上水深 = 1.6000 m 越出建议带 [1.2, 1.5]——调节方向：h_water_above（恒水位过滤）',
            'h_water_above',
        ),
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var6_full_surface() -> None:
    """用例 var6({'t_cycle': 20.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR6_OVERRIDES)
    assert dict(result.dims) == {
        'q_filter': 2129.0928749999994,
        'a_total_req': 266.1366093749999,
        'a_cell': 44.35610156249999,
        'b_raw': 4.2121776582903045,
        'b': 4.5,
        'l_raw': 9.85691145833333,
        'l': 10.0,
        'a_cell_act': 45.0,
        'a_total_act': 270.0,
        'v_filter_act': 7.8855291666666645,
        'v_forced_act': 9.462634999999997,
        'q_air': 0.675,
        'q_wash_sim': 0.1125,
        'q_wash': 0.225,
        'q_sweep': 0.081,
        'v_air_per': 243.00000000000006,
        'v_wash_per': 129.60000000000002,
        'v_wash_daily': 933.1200000000001,
        'ratio_wash': 0.026844108432799114,
        'h_total': 3.9000000000000004,
        'v_concrete': 368.54999999999995,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）V 型滤池构造；factor.vxinglvchi.cycle_band.min~fa'
            'ctor.vxinglvchi.cycle_band.max',
            '过滤周期 = 20.0000 h 越出建议带 [24.0, 48.0]——调节方向：t_cycle（V 滤长周期档）',
            't_cycle',
        ),
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }

