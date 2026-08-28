"""sludge_nongsuo golden 数值测试（期望值来源：docs/norms/sludge_nongsuo.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_nongsuo.md 主算例（NS-F1~F12 十三项：a_load=
#   106.1303/a_time=68.2227638889/a_req=106.1303 固体负荷主控/
#   a_single=53.06515/d_raw=8.2198→d=8.5 m/q_solid_act=50.0 带中值/
#   ds_out=4775.8635 截留/q_thick=119.3965875 底流三量链/q_sup=
#   289.9399958333/ds_sup=530.6515 守恒闭合/h_total=6.3/v_concrete=
#   234.0173115）与副算例（负荷带下限+底流变档：a_load=176.8838333333/
#   a_time=51.1670729167/a_single=88.4419166667/d=11.0/q_solid_act=
#   30.0 带下限/ds_out=4510.53775/q_thick=150.3512583333/q_sup=
#   258.985325/ds_sup=795.97725/v_concrete=390.0288525）；系数键值
#   逐字取自 data/coefficients 0.6.0 factors.yaml（nongsuo 12 键）
#   ——测试区字面量合法。
#   π 口径注记：表 NS-F5 内联 3.14159265 经符号 pi 绑 math.pi
#   （KI/KT/KS 先例同型）——d_raw 差 <1e-9，容差 abs=1e-8 覆盖。
#   入流口径：bengzhan 主算例出流三量（=hebing 出流穿流不变）。
#
# 【用例面】（十二条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/三口 SLUDGE——sup 口 recycle 声明/
#   removal_refs 空）②主算例双主线面积+池径逐项（NS-F1~F6+0.5 m 档
#   取整）③主算例截留 DS 守恒链逐项（NS-F7~F10——底流/上清液分流）
#   ④主算例构造/概算逐项（NS-F11~F12）+三量链回显 ⑤主算例四带
#   校核全合格零警告 ⑥副算例（负荷带下限+底流变档）逐项 ⑦越带
#   Warning——实际固体负荷带（q_solid 越带）⑧越带 Warning——底流
#   含水率带（p_out 越带）⑨底流出流 SLUDGE 三量（契约口径）+sup 口
#   无条件产股三量（GOLDEN3 D2 翻转——上清液 q_wet/ds=NS-F9/F10 主算例
#   值 289.9399958333/530.6515 ÷86400 回契约口径；moisture=1−(ds_sup/
#   q_sup)/1000 干基近似反解[固体密度按水——I2 追认证注记]；清单身份
#   测试①三口形态不动）⑩参数域拒绝（n 非正/p_out 闭边界）
#   ⑪纯函数双跑一致 ⑫formula_ids 恰 12 号（NS-F1~F12）全部可解析
#   +工况键冒烟。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/nongsuo/tests`
#   转为只读（AGENTS.md §11）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.sludge import SludgeFlow, make_sludge
from waterprint.contracts.unit_api import Severity, UnitContext, UnitResult
from waterprint.registry import formulas
from waterprint.units_lib.sludge.nongsuo import make_unit, manifest

# ── 主算例入流（表逐字：bengzhan 主算例出流三量——衔接链口径）──
_IN_REF = PortRef(unit_id="upstream_bengzhan", port_id="out")
_OUT_REF = PortRef(unit_id="test_sludge_nongsuo", port_id="out")
_SUP_REF = PortRef(unit_id="test_sludge_nongsuo", port_id="sup")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_INFLOW = make_sludge(
    q_wet=409.3365833333 / 86400, ds=5306.515 / 86400, moisture=0.9870363041
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；系数投影逐字 0.6.0）。"""
    params: dict[str, float] = {
        # manifest 默认=表主算例逐字（6 参数）
        "q_solid": 50.0,
        "t_thicken": 16.0,
        "h_eff": 4.0,
        "n": 2.0,
        "p_out": 0.96,
        "h_cone": 2.0,
        # data/coefficients factors.yaml（0.6.0）nongsuo 12 键逐字
        "factor.nongsuo.solid_load_band.min": 30.0,
        "factor.nongsuo.solid_load_band.max": 60.0,
        "factor.nongsuo.time_band.min": 12.0,
        "factor.nongsuo.time_band.max": 24.0,
        "factor.nongsuo.depth_band.min": 3.0,
        "factor.nongsuo.depth_band.max": 5.0,
        "factor.nongsuo.moisture_out_band.min": 0.95,
        "factor.nongsuo.moisture_out_band.max": 0.98,
        "factor.nongsuo.eta_capture": 0.9,
        "factor.nongsuo.superheight": 0.3,
        "factor.nongsuo.wall_thickness_coef": 0.35,
        "factor.nongsuo.elevation_loss": 0.3,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_nongsuo",
        inflows={_IN_REF: _INFLOW},
        inqualities={},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims(**overrides: float) -> dict[str, float]:
    """算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params(**overrides))).dims
    assert isinstance(dims, dict)
    return dict(dims)


def _compute(**overrides: float) -> UnitResult:
    """主算例（或覆盖档）单跑结果。"""
    return make_unit().compute(_ctx(_params(**overrides)))


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/三口 SLUDGE（sup 口 recycle=True 声明先行）/removal_refs 空。"""
    assert manifest.unit_id == "sludge_nongsuo"
    assert manifest.business_line == "sludge"
    assert [
        (p.port_id, p.fluid.name, p.direction.name, p.recycle) for p in manifest.ports
    ] == [
        ("in", "SLUDGE", "IN", False),
        ("out", "SLUDGE", "OUT", False),
        ("sup", "SLUDGE", "OUT", True),  # 上清液回流口——Q1 未裁默认关
    ]
    assert manifest.removal_refs == {}


def test_main_case_area() -> None:
    """②主算例双主线面积+池径逐项断言（NS-F1~F6——0.5 m 档取整）。"""
    dims = _dims()
    assert dims["a_load"] == pytest.approx(106.1303, abs=1e-9)  # NS-F1 固体通量主线
    assert dims["a_time"] == pytest.approx(68.2227638889, abs=1e-9)  # NS-F2 时间主线
    assert dims["a_req"] == pytest.approx(106.1303, abs=1e-9)  # NS-F3 固体负荷主控
    assert dims["a_single"] == pytest.approx(53.06515, abs=1e-9)  # NS-F4
    assert dims["d_raw"] == pytest.approx(8.2198, abs=1e-4)  # NS-F5（表 4 位截断）
    assert dims["d"] == pytest.approx(8.5, abs=1e-12)  # 0.5 m 档向上取整
    assert dims["q_solid_act"] == pytest.approx(50.0, abs=1e-9)  # NS-F6 带中值合格


def test_main_case_balance() -> None:
    """③主算例截留 DS 守恒链逐项断言（NS-F7~F10——底流/上清液分流）。"""
    dims = _dims()
    assert dims["ds_out"] == pytest.approx(4775.8635, abs=1e-9)  # NS-F7 ×0.90 截留
    assert dims["q_thick"] == pytest.approx(119.3965875, abs=1e-9)  # NS-F8 底流三量链
    assert dims["q_sup"] == pytest.approx(289.9399958333, abs=1e-9)  # NS-F9 上清液
    assert dims["ds_sup"] == pytest.approx(530.6515, abs=1e-9)  # NS-F10 守恒闭合


def test_main_case_structure_and_echo() -> None:
    """④主算例构造/概算逐项（NS-F11~F12）+进出三量链回显。"""
    dims = _dims()
    assert dims["h_total"] == pytest.approx(6.3, abs=1e-12)  # NS-F11
    assert dims["v_concrete"] == pytest.approx(234.0173115, abs=1e-8)  # NS-F12 概算
    assert dims["q_in"] == pytest.approx(409.3365833333, abs=1e-9)
    assert dims["ds_in"] == pytest.approx(5306.515, abs=1e-9)
    assert dims["p_in"] == pytest.approx(0.9870363041, abs=1e-12)
    assert dims["q_out"] == pytest.approx(119.3965875, abs=1e-9)  # =q_thick
    assert dims["p_out"] == pytest.approx(0.96, abs=1e-12)


def test_main_case_no_warning() -> None:
    """⑤主算例四带校核全合格（负荷带中值/时间/水深/含水率带内）——零警告。"""
    result = _compute()
    assert result.warnings == ()


def test_secondary_case() -> None:
    """⑥副算例（q_solid=30 带下限+p_out=0.97+截留 0.85 档）逐项断言。"""
    dims = _dims(
        q_solid=30.0,
        t_thicken=12.0,
        p_out=0.97,
        **{"factor.nongsuo.eta_capture": 0.85},
    )
    assert dims["a_load"] == pytest.approx(176.8838333333, abs=1e-9)
    assert dims["a_time"] == pytest.approx(51.1670729167, abs=1e-9)
    assert dims["a_req"] == pytest.approx(176.8838333333, abs=1e-9)  # 仍负荷主控
    assert dims["a_single"] == pytest.approx(88.4419166667, abs=1e-9)
    assert dims["d"] == pytest.approx(11.0, abs=1e-12)  # 10.6117 → 0.5 m 档
    assert dims["q_solid_act"] == pytest.approx(30.0, abs=1e-9)  # 带下限内
    assert dims["ds_out"] == pytest.approx(4510.53775, abs=1e-9)
    assert dims["q_thick"] == pytest.approx(150.3512583333, abs=1e-9)
    assert dims["q_sup"] == pytest.approx(258.985325, abs=1e-9)
    assert dims["ds_sup"] == pytest.approx(795.97725, abs=1e-9)
    assert dims["v_concrete"] == pytest.approx(390.0288525, abs=1e-8)


def test_solid_load_band_warning() -> None:
    """⑦越带 Warning：q_solid=20 越负荷带下限（param_key=q_solid）。"""
    result = _compute(q_solid=20.0)
    solid = [w for w in result.warnings if "solid_load_band" in w.source]
    assert solid and solid[0].severity is Severity.WARN
    assert solid[0].param_key == "q_solid"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["a_req"] == pytest.approx(265.32575, abs=1e-8)  # 越带实值生效
    assert dims["q_solid_act"] == pytest.approx(20.0, abs=1e-9)  # 实负荷=越带值


def test_moisture_band_warning() -> None:
    """⑧越带 Warning：p_out=0.99 越底流含水率带上限（param_key=p_out）。"""
    result = _compute(p_out=0.99)
    moisture = [w for w in result.warnings if "moisture_out_band" in w.source]
    assert moisture and moisture[0].severity is Severity.WARN
    assert moisture[0].param_key == "p_out"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["q_thick"] == pytest.approx(477.58635, abs=1e-8)  # 越带实值生效


def test_outflow_and_sup_port() -> None:
    """⑨底流出流 SLUDGE 三量（契约口径）+sup 口无条件产股三量（GOLDEN3 D2）。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(119.3965875 / 86400, abs=1e-16)
    assert out.ds == pytest.approx(4775.8635 / 86400, abs=1e-16)
    assert out.moisture == pytest.approx(0.96, abs=1e-12)
    sup = result.outflows[_SUP_REF]  # GOLDEN3 D2：sup 口无条件产股
    assert isinstance(sup, SludgeFlow)
    assert sup.q_wet == pytest.approx(289.9399958333 / 86400, abs=1e-16)  # NS-F9
    assert sup.ds == pytest.approx(530.6515 / 86400, abs=1e-16)  # NS-F10
    # 含水率干基近似反解：1−(ds_sup/q_sup)/1000（固体密度按水——I2 追认）
    assert sup.moisture == pytest.approx(
        1 - (530.6515 / 289.9399958333) / 1000, abs=1e-15
    )
    assert set(result.outqualities) == {_OUT_REF, _SUP_REF}  # 两口空水质单位元面
    assert result.outqualities[_OUT_REF].concentrations == {}
    assert result.outqualities[_SUP_REF].concentrations == {}


def test_param_domain_rejected() -> None:
    """⑩参数域拒绝：n≤0 / p_out 闭边界 1 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(p_out=1.0)))


def test_pure_function_double_run() -> None:
    """⑪纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings


def test_formula_ids_registered_and_condition_key() -> None:
    """⑫formula_ids 恰 12 号（NS-F1~F12）全部可解析+工况键形态冒烟。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"NS-F{index}" for index in range(1, 13))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id
    assert ConditionSet.key(_CONDITION) == "design"
