"""mine_water_ziwai golden 数值测试（期望值来源：docs/norms/mine_water_ziwai.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_ziwai.md 主算例（KZ-F1~F11 十一项：q_ch=
#   913.25/a_ch=2.04/v_ch=0.1243532135/t_eff=0.5240467536/i_avg=
#   15.1048770167/dose_row=14.576102948/n_rows=3/dose_act=43.728308844/
#   t_contact=2.8949794689/h_loss=0.1/h_total=1.5）与副算例（n=1 单渠
#   检修极限工况：q_ch=2739.75/v_ch=0.3730596405/dose_row=4.8587009827/
#   n_rows=7/dose_act=34.0109068786/t_contact=2.2516506981）；系数键值
#   逐字取自 data/coefficients 0.5.0 factors.yaml（mine_ziwai 11 键）/
#   removal_rates.yaml（ss/cod 显式 0.0 穿流——物理消毒无去除）——
#   测试区字面量合法。
#   t254 口径注记：带键 60.0/70.0 为百分数存储口径（R1 批内修正——
#   原 0.6 分数形态系起草笔误），公式 (t254/100)**n_t 以百分数入参，
#   主算例 65。
#
# 【用例面】主算例逐项断言 + 副算例单渠检修工况对照 + 校核带越界
#   产 Warning（渠内流速带/穿透率带）+ 参数域拒绝（n≤0、p_lamp≤0、
#   t254≤0）+ 纯函数双跑一致 + formula_ids 全部可在公式注册表解析 +
#   出流水质零变化穿流（SS 1.36/COD 51.8——全厂终水，物理消毒无
#   去除）+ 实算剂量 ≥ 设计剂量合格面断言（KZ-F8）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/ziwai/tests`
#   转为只读（AGENTS.md §11）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.mine_water.ziwai import make_unit, manifest

# ── 主算例入参（表逐字：Q_design_h=2739.75 m³/h（Q_avg_daily=43836
#    m³/d、Kz=1.5 上游口径）、n=3 渠、b_channel=1.7 m、h_channel=1.2 m、
#    t254=65、n_t=1.5、p_lamp=250 W、n_layer=6 支/排、eta_geo=0.7、
#    f_aging=0.7、f_fouling=0.8（结垢特征键）、d_long=0.12 m、xi_total=3、
#    dose=30 mJ/cm²、h_super=0.3；入流水质=vxinglvchi 表出流——
#    SS 1.36/COD 51.8） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_ziwai", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.0, "CODCR": 51.8, "SS": 1.36, "NH3N": 1.0, "TN": 60.0, "TP": 2.0}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；系数投影逐字 0.5.0）。"""
    params: dict[str, float] = {
        "n": 3.0,
        "b_channel": 1.7,
        "h_channel": 1.2,
        "p_lamp": 250.0,
        "n_layer": 6.0,
        "d_long": 0.12,
        "xi_total": 3.0,
        "n_t": 1.5,
        "t254": 65.0,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_ziwai.dose": 30.0,
        "factor.mine_ziwai.velocity_band.min": 0.05,
        "factor.mine_ziwai.velocity_band.max": 0.7,
        "factor.mine_ziwai.t254_band.min": 60.0,
        "factor.mine_ziwai.t254_band.max": 70.0,
        "factor.mine_ziwai.f_aging": 0.7,
        "factor.mine_ziwai.f_fouling": 0.8,
        "factor.mine_ziwai.eta_geo": 0.7,
        "factor.mine_ziwai.loss_min": 0.1,
        "factor.mine_ziwai.superheight": 0.3,
        "factor.mine_ziwai.wall_thickness_coef": 0.35,
        "factor.mine_ziwai.elevation_loss": 0.25,
        # removal_rates.yaml mod_default 档逐字（物理消毒无去除穿流）
        "removal.mine_ziwai.ss.mod_default": 0.0,
        "removal.mine_ziwai.cod.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_ziwai",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
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


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包（BOD5 不建键）。"""
    assert manifest.unit_id == "mine_water_ziwai"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_ziwai.ss.mod_default",
        "CODCR": "removal.mine_ziwai.cod.mod_default",
    }


def test_main_case_channel() -> None:
    """主算例（表主算例）单渠流量/断面积/渠内流速逐项断言（KZ-F1~F3）。"""
    dims = _dims()
    assert dims["q_ch"] == pytest.approx(913.25, abs=1e-9)  # KZ-F1：2739.75/3
    assert dims["a_ch"] == pytest.approx(2.04, abs=1e-9)  # KZ-F2：1.7×1.2
    assert dims["v_ch"] == pytest.approx(0.1243532135, abs=1e-9)  # KZ-F3：带内
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例两条校核面均合格


def test_main_case_dose_chain() -> None:
    """主算例穿透率/辐照强度/单排剂量/排数/实算剂量逐项断言（KZ-F4~F8）。"""
    dims = _dims()
    assert dims["t_eff"] == pytest.approx(0.5240467536, abs=1e-9)  # KZ-F4：0.65^1.5
    assert dims["i_avg"] == pytest.approx(15.1048770167, abs=1e-8)  # KZ-F5
    assert dims["dose_row"] == pytest.approx(14.576102948, abs=1e-8)  # KZ-F6
    assert dims["n_rows_raw"] == pytest.approx(2.0581632902, abs=1e-8)  # 取整前审计面
    assert dims["n_rows"] == pytest.approx(3.0, abs=1e-9)  # KZ-F7：2.058… ceil 3 排
    assert dims["dose_act"] == pytest.approx(43.728308844, abs=1e-8)  # KZ-F8：≥30 合格
    assert dims["dose_act"] >= 30.0  # 实算剂量≥设计剂量合格面（ceil 结构保证）


def test_main_case_contact_loss() -> None:
    """主算例接触时间/渠道水损/渠总高逐项断言（KZ-F9~F11）。"""
    dims = _dims()
    assert dims["t_contact"] == pytest.approx(2.8949794689, abs=1e-8)  # KZ-F9
    assert dims["h_loss"] == pytest.approx(0.1, abs=1e-9)  # KZ-F10：max(0.0024, 0.10)
    assert dims["h_total"] == pytest.approx(1.5, abs=1e-9)  # KZ-F11：0.3+1.2


def test_secondary_case_single_channel() -> None:
    """副算例（n=1 单渠检修极限工况）逐项断言（表副算例——失去备用仍可算）。"""
    dims = _dims(n=1.0)
    assert dims["q_ch"] == pytest.approx(2739.75, abs=1e-9)
    assert dims["v_ch"] == pytest.approx(0.3730596405, abs=1e-9)  # 带内
    assert dims["dose_row"] == pytest.approx(4.8587009827, abs=1e-8)  # 流速升高单排剂量降
    assert dims["n_rows_raw"] == pytest.approx(6.1744898705, abs=1e-8)
    assert dims["n_rows"] == pytest.approx(7.0, abs=1e-9)  # 7 排
    assert dims["dose_act"] == pytest.approx(34.0109068786, abs=1e-7)  # ≥30 合格
    assert dims["t_contact"] == pytest.approx(2.2516506981, abs=1e-8)
    result = make_unit().compute(_ctx(_params(n=1.0)))
    assert result.warnings == ()  # 检修工况流速带内、剂量达标


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质零变化穿流（全厂终水——物理消毒无去除）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_ziwai", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(1.36, abs=1e-9) == out_quality.SS  # ×(1−0.0) 穿流
    assert pytest.approx(51.8, abs=1e-9) == out_quality.CODCR
    assert out_quality.BOD5 == 5.0  # 无去除键穿流不变
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_velocity_band_warning() -> None:
    """校核带越界：n=1+h_channel=0.2 → v_ch≈2.236 越 0.7 上限产 WARN。

    构造场景（warning 用例参数面允许合成）：浅渠缩小断面 →
    v_ch=(2739.75/3600)/(1.7×0.2)=2.2362…>0.7 实证（param_key=b_channel
    断面构造归因）。
    """
    result = make_unit().compute(_ctx(_params(n=1.0, h_channel=0.2)))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_ch"] == pytest.approx((2739.75 / 3600) / 0.34, abs=1e-8)
    assert dims["v_ch"] > 0.7
    velocity = [w for w in result.warnings if "velocity_band" in w.source]
    assert velocity and velocity[0].severity is Severity.WARN


def test_t254_band_warning() -> None:
    """校核带越界：t254=50 越穿透率带 60~70 下限产 WARN（param_key=t254）。"""
    result = make_unit().compute(_ctx(_params(t254=50.0)))
    band = [w for w in result.warnings if "t254_band" in w.source]
    assert band and band[0].severity is Severity.WARN
    assert band[0].param_key == "t254"


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0 / p_lamp≤0 / t254≤0 / d_long≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(p_lamp=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t254=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(d_long=0.0)))


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"KZ-F{index}" for index in range(1, 12))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
