"""municipal_ziwai 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

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
from waterprint.units_lib.municipal.ziwai import make_unit

"""municipal_ziwai 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

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
_UNIT_TEST_ID = 'test_ziwai'
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
    'n_channel': 2.0,
    'v_channel': 0.4,
    'b_c': 1.2,
    'n_lamp_module': 8.0,
    'l_module': 0.6,
    'l_stab': 1.2,
    'h_module': 0.5,
    'length_disc_step': 0.1,
    'factor.ziwai.dose': 30.0,
    'factor.ziwai.q_per_lamp': 40.0,
    'factor.ziwai.f_aging': 0.8,
    'factor.ziwai.t254_band.min': 0.55,
    'factor.ziwai.t254_band.max': 0.65,
    'factor.ziwai.velocity_band.min': 0.3,
    'factor.ziwai.velocity_band.max': 0.6,
    'factor.ziwai.t_exp_band.min': 5.0,
    'factor.ziwai.t_exp_band.max': 10.0,
    'factor.ziwai.fecal.c_in_design': 100000.0,
    'factor.ziwai.fecal.log_removal': 4.0,
    'factor.ziwai.superheight': 0.5,
    'factor.ziwai.wall_thickness_coef': 0.35,
    'factor.ziwai.elevation_loss': 0.2,
    'removal.ziwai.bod5.mod_default': 0.0,
    'removal.ziwai.cod.mod_default': 0.0,
    'removal.ziwai.ss.mod_default': 0.0,
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
        'q_c': 0.2816260416666666,
        'h_w_raw': 0.5867209201388888,
        'h_w': 0.6000000000000001,
        'v_channel_act': 0.3911472800925925,
        'n_lamp_raw': 63.365859374999985,
        'n_lamp': 64.0,
        'n_module_raw': 8.0,
        'n_module': 8.0,
        'n_module_series': 4.0,
        'l_lamp_zone': 2.4,
        'l_channel': 4.8,
        't_exp': 6.135796213211227,
        'c_fecal_out': 10.0,
        'h_submerge': 0.10000000000000009,
        'h_channel': 1.1,
        'v_concrete': 4.4352,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_ziwai', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_ziwai', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.4745,
        'CODCR': 16.50599,
        'SS': 0.2272045,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n_channel': 0.0},
         "单元 'municipal_ziwai' 参数 'n_channel' 必须 > 0：得到 0.0"),
        ({'length_disc_step': 0.0},
         "单元 'municipal_ziwai' 参数 'length_disc_step' 必须 > 0：得到 0.0"),
        ({'factor.ziwai.q_per_lamp': 0.0},
         "单元 'municipal_ziwai' 系数键 'factor.ziwai.q_per_lamp' 必须 > 0（单灯处理量/老化系数/粪"
         '大肠设计值物理域）'),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:13 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('ZW-F1',
         {
             'q_design': 0.5632520833333332,
             'n_channel': 2.0,
         },
         0.2816260416666666),
        ('ZW-F2',
         {
             'q_c': 0.2816260416666666,
             'v_channel': 0.4,
             'b_c': 1.2,
         },
         0.5867209201388888),
        ('ZW-F3',
         {
             'q_c': 0.2816260416666666,
             'b_c': 1.2,
             'h_w': 0.6000000000000001,
         },
         0.3911472800925925),
        ('ZW-F4',
         {
             'q_design': 0.5632520833333332,
             'q_per_lamp': 40.0,
             'f_aging': 0.8,
         },
         63.365859374999985),
        ('ZW-F5',
         {
             'n_lamp': 64.0,
             'n_lamp_module': 8.0,
         },
         8.0),
        ('ZW-F6',
         {
             'n_module': 8.0,
             'n_channel': 2.0,
         },
         4.0),
        ('ZW-F7',
         {
             'n_module_series': 4.0,
             'l_module': 0.6,
         },
         2.4),
        ('ZW-F8',
         {
             'l_stab': 1.2,
             'l_lamp_zone': 2.4,
         },
         4.8),
        ('ZW-F9',
         {
             'b_c': 1.2,
             'h_w': 0.6000000000000001,
             'l_lamp_zone': 2.4,
             'q_c': 0.2816260416666666,
         },
         6.135796213211227),
        ('ZW-F10',
         {
             'c_fecal_in': 100000.0,
             'n_log': 4.0,
         },
         10.0),
        ('ZW-F11',
         {
             'h_w': 0.6000000000000001,
             'h_module': 0.5,
         },
         0.10000000000000009),
        ('ZW-F12',
         {
             'h_super': 0.5,
             'h_w': 0.6000000000000001,
         },
         1.1),
        ('ZW-F13',
         {
             'l_channel': 4.8,
             'b_c': 1.2,
             'h_channel': 1.1,
             'n_channel': 2.0,
             'wall_coef': 0.35,
         },
         4.4352),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
