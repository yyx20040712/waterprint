"""mine_water_chenshachi golden 数值测试（期望值来源：docs/norms/mine_water_chenshachi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_chenshachi.md 主算例（KC-F1~F10 十项含
#   l_cell=15.0/B=0.8 两离散化项）与副算例（v_h=0.20/t_stay=45 带
#   下限工况 l_cell=9.0/B=1.0）；系数键值逐字取自 data/coefficients
#   0.5.0 factors.yaml（mine_chenshachi 13 键）/removal_rates.yaml
#   （ss 0.15 一键——沉砂仅除砂粒组分，COD 非混凝沉淀滤池段不建键）
#   ——测试区字面量合法。
#
# 【用例面】主算例逐项断言 + 副算例带下限工况对照 + 校核带越界产
#   Warning（实际流速带/堰负荷上限）+ 参数域拒绝（n≤0、v_h≤0、
#   t_stay≤0）+ 纯函数双跑一致 + formula_ids 全部可在公式注册表解析
#   + 出流水质=入质×(1−removal)（SS×0.85，COD 透传）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/chenshachi/tests`
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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.mine_water.chenshachi import make_unit, manifest

# ── 主算例入参（表逐字：Q_design=0.7610416667 m³/s（Kz=1.5 上游口径）、
#    Q_avg_daily=43836.0 m³/d、n=8 格、v_h=0.25 m/s、t_stay=60 s、
#    h2=0.5 m、t_clean=2 d；入流水质=tiaojiechi 表出流——SS 800 穿流） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_chenshachi", port_id="in")
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
        "n": 8.0,
        "v_h": 0.25,
        "t_stay": 60.0,
        "h2": 0.5,
        "t_clean": 2.0,
        "side_disc_step": 0.5,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_chenshachi.velocity_band.min": 0.15,
        "factor.mine_chenshachi.velocity_band.max": 0.3,
        "factor.mine_chenshachi.retention_band.min": 30.0,
        "factor.mine_chenshachi.retention_band.max": 60.0,
        "factor.mine_chenshachi.depth_band.min": 0.4,
        "factor.mine_chenshachi.depth_band.max": 1.2,
        "factor.mine_chenshachi.cell_width.min": 0.6,
        "factor.mine_chenshachi.sand_yield_x": 60.0,
        "factor.mine_chenshachi.hopper.safety": 1.5,
        "factor.mine_chenshachi.weir_load.max": 10.0,
        "factor.mine_chenshachi.superheight": 0.3,
        "factor.mine_chenshachi.wall_thickness_coef": 0.35,
        "factor.mine_chenshachi.elevation_loss": 0.2,
        # removal_rates.yaml mod_default 档逐字（砂粒组分中值）
        "removal.mine_chenshachi.ss.mod_default": 0.15,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_chenshachi",
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
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用仅 SS 键（COD 不建）。"""
    assert manifest.unit_id == "mine_water_chenshachi"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
        ("sludge_out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_chenshachi.ss.mod_default",
    }


def test_main_case_geometry() -> None:
    """主算例（表主算例）池长/断面/池宽/实际流速逐项断言（KC-F1~F4）。"""
    dims = _dims()
    assert dims["l_cell_raw"] == pytest.approx(15.0, abs=1e-9)  # KC-F1：0.25×60
    assert dims["l_cell"] == pytest.approx(15.0, abs=1e-9)  # 0.5 m 档（恰整数）
    assert dims["a_cross"] == pytest.approx(0.3805208333, abs=1e-9)  # KC-F2：/(8×0.25)
    assert dims["b_raw"] == pytest.approx(0.7610416667, abs=1e-9)  # KC-F3：/0.5
    assert dims["b"] == pytest.approx(0.8, abs=1e-9)  # 0.1 m 档向上取整（≥0.6）
    assert dims["v_h_act"] == pytest.approx(0.2378255208, abs=1e-9)  # KC-F4


def test_main_case_sand_weir_concrete() -> None:
    """主算例沉砂/砂斗/堰负荷/总高/混凝土量逐项断言（KC-F5~F10）。"""
    dims = _dims()
    assert dims["v_sand"] == pytest.approx(2.63016, abs=1e-8)  # KC-F5：43836×60/10⁶
    assert dims["v_hopper"] == pytest.approx(7.89048, abs=1e-8)  # KC-F6：×2×1.5
    assert dims["l_weir"] == pytest.approx(132.8, abs=1e-9)  # KC-F7：8×(15+2×0.8)
    assert dims["q_weir"] == pytest.approx(5.7307354418, abs=1e-8)  # KC-F8
    assert dims["h_total"] == pytest.approx(0.8, abs=1e-9)  # KC-F9
    assert dims["v_concrete"] == pytest.approx(26.88, abs=1e-9)  # KC-F10：概算
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例五条校核面均合格


