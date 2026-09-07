"""municipal_aao 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

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
from waterprint.units_lib.municipal.aao import make_unit

"""municipal_aao 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

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
_UNIT_TEST_ID = 'test_aao'
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
    'n': 2.0,
    'ns': 0.1,
    'x_mlss': 4000.0,
    't_p': 1.5,
    'r_external': 1.0,
    'r_internal': 2.0,
    'tn_eff': 15.0,
    'sec_per_hour': 3600.0,
    'h2': 5.0,
    'ratio_lb': 2.5,
    'side_disc_step': 0.5,
    'factor.aao.ns_band.min': 0.05,
    'factor.aao.ns_band.max': 0.15,
    'factor.aao.mlss_band.min': 3500.0,
    'factor.aao.mlss_band.max': 4500.0,
    'factor.aao.sludge_age_band.min': 11.0,
    'factor.aao.sludge_age_band.max': 23.0,
    'factor.aao.hrt_anaerobic_band.min': 1.0,
    'factor.aao.hrt_anaerobic_band.max': 2.0,
    'factor.aao.hrt_anoxic_band.min': 2.0,
    'factor.aao.hrt_anoxic_band.max': 4.0,
    'factor.aao.k_denit': 0.05,
    'factor.aao.o2.a_prime': 0.5,
    'factor.aao.o2.b_prime': 0.1,
    'factor.aao.vss_ratio': 0.75,
    'factor.aao.yield.y': 0.5,
    'factor.aao.r_external_band.min': 0.5,
    'factor.aao.r_external_band.max': 1.0,
    'factor.aao.r_internal_band.min': 1.0,
    'factor.aao.r_internal_band.max': 3.0,
    'factor.aao.sludge.moisture': 0.994,
    'factor.aao.elevation_loss': 0.5,
    'factor.aao.superheight': 0.3,
    'removal.aao.bod5.mod_default': 0.9,
    'removal.aao.cod.mod_default': 0.85,
    'removal.aao.ss.mod_default': 0.9,
    'removal.aao.nh3n.mod_default': 0.9,
    'removal.aao.tn.mod_default': 0.75,
    'removal.aao.tp.mod_default': 0.93,
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
        'v_o': 10714.951014299999,
        't_o': 7.397975999999999,
        'v_anaerobic': 2172.54375,
        'delta_n': 28.0,
        'v_anoxic': 4866.498,
        't_n': 3.36,
        'v_total': 17753.992764299997,
        't_total': 12.257976,
        'v_o_series': 5357.475507149999,
        's_y': 1928.6911825739996,
        'q_wet': 321.4485304289997,
        'theta_c': 22.22222222222222,
        'x_vss': 3000.0,
        'o2_carbon': 5143.176486863999,
        'o2_nit': 4447.979172,
        'o2_denit': 2783.6368559999996,
        'o2_total': 6807.5188028640005,
        'q_return': 2027.7074999999995,
        'q_internal': 2896.725,
        'h2': 5.0,
        'a_pool': 3550.7985528599993,
        'h_pool': 5.3,
        'l_pool_raw': 94.21781350758464,
        'b_pool_raw': 37.68712540303385,
        'l_pool': 94.5,
        'b_pool': 38.0,
        'v_pool': 17955.0,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_aao', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
        PortRef(unit_id='test_aao', port_id='sludge_out'):
            SludgeFlow(q_wet=0.0037204691021874964, ds=0.022322814613124995, moisture=0.994),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_aao', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 12.329959999999996,
        'CODCR': 29.990430000000007,
        'SS': 9.321209999999999,
        'NH3N': 2.5999999999999996,
        'TN': 10.75,
        'TP': 0.4549999999999997,
    }
    quality_port = PortRef(unit_id='test_aao', port_id='sludge_out')
    assert result.outqualities[quality_port].concentrations == {}


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'ns': 0.0},
         "单元 'municipal_aao' 参数 'ns' 必须 > 0：得到 0.0"),
        ({'tn_eff': 50.0},
         "单元 'municipal_aao' 反硝化脱氮量 delta_n 必须 > 0：TN_in=43.0，tn_eff=50.0（进水 TN 须"
         '高于设计出水 TN——AO-F4 前提）'),
        ({'h2': 0.0},
         "单元 'municipal_aao' 参数 'h2' 必须 > 0：得到 0.0"),
        ({'side_disc_step': 0.0},
         "单元 'municipal_aao' 参数 'side_disc_step' 必须 > 0：得到 0.0"),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:19 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('AO-F1',
         {
             'q_avg_daily': 0.40232291666666664,
             'bod5_in': 123.2996,
             'ns': 0.1,
             'x_mlss': 4000.0,
         },
         10714.951014299999),
        ('AO-F3',
         {
             'q_avg_daily': 0.40232291666666664,
             't_p': 1.5,
         },
         2172.54375),
        ('AO-F4',
         {
             'q_avg_daily': 0.40232291666666664,
             'delta_n': 28.0,
             'k_denit': 0.05,
             'x_mlss': 4000.0,
         },
         4866.498),
        ('AO-F2',
         {
             'v_o': 10714.951014299999,
             'q_avg_daily': 0.40232291666666664,
         },
         7.397975999999999),
        ('AO-F5',
         {
             'v_anoxic': 4866.498,
             'q_avg_daily': 0.40232291666666664,
         },
         3.36),
        ('AO-F6',
         {
             'q_avg_daily': 0.40232291666666664,
             'bod5_in': 123.2996,
             'bod5_out': 12.329959999999996,
             'y_yield': 0.5,
         },
         1928.6911825739996),
        ('AO-F7',
         {
             's_y': 1928.6911825739996,
             'p_moisture': 0.994,
         },
         321.4485304289997),
        ('AO-F8',
         {
             'v_o': 10714.951014299999,
             'x_mlss': 4000.0,
             's_y': 1928.6911825739996,
         },
         22.22222222222222),
        ('AO-F9',
         {
             'a_prime': 0.5,
             'q_avg_daily': 0.40232291666666664,
             'bod5_in': 123.2996,
             'bod5_out': 12.329959999999996,
             'b_prime': 0.1,
             'v_o': 10714.951014299999,
             'x_vss': 3000.0,
         },
         5143.176486863999),
        ('AO-F10',
         {
             'q_avg_daily': 0.40232291666666664,
             'tkn_in': 43.0,
             'tn_eff': 15.0,
         },
         4447.979172),
        ('AO-F11',
         {
             'q_avg_daily': 0.40232291666666664,
             'tkn_in': 43.0,
             'tn_eff': 15.0,
         },
         2783.6368559999996),
        ('AO-F12',
         {
             'o2_carbon': 5143.176486863999,
             'o2_nit': 4447.979172,
             'o2_denit': 2783.6368559999996,
         },
         6807.5188028640005),
        ('AO-F13',
         {
             'r_external': 1.0,
             'q_design_h': 2027.7074999999995,
         },
         2027.7074999999995),
        ('AO-F14',
         {
             'r_internal': 2.0,
             'q_avg_h': 1448.3625,
         },
         2896.725),
        ('AO-F15',
         {
             'v_total': 17753.992764299997,
             'h2': 5.0,
         },
         3550.7985528599993),
        ('AO-F16',
         {
             'h_super': 0.3,
             'h2': 5.0,
         },
         5.3),
        ('AO-F17',
         {
             'a_pool': 3550.7985528599993,
             'ratio_lb': 2.5,
         },
         94.21781350758464),
        ('AO-F18',
         {
             'a_pool': 3550.7985528599993,
             'ratio_lb': 2.5,
         },
         37.68712540303385),
        ('AO-F19',
         {
             'l_pool': 94.5,
             'b_pool': 38.0,
             'h2': 5.0,
         },
         17955.0),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
