"""sludge_ganhua golden 数值测试（期望值来源：docs/norms/sludge_ganhua.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_ganhua.md 主算例（GH-F1~F8：m_in=14590.8057042614/
#   w_evap=10310.8360310114 干基差式/q_out=4.2799696732 半步 tie/
#   m_out=4279.96967325/m_check=4279.96967325 守恒闭合差 0/q_heat=
#   35351437.82061038/w_fuel=987.4703301846/a_dry=53.7022709949）与
#   副算例（浅干化 0.40 档+热效率 0.8+蒸发强度 4：w_evap=9240.8436126989/
#   q_out=5.3499620916/m_out=5349.9620915625/m_check 同值差 0/q_heat=
#   27722530.83809658/w_fuel=774.3723697792/a_dry=96.2587876323）；
#   系数键值逐字取自 data/coefficients 0.6.0 factors.yaml（ganhua
#   8 键）——测试区字面量合法。
#   浮点末位注记（照 KT-F10 π 注记先例，M3b1 二审 M1 回填表内）：
#   ①q_out 主算例恰落 11 位小数半步 tie（精确 4.27996967325——表
#   载 4.2799696732 系 10 位截断，差 5e-11，容差 1e-9 覆盖）；
#   ②q_heat 主/副表载 35351437.82061038/27722530.83809658 系 16 位
#   显示舍入——实算 35351437.820610404/27722530.838096596，差
#   <2.5e-8，容差 1e-7 覆盖。数值零变更。
#   入流口径：tuoshui 主算例泥饼出流三量（ds 3209.9772549375 kg/d /
#   q 14.5908057043 m³/d / p 0.78）。
#
# 【用例面】（十二条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 SLUDGE/removal_refs 空）②主算例
#   进泥与蒸发水量逐项（GH-F1~F2——干基差式）③主算例出泥三量链
#   与质量守恒逐项（GH-F3~F5——m_check=m_out 差 0）④主算例热量
#   衡算逐项（GH-F6~F8）+三量链回显 ⑤主算例两带校核零警告 ⑥副
#   算例（浅干化+高热效率+低蒸发强度档）逐项 ⑦越带 Warning——干化
#   后含水率带（p_out 越带）⑧越带 Warning——蒸发强度带（r_evap
#   越带）⑨出流 SLUDGE 三量（契约口径——DS 不变）⑩参数域拒绝
#   （t_op 非正/p_out 闭边界）⑪纯函数双跑一致 ⑫formula_ids 恰
#   8 号（GH-F1~GH-F8）全部可解析+工况键冒烟。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/ganhua/tests`
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
from waterprint.units_lib.sludge.ganhua import make_unit, manifest

# ── 主算例入流（表逐字：tuoshui 主算例泥饼出流三量——衔接链口径）──
_IN_REF = PortRef(unit_id="upstream_tuoshui", port_id="out")
_OUT_REF = PortRef(unit_id="test_sludge_ganhua", port_id="out")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_INFLOW = make_sludge(
    q_wet=14.5908057043 / 86400, ds=3209.9772549375 / 86400, moisture=0.78
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
        # manifest 默认=表主算例逐字（半干化 0.25 档/连续 24 h/强度 8）
        "p_out": 0.25,
        "t_op": 24.0,
        "r_evap": 8.0,
        # data/coefficients factors.yaml（0.6.0）ganhua 8 键逐字
        "factor.ganhua.moisture_out_band.min": 0.2,
        "factor.ganhua.moisture_out_band.max": 0.4,
        "factor.ganhua.h_evap": 2400.0,
        "factor.ganhua.eta_thermal": 0.7,
        "factor.ganhua.evap_rate_band.min": 4.0,
        "factor.ganhua.evap_rate_band.max": 15.0,
        "factor.ganhua.fuel_calorific": 35800.0,
        "factor.ganhua.elevation_loss": 0.15,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_ganhua",
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
    """①清单身份：UNIT_ID/业务线/两口 SLUDGE/removal_refs 空（零 removal 键）。"""
    assert manifest.unit_id == "sludge_ganhua"
    assert manifest.business_line == "sludge"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "SLUDGE", "IN"),
        ("out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_inlet_and_evap() -> None:
    """②主算例进泥湿质量与蒸发水量逐项断言（GH-F1~F2——干基差式）。"""
    dims = _dims()
    assert dims["m_in"] == pytest.approx(14590.8057042614, abs=1e-9)  # GH-F1 /0.22
    assert dims["w_evap"] == pytest.approx(10310.8360310114, abs=1e-8)  # GH-F2 ×3.2121212


def test_main_case_outlet_and_conservation() -> None:
    """③主算例出泥三量链与质量守恒逐项断言（GH-F3~F5——差 0 闭合）。"""
    dims = _dims()
    assert dims["q_out"] == pytest.approx(4.2799696732, abs=1e-9)  # GH-F3 半步 tie
    assert dims["m_out"] == pytest.approx(4279.96967325, abs=1e-12)  # GH-F4 /0.75
    assert dims["m_check"] == pytest.approx(4279.96967325, abs=1e-12)  # GH-F5 守恒
    assert dims["m_check"] == pytest.approx(dims["m_out"], abs=1e-12)  # 差 0 显式


def test_main_case_heat_and_echo() -> None:
    """④主算例热量衡算逐项（GH-F6~F8）+进出三量链回显。"""
    dims = _dims()
    assert dims["q_heat"] == pytest.approx(35351437.82061038, abs=1e-7)  # GH-F6
    assert dims["w_fuel"] == pytest.approx(987.4703301846, abs=1e-9)  # GH-F7 /35800
    assert dims["a_dry"] == pytest.approx(53.7022709949, abs=1e-9)  # GH-F8 /(8×24)
    assert dims["q_in"] == pytest.approx(14.5908057043, abs=1e-9)
    assert dims["ds_in"] == pytest.approx(3209.9772549375, abs=1e-9)
    assert dims["p_in"] == pytest.approx(0.78, abs=1e-12)
    assert dims["ds_out"] == pytest.approx(3209.9772549375, abs=1e-9)  # DS 不变
    assert dims["p_out"] == pytest.approx(0.25, abs=1e-12)


def test_main_case_no_warning() -> None:
    """⑤主算例两带校核合格（p_out 0.25 带内/r_evap 8 带内）——零警告。"""
    result = _compute()
    assert result.warnings == ()


def test_secondary_case() -> None:
    """⑥副算例（p_out=0.40 浅干化+eta 0.8+r_evap 4 档）逐项断言。"""
    dims = _dims(
        p_out=0.40, r_evap=4.0, **{"factor.ganhua.eta_thermal": 0.8}
    )
    assert dims["w_evap"] == pytest.approx(9240.8436126989, abs=1e-8)
    assert dims["q_out"] == pytest.approx(5.3499620916, abs=1e-9)
    assert dims["m_out"] == pytest.approx(5349.9620915625, abs=1e-12)
    assert dims["m_check"] == pytest.approx(5349.9620915625, abs=1e-12)  # 差 0
    assert dims["q_heat"] == pytest.approx(27722530.83809658, abs=1e-7)
    assert dims["w_fuel"] == pytest.approx(774.3723697792, abs=1e-9)
    assert dims["a_dry"] == pytest.approx(96.2587876323, abs=1e-9)


def test_moisture_band_warning() -> None:
    """⑦越带 Warning：p_out=0.10 越干化含水率带下限（param_key=p_out）。"""
    result = _compute(p_out=0.10)
    moisture = [w for w in result.warnings if "moisture_out_band" in w.source]
    assert moisture and moisture[0].severity is Severity.WARN
    assert moisture[0].param_key == "p_out"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["q_out"] == pytest.approx(3.5666413944, abs=1e-9)  # 越带实值生效


def test_evap_band_warning() -> None:
    """⑧越带 Warning：r_evap=20 越蒸发强度带上限（param_key=r_evap）。"""
    result = _compute(r_evap=20.0)
    evap = [w for w in result.warnings if "evap_rate_band" in w.source]
    assert evap and evap[0].severity is Severity.WARN
    assert evap[0].param_key == "r_evap"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["a_dry"] == pytest.approx(21.480908398, abs=1e-8)  # 越带实值生效


def test_outflow_sludge_triple() -> None:
    """⑨出流 SLUDGE 三量（契约口径：q_out 换算/ds 不变/p_out 直通）。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(4.27996967325 / 86400, abs=1e-15)
    assert out.ds == pytest.approx(_INFLOW.ds, abs=1e-18)  # DS 不变
    assert out.moisture == pytest.approx(0.25, abs=1e-12)
    assert set(result.outqualities) == {_OUT_REF}  # 空水质单位元面（executor 入流装配前提）
    assert result.outqualities[_OUT_REF].concentrations == {}


def test_param_domain_rejected() -> None:
    """⑩参数域拒绝：t_op≤0 / p_out 闭边界 1 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_op=0.0)))
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
    """⑫formula_ids 恰 8 号（GH-F1~GH-F8）全部可解析+工况键形态冒烟。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"GH-F{index}" for index in range(1, 9))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id
    assert ConditionSet.key(_CONDITION) == "design"
