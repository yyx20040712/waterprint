"""municipal_ziwai golden 数值测试（期望值来源：docs/norms/ziwai.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=四表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/ziwai.md 算例 1（含 h_w=0.6/n_lamp=64/n_module=8 离散化项）；
#   系数键值逐字取自 data/coefficients 0.3.0 数据包 factors/removal_rates
#   yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q_c/h_w_raw/h_w/v_channel_act/n_lamp_raw/
#   n_lamp/n_module_raw/n_module/n_module_series/l_lamp_zone/l_channel/
#   t_exp/c_fecal_out/h_submerge/h_channel/v_concrete）+ ZW-F6 模块分置
#   ×2 渠断言（n_module = n_module_series×n_channel 按表 8=4×2；非整除
#   时串列 ceil 放大布置）+ 校核带越界产 Warning（流速带/接触时间带/
#   灯管淹没校核——单渠事故 0.78 m/s 为表内注记非运行时警告）+
#   参数域拒绝（n_channel≤0/v_channel≤0/q_per_lamp≤0）+ 纯函数双跑
#   一致 + formula_ids 全部可在公式注册表解析。
# 【口径注记】入流水质=四表衔接式值（SS 0.2272045/BOD5 5.474500/
#   COD 16.50599，上游 V 型滤池出流=全厂终水）；出流=零去除键透传
#   （全指标原样穿流——紫外只改变粪大肠指标，与 M1a ×(1−r) 形态差异
#   记档）。
# 【容差注记】四表手算取 Q_design=0.56325（5 位舍入），引擎用精确
#   34760.7/86400×1.4=0.5632520833——差 <4e-6 m³/s，q_c/v/t_exp 面
#   1e-4~1e-5 容差覆盖该舍入差；离散化项（h_w=0.6/n_lamp=64）不受扰。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/ziwai/tests`
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
from waterprint.units_lib.municipal.ziwai import make_unit, manifest

# ── 算例 1 入参（四表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    四表衔接式值——上游 V 型滤池出流=全厂终水） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_ziwai", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.474500, "CODCR": 16.50599, "SS": 0.2272045, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
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
        "n_channel": 2.0,
        "v_channel": 0.4,
        "b_c": 1.2,
        "n_lamp_module": 8.0,
        "l_module": 0.6,
        "l_stab": 1.2,
        "h_module": 0.5,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.3.0 M2b1 四单元批）逐字
        "factor.ziwai.dose": 30.0,
        "factor.ziwai.q_per_lamp": 40.0,
        "factor.ziwai.f_aging": 0.8,
        "factor.ziwai.t254_band.min": 0.55,
        "factor.ziwai.t254_band.max": 0.65,
        "factor.ziwai.velocity_band.min": 0.3,
        "factor.ziwai.velocity_band.max": 0.6,
        "factor.ziwai.t_exp_band.min": 5.0,
        "factor.ziwai.t_exp_band.max": 10.0,
        "factor.ziwai.fecal.c_in_design": 100000.0,
        "factor.ziwai.fecal.log_removal": 4.0,
        "factor.ziwai.superheight": 0.5,
        "factor.ziwai.wall_thickness_coef": 0.35,
        "factor.ziwai.elevation_loss": 0.2,
        # removal_rates.yaml mod_default 档逐字（物理消毒无去除）
        "removal.ziwai.bod5.mod_default": 0.0,
        "removal.ziwai.cod.mod_default": 0.0,
        "removal.ziwai.ss.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_ziwai",
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
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包（全 0.0）。"""
    assert manifest.unit_id == "municipal_ziwai"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.ziwai.bod5.mod_default",
        "CODCR": "removal.ziwai.cod.mod_default",
        "SS": "removal.ziwai.ss.mod_default",
    }


def test_main_case_channel() -> None:
    """主算例（四表算例 1）渠道水力逐项断言（ZW-F1~F3）。"""
    dims = _dims()
    assert dims["q_c"] == pytest.approx(0.281625, abs=1e-5)  # ZW-F1：双渠各半
    assert dims["h_w_raw"] == pytest.approx(0.586721, abs=1e-5)  # ZW-F2
    assert dims["h_w"] == pytest.approx(0.6, abs=1e-9)  # 0.1 m 档向上取整
    assert dims["v_channel_act"] == pytest.approx(0.3911458, abs=1e-5)  # ZW-F3：带内


