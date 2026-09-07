"""municipal_bashi_jiliangcao 向量化重写前基线锚(批 13-D 基线先行独立笔·件 1/2)。

输入:  本包 make_unit/compute——重写前树态(d445483429)全表面输出冻结
输出:  主算例全表面精确锚+域拒消息锚+公式级逐行锚(== 精确);参数
       变体面=件 2 test_vector_variants.py
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-D 基线先行独立笔;task-13D-batch-plan §五/§六)
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
#   abs=1e-3~1e-9)且仅覆盖选中键:末位 ulp 漂移不可检出+warnings
#   全文本/出流值/公式级逐行值零锚定=重写等价性验收面缺位(锁窗
#   附加条件举证——批 A/B/C 形态同款)。
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
from waterprint.units_lib.municipal.bashi_jiliangcao import make_unit

# ── 冻结入参(重写前包内 test_compute 权威夹具的 round-trip 字面量化;
#    变体件与本件同源副本——包内 tests 无包语义,自包含纪律) ──
_UNIT_TEST_ID = 'test_bashi'
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
    'b_throat': 0.75,
    'factor.bashi_jiliangcao.flume.b025.c': 561.0,
    'factor.bashi_jiliangcao.flume.b025.n': 1.513,
    'factor.bashi_jiliangcao.flume.b025.scrit': 0.6,
    'factor.bashi_jiliangcao.flume.b025.hmin': 0.03,
    'factor.bashi_jiliangcao.flume.b025.hmax': 0.6,
    'factor.bashi_jiliangcao.flume.b045.c': 1038.0,
    'factor.bashi_jiliangcao.flume.b045.n': 1.537,
    'factor.bashi_jiliangcao.flume.b045.scrit': 0.6,
    'factor.bashi_jiliangcao.flume.b045.hmin': 0.03,
    'factor.bashi_jiliangcao.flume.b045.hmax': 0.75,
    'factor.bashi_jiliangcao.flume.b075.c': 1772.0,
    'factor.bashi_jiliangcao.flume.b075.n': 1.557,
    'factor.bashi_jiliangcao.flume.b075.scrit': 0.6,
    'factor.bashi_jiliangcao.flume.b075.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b075.hmax': 0.75,
    'factor.bashi_jiliangcao.flume.b100.c': 2397.0,
    'factor.bashi_jiliangcao.flume.b100.n': 1.569,
    'factor.bashi_jiliangcao.flume.b100.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b100.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b100.hmax': 0.8,
    'factor.bashi_jiliangcao.flume.b120.c': 2904.0,
    'factor.bashi_jiliangcao.flume.b120.n': 1.577,
    'factor.bashi_jiliangcao.flume.b120.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b120.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b120.hmax': 0.8,
    'factor.bashi_jiliangcao.flume.b150.c': 3668.0,
    'factor.bashi_jiliangcao.flume.b150.n': 1.586,
    'factor.bashi_jiliangcao.flume.b150.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b150.hmin': 0.06,
    'factor.bashi_jiliangcao.flume.b150.hmax': 0.8,
    'factor.bashi_jiliangcao.flume.b210.c': 5222.0,
    'factor.bashi_jiliangcao.flume.b210.n': 1.599,
    'factor.bashi_jiliangcao.flume.b210.scrit': 0.7,
    'factor.bashi_jiliangcao.flume.b210.hmin': 0.08,
    'factor.bashi_jiliangcao.flume.b210.hmax': 0.8,
    'factor.bashi_jiliangcao.hb_design': 0.25,
    'factor.bashi_jiliangcao.loss_ratio': 0.25,
    'factor.bashi_jiliangcao.geometry.l_throat': 0.6,
    'factor.bashi_jiliangcao.geometry.l_diffuse': 0.92,
    'factor.bashi_jiliangcao.geometry.n_depress': 0.23,
    'factor.bashi_jiliangcao.geometry.k_margin': 0.08,
    'factor.bashi_jiliangcao.elevation_loss': 0.15,
    'removal.bashi_jiliangcao.bod5.mod_default': 0.0,
    'removal.bashi_jiliangcao.cod.mod_default': 0.0,
    'removal.bashi_jiliangcao.ss.mod_default': 0.0,
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
        'ha_design': 0.47896932471441167,
        'ha_avg': 0.385882778771218,
        'q_meas': 402.32291666666663,
        'b1': 1.38,
        'l1': 1.575,
        'b2': 1.05,
        'l_total': 3.0949999999999998,
        'l_throat': 0.6,
        'l_diffuse': 0.92,
        'n_depress': 0.23,
        'k_margin': 0.08,
        'sigma': 0.521954094135494,
        'h_loss': 0.11974233117860292,
    }
    assert [
        (w.severity.name, w.source, w.message, w.param_key)
        for w in result.warnings
    ] == [
    ]
    ports = {
        PortRef(unit_id='test_bashi', port_id='out'):
            WaterFlow(q_avg_daily=0.40232291666666664, kz=1.4),
    }
    assert set(result.outflows) == set(ports)
    for port, expected in ports.items():
        assert result.outflows[port] == expected
    quality_port = PortRef(unit_id='test_bashi', port_id='out')
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
        ({'b_throat': 0.0},
         "单元 'municipal_bashi_jiliangcao' 参数 'b_throat' 必须 > 0：得到 0.0"),
        ({'b_throat': 0.5},
         "单元 'municipal_bashi_jiliangcao' 喉宽 0.5 非 B7 七档标准档位（合法 [0.25, 0.45, 0.75, 1"
         '.0, 1.2, 1.5, 2.1]——档位面经 manifest grid 声明，起草表追认点 1）'),
    ]:
        with pytest.raises(InvalidUnitConfig) as excinfo:
            _compute(overrides)
        assert str(excinfo.value) == message


def test_baseline_formula_lines() -> None:
    """公式级逐行锚:9 条主算例路径绑定→apply 精确值。"""
    for formula_id, bindings, expected in [
        ('BL-F2',
         {
             'q_design': 0.5632520833333332,
             'c_coef': 1772.0,
             'n_exp': 1.557,
         },
         0.47896932471441167),
        ('BL-F3',
         {
             'q_avg_daily': 0.40232291666666664,
             'c_coef': 1772.0,
             'n_exp': 1.557,
         },
         0.385882778771218),
        ('BL-F1',
         {
             'ha': 0.385882778771218,
             'c_coef': 1772.0,
             'n_exp': 1.557,
         },
         402.32291666666663),
        ('BL-F5',
         {
             'b_throat': 0.75,
         },
         1.575),
        ('BL-F4',
         {
             'b_throat': 0.75,
         },
         1.38),
        ('BL-F6',
         {
             'b_throat': 0.75,
         },
         1.05),
        ('BL-F7',
         {
             'l1': 1.575,
             'l_throat': 0.6,
             'l_diffuse': 0.92,
         },
         3.0949999999999998),
        ('BL-F8',
         {
             'hb_design': 0.25,
             'ha_design': 0.47896932471441167,
         },
         0.521954094135494),
        ('BL-F9',
         {
             'loss_ratio': 0.25,
             'ha_design': 0.47896932471441167,
         },
         0.11974233117860292),
    ]:
        result = formulas.apply(
            formula_id, dict(bindings), (_UNIT_TEST_ID, "design")
        )
        assert result == expected
