"""municipal_chuchenchi 向量化重写前基线锚(批 13-B 基线先行独立笔·件 1/2)。

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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.registry import formulas
from waterprint.units_lib.municipal.chuchenchi import make_unit

"""municipal_chuchenchi 向量化重写前基线锚(批 13-B 基线先行独立笔·件 1/2)。

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


def test_baseline_main_full_surface() -> None:
    """用例 main(默认主算例):dims/warnings/出流出质精确恒等。"""
    result = _compute()
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
        'v_need': 81.00294611174992,
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


_QUALITY_DOMAIN: dict[str, float] = {
    'BOD5': 160.0,
}

def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'municipal_chuchenchi' 参数 'n' 必须 > 0：得到 0.0"),
        ({'q_prime': 0.0},
         "单元 'municipal_chuchenchi' 参数 'q_prime' 必须 > 0：得到 0.0"),
        ({'length_disc_step': 0.0},
         "单元 'municipal_chuchenchi' 参数 'length_disc_step' 必须 > 0：得到 0.0"),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message

    in_ref = PortRef(unit_id=_UNIT_TEST_ID, port_id=_IN_PORT)
    ctx = UnitContext(
        unit_id=_UNIT_TEST_ID,
        inflows={in_ref: WaterFlow(**_FLOW_ARGS)},
        inqualities={in_ref: WaterQuality(dict(_QUALITY_DOMAIN))},
        params=dict(_MAIN_PARAMS),
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=_Sink(),
    )
    with pytest.raises(InvalidUnitConfig) as excinfo:
        make_unit().compute(ctx)
    assert str(excinfo.value) == (
        "单元 'test_chuchenchi' 入流缺 SS 浓度（CC-F10 排泥量计算前提，GR-09）"
    )


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:18 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('CC-F1',
         {
             'q_design': 0.5632520833333332,
             'n': 2.0,
         },
         1013.8537499999998),
        ('CC-F2',
         {
             'q1h': 1013.8537499999998,
             'q_prime': 2.3,
         },
         440.8059782608695),
        ('CC-F3',
         {
             'f_req': 440.8059782608695,
             'pi': 3.141592653589793,
         },
         23.690749314392896),
        ('CC-F4',
         {
             'pi': 3.141592653589793,
             'D': 24.0,
         },
         452.3893421169302),
        ('CC-F5',
         {
             'q1h': 1013.8537499999998,
             'f_act': 452.3893421169302,
         },
         2.2411088317327033),
        ('CC-F6',
         {
             'q_prime_act': 2.2411088317327033,
             't_settle': 1.2,
         },
         2.689330598079244),
        ('CC-F7',
         {
             'D': 24.0,
             'h2': 2.689330598079244,
         },
         8.924153845994658),
        ('CC-F8',
         {
             'q1': 0.2816260416666666,
             'pi': 3.141592653589793,
             'v_center': 0.3,
         },
         1.0932785754741448),
        ('CC-F9',
         {
             'q1': 0.2816260416666666,
             'pi': 3.141592653589793,
             'D': 24.0,
         },
         1.9487902884632204),
        ('CC-F10',
         {
             'q_avg_daily': 0.40232291666666664,
             'ss_in': 186.4242,
             'ss_out': 93.2121,
             'n': 2.0,
         },
         1620.058922235),
        ('CC-F11',
         {
             's_dry_1': 1620.058922235,
             'p_moisture': 0.96,
         },
         40.50147305587496),
        ('CC-F12',
         {
             's_wet_1': 40.50147305587496,
             't_sludge': 2.0,
         },
         81.00294611174992),
        ('CC-F13',
         {
             'pi': 3.141592653589793,
             'h5': 1.5,
             'r1': 1.8,
             'r2': 0.8,
         },
         8.35663645854885),
        ('CC-F14',
         {
             'i_slope': 0.05,
             'D': 24.0,
             'r1': 1.8,
         },
         0.51),
        ('CC-F15',
         {
             'pi': 3.141592653589793,
             'h4': 0.6000000000000001,
             'D': 24.0,
             'r1': 1.8,
         },
         106.08530072642016),
        ('CC-F16',
         {
             'v1_hopper': 8.35663645854885,
             'v2_cone': 106.08530072642016,
         },
         114.441937184969),
        ('CC-F17',
         {
             'h_super': 0.3,
             'h2': 2.689330598079244,
             'h_buf': 0.3,
             'h4': 0.6000000000000001,
             'h5': 1.5,
         },
         5.389330598079244),
        ('CC-F18',
         {
             'pi': 3.141592653589793,
             'D': 24.0,
             'h_total': 5.4,
             'n': 2.0,
             'wall_coef': 0.4,
         },
         1954.3219579451388),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
