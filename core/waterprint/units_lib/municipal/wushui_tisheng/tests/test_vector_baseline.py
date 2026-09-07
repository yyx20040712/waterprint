"""municipal_wushui_tisheng 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(a684dc1689)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-C 基线先行独立笔;task-13C-batch-plan §五/§六)
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
#   abs=1e-2~1e-9)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
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
from waterprint.units_lib.municipal.wushui_tisheng import make_unit

"""municipal_wushui_tisheng 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(a684dc1689)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-C 基线先行独立笔;task-13C-batch-plan §五/§六)
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
#   abs=1e-2~1e-9)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
#   全文本/出流值/公式级逐行值零锚定=重写等价性验收面缺位(锁窗
#   附加条件举证——批14 三件形态同款)。
# ════════════════════════════════════════════════════════════


# ── 冻结入参(重写前包内 test_compute 权威夹具的 round-trip 字面量化;
#    变体件与本件同源副本——包内 tests 无包语义,自包含纪律) ──
_UNIT_TEST_ID = 'test_wushui'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 198.0,
    'CODCR': 344.0,
    'SS': 237.0,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'h_static': 10.0,
    'v_pipe': 1.2,
    'l_pipe': 100.0,
    'n_standby': 1.0,
    'h_well': 2.0,
    't_well': 10.0,
    'dia_disc_step': 0.1,
    'g_gravity': 9.81,
    'sec_per_hour': 3600.0,
    'factor.wushui_tisheng.pump.q_per_unit': 1100.0,
    'factor.wushui_tisheng.pump.q_flow_band.min': 400.0,
    'factor.wushui_tisheng.pump.q_flow_band.max': 1500.0,
    'factor.wushui_tisheng.pump.free_head': 1.5,
    'factor.wushui_tisheng.pump.start_band.max': 6.0,
    'factor.wushui_tisheng.pipe.resistance.dn300': 1.025,
    'factor.wushui_tisheng.pipe.resistance.dn350': 0.4529,
    'factor.wushui_tisheng.pipe.resistance.dn400': 0.2232,
    'factor.wushui_tisheng.pipe.resistance.dn450': 0.1195,
    'factor.wushui_tisheng.pipe.resistance.dn500': 0.06839,
    'factor.wushui_tisheng.pipe.resistance.dn600': 0.02602,
    'factor.wushui_tisheng.pipe.resistance.dn700': 0.01149,
    'factor.wushui_tisheng.pipe.resistance.dn800': 0.005665,
    'factor.wushui_tisheng.pipe.velocity_band.min': 0.7,
    'factor.wushui_tisheng.pipe.velocity_band.max': 1.5,
    'factor.wushui_tisheng.pipe.zeta_total': 5.0,
    'factor.wushui_tisheng.well.t_band.min': 5.0,
    'factor.wushui_tisheng.well.t_band.max': 15.0,
    'factor.wushui_tisheng.well.depth_band.min': 1.5,
    'factor.wushui_tisheng.well.depth_band.max': 2.5,
    'factor.wushui_tisheng.superheight': 0.5,
    'factor.wushui_tisheng.wall_thickness_coef': 0.35,
    'factor.wushui_tisheng.elevation_loss': 0.3,
    'removal.wushui_tisheng.bod5.mod_default': 0.0,
    'removal.wushui_tisheng.cod.mod_default': 0.0,
    'removal.wushui_tisheng.ss.mod_default': 0.0,
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
        'q_design_h': 2027.7074999999995,
        'n_pump_raw': 1.8433704545454541,
        'n_pump_duty': 2.0,
        'q_pump': 1013.8537499999998,
        'n_pump_total': 3.0,
        'q_pump_si': 0.2816260416666666,
        'd_pipe_raw': 0.5466392880493856,
        'd_pipe': 0.6000000000000001,
        'v_pipe_act': 0.9960483707971302,
        'h_friction': 0.20637301755126078,
        'h_local': 0.25283189525168637,
        'h_loss': 0.4592049128029472,
        'h_pump': 11.959204912802948,
        'v_well': 168.97562499999995,
        'a_well': 84.48781249999998,
        'n_start': 1.5,
        'h_well_total': 2.5,
        'v_concrete': 73.92683593749997,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_wushui', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_wushui', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 198.0,
        'CODCR': 344.0,
        'SS': 237.0,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'h_static': 0.0},
         "单元 'municipal_wushui_tisheng' 参数 'h_static' 必须 > 0：得到 0.0"),
        ({'dia_disc_step': 0.0},
         "单元 'municipal_wushui_tisheng' 参数 'dia_disc_step' 必须 > 0：得到 0.0"),
        ({'v_pipe': 10.0},
         "单元 'municipal_wushui_tisheng' DN 档 0.2 越比阻表覆盖面（录入 DN300~DN800；扩档待数据包"
         '增补键——起草表追认点 4）'),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:14 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('TS-F1',
         {
             'q_design_h': 2027.7074999999995,
             'q_per_pump': 1100.0,
         },
         1.8433704545454541),
        ('TS-F2',
         {
             'q_design_h': 2027.7074999999995,
             'n_pump_duty': 2.0,
         },
         1013.8537499999998),
        ('TS-F3',
         {
             'n_pump_duty': 2.0,
             'n_standby': 1.0,
         },
         3.0),
        ('TS-F4',
         {
             'q_pump_si': 0.2816260416666666,
             'v_pipe': 1.2,
         },
         0.5466392880493856),
        ('TS-F6',
         {
             'a_pipe': 0.02602,
             'l_pipe': 100.0,
             'q_pump_si': 0.2816260416666666,
         },
         0.20637301755126078),
        ('TS-F5',
         {
             'q_pump_si': 0.2816260416666666,
             'd_pipe': 0.6000000000000001,
         },
         0.9960483707971302),
        ('TS-F7',
         {
             'zeta_total': 5.0,
             'v_pipe_act': 0.9960483707971302,
             'g_gravity': 9.81,
         },
         0.25283189525168637),
        ('TS-F8',
         {
             'h_friction': 0.20637301755126078,
             'h_local': 0.25283189525168637,
         },
         0.4592049128029472),
        ('TS-F9',
         {
             'h_static': 10.0,
             'h_loss': 0.4592049128029472,
             'h_free': 1.5,
         },
         11.959204912802948),
        ('TS-F10',
         {
             'q_pump_si': 0.2816260416666666,
             't_well': 10.0,
         },
         168.97562499999995),
        ('TS-F11',
         {
             'v_well': 168.97562499999995,
             'h_well': 2.0,
         },
         84.48781249999998),
        ('TS-F13',
         {
             'h_super': 0.5,
             'h_well': 2.0,
         },
         2.5),
        ('TS-F12',
         {
             'q_pump_si': 0.2816260416666666,
             'v_well': 168.97562499999995,
         },
         1.5),
        ('TS-F14',
         {
             'a_well': 84.48781249999998,
             'h_well_total': 2.5,
             'wall_coef': 0.35,
         },
         73.92683593749997),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
