"""municipal_gaomidu 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(c97bd24ee8)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-A 基线先行独立笔;task-13A-batch-plan §六)
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
#   abs=1e-2~1e-4)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
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
from waterprint.units_lib.municipal.gaomidu import make_unit

"""municipal_gaomidu 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(c97bd24ee8)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-A 基线先行独立笔;task-13A-batch-plan §六)
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
#   abs=1e-2~1e-4)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
#   全文本/出流值/公式级逐行值零锚定=重写等价性验收面缺位(锁窗
#   附加条件举证——批14 三件形态同款)。
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


def test_baseline_main_full_surface() -> None:
    """用例 main(默认主算例):dims/warnings/出流出质精确恒等。"""
    result = _compute()
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


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'municipal_gaomidu' 参数 'n' 必须 > 0：得到 0.0"),
        ({'q_surface': 0.0},
         "单元 'municipal_gaomidu' 参数 'q_surface' 必须 > 0：得到 0.0"),
        ({'factor.gaomidu.g_mix': 0.0},
         "单元 'municipal_gaomidu' 系数键 'factor.gaomidu.g_mix' 必须 > 0（G 值/含固率/药剂投加量"
         '物理域）'),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:20 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('GM-F1',
         {
             'q_design': 0.5632520833333332,
             'n': 2.0,
         },
         1013.8537499999998),
        ('GM-F2',
         {
             'q1h': 1013.8537499999998,
             'q_surface': 15.0,
         },
         67.59024999999998),
        ('GM-F3',
         {
             'a_incl_req': 67.59024999999998,
         },
         8.22132896799538),
        ('GM-F4',
         {
             'B': 8.5,
         },
         72.25),
        ('GM-F5',
         {
             'q1h': 1013.8537499999998,
             'a_act': 72.25,
         },
         14.032577854671278),
        ('GM-F6',
         {
             'q1h': 1013.8537499999998,
             't_mix': 1.5,
         },
         25.346343749999996),
        ('GM-F7',
         {
             'q1h': 1013.8537499999998,
             't_floc': 12.0,
         },
         202.77074999999996),
        ('GM-F8',
         {
             'g_mix': 500.0,
             'v_mix': 25.346343749999996,
         },
         6.336585937499999),
        ('GM-F9',
         {
             'g_floc': 50.0,
             'v_floc': 202.77074999999996,
         },
         0.5069268749999999),
        ('GM-F10',
         {
             'g_floc': 50.0,
             't_floc': 12.0,
         },
         36000.0),
        ('GM-F12',
         {
             'q_avg_daily': 0.40232291666666664,
             'ss_in': 4.660605,
             'ss_out': 0.6990907500000002,
         },
         137.705008389975),
        ('GM-F11',
         {
             'r_sludge': 0.04,
             'q_design_h': 2027.7074999999995,
         },
         81.10829999999999),
        ('GM-F13',
         {
             's_dry': 137.705008389975,
             'c_sludge': 20.0,
         },
         6.8852504194987505),
        ('GM-F14',
         {
             'q_avg_daily': 0.40232291666666664,
             'dose_pac': 30.0,
         },
         1042.821),
        ('GM-F15',
         {
             'q_avg_daily': 0.40232291666666664,
             'dose_pam': 1.0,
         },
         34.7607),
        ('GM-F16',
         {
             'l_tube': 1.0,
         },
         0.8660254),
        ('GM-F17',
         {
             'h_clear': 1.2,
             'h_tube_zone': 0.8660254,
             'h_buffer': 1.2,
             'h_thick': 2.0,
         },
         5.2660254),
        ('GM-F18',
         {
             'h_super': 0.3,
             'h_settle': 5.2660254,
         },
         5.5660254),
        ('GM-F19',
         {
             'v_floc': 202.77074999999996,
             'a_act': 72.25,
         },
         2.8065155709342555),
        ('GM-F20',
         {
             'a_act': 72.25,
             'h_total': 5.6000000000000005,
             'n': 2.0,
             'wall_coef': 0.35,
         },
         283.21999999999997),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
