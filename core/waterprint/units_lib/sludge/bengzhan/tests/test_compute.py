"""sludge_bengzhan golden 数值测试（期望值来源：docs/norms/sludge_bengzhan.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_bengzhan.md 主算例（BZ-F1~F18：q_h=17.0556909722/
#   n_pump_raw=1.7056→n_pump_duty=2/q_pump_h=8.5278454861/q_pump_si=
#   0.002368846/n_total=3/d_raw=0.0448412635/d_pipe=DN50 0.05/v_act=
#   1.2064433463/h_friction=3.7092394185/h_local=0.3709239419/h_loss=
#   4.8961960325/h_pump=16.3961960325/v_well=1.421307581/a_well=
#   0.7106537905/n_start=1.5/h_well_total=2.5/v_concrete=0.6218220667/
#   ds_out=5306.515/p_out=0.9870363041 穿流）与副算例（单泵上限锚+高
#   扬程长管档：n_pump_duty=1/q_pump_h=17.0556909722/n_total=2/d_raw=
#   0.0549191075/DN75 0.075/v_act=1.0723940856/h_friction=3.9076760953/
#   h_local=0.4689211314/h_loss=5.251916672/h_pump=22.251916672/v_well=
#   4.2639227431/a_well=2.842615162/n_start=1.0/h_well_total=2.0/
#   v_concrete=1.9898306134）；系数键值逐字取自 data/coefficients
#   0.6.0 factors.yaml（bengzhan 17 键）——测试区字面量合法。
#   π 口径注记：表 BZ-F6/F7 内联 3.14159265 经符号 pi 绑 math.pi
#   （KI/KT/KS 先例同型）——d_raw/v_act 差 <1e-9，容差 abs=1e-8 覆盖。
#   入流口径：shusong 主算例出流三量（=hebing 出流穿流不变）。
#
# 【用例面】（十二条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 SLUDGE/removal_refs 空）②主算例
#   泵组选型逐项（BZ-F1~F5 整台取整+备用）③主算例出泥管逐项
#   （BZ-F6~F7 DN25 档取整）④主算例扬程三分量逐项（BZ-F8~F11 λ 式+
#   污泥修正）⑤主算例集泥井逐项（BZ-F12~F16 容积/启停/概算）⑥主
#   算例五带校核全合格零警告+三量链回显 ⑦副算例（上限锚+高扬程长
#   管档）逐项 ⑧越带 Warning——出泥管流速带（v_pipe 越带）⑨越带
#   Warning——集泥井水深带（h_well 越带）⑩出流 SLUDGE 三量穿流
#   （契约口径）⑪参数域拒绝（v_pipe/t_well 非正）⑫formula_ids 恰
#   18 号（BZ-F1~F18）且全部可在公式注册表解析+工况键冒烟。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/bengzhan/tests`
#   转为只读（AGENTS.md §11）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.sludge import SludgeFlow, make_sludge
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.sludge.bengzhan import make_unit, manifest

# ── 主算例入流（表逐字：shusong 主算例出流三量——衔接链口径）──
_IN_REF = PortRef(unit_id="upstream_shusong", port_id="out")
_OUT_REF = PortRef(unit_id="test_sludge_bengzhan", port_id="out")
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
        "n_standby": 1.0,
        "h_static": 10.0,
        "l_pipe": 100.0,
        "v_pipe": 1.5,
        "t_well": 10.0,
        "h_well": 2.0,
        # data/coefficients factors.yaml（0.6.0）bengzhan 17 键逐字
        "factor.bengzhan.pump.q_per_unit": 10.0,
        "factor.bengzhan.pump.q_flow_band.min": 5.0,
        "factor.bengzhan.pump.q_flow_band.max": 50.0,
        "factor.bengzhan.pump.free_head": 1.5,
        "factor.bengzhan.pump.start_band.max": 6.0,
        "factor.bengzhan.pipe.velocity_band.min": 1.0,
        "factor.bengzhan.pipe.velocity_band.max": 2.0,
        "factor.bengzhan.pipe.zeta_total": 5.0,
        "factor.bengzhan.friction_lambda": 0.025,
        "factor.bengzhan.k_sludge": 1.2,
        "factor.bengzhan.well.t_band.min": 5.0,
        "factor.bengzhan.well.t_band.max": 15.0,
        "factor.bengzhan.well.depth_band.min": 1.5,
        "factor.bengzhan.well.depth_band.max": 2.5,
        "factor.bengzhan.superheight": 0.5,
        "factor.bengzhan.wall_thickness_coef": 0.35,
        "factor.bengzhan.elevation_loss": 0.3,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_bengzhan",
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


def _compute(**overrides: float):
    """主算例（或覆盖档）单跑结果。"""
    return make_unit().compute(_ctx(_params(**overrides)))


def _secondary_overrides() -> dict[str, float]:
    """副算例覆盖面（表副算例：单泵上限锚+高扬程长管档）。"""
    return {
        "factor.bengzhan.pump.q_per_unit": 20.0,
        "v_pipe": 2.0,
        "l_pipe": 200.0,
        "factor.bengzhan.pipe.zeta_total": 8.0,
        "h_static": 15.0,
        "factor.bengzhan.pump.free_head": 2.0,
        "t_well": 15.0,
        "h_well": 1.5,
    }


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/两口 SLUDGE/removal_refs 空（零 removal 键）。"""
    assert manifest.unit_id == "sludge_bengzhan"
    assert manifest.business_line == "sludge"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "SLUDGE", "IN"),
        ("out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_pump_selection() -> None:
    """②主算例泵组选型逐项断言（BZ-F1~F5——锚值取整+均分反算+备用）。"""
    dims = _dims()
    assert dims["q_h"] == pytest.approx(17.0556909722, abs=1e-9)  # BZ-F1
    assert dims["n_pump_raw"] == pytest.approx(1.7055690972, abs=1e-9)  # BZ-F2
    assert dims["n_pump_duty"] == 2.0  # 1.7056 → 整台向上取整 2 台（工作）
    assert dims["q_pump_h"] == pytest.approx(8.5278454861, abs=1e-9)  # BZ-F3 带内
    assert dims["q_pump_si"] == pytest.approx(0.002368846, abs=1e-9)  # BZ-F4
    assert dims["n_total"] == pytest.approx(3.0, abs=1e-12)  # BZ-F5：2 用 1 备


def test_main_case_pipe() -> None:
    """③主算例出泥管径/流速逐项断言（BZ-F6~F7——DN25 档取整）。"""
    dims = _dims()
    assert dims["d_raw"] == pytest.approx(0.0448412635, abs=1e-8)  # BZ-F6 π 差 <1e-9
    assert dims["d_pipe"] == pytest.approx(0.05, abs=1e-12)  # 0.0448→DN50
    assert dims["v_act"] == pytest.approx(1.2064433463, abs=1e-8)  # BZ-F7 带内


def test_main_case_head() -> None:
    """④主算例扬程三分量逐项断言（BZ-F8~F11——λ 式+污泥粘度修正）。"""
    dims = _dims()
    # 扬程链四量为链式求值（v_act→损失→扬程），表载 10 位舍入累积差
    # ~1.2e-8——容差 abs=1e-7 覆盖（浮点末位注记同 hebing 先例）
    assert dims["h_friction"] == pytest.approx(3.7092394185, abs=1e-7)  # BZ-F8
    assert dims["h_local"] == pytest.approx(0.3709239419, abs=1e-8)  # BZ-F9
    assert dims["h_loss"] == pytest.approx(4.8961960325, abs=1e-7)  # BZ-F10 ×1.2
    assert dims["h_pump"] == pytest.approx(16.3961960325, abs=1e-7)  # BZ-F11 三分量


def test_main_case_well() -> None:
    """⑤主算例集泥井逐项断言（BZ-F12~F16——容积/面积/启停/总高/概算）。"""
    dims = _dims()
    assert dims["v_well"] == pytest.approx(1.421307581, abs=1e-9)  # BZ-F12
    assert dims["a_well"] == pytest.approx(0.7106537905, abs=1e-9)  # BZ-F13
    assert dims["n_start"] == pytest.approx(1.5, abs=1e-9)  # BZ-F14 ≤6 合格
    assert dims["h_well_total"] == pytest.approx(2.5, abs=1e-12)  # BZ-F15
    assert dims["v_concrete"] == pytest.approx(0.6218220667, abs=1e-9)  # BZ-F16


def test_main_case_no_warning_and_echo() -> None:
    """⑥主算例五带校核全合格零警告+穿流三量与三量链回显六键。"""
    result = _compute()
    assert result.warnings == ()
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["ds_out"] == pytest.approx(5306.515, abs=1e-9)  # BZ-F17 穿流
    assert dims["p_out"] == pytest.approx(0.9870363041, abs=1e-12)  # BZ-F18
    assert dims["q_in"] == pytest.approx(409.3365833333, abs=1e-9)
    assert dims["ds_in"] == pytest.approx(5306.515, abs=1e-9)
    assert dims["p_in"] == pytest.approx(0.9870363041, abs=1e-12)
    assert dims["q_out"] == pytest.approx(409.3365833333, abs=1e-9)


def test_secondary_case() -> None:
    """⑦副算例（q_per_pump=20 上限锚+h_static 15+l_pipe 200 长管档）逐项断言。"""
    dims = _dims(**_secondary_overrides())
    assert dims["n_pump_raw"] == pytest.approx(0.8527845486, abs=1e-9)
    assert dims["n_pump_duty"] == 1.0  # 0.8528 → 取整 1 台（工作）
    assert dims["q_pump_h"] == pytest.approx(17.0556909722, abs=1e-9)
    assert dims["q_pump_si"] == pytest.approx(0.0047376919, abs=1e-9)
    assert dims["n_total"] == pytest.approx(2.0, abs=1e-12)  # 1 用 1 备
    assert dims["d_raw"] == pytest.approx(0.0549191075, abs=1e-8)
    assert dims["d_pipe"] == pytest.approx(0.075, abs=1e-12)  # DN75
    assert dims["v_act"] == pytest.approx(1.0723940856, abs=1e-8)
    assert dims["h_friction"] == pytest.approx(3.9076760953, abs=1e-7)
    assert dims["h_local"] == pytest.approx(0.4689211314, abs=1e-8)
    assert dims["h_loss"] == pytest.approx(5.251916672, abs=1e-7)
    assert dims["h_pump"] == pytest.approx(22.251916672, abs=1e-7)
    assert dims["v_well"] == pytest.approx(4.2639227431, abs=1e-8)
    assert dims["a_well"] == pytest.approx(2.842615162, abs=1e-8)
    assert dims["n_start"] == pytest.approx(1.0, abs=1e-9)
    assert dims["h_well_total"] == pytest.approx(2.0, abs=1e-12)
    assert dims["v_concrete"] == pytest.approx(1.9898306134, abs=1e-8)


def test_velocity_band_warning() -> None:
    """⑧越带 Warning：v_pipe=0.6 名义流速缩档使 v_act 落带外（param_key=v_pipe）。"""
    result = _compute(v_pipe=0.6)
    band = [w for w in result.warnings if "velocity_band" in w.source]
    assert band and band[0].severity is Severity.WARN
    assert band[0].param_key == "v_pipe"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_act"] < 1.0  # 越带下限实证


def test_well_depth_band_warning() -> None:
    """⑨越带 Warning：h_well=3.0 越有效水深带上限（param_key=h_well）。"""
    result = _compute(h_well=3.0)
    depth = [w for w in result.warnings if "depth_band" in w.source]
    assert depth and depth[0].severity is Severity.WARN
    assert depth[0].param_key == "h_well"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["h_well_total"] == pytest.approx(3.5, abs=1e-12)  # 越带实值生效


def test_outflow_sludge_passthrough() -> None:
    """⑩出流 SLUDGE 三量穿流（契约口径：q_wet/ds 直通、moisture 不变）。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(_INFLOW.q_wet, abs=1e-18)
    assert out.ds == pytest.approx(_INFLOW.ds, abs=1e-18)
    assert out.moisture == _INFLOW.moisture
    assert result.outqualities == {}


def test_param_domain_rejected() -> None:
    """⑪参数域拒绝：v_pipe≤0 / t_well≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_pipe=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_well=0.0)))


def test_formula_ids_registered_and_condition_key() -> None:
    """⑫formula_ids 恰 18 号（BZ-F1~F18）全部可解析+工况键形态冒烟。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"BZ-F{index}" for index in range(1, 19))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id
    assert ConditionSet.key(_CONDITION) == "design"
