"""sludge_tuoshui golden 数值测试（期望值来源：docs/norms/sludge_tuoshui.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_tuoshui.md 主算例（带式主线档，TU-F1~F8：w_pam=
#   13.515693705/q_in_h=4.9166519761/n_machine_raw=0.2458→n_machine_
#   duty=1/n_machine_total=2（1 用 1 备）/ds_cake=3209.9772549375
#   回收/q_cake=14.5908057043 三量链/q_filtrate=103.408841722/
#   ds_filtrate=168.9461713125 守恒闭合）与副算例（离心档 q_machine=
#   10/dose=3/p_cake=0.75：w_pam=10.1367702787/n_machine_raw=0.4917→
#   1 台/q_cake=12.8399090197 低含水档减量/q_filtrate=105.1597384065/
#   ds_filtrate 同主）；系数键值逐字取自 data/coefficients 0.6.0
#   factors.yaml（tuoshui 8 键）——测试区字面量合法。
#   浮点末位注记（照 KT-F10 π 注记先例，M3b1 二审 M1 回填表内）：
#   q_filtrate 主算例表载 103.408841722 系 12 位显示舍入——链式实算
#   （入流往返 117.99964742624991−q_cake 实算）得 103.40884172198854，
#   差 <1.2e-12，断言容差 abs=1e-9 覆盖，数值零变更。
#   入流口径：xiaohua 主算例出流三量（ds 3378.92342625 kg/d /
#   q 117.9996474262 m³/d / p 0.9713649702）。
#
# 【用例面】（十二条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/三口 SLUDGE——filtrate 口 recycle
#   声明/removal_refs 空）②主算例带式档药耗与台数逐项（TU-F1~F4
#   整台取整+备用）③主算例 DS 回收守恒链逐项（TU-F5~F8——泥饼/
#   滤液分流闭合）+三量链回显 ④主算例两带校核零警告 ⑤副算例
#   （离心档）逐项——机档键选实证 ⑥越带 Warning——PAM 带（dose_pam
#   越带）⑦越带 Warning——泥饼含水率带（p_cake 越带）⑧泥饼出流
#   SLUDGE 三量（契约口径）+filtrate 口不产股（Q1 默认关注记）
#   ⑨参数域拒绝（machine_type 非枚举值/p_cake 闭边界）⑩纯函数
#   双跑一致 ⑪formula_ids 恰 8 号（TU-F1~F8）全部可解析 ⑫工况键
#   形态冒烟。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/tuoshui/tests`
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
from waterprint.units_lib.sludge.tuoshui import make_unit, manifest

# ── 主算例入流（表逐字：xiaohua 主算例出流三量——衔接链口径）──
_IN_REF = PortRef(unit_id="upstream_xiaohua", port_id="out")
_OUT_REF = PortRef(unit_id="test_sludge_tuoshui", port_id="out")
_FILTRATE_REF = PortRef(unit_id="test_sludge_tuoshui", port_id="filtrate")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_INFLOW = make_sludge(
    q_wet=117.9996474262 / 86400, ds=3378.92342625 / 86400, moisture=0.9713649702
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
        # manifest 默认=表主算例逐字（带式主线档）
        "machine_type": 1.0,
        "dose_pam": 4.0,
        "p_cake": 0.78,
        "n_standby": 1.0,
        # data/coefficients factors.yaml（0.6.0）tuoshui 8 键逐字
        "factor.tuoshui.cake_moisture_band.min": 0.75,
        "factor.tuoshui.cake_moisture_band.max": 0.8,
        "factor.tuoshui.dose_pam_band.min": 2.0,
        "factor.tuoshui.dose_pam_band.max": 8.0,
        "factor.tuoshui.eta_capture": 0.95,
        "factor.tuoshui.machine.belt_capacity": 20.0,
        "factor.tuoshui.machine.centrifuge_capacity": 10.0,
        "factor.tuoshui.elevation_loss": 0.2,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_tuoshui",
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


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/三口 SLUDGE（filtrate 口 recycle 声明先行）/removal_refs 空。"""
    assert manifest.unit_id == "sludge_tuoshui"
    assert manifest.business_line == "sludge"
    assert [
        (p.port_id, p.fluid.name, p.direction.name, p.recycle) for p in manifest.ports
    ] == [
        ("in", "SLUDGE", "IN", False),
        ("out", "SLUDGE", "OUT", False),
        ("filtrate", "SLUDGE", "OUT", True),  # 滤液回流口——Q1 未裁默认关
    ]
    assert manifest.removal_refs == {}


