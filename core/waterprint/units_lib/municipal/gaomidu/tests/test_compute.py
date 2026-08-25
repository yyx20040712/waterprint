"""municipal_gaomidu golden 数值测试（期望值来源：docs/norms/gaomidu.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=四表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/gaomidu.md 算例 1（含 B=8.5/h_total=5.6 离散化项）；
#   系数键值逐字取自 data/coefficients 0.3.0 数据包 factors/removal_rates
#   yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q1h/a_incl_req/b_raw/B/a_act/q_surface_act/
#   v_mix/v_floc/p_mix/p_floc/gt_floc/q_return/ss_out/s_dry/q_sludge/
#   m_pac/m_pam/h_tube_zone/h_settle/h_total_raw/h_total/h_floc_calc/
#   v_concrete）+ 校核带越界产 Warning（液面负荷带/回流比带/快混·絮凝
#   停留带/GT 带/絮凝区布置校核）+ 参数域拒绝（n≤0/q_surface≤0/
#   g_mix≤0/缺 SS 入流）+ 纯函数双跑一致 + formula_ids 全部可在公式
#   注册表解析。
# 【口径注记】入流水质=四表衔接式值（SS 4.660605/BOD5 9.863964/
#   COD 25.49187，上游 M2a1 三单元+M2a2 三单元去除链后=二沉出流）；
#   出流=衔接下游 V 滤表值（5.918378/17.84431/0.6990908）。
# 【容差注记】四表手算取 Q_design=0.56325（5 位舍入），引擎用精确
#   34760.7/86400×1.4=0.5632520833——差 <4e-6 m³/s，q1h 面 1e-2 容差
#   覆盖该舍入差；离散化项（B=8.5）不受扰。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/gaomidu/tests`
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
from waterprint.units_lib.municipal.gaomidu import make_unit, manifest

# ── 算例 1 入参（四表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    四表衔接式值——全厂去除链后二沉池出流） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_gaomidu", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 9.863964, "CODCR": 25.49187, "SS": 4.660605, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """算例 1 参数面（manifest 默认即算例值；factor.*/removal.* 系数投影逐字）。"""
    params: dict[str, float] = {
        "n": 2.0,
        "q_surface": 15.0,
        "r_sludge": 0.04,
        "t_mix": 1.5,
        "t_floc": 12.0,
        "l_tube": 1.0,
        "h_clear": 1.2,
        "h_buffer": 1.2,
        "h_thick": 2.0,
        "side_disc_step": 0.5,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.3.0 M2b1 四单元批）逐字
        "factor.gaomidu.surface_load_band.min": 10.0,
        "factor.gaomidu.surface_load_band.max": 20.0,
        "factor.gaomidu.r_sludge_band.min": 0.03,
        "factor.gaomidu.r_sludge_band.max": 0.05,
        "factor.gaomidu.t_mix_band.min": 1.0,
        "factor.gaomidu.t_mix_band.max": 2.0,
        "factor.gaomidu.t_floc_band.min": 8.0,
        "factor.gaomidu.t_floc_band.max": 15.0,
        "factor.gaomidu.g_mix": 500.0,
        "factor.gaomidu.g_floc": 50.0,
        "factor.gaomidu.gt_band.min": 10000.0,
        "factor.gaomidu.gt_band.max": 100000.0,
        "factor.gaomidu.sludge.concentration": 20.0,
        "factor.gaomidu.dose.pac": 30.0,
        "factor.gaomidu.dose.pam": 1.0,
        "factor.gaomidu.superheight": 0.3,
        "factor.gaomidu.wall_thickness_coef": 0.35,
        "factor.gaomidu.elevation_loss": 0.8,
        # removal_rates.yaml mod_default 档逐字
        "removal.gaomidu.bod5.mod_default": 0.40,
        "removal.gaomidu.cod.mod_default": 0.30,
        "removal.gaomidu.ss.mod_default": 0.85,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_gaomidu",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims() -> dict[str, float]:
    """主算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params())).dims
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包。"""
    assert manifest.unit_id == "municipal_gaomidu"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.gaomidu.bod5.mod_default",
        "CODCR": "removal.gaomidu.cod.mod_default",
        "SS": "removal.gaomidu.ss.mod_default",
    }


def test_main_case_basin() -> None:
    """主算例（四表算例 1）沉淀区水力逐项断言（GM-F1~F5）。"""
    dims = _dims()
    assert dims["q1h"] == pytest.approx(1013.85, abs=1e-2)  # GM-F1：×3600 单池
    assert dims["q_design_h"] == pytest.approx(2027.70, abs=1e-2)  # 导出量（全厂）
    assert dims["a_incl_req"] == pytest.approx(67.59, abs=1e-2)  # GM-F2
    assert dims["b_raw"] == pytest.approx(8.221314, abs=1e-3)  # GM-F3
    assert dims["b"] == pytest.approx(8.5, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["a_act"] == pytest.approx(72.25, abs=1e-9)  # GM-F4：8.5²
    assert dims["q_surface_act"] == pytest.approx(14.03253, abs=1e-4)  # GM-F5：带内


def test_main_case_mix_floc() -> None:
    """主算例混合/絮凝区逐项断言（GM-F6~F10）。"""
    dims = _dims()
    assert dims["v_mix"] == pytest.approx(25.34625, abs=1e-3)  # GM-F6
    assert dims["v_floc"] == pytest.approx(202.77, abs=1e-2)  # GM-F7
    assert dims["p_mix"] == pytest.approx(6.336563, abs=1e-4)  # GM-F8：单池
    assert dims["p_floc"] == pytest.approx(0.506925, abs=1e-5)  # GM-F9：单池
    assert dims["gt_floc"] == pytest.approx(36000.0, abs=1e-6)  # GM-F10：带内


def test_main_case_sludge_dose() -> None:
    """主算例回流/干泥量/排泥/药剂逐项断言（GM-F11~F15，平均日口径）。"""
    dims = _dims()
    assert dims["q_return"] == pytest.approx(81.108, abs=1e-2)  # GM-F11：全厂回流泵
    assert dims["ss_out"] == pytest.approx(0.6990908, abs=1e-6)  # 衔接式
    assert dims["s_dry"] == pytest.approx(137.7050, abs=1e-3)  # GM-F12：全厂
    assert dims["q_sludge"] == pytest.approx(6.885250, abs=1e-4)  # GM-F13
    assert dims["m_pac"] == pytest.approx(1042.821, abs=1e-3)  # GM-F14
    assert dims["m_pam"] == pytest.approx(34.7607, abs=1e-4)  # GM-F15


def test_main_case_depth() -> None:
    """主算例沉淀区高度/总高/混凝土量逐项断言（GM-F16~F20）。"""
    dims = _dims()
    assert dims["h_tube_zone"] == pytest.approx(0.8660254, abs=1e-7)  # GM-F16：sin60°
    assert dims["h_settle"] == pytest.approx(5.266025, abs=1e-6)  # GM-F17
    assert dims["h_total_raw"] == pytest.approx(5.566025, abs=1e-6)  # GM-F18
    assert dims["h_total"] == pytest.approx(5.6, abs=1e-9)  # 0.1 m 档向上取整
    assert dims["h_floc_calc"] == pytest.approx(2.806505, abs=1e-4)  # GM-F19：布置可行
    assert dims["v_concrete"] == pytest.approx(283.22, abs=1e-6)  # GM-F20：概算口径
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例六条校核带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal.mod_default)，NH3N/TN/TP 透传。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_gaomidu", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(9.863964 * (1 - 0.40)) == out_quality.BOD5  # 5.918378
    assert pytest.approx(25.49187 * (1 - 0.30)) == out_quality.CODCR  # 17.84431
    assert pytest.approx(4.660605 * (1 - 0.85)) == out_quality.SS  # 0.6990908
    assert out_quality.NH3N == 26.0  # 无去除键穿流不变
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_surface_load_band_warning() -> None:
    """校核带越界：q_surface=25 → 面积缩至 42.25、实际负荷≈24.0 越 10~20 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(q_surface=25.0)))
    surf = [w for w in result.warnings if "surface_load_band" in w.source]
    assert surf and surf[0].severity is Severity.WARN
    assert surf[0].param_key == "q_surface"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["q_surface_act"] == pytest.approx(24.0022, abs=1e-2)


