"""municipal_chenshachi 向量化重写前基线锚(批 13-B 基线先行独立笔·件 1/2)。

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
from waterprint.units_lib.municipal.chenshachi import make_unit

"""municipal_chenshachi 向量化重写前基线锚(批 13-B 基线先行独立笔·件 1/2)。

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
_UNIT_TEST_ID = 'test_chenshachi'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 2.0,
    'q_surf': 150.0,
    't_retention': 30.0,
    't_clean': 2.0,
    'theta': 55.0,
    'd_r': 0.5,
    'b_channel': 0.8,
    'v_channel': 1.0,
    'length_disc_step': 0.1,
    'sec_per_hour': 3600.0,
    'factor.chenshachi.sand_yield_x': 30.0,
    'factor.chenshachi.hopper.safety': 1.5,
    'factor.chenshachi.buffer_h3': 0.5,
    'factor.chenshachi.superheight': 0.3,
    'factor.chenshachi.grit.moisture': 0.6,
    'factor.chenshachi.grit.vs': 0.05,
    'factor.chenshachi.grit.density': 1600.0,
    'factor.chenshachi.channel.straight_mult': 7.0,
    'factor.chenshachi.channel.straight_min': 4.5,
    'factor.chenshachi.channel.outlet_mult': 2.0,
    'factor.chenshachi.surface_load_band.min': 150.0,
    'factor.chenshachi.surface_load_band.max': 200.0,
    'factor.chenshachi.retention_band.min': 25.0,
    'factor.chenshachi.retention_band.max': 60.0,
    'factor.chenshachi.h2_band.min': 1.0,
    'factor.chenshachi.h2_band.max': 2.0,
    'factor.chenshachi.ratio_dh2_band.min': 2.0,
    'factor.chenshachi.ratio_dh2_band.max': 2.5,
    'factor.chenshachi.wall_thickness_coef': 0.4,
    'factor.chenshachi.hopper_upper_ratio': 0.5,
    'removal.chenshachi.bod5.mod_default': 0.05,
    'removal.chenshachi.cod.mod_default': 0.05,
    'removal.chenshachi.ss.mod_default': 0.1,
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
        'd': 3.0,
        'h2': 1.25,
        'ratio_dh2': 2.4,
        'v_eff': 8.835729338221293,
        't_actual': 31.373978364824968,
        'v_sand': 0.5214104999999999,
        'v_hopper': 1.5642314999999996,
        'd_upper': 1.5,
        'h4': 0.3501037691048549,
        'v_cone': 0.29788509535793384,
        'h_cyl': 0.8,
        'v_storage': 1.7116017894733409,
        'h_total': 3.3000000000000003,
        'a_channel': 0.2816260416666666,
        'h_channel': 0.35203255208333323,
        'ratio_bh': 2.2725171160041584,
        'l_straight': 5.6000000000000005,
        'b_outlet': 1.6,
        'q_wet': 1.0428209999999998,
        'ds_grit': 667.4054399999999,
        'v_concrete': 18.661060362323372,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_chenshachi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_chenshachi', port_id='out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'municipal_chenshachi' 参数 'n' 必须 > 0：得到 0.0"),
        ({'q_surf': 0.0},
         "单元 'municipal_chenshachi' 参数 'q_surf' 必须 > 0：得到 0.0"),
        ({'length_disc_step': 0.0},
         "单元 'municipal_chenshachi' 的 length_disc_step 必须 > 0：得到 0.0"),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:18 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('CS-F1',
         {
             'q_design': 0.5632520833333332,
             'n': 2.0,
         },
         0.2816260416666666),
        ('CS-F2',
         {
             'q1': 0.2816260416666666,
             'sec_per_hour': 3600.0,
             'pi': 3.141592653589793,
             'q_surf': 150.0,
         },
         2.9335742557251865),
        ('CS-F3',
         {
             'q_surf': 150.0,
             't_retention': 30.0,
         },
         1.25),
        ('CS-F5',
         {
             'pi': 3.141592653589793,
             'd': 3.0,
             'h2': 1.25,
         },
         8.835729338221293),
        ('CS-F4',
         {
             'd': 3.0,
             'h2': 1.25,
         },
         2.4),
        ('CS-F6',
         {
             'v_eff': 8.835729338221293,
             'q1': 0.2816260416666666,
         },
         31.373978364824968),
        ('CS-F7',
         {
             'q_avg_daily': 0.40232291666666664,
             'x_sand': 30.0,
             'n': 2.0,
         },
         0.5214104999999999),
        ('CS-F8',
         {
             'v_sand': 0.5214104999999999,
             't_clean': 2.0,
             'safety': 1.5,
         },
         1.5642314999999996),
        ('CS-F9',
         {
             'upper_ratio': 0.5,
             'd': 3.0,
         },
         1.5),
        ('CS-F10',
         {
             'd_upper': 1.5,
             'd_r': 0.5,
             'tan_theta': 1.4281480067421144,
         },
         0.3501037691048549),
        ('CS-F11',
         {
             'pi': 3.141592653589793,
             'h4': 0.3501037691048549,
             'd_upper': 1.5,
             'd_r': 0.5,
         },
         0.29788509535793384),
        ('CS-F12',
         {
             'v_hopper': 1.5642314999999996,
             'v_cone': 0.29788509535793384,
             'pi': 3.141592653589793,
             'd_upper': 1.5,
         },
         0.716605475432655),
        ('CS-F13',
         {
             'h1_super': 0.3,
             'h2': 1.25,
             'h3_buffer': 0.5,
             'h4': 0.3501037691048549,
             'h_cyl': 0.8,
         },
         3.200103769104855),
        ('CS-F14',
         {
             'q1': 0.2816260416666666,
             'v_channel': 1.0,
             'b_channel': 0.8,
         },
         0.35203255208333323),
        ('CS-F15',
         {
             'straight_mult': 7.0,
             'b_channel': 0.8,
             'straight_min': 4.5,
         },
         5.6000000000000005),
        ('CS-F16',
         {
             'outlet_mult': 2.0,
             'b_channel': 0.8,
         },
         1.6),
        ('CS-F17',
         {
             'v_sand': 0.5214104999999999,
             'moisture': 0.6,
             'grit_density': 1600.0,
             'n': 2.0,
         },
         667.4054399999999),
        ('CS-F18',
         {
             'pi': 3.141592653589793,
             'd': 3.0,
             'h_total': 3.3000000000000003,
             'n': 2.0,
             'wall_coef': 0.4,
         },
         18.661060362323372),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
