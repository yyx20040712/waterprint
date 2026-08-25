"""municipal_tiaojiechi golden 数值测试（期望值来源：docs/norms/tiaojiechi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=四表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/tiaojiechi.md 算例 1（含 B=22.0/L=53.0/DN=0.9 离散化项）；
#   系数键值逐字取自 data/coefficients 0.3.0 数据包 factors/removal_rates
#   yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（v_total/v1/a1/b_raw/B/l_raw/L/a_act/
#   v_act_total/t_reg_act/p_stir/q_pump1/d_overflow/h_total/v_concrete）+
#   校核带越界产 Warning（停留时间带/有效水深带/长宽比带/调节容积
#   充足性）+ 参数域拒绝（n≤0/t_reg≤0/搅拌功率密度≤0/溢流管流速≤0
#   溢流·搅拌档负例）+ 纯函数双跑一致 + formula_ids 全部可在公式注册表
#   解析。
# 【口径注记】入流水质=四表衔接式值（SS 186.4242/BOD5 164.3994/
#   COD 285.6232，上游沉砂池出流链）；出流=零去除键透传（全指标
#   原样穿流，与 M1a 三单元 ×(1−r) 形态差异记档）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/tiaojiechi/tests`
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
from waterprint.units_lib.municipal.tiaojiechi import make_unit, manifest

# ── 算例 1 入参（四表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    四表衔接式值——上游粗格栅/细格栅/旋流沉砂池去除链后） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_tiaojiechi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 164.3994, "CODCR": 285.6232, "SS": 186.4242, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
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
        "t_reg": 8.0,
        "h2": 5.0,
        "ratio_lb": 2.5,
        "n_pump_duty": 2.0,
        "side_disc_step": 0.5,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.3.0 M2b1 四单元批）逐字
        "factor.tiaojiechi.hrt_band.min": 6.0,
        "factor.tiaojiechi.hrt_band.max": 12.0,
        "factor.tiaojiechi.depth_band.min": 4.0,
        "factor.tiaojiechi.depth_band.max": 6.0,
        "factor.tiaojiechi.ratio_lb_band.min": 2.0,
        "factor.tiaojiechi.ratio_lb_band.max": 3.0,
        "factor.tiaojiechi.superheight": 0.5,
        "factor.tiaojiechi.stir.power_density": 6.0,
        "factor.tiaojiechi.overflow_velocity": 0.9,
        "factor.tiaojiechi.wall_thickness_coef": 0.35,
        "factor.tiaojiechi.elevation_loss": 0.5,
        # removal_rates.yaml mod_default 档逐字（物理均化无去除）
        "removal.tiaojiechi.bod5.mod_default": 0.0,
        "removal.tiaojiechi.cod.mod_default": 0.0,
        "removal.tiaojiechi.ss.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_tiaojiechi",
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
    assert manifest.unit_id == "municipal_tiaojiechi"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.tiaojiechi.bod5.mod_default",
        "CODCR": "removal.tiaojiechi.cod.mod_default",
        "SS": "removal.tiaojiechi.ss.mod_default",
    }


def test_main_case_basin() -> None:
    """主算例（四表算例 1）调节容积与池体几何逐项断言（TJ-F1~F8）。"""
    dims = _dims()
    assert dims["v_total"] == pytest.approx(11586.9, abs=1e-6)  # TJ-F1：平均日口径
    assert dims["v1"] == pytest.approx(5793.45, abs=1e-6)  # TJ-F2
    assert dims["a1"] == pytest.approx(1158.69, abs=1e-6)  # TJ-F3
    assert dims["b_raw"] == pytest.approx(21.52848, abs=1e-4)  # TJ-F4：√463.476
    assert dims["b"] == pytest.approx(22.0, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["l_raw"] == pytest.approx(52.66773, abs=1e-4)  # TJ-F5
    assert dims["l"] == pytest.approx(53.0, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["a_act"] == pytest.approx(1166.0, abs=1e-9)  # TJ-F6
    assert dims["v_act_total"] == pytest.approx(11660.0, abs=1e-6)  # TJ-F7：≥v_total
    assert dims["t_reg_act"] == pytest.approx(8.050471, abs=1e-5)  # TJ-F8：带内


def test_main_case_stir_pump_depth() -> None:
    """主算例搅拌/出水泵/溢流管/总高/混凝土量逐项断言（TJ-F9~F13）。"""
    dims = _dims()
    assert dims["p_stir"] == pytest.approx(69.96, abs=1e-9)  # TJ-F9：全池
    assert dims["q_pump1"] == pytest.approx(724.18125, abs=1e-9)  # TJ-F10：平均时
    assert dims["d_overflow"] == pytest.approx(0.9, abs=1e-9)  # TJ-F11：DN900，0.1 m 档
    assert dims["h_total"] == pytest.approx(5.5, abs=1e-9)  # TJ-F12：整值
    assert dims["v_concrete"] == pytest.approx(4489.10, abs=1e-6)  # TJ-F13：概算口径
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例四条校核带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=零去除键透传（全指标原样穿流）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_tiaojiechi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert out_quality.BOD5 == 164.3994  # 透传（removal 全 0.0，不经 apply）
    assert out_quality.CODCR == 285.6232
    assert out_quality.SS == 186.4242
    assert out_quality.NH3N == 26.0
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_hrt_band_warning() -> None:
    """校核带越界：t_reg=13 → 实际停留时间≈13.006 越 6~12 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(t_reg=13.0)))
    hrt = [w for w in result.warnings if "hrt_band" in w.source]
    assert hrt and hrt[0].severity is Severity.WARN
    assert hrt[0].param_key == "t_reg"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["t_reg_act"] == pytest.approx(13.0061, abs=1e-3)


def test_depth_and_ratio_band_warnings() -> None:
    """校核带越界：h2=3.5 越深带；ratio_lb=3.5 越长宽比带（param_key 归因）。"""
    dep = [
        w for w in make_unit().compute(_ctx(_params(h2=3.5))).warnings
        if "depth_band" in w.source
    ]
    assert dep and dep[0].severity is Severity.WARN
    assert dep[0].param_key == "h2"
    ratio = [
        w for w in make_unit().compute(_ctx(_params(ratio_lb=3.5))).warnings
        if "ratio_lb_band" in w.source
    ]
    assert ratio and ratio[0].severity is Severity.WARN
    assert ratio[0].param_key == "ratio_lb"


def test_volume_sufficiency_invariant() -> None:
    """调节容积充足性不变式（TJ-F7 表内校核行）：B/L 双 0.5 m 档 ceil
    构造保证 v_act_total ≥ v_total（l_raw=a1/ceil(b_raw) 后再 ceil，
    b×l ≥ a1 恒成立）——三组参数扰动下校核合格（无容积警告）且逐例
    满足不等式；compute 侧守卫为不变式防线（含浮点安全网）。
    """
    for overrides in ({}, {"t_reg": 12.0}, {"side_disc_step": 0.01}):
        result = make_unit().compute(_ctx(_params(**overrides)))
        dims = result.dims
        assert isinstance(dims, dict)
        assert dims["v_act_total"] >= dims["v_total"]
        assert not [w for w in result.warnings if "调节容积校核" in w.source]


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0/t_reg≤0/搅拌功率密度≤0/溢流管流速≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_reg=0.0)))
    # 溢流/搅拌档负例（系数投影面，物理域守卫）
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(**{"factor.tiaojiechi.overflow_velocity": -0.5})))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(**{"factor.tiaojiechi.stir.power_density": 0.0})))


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
    assert result.formula_ids == tuple(f"TJ-F{index}" for index in range(1, 14))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