def test_secondary_case_lower_band() -> None:
    """副算例（v_h=0.20、t_stay=45 带下限工况）逐项断言（表副算例）。"""
    dims = _dims(v_h=0.20, t_stay=45.0)
    assert dims["l_cell"] == pytest.approx(9.0, abs=1e-9)  # 0.20×45=9.0
    assert dims["a_cross"] == pytest.approx(0.4756510417, abs=1e-9)
    assert dims["b"] == pytest.approx(1.0, abs=1e-9)  # 0.9513 → 0.1 m 档
    assert dims["v_h_act"] == pytest.approx(0.1902604167, abs=1e-9)
    assert dims["l_weir"] == pytest.approx(88.0, abs=1e-9)  # 8×(9+2×1.0)
    assert dims["q_weir"] == pytest.approx(8.6482007576, abs=1e-8)
    assert dims["v_concrete"] == pytest.approx(20.16, abs=1e-9)
    result = make_unit().compute(_ctx(_params(v_h=0.20, t_stay=45.0)))
    assert result.warnings == ()  # 副算例各校核面均带内合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal)（SS×0.85=680，COD 透传）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_chenshachi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(680.0, abs=1e-9) == out_quality.SS  # 800×(1−0.15)
    assert out_quality.CODCR == 200.0  # 无去除键穿流不变
    assert out_quality.BOD5 is None  # 不建键缺项=None（P6 契约）
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_velocity_band_warning() -> None:
    """校核带越界：v_h=0.15、h2=0.4 → b 收窄为 1.6、v_h_act≈0.1486 越 0.15~0.30 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(v_h=0.15, h2=0.4)))
    vel = [w for w in result.warnings if "velocity_band" in w.source]
    assert vel and vel[0].severity is Severity.WARN
    assert vel[0].param_key == "v_h"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_h_act"] < 0.15  # 越下限实证（构造取整放大断面所致）


def test_weir_load_warning() -> None:
    """校核带越界：v_h=0.18、t_stay=30 → l_weir 短、q_weir 越 ≤10 上限产 WARN。"""
    result = make_unit().compute(_ctx(_params(v_h=0.18, t_stay=30.0)))
    weir = [w for w in result.warnings if "weir_load" in w.source]
    dims = result.dims
    assert isinstance(dims, dict)
    assert weir and weir[0].severity is Severity.WARN
    assert dims["q_weir"] > 10.0  # 越上限实证


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0 / v_h≤0 / t_stay≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_h=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_stay=0.0)))


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
    # GOLDEN4b R1（2026-08-28）：MS-F2 沉砂股衔接式收编（sludge_out 产股消费）
    assert result.formula_ids == (*tuple(f"KC-F{index}" for index in range(1, 11)), "MS-F2")
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"

def test_sludge_out_port() -> None:
    """GOLDEN4a D3 产股口：sludge_out 无条件产股（nongsuo sup 先例同构）。

    值链（手算表 MS-F2 口径）：ds=v_sand×rho_sand_wet×(1−p_sand)×1000
    （KC-F5 湿砂 2.63016 m³/d×湿砂容重 1.6 t/m³×干固分 0.90——3787.4304
    直对 MSLUDGE2 锚）；q_wet=v_sand 直用（湿砂体积——映射表"上游直算
    口径"列）；moisture=p_sand=0.10（hebing p_bio 注入位同源）。湿砂
    容重/含水率系链级衔接键（手算表参数档 1.5~1.7 取 1.6/0.05~0.15 取
    0.10）——manifest 常量直值注记，系数键化归后续批呈报不扩 coefficients。"""
    result = make_unit().compute(_ctx(_params()))
    dims = result.dims
    assert isinstance(dims, dict)
    ref = PortRef(unit_id="test_mine_chenshachi", port_id="sludge_out")
    stock = result.outflows[ref]
    assert isinstance(stock, SludgeFlow)
    assert stock.ds * 86400 == pytest.approx(3787.4304, abs=1e-9)  # MS-F2/MSLUDGE2 锚
    assert stock.q_wet == pytest.approx(dims["v_sand"] / 86400, abs=1e-15)  # KC-F5 直用
    assert stock.q_wet * 86400 == pytest.approx(2.63016, abs=1e-9)
    assert stock.moisture == pytest.approx(0.10, abs=1e-12)
    assert result.outqualities[ref].concentrations == {}  # 空 WaterQuality（GR-04）
