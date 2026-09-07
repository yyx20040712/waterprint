"""municipal_cass 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

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
from waterprint.contracts.unit_api import UnitContext, UnitResult
from waterprint.registry import formulas
from waterprint.units_lib.municipal.cass import make_unit

"""municipal_cass 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

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
_UNIT_TEST_ID = 'test_cass'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 123.2996,
    'CODCR': 199.9362,
    'SS': 93.2121,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n_pool': 4.0,
    't_cycle': 4.0,
    't_react': 2.0,
    't_settle': 1.0,
    't_draw': 1.0,
    'ns': 0.1,
    'x_mlss': 4000.0,
    't_selector': 0.75,
    'h2': 5.0,
    'ratio_lb': 2.5,
    'tn_eff': 15.0,
    'side_disc_step': 0.5,
    'factor.cass.ns_band.min': 0.05,
    'factor.cass.ns_band.max': 0.15,
    'factor.cass.mlss_band.min': 3000.0,
    'factor.cass.mlss_band.max': 5000.0,
    'factor.cass.sludge_age_band.min': 15.0,
    'factor.cass.sludge_age_band.max': 25.0,
    'factor.cass.draw_band.min': 1.0,
    'factor.cass.draw_band.max': 2.0,
    'factor.cass.selector_band.min': 0.5,
    'factor.cass.selector_band.max': 1.0,
    'factor.cass.yield.y': 0.5,
    'factor.cass.o2.a_prime': 0.5,
    'factor.cass.o2.b_prime': 0.1,
    'factor.cass.vss_ratio': 0.75,
    'factor.cass.sludge.moisture': 0.994,
    'factor.cass.decant.q_per_unit': 800.0,
    'factor.cass.superheight': 0.5,
    'factor.cass.wall_thickness_coef': 0.4,
    'factor.cass.elevation_loss': 0.5,
    'removal.cass.bod5.mod_default': 0.9,
    'removal.cass.cod.mod_default': 0.85,
    'removal.cass.ss.mod_default': 0.9,
    'removal.cass.nh3n.mod_default': 0.9,
    'removal.cass.tn.mod_default': 0.7,
    'removal.cass.tp.mod_default': 0.93,
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
        'n_cycle': 6.0,
        'v_draw': 1448.3625,
        'v_load': 10714.951014299999,
        'v_selector': 1086.271875,
        'v_bio': 11801.2228893,
        'h_draw_max': 1.6666666666666667,
        'a_draw': 869.0174999999999,
        'a_load': 590.061144465,
        'a_pool': 869.0174999999999,
        'h_draw': 1.6666666666666667,
        'v_pool': 4345.0875,
        'v_plant': 17380.35,
        't_phase_sum': 4.0,
        'q_decant': 1448.3625,
        'n_decant_raw': 1.810453125,
        'n_decant': 2.0,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'ns_act': 0.06789980000000001,
        'h_pool': 5.5,
        'l_pool_raw': 46.61055406235802,
        'l_pool': 47.0,
        'b_pool_raw': 18.64422162494321,
        'b_pool': 19.0,
        'v_concrete': 7647.353999999999,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_cass', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_cass', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 12.900000000000002,
        'TP': 0.4549999999999997,
    }


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n_pool': 0.0},
         "单元 'municipal_cass' 参数 'n_pool' 必须 > 0：得到 0.0"),
        ({'ns': 0.0},
         "单元 'municipal_cass' 参数 'ns' 必须 > 0：得到 0.0"),
        ({'t_cycle': 0.0},
         "单元 'municipal_cass' 参数 't_cycle' 必须 > 0：得到 0.0"),
        ({'t_cycle': 6.0},
         "单元 'municipal_cass' 时段和=周期不变性破坏：t_react+t_settle+t_draw = 4.0 ≠ t_cycle = 6"
         '.0（business-logic §8/CA-F13——时段分配须与周期档一致）'),
        ({'factor.cass.sludge.moisture': 1.0},
         "单元 'municipal_cass' 剩余污泥含水率须 ∈ (0,1)：得到 1.0"),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:27 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('CA-F1',
         {
             't_cycle': 4.0,
         },
         6.0),
        ('CA-F2',
         {
             'q_avg_daily': 0.40232291666666664,
             'n_pool': 4.0,
             'n_cycle': 6.0,
         },
         1448.3625),
        ('CA-F3',
         {
             'q_avg_daily': 0.40232291666666664,
             'bod5_in': 123.2996,
             'ns': 0.1,
             'x_mlss': 4000.0,
         },
         10714.951014299999),
        ('CA-F4',
         {
             'q_avg_daily': 0.40232291666666664,
             't_selector': 0.75,
         },
         1086.271875),
        ('CA-F5',
         {
             'v_load': 10714.951014299999,
             'v_selector': 1086.271875,
         },
         11801.2228893),
        ('CA-F6',
         {
             'h2': 5.0,
         },
         1.6666666666666667),
        ('CA-F7',
         {
             'v_draw': 1448.3625,
             'h_draw_max': 1.6666666666666667,
         },
         869.0174999999999),
        ('CA-F8',
         {
             'v_bio': 11801.2228893,
             'n_pool': 4.0,
             'h2': 5.0,
         },
         590.061144465),
        ('CA-F9',
         {
             'a_load': 590.061144465,
             'a_draw': 869.0174999999999,
         },
         869.0174999999999),
        ('CA-F11',
         {
             'a_pool': 869.0174999999999,
             'h2': 5.0,
         },
         4345.0875),
        ('CA-F10',
         {
             'v_draw': 1448.3625,
             'a_pool': 869.0174999999999,
         },
         1.6666666666666667),
        ('CA-F12',
         {
             'v_pool': 4345.0875,
             'n_pool': 4.0,
         },
         17380.35),
        ('CA-F14',
         {
             'v_draw': 1448.3625,
             't_draw': 1.0,
         },
         1448.3625),
        ('CA-F15',
         {
             'q_decant': 1448.3625,
             'q_per_decant': 800.0,
         },
         1.810453125),
        ('CA-F13',
         {
             't_react': 2.0,
             't_settle': 1.0,
             't_draw': 1.0,
         },
         4.0),
        ('CA-F16',
         {
             'q_avg_daily': 0.40232291666666664,
             'bod5_in': 123.2996,
             'bod5_out': 12.329959999999996,
             'y_yield': 0.5,
         },
         1928.6911825739996),
        ('CA-F17',
         {
             's_y': 1928.6911825739996,
             'p_moisture': 0.994,
         },
         321.4485304289997),
        ('CA-F18',
         {
             'v_load': 10714.951014299999,
             'x_mlss': 4000.0,
             's_y': 1928.6911825739996,
         },
         22.22222222222222),
        ('CA-F19',
         {
             'a_prime': 0.5,
             'q_avg_daily': 0.40232291666666664,
             'bod5_in': 123.2996,
             'bod5_out': 12.329959999999996,
             'b_prime': 0.1,
             'v_load': 10714.951014299999,
             'x_vss': 3000.0,
         },
         5143.176486863999),
        ('CA-F20',
         {
             'q_avg_daily': 0.40232291666666664,
             'tkn_in': 43.0,
             'tn_eff': 15.0,
         },
         4447.979172),
        ('CA-F21',
         {
             'q_avg_daily': 0.40232291666666664,
             'tkn_in': 43.0,
             'tn_eff': 15.0,
         },
         2783.6368559999996),
        ('CA-F22',
         {
             'o2_carbon': 5143.176486863999,
             'o2_nit': 4447.979172,
             'o2_denit': 2783.6368559999996,
         },
         6807.5188028640005),
        ('CA-F23',
         {
             'ns': 0.1,
             'v_bio': 11801.2228893,
             'v_plant': 17380.35,
         },
         0.06789980000000001),
        ('CA-F24',
         {
             'h_super': 0.5,
             'h2': 5.0,
         },
         5.5),
        ('CA-F25',
         {
             'a_pool': 869.0174999999999,
             'ratio_lb': 2.5,
         },
         46.61055406235802),
        ('CA-F26',
         {
             'a_pool': 869.0174999999999,
             'ratio_lb': 2.5,
         },
         18.64422162494321),
        ('CA-F27',
         {
             'a_pool': 869.0174999999999,
             'h_pool': 5.5,
             'n_pool': 4.0,
             'wall_coef': 0.4,
         },
         7647.353999999999),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
