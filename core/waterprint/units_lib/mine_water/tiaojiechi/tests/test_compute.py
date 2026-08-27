"""mine_water_tiaojiechi golden 数值测试（期望值来源：docs/norms/mine_water_tiaojiechi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_tiaojiechi.md 主算例（KT-F1~F12 十二项含
#   B=10.5/L=29.0/DN700 三离散化项）与副算例（t_reg=12 带上限工况
#   B=12.5/L=37.0/DN700）；系数键值逐字取自 data/coefficients 0.5.0
#   factors.yaml（mine_tiaojiechi 11 键）/removal_rates.yaml（ss/cod
#   显式 0.0 穿流两键；BOD5 全线不建键）——测试区字面量合法。
#
# 【用例面】主算例逐项断言 + 副算例带上限工况对照（越上带产 WARN）
#   + 校核带越界产 Warning（实际停留时间带/有效水深带）+ 参数域拒绝
#   （n≤0、t_reg≤0、h2≤0）+ 纯函数双跑一致 + formula_ids 全部可在公式
#   注册表解析 + 出流水质=入质×(1−removal)（SS/COD 零去除穿流）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/tiaojiechi/tests`
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
from waterprint.units_lib.mine_water.tiaojiechi import make_unit, manifest

# ── 主算例入参（表逐字：Q_avg_daily=43836.0 m³/d（Kz=1.5 上游口径）、
#    n=16 分格、t_reg=8.0 h、h2=3.0 m、ratio_lb=3.0；入流水质=input 表
#    出流——SS 800/COD 200 双指标面） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_tiaojiechi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"CODCR": 200.0, "SS": 800.0, "NH3N": 1.0, "TN": 60.0, "TP": 2.0}
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
        "n": 16.0,
        "t_reg": 8.0,
        "h2": 3.0,
        "ratio_lb": 3.0,
        "side_disc_step": 0.5,
        "length_disc_step": 0.05,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_tiaojiechi.hrt_band.min": 8.0,
        "factor.mine_tiaojiechi.hrt_band.max": 12.0,
        "factor.mine_tiaojiechi.depth_band.min": 3.0,
        "factor.mine_tiaojiechi.depth_band.max": 5.0,
        "factor.mine_tiaojiechi.ratio_lb_band.min": 2.0,
        "factor.mine_tiaojiechi.ratio_lb_band.max": 4.0,
        "factor.mine_tiaojiechi.superheight": 0.5,
        "factor.mine_tiaojiechi.stir.power_density": 8.0,
        "factor.mine_tiaojiechi.overflow_velocity": 1.5,
        "factor.mine_tiaojiechi.wall_thickness_coef": 0.35,
        "factor.mine_tiaojiechi.elevation_loss": 0.3,
        # removal_rates.yaml mod_default 档逐字（纯均化零去除穿流）
        "removal.mine_tiaojiechi.ss.mod_default": 0.0,
        "removal.mine_tiaojiechi.cod.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_tiaojiechi",
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
    assert manifest.unit_id == "mine_water_tiaojiechi"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_tiaojiechi.ss.mod_default",
        "CODCR": "removal.mine_tiaojiechi.cod.mod_default",
    }


def test_main_case_basin() -> None:
    """主算例（表主算例）调节容积与单格几何逐项断言（KT-F1~F8）。"""
    dims = _dims()
    assert dims["v_total"] == pytest.approx(14612.0, abs=1e-6)  # KT-F1
    assert dims["v1"] == pytest.approx(913.25, abs=1e-9)  # KT-F2：/16
    assert dims["a1"] == pytest.approx(304.4166666667, abs=1e-8)  # KT-F3：/3.0
    assert dims["b_raw"] == pytest.approx(10.0733421575, abs=1e-8)  # KT-F4
    assert dims["b"] == pytest.approx(10.5, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["l_raw"] == pytest.approx(28.9920634921, abs=1e-8)  # KT-F5
    assert dims["l"] == pytest.approx(29.0, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["a_act"] == pytest.approx(304.5, abs=1e-9)  # KT-F6
    assert dims["v_act_total"] == pytest.approx(14616.0, abs=1e-6)  # KT-F7：≥v_total
    assert dims["t_reg_act"] == pytest.approx(8.0021899808, abs=1e-8)  # KT-F8


def test_main_case_outlet_concrete() -> None:
    """主算例搅拌/出水管/总高/混凝土量逐项断言（KT-F9~F12）。"""
    dims = _dims()
    assert dims["p_stir"] == pytest.approx(116.928, abs=1e-9)  # KT-F9：全池
    assert dims["d_out_raw"] == pytest.approx(0.6562480375, abs=1e-7)  # KT-F10
    assert dims["dn_out"] == pytest.approx(0.70, abs=1e-9)  # DN700（0.05 m 档）
    assert dims["h_total"] == pytest.approx(3.5, abs=1e-9)  # KT-F11
    assert dims["v_concrete"] == pytest.approx(5968.2, abs=1e-6)  # KT-F12：概算
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例四条校核面均合格


def test_secondary_case_upper_band() -> None:
    """副算例（t_reg=12 带上限工况）逐项断言+实际停留越上带产 WARN。

    表副算例：v_total=21918/B=12.5/L=37.0/t_reg_act=12.1543936491
    （越上带 12——构造取整放大所致，贴限记录归表内追认点 3）/
    p_stir=177.6/DN700。
    """
    dims = _dims(t_reg=12.0)
    assert dims["v_total"] == pytest.approx(21918.0, abs=1e-6)
    assert dims["b"] == pytest.approx(12.5, abs=1e-9)
    assert dims["l"] == pytest.approx(37.0, abs=1e-9)
    assert dims["v_act_total"] == pytest.approx(22200.0, abs=1e-6)
    assert dims["t_reg_act"] == pytest.approx(12.1543936491, abs=1e-8)
    assert dims["p_stir"] == pytest.approx(177.6, abs=1e-9)
    assert dims["dn_out"] == pytest.approx(0.70, abs=1e-9)
    result = make_unit().compute(_ctx(_params(t_reg=12.0)))
    hrt = [w for w in result.warnings if "hrt_band" in w.source]
    assert hrt and hrt[0].severity is Severity.WARN
    assert hrt[0].param_key == "t_reg"


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal) 零去除穿流，余指标透传。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_tiaojiechi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(800.0, abs=1e-9) == out_quality.SS  # ×(1−0.0) 穿流
    assert pytest.approx(200.0, abs=1e-9) == out_quality.CODCR
    assert out_quality.BOD5 is None  # 不建键缺项=None（P6 契约）
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_depth_band_warning() -> None:
    """校核带越界：h2=6.0 越矿井水带 3.0~5.0 产 WARN（param_key=h2）。"""
    result = make_unit().compute(_ctx(_params(h2=6.0)))
    dep = [w for w in result.warnings if "depth_band" in w.source]
    assert dep and dep[0].severity is Severity.WARN
    assert dep[0].param_key == "h2"


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0 / t_reg≤0 / h2≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_reg=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(h2=0.0)))


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
    assert result.formula_ids == tuple(f"KT-F{index}" for index in range(1, 13))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
