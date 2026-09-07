"""municipal_cugeshan 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

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
from waterprint.units_lib.municipal.cugeshan import make_unit

"""municipal_cugeshan 向量化重写前基线锚(批 13-C 基线先行独立笔·件 1/2)。

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
_UNIT_TEST_ID = 'test_cugeshan'
_IN_PORT = 'in'
_FLOW_ARGS: dict[str, float] = {
    'q_avg_daily': 0.40232291666666664,
    'kz': 1.4,
}
_QUALITY: dict[str, float] = {
}
_MAIN_PARAMS: dict[str, float] = {
    'n': 3.0,
    'b': 0.065,
    'alpha': 75.0,
    'h': 0.6,
    'v': 0.8,
    'v1': 0.7,
    's': 0.01,
    'bar_shape': 0.0,
    'g_gravity': 9.81,
    'length_disc_step': 0.1,
    'factor.screen.beta.rect': 2.42,
    'factor.screen.beta.semicircle': 1.97,
    'factor.screen.beta.circle': 1.83,
    'factor.screen.headloss.k': 3.0,
    'factor.screen.superheight': 0.3,
    'factor.screen.trough_width_margin': 0.2,
    'factor.screen.trough_length.l3_fixed': 1.0,
    'factor.screen.trough_length.l4_fixed': 0.5,
    'factor.screen.trough_length.drop_constant': 0.2,
    'factor.screen.slag.moisture': 0.8,
    'factor.screen.mech_clean_threshold': 0.2,
    'factor.screen.velocity_band.v.min': 0.6,
    'factor.screen.velocity_band.v.max': 1.0,
    'factor.screen.velocity_band.v1.min': 0.4,
    'factor.screen.velocity_band.v1.max': 0.9,
    'factor.screen.wall_thickness_coef': 0.3,
    'factor.cugeshan.w1_slag': 0.02,
    'removal.cugeshan.bod5.mod_default': 0.05,
    'removal.cugeshan.cod.mod_default': 0.05,
    'removal.cugeshan.ss.mod_default': 0.05,
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
        'q': 0.1877506944444444,
        'n_gap': 6.0,
        'B': 0.7000000000000001,
        'B1': 0.5,
        'v_checked': 0.7885651569058347,
        'v1_checked': 0.625835648148148,
        'xi': 0.19949448329320632,
        'h1': 0.01832196661969464,
        'H': 1.0,
        'L': 1.8,
        'w_slag': 0.6952139999999999,
        'mech_clean': 1.0,
        'ds_slag': 139.04279999999994,
        'v_concrete': 1.1340000000000001,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_cugeshan', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    assert result.outqualities[PortRef(unit_id='test_cugeshan', port_id='out')].concentrations == {}


def test_baseline_domain_rejections() -> None:
    """域拒消息逐字锚(类型 InvalidUnitConfig+文本恒等)。"""
    for overrides, message in [
        ({'n': 0.0},
         "单元 'test_cugeshan' 参数 'n' 必须 > 0：得到 0.0"),
        ({'length_disc_step': 0.0},
         "单元 'test_cugeshan' 的 length_disc_step 必须 > 0：得到 0.0"),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:14 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('CG-F1',
         {
             'q_design': 0.5632520833333332,
             'n': 3.0,
         },
         0.1877506944444444),
        ('CG-F2',
         {
             'q': 0.1877506944444444,
             'sqrt_sin_alpha': 0.9828152554214186,
             'b': 0.065,
             'h': 0.6,
             'v': 0.8,
         },
         5.91423867679376),
        ('CG-F3',
         {
             's': 0.01,
             'n_gap': 6.0,
             'b': 0.065,
             'margin': 0.2,
         },
         0.64),
        ('CG-F4',
         {
             'q': 0.1877506944444444,
             'h': 0.6,
             'v1': 0.7,
         },
         0.44702546296296286),
        ('CG-F5',
         {
             'q': 0.1877506944444444,
             'sqrt_sin_alpha': 0.9828152554214186,
             'b': 0.065,
             'h': 0.6,
             'n_gap': 6.0,
         },
         0.7885651569058347),
        ('CG-F6',
         {
             'q': 0.1877506944444444,
             'h': 0.6,
             'b1': 0.5,
         },
         0.625835648148148),
        ('CG-F7',
         {
             'beta': 2.42,
             's_over_b': 0.15384615384615385,
         },
         0.19949448329320632),
        ('CG-F8',
         {
             'k_headloss': 3.0,
             'xi': 0.19949448329320632,
             'v_checked': 0.7885651569058347,
             'g': 9.81,
             'sin_alpha': 0.9659258262890683,
         },
         0.01832196661969464),
        ('CG-F9',
         {
             'h': 0.6,
             'h1': 0.01832196661969464,
             'superheight': 0.3,
         },
         0.9183219666196947),
        ('CG-F10',
         {
             'B': 0.7000000000000001,
             'b1': 0.5,
             'tan_alpha': 3.7320508075688776,
             'l3_fixed': 1.0,
             'l4_fixed': 0.5,
             'drop_constant': 0.2,
             'h': 0.6,
         },
         1.7545517328095666),
        ('CG-F11',
         {
             'q_design': 0.5632520833333332,
             'w1': 0.02,
             'kz': 1.4,
         },
         0.6952139999999999),
        ('CG-F12',
         {
             'w_slag': 0.6952139999999999,
             'mech_clean_threshold': 0.2,
         },
         0.4952139999999999),
        ('CG-F13',
         {
             'w_slag': 0.6952139999999999,
             'moisture': 0.8,
         },
         139.04279999999994),
        ('CG-F14',
         {
             'L': 1.8,
             'B': 0.7000000000000001,
             'H': 1.0,
             'n': 3.0,
             'wall_coef': 0.3,
         },
         1.1340000000000001),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
