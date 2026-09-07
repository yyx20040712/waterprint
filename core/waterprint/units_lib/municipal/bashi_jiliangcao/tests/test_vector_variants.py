"""municipal_bashi_jiliangcao 向量化重写前基线锚·参数变体面(批 13-D·件 2/2)。

输入:  本包 make_unit/compute——重写前树态(d445483429)变体全表面冻结
输出:  参数变体全表面精确锚(dims/warnings/出流出质——== 精确;锚
       层级与即绿注记见件 1 test_vector_baseline.py 头注)
"""

# ════════════════════════════════════════════════════════════
# 规格说明:件 1 同款(批 13-D 基线先行独立笔;自包含纪律——冻结
# 入参与件 1 同源副本,零跨测试件 import)。
# ════════════════════════════════════════════════════════════


from __future__ import annotations

from typing import Any

from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.units_lib.municipal.bashi_jiliangcao import make_unit

# ── 冻结入参(重写前包内 test_compute 权威夹具的 round-trip 字面量化;
#    变体件与本件同源副本——包内 tests 无包语义,自包含纪律) ──
_UNIT_TEST_ID = 'test_bashi'
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
    'b_throat': 0.75,
    'factor.bashi_jiliangcao.flume.b025.c': 561.0,
    'factor.bashi_jiliangcao.flume.b025.n': 1.513,
    'factor.bashi_jiliangcao.flume.b025.scrit': 0.6,
    'factor.bashi_jiliangcao.flume.b025.hmin': 0.03,
    'factor.bashi_jiliangcao.flume.b025.hmax': 0.6,
    'factor.bashi_jiliangcao.flume.b045.c': 1038.0,
    'factor.bashi_jiliangcao.flume.b045.n': 1.537,
    'factor.bashi_jiliangcao.flume.b045.scrit': 0.6,
    'factor.bashi_jiliangcao.flume.b045.hmin': 0.03,
    'factor.bashi_jiliangcao.flume.b045.hmax': 0.75,
    'factor.bashi_jiliangcao.flume.b075.c': 1772.0,
    'factor.bashi_jiliangcao.flume.b075.n': 1.557,
    'factor.bashi_jiliangcao.flume.b075.scrit': 0.6,
    'factor.bashi_jiliangcao.flume.b075.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b075.hmax': 0.75,
    'factor.bashi_jiliangcao.flume.b100.c': 2397.0,
    'factor.bashi_jiliangcao.flume.b100.n': 1.569,
    'factor.bashi_jiliangcao.flume.b100.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b100.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b100.hmax': 0.8,
    'factor.bashi_jiliangcao.flume.b120.c': 2904.0,
    'factor.bashi_jiliangcao.flume.b120.n': 1.577,
    'factor.bashi_jiliangcao.flume.b120.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b120.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b120.hmax': 0.8,
    'factor.bashi_jiliangcao.flume.b150.c': 3668.0,
    'factor.bashi_jiliangcao.flume.b150.n': 1.586,
    'factor.bashi_jiliangcao.flume.b150.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b150.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b150.hmax': 0.8,
    'factor.bashi_jiliangcao.flume.b210.c': 5222.0,
    'factor.bashi_jiliangcao.flume.b210.n': 1.599,
    'factor.bashi_jiliangcao.flume.b210.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b210.hmin': 0.08,
    'factor.bashi_jiliangcao.flume.b210.hmax': 0.8,
    'factor.bashi_jiliangcao.hb_design': 0.25,
    'factor.bashi_jiliangcao.loss_ratio': 0.25,
    'factor.bashi_jiliangcao.geometry.l_throat': 0.6,
    'factor.bashi_jiliangcao.geometry.l_diffuse': 0.92,
    'factor.bashi_jiliangcao.geometry.n_depress': 0.23,
    'factor.bashi_jiliangcao.geometry.k_margin': 0.08,
    'factor.bashi_jiliangcao.elevation_loss': 0.15,
    'removal.bashi_jiliangcao.bod5.mod_default': 0.0,
    'removal.bashi_jiliangcao.cod.mod_default': 0.0,
    'removal.bashi_jiliangcao.ss.mod_default': 0.0,
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
    'b_throat': 0.25,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'b_throat': 2.1,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'factor.bashi_jiliangcao.hb_design': 0.45,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'b_throat': 0.25}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'ha_design': 1.0026514749563815,
        'ha_avg': 0.802727881040776,
        'q_meas': 402.32291666666663,
        'b1': 0.78,
        'l1': 1.325,
        'b2': 0.55,
        'l_total': 2.8449999999999998,
        'l_throat': 0.6,
        'l_diffuse': 0.92,
        'n_depress': 0.23,
        'k_margin': 0.08,
        'sigma': 0.2493388841929104,
        'h_loss': 0.2506628687390954,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）量水堰槽章；factor.bashi_jiliangcao.flume.b025.hm'
            'in/hmax',
            '设计水头 ha_design = 1.0027 m 越出本档适用带 [0.03, 0.6]——调节方向：b_throat（换档：'
            '小档加深水头/大档减浅水头，B7 七档 grid）',
            'b_throat',
        ),
    ]
    ports = {
        PortRef(unit_id='test_bashi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_bashi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'b_throat': 2.1}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'ha_design': 0.24840663343518726,
        'ha_avg': 0.2012686111525815,
        'q_meas': 402.32291666666663,
        'b1': 3.0,
        'l1': 2.25,
        'b2': 2.4,
        'l_total': 3.77,
        'l_throat': 0.6,
        'l_diffuse': 0.92,
        'n_depress': 0.23,
        'k_margin': 0.08,
        'sigma': 1.0064143478890972,
        'h_loss': 0.062101658358796816,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）量水堰槽章；factor.bashi_jiliangcao.flume.b210.sc'
            'rit',
            '淹没度 sigma = 1.0064 超临界淹没度 0.7（淹没流，Q=C·h^n 自由流式失效）——调节方向：hb_'
            'design（降低下游水深设计假定）或 b_throat（大档加深 ha）',
            'b_throat',
        ),
    ]
    ports = {
        PortRef(unit_id='test_bashi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_bashi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'factor.bashi_jiliangcao.hb_design': 0.45}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'ha_design': 0.47896932471441167,
        'ha_avg': 0.385882778771218,
        'q_meas': 402.32291666666663,
        'b1': 1.38,
        'l1': 1.575,
        'b2': 1.05,
        'l_total': 3.0949999999999998,
        'l_throat': 0.6,
        'l_diffuse': 0.92,
        'n_depress': 0.23,
        'k_margin': 0.08,
        'sigma': 0.9395173694438892,
        'h_loss': 0.11974233117860292,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            '给水排水设计手册（第 5 册 城镇排水）量水堰槽章；factor.bashi_jiliangcao.flume.b075.sc'
            'rit',
            '淹没度 sigma = 0.9395 超临界淹没度 0.6（淹没流，Q=C·h^n 自由流式失效）——调节方向：hb_'
            'design（降低下游水深设计假定）或 b_throat（大档加深 ha）',
            'b_throat',
        ),
    ]
    ports = {
        PortRef(unit_id='test_bashi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_bashi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }

