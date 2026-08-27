"""sludge_shusong golden 数值测试（期望值来源：docs/norms/sludge_shusong.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_shusong.md 主算例（ST-F1~F9 十项：q_h=17.0556909722/
#   q_si=0.0047376919/d_raw=0.063415123/d_pipe=0.075 DN75/v_act=
#   1.0723940856/i_req=0.0065974246/i_slope=0.01/v_grav=0.8618085957/
#   ds_out=5306.515 穿流/p_out=0.9870363041 穿流）与副算例（上限流速+
#   DN200 重力档：d_raw=0.0549191075/d_pipe=0.075 同档覆盖/v_act 同值/
#   i_req=0.0044956185/i_slope=0.01/v_grav=1.0440067652）；系数键值逐字
#   取自 data/coefficients 0.6.0 factors.yaml（shusong 6 键）——测试区
#   字面量合法。
#   π 口径注记：表 ST-F3/ST-F4 内联 3.14159265 按模板惯例经符号 pi
#   绑定 math.pi（KI/KT/KS 先例同型）——d_raw/v_act 差 <1e-9，断言
#   容差 abs=1e-8 覆盖。
#   入流口径：hebing 主算例出流三量（q 409.3365833333 m³/d、ds
#   5306.515 kg/d、p 0.9870363041——衔接链口径，表单元信息节）。
#
# 【用例面】（十三条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 SLUDGE/removal_refs 空）②主算例
#   流量与压力管径逐项（ST-F1~F3+DN25 档取整）③主算例实流速/重力
#   三量逐项（ST-F4~F7）④主算例穿流三量+三量链回显六键（ST-F8~F9）
#   ⑤主算例双校核合格零警告 ⑥副算例（上限流速+DN200 档）逐项
#   ⑦越带 Warning——压力流速带（v_press 越带实证 v_act 落带外档）
#   ⑧越带 Warning——重力最小流速（d_grav 缩径至 v_grav<0.7）⑨出流
#   SLUDGE 三量穿流（契约口径）⑩参数域拒绝（v_press/d_grav 非正）
#   ⑪纯函数双跑一致 ⑫formula_ids 恰 9 号（ST-F1~F9）且全部可在公式
#   注册表解析 ⑬工况键形态冒烟（condition_key 口径）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/shusong/tests`
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
from waterprint.units_lib.sludge.shusong import make_unit, manifest

# ── 主算例入流（表逐字：hebing 主算例出流三量——衔接链口径）──
_IN_REF = PortRef(unit_id="upstream_hebing", port_id="out")
_OUT_REF = PortRef(unit_id="test_sludge_shusong", port_id="out")
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
        # manifest 默认=表主算例逐字
        "v_press": 1.5,
        "d_grav": 0.15,
        # data/coefficients factors.yaml（0.6.0）shusong 6 键逐字
        "factor.shusong.velocity_band.min": 1.0,
        "factor.shusong.velocity_band.max": 2.0,
        "factor.shusong.gravity_v_min": 0.7,
        "factor.shusong.slope_min": 0.01,
        "factor.shusong.n_manning": 0.013,
        "factor.shusong.elevation_loss": 0.3,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_shusong",
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
    assert manifest.unit_id == "sludge_shusong"
    assert manifest.business_line == "sludge"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "SLUDGE", "IN"),
        ("out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_flow_and_pipe() -> None:
    """②主算例时/秒输泥量与压力管径逐项断言（ST-F1~F3+DN25 档取整）。"""
    dims = _dims()
    assert dims["q_h"] == pytest.approx(17.0556909722, abs=1e-9)  # ST-F1
    assert dims["q_si"] == pytest.approx(0.0047376919, abs=1e-9)  # ST-F2（往返换算噪声 <4e-14）
    assert dims["d_raw"] == pytest.approx(0.063415123, abs=1e-8)  # ST-F3 π 差 <1e-9
    assert dims["d_pipe"] == pytest.approx(0.075, abs=1e-12)  # 0.0634→0.075 DN75


def test_main_case_velocity_and_gravity() -> None:
    """③主算例实流速/重力三量逐项断言（ST-F4~F7——曼宁+最小坡度条款）。"""
    dims = _dims()
    assert dims["v_act"] == pytest.approx(1.0723940856, abs=1e-8)  # ST-F4 带内
    assert dims["i_req"] == pytest.approx(0.0065974246, abs=1e-9)  # ST-F5 DN150 满流
    assert dims["i_slope"] == pytest.approx(0.01, abs=1e-12)  # ST-F7 最小坡度控制
    assert dims["v_grav"] == pytest.approx(0.8618085957, abs=1e-8)  # ST-F6 ≥0.7


def test_main_case_passthrough_and_echo() -> None:
    """④主算例穿流三量+三量链回显六键（ST-F8~F9——DS/含水率守恒显式）。"""
    dims = _dims()
    assert dims["ds_out"] == pytest.approx(5306.515, abs=1e-9)  # ST-F8 穿流
    assert dims["p_out"] == pytest.approx(0.9870363041, abs=1e-12)  # ST-F9 穿流
    assert dims["q_in"] == pytest.approx(409.3365833333, abs=1e-9)  # 进端回显
    assert dims["ds_in"] == pytest.approx(5306.515, abs=1e-9)
    assert dims["p_in"] == pytest.approx(0.9870363041, abs=1e-12)
    assert dims["q_out"] == pytest.approx(409.3365833333, abs=1e-9)  # 出端回显


def test_main_case_no_warning() -> None:
    """⑤主算例双校核合格（v_act 带内/v_grav≥0.7）——warnings 全空。"""
    result = _compute()
    assert result.warnings == ()


def test_secondary_case() -> None:
    """⑥副算例（v_press=2.0 上限流速+d_grav=0.20 DN200 档）逐项断言。"""
    dims = _dims(v_press=2.0, d_grav=0.20)
    assert dims["d_raw"] == pytest.approx(0.0549191075, abs=1e-8)
    assert dims["d_pipe"] == pytest.approx(0.075, abs=1e-12)  # 同档覆盖（档距实证）
    assert dims["v_act"] == pytest.approx(1.0723940856, abs=1e-8)  # 同管同量
    assert dims["i_req"] == pytest.approx(0.0044956185, abs=1e-9)  # DN200 满流
    assert dims["i_slope"] == pytest.approx(0.01, abs=1e-12)
    assert dims["v_grav"] == pytest.approx(1.0440067652, abs=1e-8)


def test_velocity_band_warning() -> None:
    """⑦越带 Warning：v_press=0.5 名义流速缩小使 DN25 档落带外（param_key=v_press）。"""
    result = _compute(v_press=0.5)
    band = [w for w in result.warnings if "velocity_band" in w.source]
    assert band and band[0].severity is Severity.WARN
    assert band[0].param_key == "v_press"
    dims = result.dims
    assert isinstance(dims, dict)
    # 0.5 m/s 名义 → d_raw 增大 → DN125 档 → 实流速落带下限外（越带实证）
    assert dims["d_pipe"] == pytest.approx(0.125, abs=1e-12)
    assert dims["v_act"] < 1.0


def test_gravity_v_min_warning() -> None:
    """⑧越带 Warning：d_grav 缩径（0.05）使 v_grav<0.7（param_key=d_grav）。"""
    result = _compute(d_grav=0.05)
    grav = [w for w in result.warnings if "gravity_v_min" in w.source]
    assert grav and grav[0].severity is Severity.WARN
    assert grav[0].param_key == "d_grav"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_grav"] < 0.7  # 越带实证


def test_outflow_sludge_passthrough() -> None:
    """⑨出流 SLUDGE 三量穿流（契约口径：q_wet/ds 直通、moisture 不变）。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(_INFLOW.q_wet, abs=1e-18)
    assert out.ds == pytest.approx(_INFLOW.ds, abs=1e-18)
    assert out.moisture == _INFLOW.moisture
    assert set(result.outqualities) == {_OUT_REF}  # 空水质单位元面（executor 入流装配前提）
    assert result.outqualities[_OUT_REF].concentrations == {}


def test_param_domain_rejected() -> None:
    """⑩参数域拒绝：v_press≤0 / d_grav≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_press=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(d_grav=0.0)))


def test_pure_function_double_run() -> None:
    """⑪纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings


def test_formula_ids_registered() -> None:
    """⑫formula_ids 恰 9 号（ST-F1~F9）且全部可在公式注册表解析（A1 防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"ST-F{index}" for index in range(1, 10))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
