"""municipal_tiaojiechi 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

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
from waterprint.units_lib.municipal.tiaojiechi import make_unit

"""municipal_tiaojiechi 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

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
_UNIT_TEST_ID = 'test_tiaojiechi'
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
    't_reg': 8.0,
    'h2': 5.0,
    'ratio_lb': 2.5,
    'n_pump_duty': 2.0,
    'side_disc_step': 0.5,
    'length_disc_step': 0.1,
    'factor.tiaojiechi.hrt_band.min': 6.0,
    'factor.tiaojiechi.hrt_band.max': 12.0,
    'factor.tiaojiechi.depth_band.min': 4.0,
    'factor.tiaojiechi.depth_band.max': 6.0,
    'factor.tiaojiechi.ratio_lb_band.min': 2.0,
    'factor.tiaojiechi.ratio_lb_band.max': 3.0,
    'factor.tiaojiechi.superheight': 0.5,
    'factor.tiaojiechi.stir.power_density': 6.0,
    'factor.tiaojiechi.overflow_velocity': 0.9,
    'factor.tiaojiechi.wall_thickness_coef': 0.35,
    'factor.tiaojiechi.elevation_loss': 0.5,
    'removal.tiaojiechi.bod5.mod_default': 0.0,
    'removal.tiaojiechi.cod.mod_default': 0.0,
    'removal.tiaojiechi.ss.mod_default': 0.0,
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
    't_reg': 13.0,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'h2': 3.5,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'ratio_lb': 3.5,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'side_disc_step': 0.01,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'t_reg': 13.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'v_total': 18828.712499999998,
        'v1': 9414.356249999999,
        'a1': 1882.8712499999997,
        'b_raw': 27.443551155052802,
        'b': 27.5,
        'l_raw': 68.46804545454545,
        'l': 68.5,
        'a_act': 1883.75,
        'v_act_total': 18837.5,
        't_reg_act': 13.006067196575444,
        'p_stir': 113.025,
        'q_pump1': 724.18125,
        'd_overflow': 0.9,
        'h_total': 5.5,
        'v_concrete': 7252.437499999999,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）调节池/泵站章；factor.tiaojiechi.hrt_band.min~fac'
            'tor.tiaojiechi.hrt_band.max',
            '实际调节停留时间 = 13.0061 h 越出建议带 [6.0, 12.0]——调节方向：t_reg（↑扩容）或 h2/n'
            '（↑加深加格）',
            't_reg',
        ),
    ]
    ports = {
        PortRef(unit_id='test_tiaojiechi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_tiaojiechi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 164.3994,
        'CODCR': 285.6232,
        'SS': 186.4242,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'h2': 3.5}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'v_total': 11586.9,
        'v1': 5793.45,
        'a1': 1655.2714285714285,
        'b_raw': 25.731470448238504,
        'b': 26.0,
        'l_raw': 63.66428571428571,
        'l': 64.0,
        'a_act': 1664.0,
        'v_act_total': 11648.0,
        't_reg_act': 8.042185571636935,
        'p_stir': 69.888,
        'q_pump1': 724.18125,
        'd_overflow': 0.9,
        'h_total': 4.0,
        'v_concrete': 4659.2,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）调节池/泵站章；factor.tiaojiechi.depth_band.min~f'
            'actor.tiaojiechi.depth_band.max',
            '有效水深 h2 = 3.5000 m 越出建议带 [4.0, 6.0]——调节方向：h2（工程常用带内取值）',
            'h2',
        ),
    ]
    ports = {
        PortRef(unit_id='test_tiaojiechi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_tiaojiechi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 164.3994,
        'CODCR': 285.6232,
        'SS': 186.4242,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'ratio_lb': 3.5}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'v_total': 11586.9,
        'v1': 5793.45,
        'a1': 1158.69,
        'b_raw': 18.194897243850697,
        'b': 18.5,
        'l_raw': 62.6318918918919,
        'l': 63.0,
        'a_act': 1165.5,
        'v_act_total': 11655.0,
        't_reg_act': 8.047018615850659,
        'p_stir': 69.93,
        'q_pump1': 724.18125,
        'd_overflow': 0.9,
        'h_total': 5.5,
        'v_concrete': 4487.174999999999,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）调节池/泵站章；factor.tiaojiechi.ratio_lb_band.mi'
            'n~factor.tiaojiechi.ratio_lb_band.max',
            '池长宽比 L/B = 3.5000 越出建议带 [2.0, 3.0]——调节方向：ratio_lb（矩形池工程常用）',
            'ratio_lb',
        ),
    ]
    ports = {
        PortRef(unit_id='test_tiaojiechi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_tiaojiechi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 164.3994,
        'CODCR': 285.6232,
        'SS': 186.4242,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'side_disc_step': 0.01}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'v_total': 11586.9,
        'v1': 5793.45,
        'a1': 1158.69,
        'b_raw': 21.528492747984007,
        'b': 21.53,
        'l_raw': 53.81746400371574,
        'l': 53.82,
        'a_act': 1158.7446,
        'v_act_total': 11587.446,
        't_reg_act': 8.000376977448672,
        'p_stir': 69.52467600000001,
        'q_pump1': 724.18125,
        'd_overflow': 0.9,
        'h_total': 5.5,
        'v_concrete': 4461.1667099999995,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_tiaojiechi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_tiaojiechi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 164.3994,
        'CODCR': 285.6232,
        'SS': 186.4242,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }

