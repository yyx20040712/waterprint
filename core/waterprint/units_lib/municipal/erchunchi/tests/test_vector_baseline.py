"""municipal_erchunchi 向量化重写前基线锚(批 13-B 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(38fc4b4390)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-B 基线先行独立笔;task-13B-batch-plan §五/§六)
#
# 【锚层级】①主算例全表面(dims 全键/warnings 全量/出流出质全端口
#   值)——浮点 round-trip 字面量**精确 ==**(非 approx:末位 ulp 漂移
#   即红=向量化等价性验收面);②域拒消息逐字锚;③公式级逐行锚
#   (每条公式=主算例 golden 路径绑定+结果精确值——公式核漂移与
#   单元接线漂移分离定位)。
# 【即绿注记】本件由生成器(.workflow/b13-probe/baseline_gen.py)于
#   重写前树态运行产出,对当前实现即绿(B15 覆盖补强先例);向量化
#   重写后必须全数恒等——漂移=R 轮(两轮修不复=整批回滚上呈)。
# 【4b 举证】包内 test_compute golden 锚为容差锚(pytest.approx
#   abs=1e-2~1e-5)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
#   全文本/出流值/公式级逐行值零锚定=重写等价性验收面缺位(锁窗
#   附加条件举证——批14 三件形态同款)。
# ════════════════════════════════════════════════════════════


from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.registry import formulas
from waterprint.units_lib.municipal.erchunchi import make_unit

"""municipal_erchunchi 向量化重写前基线锚(批 13-B 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(38fc4b4390)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-B 基线先行独立笔;task-13B-batch-plan §五/§六)
#
# 【锚层级】①主算例全表面(dims 全键/warnings 全量/出流出质全端口
#   值)——浮点 round-trip 字面量**精确 ==**(非 approx:末位 ulp 漂移
#   即红=向量化等价性验收面);②域拒消息逐字锚;③公式级逐行锚
#   (每条公式=主算例 golden 路径绑定+结果精确值——公式核漂移与
#   单元接线漂移分离定位)。
# 【即绿注记】本件由生成器(.workflow/b13-probe/baseline_gen.py)于
#   重写前树态运行产出,对当前实现即绿(B15 覆盖补强先例);向量化
#   重写后必须全数恒等——漂移=R 轮(两轮修不复=整批回滚上呈)。
# 【4b 举证】包内 test_compute golden 锚为容差锚(pytest.approx
#   abs=1e-2~1e-5)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
#   全文本/出流值/公式级逐行值零锚定=重写等价性验收面缺位(锁窗
#   附加条件举证——批14 三件形态同款)。
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


def test_baseline_main_full_surface() -> None:
    """用例 main(默认主算例):dims/warnings/出流出质精确恒等。"""
    result = _compute()
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
        'v_check': 3960.762938013331,
        't_hrt': 3.906641306020057,
        'q_return_sludge': 1013.8537499999998,
        'q_weir': 1.0932238203574165,
        'd_center': 1.6,
        'h4': 1.0,
        'h_total': 4.6000000000000005,
        'v_concrete': 4858.535870629687,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
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


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'municipal_erchunchi' 参数 'n' 必须 > 0：得到 0.0"),
        ({'q_nom': 0.0},
         "单元 'municipal_erchunchi' 参数 'q_nom' 必须 > 0：得到 0.0"),
        ({'dia_disc_step': 0.0},
         "单元 'municipal_erchunchi' 参数 'dia_disc_step' 必须 > 0：得到 0.0"),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:15 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('EC-F1',
         {
             'q_design': 0.5632520833333332,
             'n': 2.0,
         },
         1013.8537499999998),
        ('EC-F2',
         {
             'q1h': 1013.8537499999998,
             'q_nom': 1.2,
         },
         844.8781249999998),
        ('EC-F3',
         {
             'r_external': 1.0,
             'q1h': 1013.8537499999998,
             'x_mlss': 4000.0,
         },
         194659.91999999995),
        ('EC-F4',
         {
             'm_solid': 194659.91999999995,
             'g_max': 150.0,
         },
         1297.7327999999998),
        ('EC-F5',
         {
             'a_q': 844.8781249999998,
             'a_solid': 1297.7327999999998,
         },
         1297.7327999999998),
        ('EC-F6',
         {
             'a_tank': 1297.7327999999998,
             'pi': 3.141592653589793,
         },
         40.64879726953662),
        ('EC-F7',
         {
             'pi': 3.141592653589793,
             'D': 41.0,
         },
         1320.2543126711105),
        ('EC-F8',
         {
             'q1h': 1013.8537499999998,
             'a_act': 1320.2543126711105,
         },
         0.7679230738120388),
        ('EC-F9',
         {
             'm_solid': 194659.91999999995,
             'a_act': 1320.2543126711105,
         },
         147.44123017191146),
        ('EC-F10',
         {
             'x_mlss': 4000.0,
             'r_external': 1.0,
         },
         8000.0),
        ('EC-F13',
         {
             'i_slope': 0.05,
             'D': 41.0,
             'r_pit': 1.0,
         },
         0.9750000000000001),
        ('EC-F14',
         {
             'h_super': 0.3,
             'h2': 3.0,
             'h_buf': 0.3,
             'h4': 1.0,
         },
         4.6),
        ('EC-F11',
         {
             'q1': 0.2816260416666666,
             'pi': 3.141592653589793,
             'D': 41.0,
         },
         1.0932238203574165),
        ('EC-F12',
         {
             'r_external': 1.0,
             'q1': 0.2816260416666666,
             'pi': 3.141592653589793,
             'v_center': 0.3,
         },
         1.5461293888874728),
        ('EC-F15',
         {
             'pi': 3.141592653589793,
             'D': 41.0,
             'h_total': 4.6000000000000005,
             'n': 2.0,
             'wall_coef': 0.4,
         },
         4858.535870629687),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
