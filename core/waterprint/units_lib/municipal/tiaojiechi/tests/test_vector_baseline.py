"""municipal_tiaojiechi 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

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
from waterprint.units_lib.municipal.tiaojiechi import make_unit

"""municipal_tiaojiechi 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

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


def test_baseline_main_full_surface() -> None:
    """用例 main(默认主算例):dims/warnings/出流出质精确恒等。"""
    result = _compute()
    assert dict(result.dims) == {
        'v_total': 11586.9,
        'v1': 5793.45,
        'a1': 1158.69,
        'b_raw': 21.528492747984007,
        'b': 22.0,
        'l_raw': 52.66772727272728,
        'l': 53.0,
        'a_act': 1166.0,
        'v_act_total': 11660.0,
        't_reg_act': 8.050470790289033,
        'p_stir': 69.96,
        'q_pump1': 724.18125,
        'd_overflow': 0.9,
        'h_total': 5.5,
        'v_concrete': 4489.099999999999,
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


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'municipal_tiaojiechi' 参数 'n' 必须 > 0：得到 0.0"),
        ({'side_disc_step': 0.0},
         "单元 'municipal_tiaojiechi' 参数 'side_disc_step' 必须 > 0：得到 0.0"),
        ({'factor.tiaojiechi.overflow_velocity': -0.5},
         "单元 'municipal_tiaojiechi' 系数键 'factor.tiaojiechi.overflow_velocity' 必须 > 0（搅拌"
         '功率密度/溢流管流速物理域）'),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:13 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('TJ-F1',
         {
             'q_avg_daily': 0.40232291666666664,
             't_reg': 8.0,
         },
         11586.9),
        ('TJ-F2',
         {
             'v_total': 11586.9,
             'n': 2.0,
         },
         5793.45),
        ('TJ-F3',
         {
             'v1': 5793.45,
             'h2': 5.0,
         },
         1158.69),
        ('TJ-F4',
         {
             'a1': 1158.69,
             'ratio_lb': 2.5,
         },
         21.528492747984007),
        ('TJ-F5',
         {
             'a1': 1158.69,
             'B': 22.0,
         },
         52.66772727272728),
        ('TJ-F6',
         {
             'B': 22.0,
             'L': 53.0,
         },
         1166.0),
        ('TJ-F7',
         {
             'a_act': 1166.0,
             'h2': 5.0,
             'n': 2.0,
         },
         11660.0),
        ('TJ-F8',
         {
             'v_act_total': 11660.0,
             'q_avg_daily': 0.40232291666666664,
         },
         8.050470790289033),
        ('TJ-F9',
         {
             'v_act_total': 11660.0,
             'w_stir': 6.0,
         },
         69.96),
        ('TJ-F10',
         {
             'q_avg_daily': 0.40232291666666664,
             'n_pump_duty': 2.0,
         },
         724.18125),
        ('TJ-F11',
         {
             'q_design': 0.5632520833333332,
             'pi': 3.141592653589793,
             'v_overflow': 0.9,
         },
         0.892658218876174),
        ('TJ-F12',
         {
             'h_super': 0.5,
             'h2': 5.0,
         },
         5.5),
        ('TJ-F13',
         {
             'a_act': 1166.0,
             'h_total': 5.5,
             'n': 2.0,
             'wall_coef': 0.35,
         },
         4489.099999999999),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