def test_main_case_lamps() -> None:
    """主算例灯管概算与模块分置逐项断言（ZW-F4~F8，×2 渠按表）。"""
    dims = _dims()
    assert dims["n_lamp_raw"] == pytest.approx(63.36586, abs=1e-3)  # ZW-F4：老化修正
    assert dims["n_lamp"] == pytest.approx(64.0, abs=1e-9)  # 整支向上取整
    assert dims["n_module_raw"] == pytest.approx(8.0, abs=1e-9)  # ZW-F5：64/8
    assert dims["n_module"] == pytest.approx(8.0, abs=1e-9)  # 整模块取整
    assert dims["n_module_series"] == pytest.approx(4.0, abs=1e-9)  # ZW-F6：8/2
    assert dims["l_lamp_zone"] == pytest.approx(2.4, abs=1e-9)  # ZW-F7：4×0.6
    assert dims["l_channel"] == pytest.approx(4.8, abs=1e-9)  # ZW-F8：2×1.2+2.4
    # ZW-F6 模块分置×2 渠断言（四表 R1 口径：n_module = n_module_series×n_channel）
    assert dims["n_module"] == dims["n_module_series"] * 2.0


def test_main_case_check_depth() -> None:
    """主算例接触时间/粪大肠/淹没/渠高/混凝土量逐项断言（ZW-F9~F13）。"""
    dims = _dims()
    assert dims["t_exp"] == pytest.approx(6.135819, abs=1e-4)  # ZW-F9：带内
    assert dims["c_fecal_out"] == pytest.approx(10.0, abs=1e-9)  # ZW-F10：1e5/1e4
    assert dims["h_submerge"] == pytest.approx(0.1, abs=1e-9)  # ZW-F11：≥0 淹没
    assert dims["h_channel"] == pytest.approx(1.1, abs=1e-9)  # ZW-F12
    assert dims["v_concrete"] == pytest.approx(4.4352, abs=1e-6)  # ZW-F13：概算口径
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例三条校核带均合格（实际过流态）


def test_module_series_ceil_placement() -> None:
    """模块分置非整除收口：n_lamp_module=6 → n_module=11、串列=ceil(11/2)=6
    （灯区按渠放大布置：6×2=12 ≥ 11），渠长随灯区放大。"""
    dims = make_unit().compute(_ctx(_params(n_lamp_module=6.0))).dims
    assert isinstance(dims, dict)
    assert dims["n_module"] == pytest.approx(11.0, abs=1e-9)
    assert dims["n_module_series"] == pytest.approx(6.0, abs=1e-9)
    assert dims["n_module_series"] * 2.0 >= dims["n_module"]
    assert dims["l_lamp_zone"] == pytest.approx(3.6, abs=1e-9)  # 6×0.6
    assert dims["l_channel"] == pytest.approx(6.0, abs=1e-9)  # 2×1.2+3.6


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=零去除键透传（全厂终水原样穿流）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_ziwai", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert out_quality.BOD5 == 5.474500  # 透传（removal 全 0.0，不经 apply）
    assert out_quality.CODCR == 16.50599
    assert out_quality.SS == 0.2272045
    assert out_quality.NH3N == 26.0
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_velocity_band_warning() -> None:
    """校核带越界：v_channel=0.25 → h_w 加深、实际流速≈0.235 越 0.3~0.6 带产 WARN
    （实际过流态口径——单渠事故 0.78 m/s 超带为表内注记非运行时警告）。"""
    result = make_unit().compute(_ctx(_params(v_channel=0.25)))
    vel = [w for w in result.warnings if "velocity_band" in w.source]
    assert vel and vel[0].severity is Severity.WARN
    assert vel[0].param_key == "v_channel"
    assert "表内注记非运行时" in vel[0].source
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_channel_act"] == pytest.approx(0.2346886, abs=1e-5)


def test_exposure_band_warning() -> None:
    """校核带越界：n_lamp_module=4+b_c=2.0 → 灯区加长拓宽、t_exp≈13.6 越 5~10 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(n_lamp_module=4.0, b_c=2.0)))
    texp = [w for w in result.warnings if "t_exp_band" in w.source]
    assert texp and texp[0].severity is Severity.WARN
    assert texp[0].param_key == "n_lamp_module"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["t_exp"] == pytest.approx(13.6351, abs=1e-2)


def test_submerge_warning() -> None:
    """灯管淹没校核：h_module=0.7 → h_submerge=−0.1 <0（灯管露出水面）产 WARN。"""
    result = make_unit().compute(_ctx(_params(h_module=0.7)))
    sub = [w for w in result.warnings if "淹没校核" in w.source]
    assert sub and sub[0].severity is Severity.WARN
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["h_submerge"] == pytest.approx(-0.1, abs=1e-9)


def test_param_domain_rejected() -> None:
    """参数域拒绝：n_channel≤0/v_channel≤0/n_lamp_module≤0/q_per_lamp≤0
    → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n_channel=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_channel=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n_lamp_module=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(**{"factor.ziwai.q_per_lamp": 0.0})))


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
    assert result.formula_ids == tuple(f"ZW-F{index}" for index in range(1, 14))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