def test_retention_and_return_band_warnings() -> None:
    """校核带越界：t_mix=3 越快混带；t_floc=16 越絮凝带；r_sludge=0.06 越回流比带。"""
    mix = [
        w for w in make_unit().compute(_ctx(_params(t_mix=3.0))).warnings
        if "t_mix_band" in w.source
    ]
    assert mix and mix[0].severity is Severity.WARN
    assert mix[0].param_key == "t_mix"
    floc = [
        w for w in make_unit().compute(_ctx(_params(t_floc=16.0))).warnings
        if "t_floc_band" in w.source
    ]
    assert floc and floc[0].severity is Severity.WARN
    assert floc[0].param_key == "t_floc"
    ret = [
        w for w in make_unit().compute(_ctx(_params(r_sludge=0.06))).warnings
        if "r_sludge_band" in w.source
    ]
    assert ret and ret[0].severity is Severity.WARN
    assert ret[0].param_key == "r_sludge"


def test_gt_band_and_layout_warnings() -> None:
    """GT 带越界（g_floc 系数投影 150 → GT=108000>1e5）与絮凝区布置校核
    （q_surface=25 缩面+t_floc=15 → h_floc_calc≈6.0 ≥ h_settle）。"""
    gt = [
        w for w in make_unit().compute(_ctx(_params(**{"factor.gaomidu.g_floc": 150.0}))).warnings
        if "gt_band" in w.source
    ]
    assert gt and gt[0].severity is Severity.WARN
    assert gt[0].param_key == "t_floc"
    layout = [
        w for w in make_unit().compute(_ctx(_params(q_surface=25.0, t_floc=15.0))).warnings
        if "布置校核" in w.source
    ]
    assert layout and layout[0].severity is Severity.WARN
    dims = make_unit().compute(_ctx(_params(q_surface=25.0, t_floc=15.0))).dims
    assert isinstance(dims, dict)
    assert dims["h_floc_calc"] >= dims["h_settle"]


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0/q_surface≤0/g_mix≤0/缺 SS 入流 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(q_surface=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(**{"factor.gaomidu.g_mix": 0.0})))
    ctx = UnitContext(
        unit_id="test_gaomidu",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: WaterQuality({"BOD5": 10.0})},
        params=_params(),
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(ctx)


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
    assert result.formula_ids == tuple(f"GM-F{index}" for index in range(1, 21))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
