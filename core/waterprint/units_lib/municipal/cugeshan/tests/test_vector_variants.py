"""municipal_cugeshan 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

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
from waterprint.units_lib.municipal.cugeshan import make_unit

"""municipal_cugeshan 向量化重写前基线锚·参数变体面(批 13-C·件 2/2)。

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
_UNIT_TEST_ID = 'test_cugeshan'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 3.0,
    'b': 0.065,
    'alpha': 75.0,
    'h': 0.6,
    'v': 0.8,
    'v1': 0.7,
    's': 0.01,
    'bar_shape': 0.0,
    'g_gravity': 9.81,
    'length_disc_step': 0.1,
    'factor.screen.beta.rect': 2.42,
    'factor.screen.beta.semicircle': 1.97,
    'factor.screen.beta.circle': 1.83,
    'factor.screen.headloss.k': 3.0,
    'factor.screen.superheight': 0.3,
    'factor.screen.trough_width_margin': 0.2,
    'factor.screen.trough_length.l3_fixed': 1.0,
    'factor.screen.trough_length.l4_fixed': 0.5,
    'factor.screen.trough_length.drop_constant': 0.2,
    'factor.screen.slag.moisture': 0.8,
    'factor.screen.mech_clean_threshold': 0.2,
    'factor.screen.velocity_band.v.min': 0.6,
    'factor.screen.velocity_band.v.max': 1.0,
    'factor.screen.velocity_band.v1.min': 0.4,
    'factor.screen.velocity_band.v1.max': 0.9,
    'factor.screen.wall_thickness_coef': 0.3,
    'factor.cugeshan.w1_slag': 0.02,
    'removal.cugeshan.bod5.mod_default': 0.05,
    'removal.cugeshan.cod.mod_default': 0.05,
    'removal.cugeshan.ss.mod_default': 0.05,
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
    'v': 0.5,
}

_VAR2_OVERRIDES: dict[str, float] = {
    'v1': 0.2,
}

_VAR3_OVERRIDES: dict[str, float] = {
    'alpha': 75.0,
}

_VAR4_OVERRIDES: dict[str, float] = {
    'b': 0.012,
}

def test_baseline_var1_full_surface() -> None:
    """用例 var1({'v': 0.5}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR1_OVERRIDES)
    assert dict(result.dims) == {
        'q': 0.1877506944444444,
        'n_gap': 10.0,
        'B': 1.0,
        'B1': 0.5,
        'v_checked': 0.4731390941435008,
        'v1_checked': 0.625835648148148,
        'xi': 0.19949448329320632,
        'h1': 0.00659590798309007,
        'H': 1.0,
        'L': 1.9000000000000001,
        'w_slag': 0.6952139999999999,
        'mech_clean': 1.0,
        'ds_slag': 139.04279999999994,
        'v_concrete': 1.71,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.3（条文号待核对原文）；factor.screen.velocity_band.v.min~factor.scre'
            'en.velocity_band.v.max',
            '校核流速 0.4731 m/s 越出建议带 [0.6, 1.0] m/s（参数 v——调节过栅/栅前流速设计值）',
            'v',
        ),
    ]
    ports = {
        PortRef(unit_id='test_cugeshan', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    assert result.outqualities[PortRef(unit_id='test_cugeshan', port_id='out')].concentrations == {}


def test_baseline_var2_full_surface() -> None:
    """用例 var2({'v1': 0.2}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR2_OVERRIDES)
    assert dict(result.dims) == {
        'q': 0.1877506944444444,
        'n_gap': 6.0,
        'B': 0.7000000000000001,
        'B1': 1.6,
        'v_checked': 0.7885651569058347,
        'v1_checked': 0.19557364004629624,
        'xi': 0.19949448329320632,
        'h1': 0.01832196661969464,
        'H': 1.0,
        'L': 1.6,
        'w_slag': 0.6952139999999999,
        'mech_clean': 1.0,
        'ds_slag': 139.04279999999994,
        'v_concrete': 1.008,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
        (
            "WARN",
            'GB 50014-2021 §6.3（条文号待核对原文）；factor.screen.velocity_band.v1.min~factor.scr'
            'een.velocity_band.v1.max',
            '校核流速 0.1956 m/s 越出建议带 [0.4, 0.9] m/s（参数 v1——调节过栅/栅前流速设计值）',
            'v1',
        ),
    ]
    ports = {
        PortRef(unit_id='test_cugeshan', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    assert result.outqualities[PortRef(unit_id='test_cugeshan', port_id='out')].concentrations == {}


def test_baseline_var3_full_surface() -> None:
    """用例 var3({'alpha': 75.0}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR3_OVERRIDES)
    assert dict(result.dims) == {
        'q': 0.1877506944444444,
        'n_gap': 6.0,
        'B': 0.7000000000000001,
        'B1': 0.5,
        'v_checked': 0.7885651569058347,
        'v1_checked': 0.625835648148148,
        'xi': 0.19949448329320632,
        'h1': 0.01832196661969464,
        'H': 1.0,
        'L': 1.8,
        'w_slag': 0.6952139999999999,
        'mech_clean': 1.0,
        'ds_slag': 139.04279999999994,
        'v_concrete': 1.1340000000000001,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_cugeshan', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    assert result.outqualities[PortRef(unit_id='test_cugeshan', port_id='out')].concentrations == {}


def test_baseline_var4_full_surface() -> None:
    """用例 var4({'b': 0.012}):dims/warnings/出流出质精确恒等。"""
    result = _compute(_VAR4_OVERRIDES)
    assert dict(result.dims) == {
        'q': 0.1877506944444444,
        'n_gap': 33.0,
        'B': 1.0,
        'B1': 0.5,
        'v_checked': 0.776617199983019,
        'v1_checked': 0.625835648148148,
        'xi': 1.897755991576741,
        'h1': 0.1690520379296253,
        'H': 1.1,
        'L': 1.9000000000000001,
        'w_slag': 0.6952139999999999,
        'mech_clean': 1.0,
        'ds_slag': 139.04279999999994,
        'v_concrete': 1.8810000000000002,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_cugeshan', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    assert result.outqualities[PortRef(unit_id='test_cugeshan', port_id='out')].concentrations == {}