def test_main_case_dosing_and_machines() -> None:
    """②主算例带式档药耗与台数逐项断言（TU-F1~F4——整台取整+备用）。"""
    dims = _dims()
    assert dims["w_pam"] == pytest.approx(13.515693705, abs=1e-9)  # TU-F1 ×4/1000
    assert dims["q_in_h"] == pytest.approx(4.9166519761, abs=1e-9)  # TU-F2 /24
    assert dims["n_machine_raw"] == pytest.approx(0.2458, abs=1e-4)  # TU-F3 /20
    assert dims["n_machine_duty"] == 1.0  # 0.2458 → 整台向上取整 1 台（带式）
    assert dims["n_machine_total"] == pytest.approx(2.0, abs=1e-12)  # TU-F4 1 用 1 备


def test_main_case_ds_chain_and_echo() -> None:
    """③主算例 DS 回收守恒链逐项（TU-F5~F8）+进出三量链回显。"""
    dims = _dims()
    assert dims["ds_cake"] == pytest.approx(3209.9772549375, abs=1e-9)  # TU-F5 ×0.95
    assert dims["q_cake"] == pytest.approx(14.5908057043, abs=1e-9)  # TU-F6 三量链
    assert dims["q_filtrate"] == pytest.approx(103.408841722, abs=1e-9)  # TU-F7
    assert dims["ds_filtrate"] == pytest.approx(168.9461713125, abs=1e-9)  # TU-F8 闭合
    assert dims["q_in"] == pytest.approx(117.9996474262, abs=1e-9)
    assert dims["ds_in"] == pytest.approx(3378.92342625, abs=1e-9)
    assert dims["p_in"] == pytest.approx(0.9713649702, abs=1e-12)
    assert dims["q_out"] == pytest.approx(14.5908057043, abs=1e-9)  # =q_cake
    assert dims["ds_out"] == pytest.approx(3209.9772549375, abs=1e-9)  # =ds_cake
    assert dims["p_out"] == pytest.approx(0.78, abs=1e-12)


def test_main_case_no_warning() -> None:
    """④主算例两带校核合格（dose 4 带内/p_cake 0.78 带内）——零警告。"""
    result = _compute()
    assert result.warnings == ()


def test_secondary_case_centrifuge() -> None:
    """⑤副算例（离心档 machine_type=2/单机 10/dose 3/p_cake 0.75）逐项——机档键选实证。"""
    dims = _dims(machine_type=2.0, dose_pam=3.0, p_cake=0.75)
    assert dims["w_pam"] == pytest.approx(10.1367702787, abs=1e-9)  # ×3/1000
    assert dims["n_machine_raw"] == pytest.approx(0.4917, abs=1e-4)  # /10 离心档
    assert dims["n_machine_duty"] == 1.0  # 离心 1 台
    assert dims["ds_cake"] == pytest.approx(3209.9772549375, abs=1e-9)  # 同主（回收率同）
    assert dims["q_cake"] == pytest.approx(12.8399090197, abs=1e-9)  # 低含水档减量
    assert dims["q_filtrate"] == pytest.approx(105.1597384065, abs=1e-9)
    assert dims["ds_filtrate"] == pytest.approx(168.9461713125, abs=1e-9)  # 同主


def test_dose_band_warning() -> None:
    """⑥越带 Warning：dose_pam=10 越 PAM 带上限（param_key=dose_pam）。"""
    result = _compute(dose_pam=10.0)
    dose = [w for w in result.warnings if "dose_pam_band" in w.source]
    assert dose and dose[0].severity is Severity.WARN
    assert dose[0].param_key == "dose_pam"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["w_pam"] == pytest.approx(33.7892342625, abs=1e-8)  # 越带实值生效


def test_cake_band_warning() -> None:
    """⑦越带 Warning：p_cake=0.70 越泥饼含水率带下限（param_key=p_cake）。"""
    result = _compute(p_cake=0.70)
    cake = [w for w in result.warnings if "cake_moisture_band" in w.source]
    assert cake and cake[0].severity is Severity.WARN
    assert cake[0].param_key == "p_cake"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["q_cake"] == pytest.approx(10.699924182, abs=1e-8)  # 越带实值生效


def test_outflow_and_filtrate_port() -> None:
    """⑧泥饼出流 SLUDGE 三量（契约口径）+filtrate 口不产股（Q1 默认关注记）。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(14.5908057043 / 86400, abs=1e-15)
    assert out.ds == pytest.approx(3209.9772549375 / 86400, abs=1e-15)
    assert out.moisture == pytest.approx(0.78, abs=1e-12)
    assert _FILTRATE_REF not in result.outflows  # filtrate 端口声明先行、不产股
    assert result.outqualities == {}


def test_param_domain_rejected() -> None:
    """⑨参数域拒绝：machine_type 非枚举值 / p_cake 闭边界 1 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(machine_type=3.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(p_cake=1.0)))


def test_pure_function_double_run() -> None:
    """⑩纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings


def test_formula_ids_registered() -> None:
    """⑪formula_ids 恰 8 号（TU-F1~TU-F8）且全部可在公式注册表解析（A1 防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"TU-F{index}" for index in range(1, 9))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """⑫工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
