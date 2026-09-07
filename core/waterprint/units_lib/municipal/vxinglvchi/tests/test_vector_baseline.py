"""municipal_vxinglvchi 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

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
from waterprint.units_lib.municipal.vxinglvchi import make_unit

"""municipal_vxinglvchi 向量化重写前基线锚(批 13-A 基线先行独立笔·件 1/2)。

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
_UNIT_TEST_ID = 'test_vxinglvchi'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
    'BOD5': 5.918378,
    'CODCR': 17.84431,
    'SS': 0.6990908,
    'NH3N': 26.0,
    'TN': 43.0,
    'TP': 6.5,
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 6.0,
    'v_filter': 8.0,
    'ratio_lb': 2.5,
    'h_water_above': 1.3,
    'h_sand': 1.3,
    'h_bottom': 1.0,
    't_cycle': 24.0,
    'side_disc_step': 0.5,
    'factor.vxinglvchi.v_filter_band.min': 7.0,
    'factor.vxinglvchi.v_filter_band.max': 10.0,
    'factor.vxinglvchi.v_forced_band.min': 11.0,
    'factor.vxinglvchi.v_forced_band.max': 13.0,
    'factor.vxinglvchi.selfuse_coef': 1.05,
    'factor.vxinglvchi.cell_ratio_lb_band.min': 2.0,
    'factor.vxinglvchi.cell_ratio_lb_band.max': 3.0,
    'factor.vxinglvchi.media.depth_band.min': 1.2,
    'factor.vxinglvchi.media.depth_band.max': 1.5,
    'factor.vxinglvchi.media.d10_band.min': 0.9,
    'factor.vxinglvchi.media.d10_band.max': 1.2,
    'factor.vxinglvchi.water_above_band.min': 1.2,
    'factor.vxinglvchi.water_above_band.max': 1.5,
    'factor.vxinglvchi.superheight': 0.3,
    'factor.vxinglvchi.wash.air': 15.0,
    'factor.vxinglvchi.wash.water_sim': 2.5,
    'factor.vxinglvchi.wash.water': 5.0,
    'factor.vxinglvchi.wash.sweep': 1.8,
    'factor.vxinglvchi.wash.t_air': 2.0,
    'factor.vxinglvchi.wash.t_sim': 4.0,
    'factor.vxinglvchi.wash.t_water': 4.0,
    'factor.vxinglvchi.cycle_band.min': 24.0,
    'factor.vxinglvchi.cycle_band.max': 48.0,
    'factor.vxinglvchi.wall_thickness_coef': 0.35,
    'factor.vxinglvchi.elevation_loss': 2.5,
    'removal.vxinglvchi.bod5.mod_default': 0.075,
    'removal.vxinglvchi.cod.mod_default': 0.075,
    'removal.vxinglvchi.ss.mod_default': 0.675,
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
        'q_filter': 2129.0928749999994,
        'a_total_req': 266.1366093749999,
        'a_cell': 44.35610156249999,
        'b_raw': 4.2121776582903045,
        'b': 4.5,
        'l_raw': 9.85691145833333,
        'l': 10.0,
        'a_cell_act': 45.0,
        'a_total_act': 270.0,
        'v_filter_act': 7.8855291666666645,
        'v_forced_act': 9.462634999999997,
        'q_air': 0.675,
        'q_wash_sim': 0.1125,
        'q_wash': 0.225,
        'q_sweep': 0.081,
        'v_air_per': 243.00000000000006,
        'v_wash_per': 129.60000000000002,
        'v_wash_daily': 777.6,
        'ratio_wash': 0.022370090360665926,
        'h_total': 3.9000000000000004,
        'v_concrete': 368.54999999999995,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_vxinglvchi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_vxinglvchi', port_id='out')
    assert dict(result.outqualities[quality_port].concentrations) == {
        'BOD5': 5.47449965,
        'CODCR': 16.50598675,
        'SS': 0.22720450999999997,
        'NH3N': 26.0,
        'TN': 43.0,
        'TP': 6.5,
    }


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'municipal_vxinglvchi' 参数 'n' 必须 > 0：得到 0.0"),
        ({'n': 1.0},
         "单元 'municipal_vxinglvchi' 参数 'n' 必须 ≥ 2（一格冲洗时其余格过全部流量——强制滤速 XL-F"
         '9 分母 a_total_act−a_cell_act 需 n≥2）：得到 1.0'),
        ({'v_filter': 0.0},
         "单元 'municipal_vxinglvchi' 参数 'v_filter' 必须 > 0：得到 0.0"),
        ({'factor.vxinglvchi.wash.air': 0.0},
         "单元 'municipal_vxinglvchi' 系数键 'factor.vxinglvchi.wash.air' 必须 > 0（自用水/冲洗强"
         '度/历时物理域）'),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:19 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('XL-F1',
         {
             'q_design': 0.5632520833333332,
             'selfuse_coef': 1.05,
         },
         2129.0928749999994),
        ('XL-F2',
         {
             'q_filter': 2129.0928749999994,
             'v_filter': 8.0,
         },
         266.1366093749999),
        ('XL-F3',
         {
             'a_total_req': 266.1366093749999,
             'n': 6.0,
         },
         44.35610156249999),
        ('XL-F4',
         {
             'a_cell': 44.35610156249999,
             'ratio_lb': 2.5,
         },
         4.2121776582903045),
        ('XL-F5',
         {
             'a_cell': 44.35610156249999,
             'B': 4.5,
         },
         9.85691145833333),
        ('XL-F6',
         {
             'B': 4.5,
             'L': 10.0,
         },
         45.0),
        ('XL-F7',
         {
             'a_cell_act': 45.0,
             'n': 6.0,
         },
         270.0),
        ('XL-F8',
         {
             'q_filter': 2129.0928749999994,
             'a_total_act': 270.0,
         },
         7.8855291666666645),
        ('XL-F9',
         {
             'q_filter': 2129.0928749999994,
             'a_total_act': 270.0,
             'a_cell_act': 45.0,
         },
         9.462634999999997),
        ('XL-F10',
         {
             'a_cell_act': 45.0,
             'w_air': 15.0,
         },
         0.675),
        ('XL-F11',
         {
             'a_cell_act': 45.0,
             'w_water_sim': 2.5,
         },
         0.1125),
        ('XL-F12',
         {
             'a_cell_act': 45.0,
             'w_water': 5.0,
         },
         0.225),
        ('XL-F13',
         {
             'a_cell_act': 45.0,
             'w_sweep': 1.8,
         },
         0.081),
        ('XL-F14',
         {
             'q_air': 0.675,
             't_air': 2.0,
             't_sim': 4.0,
         },
         243.00000000000006),
        ('XL-F15',
         {
             'q_wash_sim': 0.1125,
             'q_wash': 0.225,
             'q_sweep': 0.081,
             't_air': 2.0,
             't_sim': 4.0,
             't_water': 4.0,
         },
         129.60000000000002),
        ('XL-F16',
         {
             'v_wash_per': 129.60000000000002,
             'n': 6.0,
             't_cycle': 24.0,
         },
         777.6),
        ('XL-F17',
         {
             'v_wash_daily': 777.6,
             'q_avg_daily': 0.40232291666666664,
         },
         0.022370090360665926),
        ('XL-F18',
         {
             'h_super': 0.3,
             'h_water_above': 1.3,
             'h_sand': 1.3,
             'h_bottom': 1.0,
         },
         3.9000000000000004),
        ('XL-F19',
         {
             'a_total_act': 270.0,
             'h_total': 3.9000000000000004,
             'wall_coef': 0.35,
         },
         368.54999999999995),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
