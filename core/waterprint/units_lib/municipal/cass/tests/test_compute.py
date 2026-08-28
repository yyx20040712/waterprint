"""municipal_cass golden 数值测试（期望值来源：docs/norms/cass.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-26 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/cass.md 算例 1（含 n_decant=2/l_pool=47.0/b_pool=19.0
#   离散化项）；系数键值逐字取自 data/coefficients 0.4.0 数据包
#   factors/removal_rates yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（n_cycle/v_draw/v_load/v_selector/v_bio/
#   h_draw_max/a_draw/a_load/a_pool/h_draw/v_pool/v_plant/t_phase_sum/
#   q_decant/n_decant_raw/n_decant/s_y/q_wet/theta_c/x_vss/o2_四式/
#   ns_act/h_pool/l_pool/b_pool/v_concrete）+ 两条不变性断言
#   （business-logic §8 行 8 联动）：①时段和=周期（t_phase_sum ==
#   t_cycle；破坏配比=InvalidUnitConfig 域拒）②滗水容积≤池容
#   （h_draw ≤ h_draw_max=h2/3 且 v_draw ≤ v_pool）+ 池数守卫 Ruling ④
#   （n_pool=0 拒；n_pool=1 compute 层放行=grid 层职责）+ AAO 同族量
#   断言（v_load==aao 表 v_o=10714.95/o2 同值）+ 校核带越界产 Warning
#   （ns 带/泥龄带/滗水带）+ 纯函数双跑一致 + formula_ids 全部可在
#   公式注册表解析。
# 【口径注记】入流水质=三表衔接式值（BOD5 123.2996/COD 199.9362/
#   SS 93.2121——初沉出流，与 aao 表同入流）；出流=×(1−removal.cass.*)
#   AAO 同族形态（BOD5 12.32996/COD 29.99043/SS 9.32121）。
# 【容差注记】引擎 q_avg_daily = 34760.7/86400 精确值，本表 m³/d 面
#   手算与引擎差异仅浮点尾数（<1e-6 相对），1e-3 容差覆盖。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/cass/tests`
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
from waterprint.units_lib.municipal.cass import make_unit, manifest

# ── 算例 1 入参（三表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    三表衔接式值——初沉出流，与 aao 表同入流） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_cass", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 123.2996, "CODCR": 199.9362, "SS": 93.2121, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
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
        "n_pool": 4.0,
        "t_cycle": 4.0,
        "t_react": 2.0,
        "t_settle": 1.0,
        "t_draw": 1.0,
        "ns": 0.10,
        "x_mlss": 4000.0,
        "t_selector": 0.75,
        "h2": 5.0,
        "ratio_lb": 2.5,
        "tn_eff": 15.0,
        "side_disc_step": 0.5,
        # data/coefficients factors.yaml（0.4.0 M2c 三单元批）逐字
        "factor.cass.ns_band.min": 0.05,
        "factor.cass.ns_band.max": 0.15,
        "factor.cass.mlss_band.min": 3000.0,
        "factor.cass.mlss_band.max": 5000.0,
        "factor.cass.sludge_age_band.min": 15.0,
        "factor.cass.sludge_age_band.max": 25.0,
        "factor.cass.draw_band.min": 1.0,
        "factor.cass.draw_band.max": 2.0,
        "factor.cass.selector_band.min": 0.5,
        "factor.cass.selector_band.max": 1.0,
        "factor.cass.yield.y": 0.5,
        "factor.cass.o2.a_prime": 0.5,
        "factor.cass.o2.b_prime": 0.10,
        "factor.cass.vss_ratio": 0.75,
        "factor.cass.sludge.moisture": 0.994,
        "factor.cass.decant.q_per_unit": 800.0,
        "factor.cass.superheight": 0.5,
        "factor.cass.wall_thickness_coef": 0.40,
        "factor.cass.elevation_loss": 0.5,
        # removal_rates.yaml mod_default 档逐字（AAO 同族档+N/P 三键 0.8.0
        # NP1/RATIFY3——tn 档 0.70 略低于 aao 0.75，SBR 时空分档）
        "removal.cass.bod5.mod_default": 0.90,
        "removal.cass.cod.mod_default": 0.85,
        "removal.cass.ss.mod_default": 0.90,
        "removal.cass.nh3n.mod_default": 0.90,
        "removal.cass.tn.mod_default": 0.70,
        "removal.cass.tp.mod_default": 0.93,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_cass",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims(**overrides: float) -> dict[str, float]:
    """主算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params(**overrides))).dims
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包（AAO 同族档）。"""
    assert manifest.unit_id == "municipal_cass"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {  # 六指标全键（N/P 三键 NP1/RATIFY3）
        "BOD5": "removal.cass.bod5.mod_default",
        "CODCR": "removal.cass.cod.mod_default",
        "SS": "removal.cass.ss.mod_default",
        "NH3N": "removal.cass.nh3n.mod_default",
        "TN": "removal.cass.tn.mod_default",
        "TP": "removal.cass.tp.mod_default",
    }


def test_pool_grid_declared() -> None:
    """池数守卫 Ruling ④：档位下限经 ParamSpec.grid 声明（[2,3,4,5,6]），
    compute 不硬编码 ≥2（n_pool=1 放行=grid 层职责）。"""
    by_field = {spec.field_id: spec for spec in manifest.params}
    assert by_field["n_pool"].grid == (2.0, 3.0, 4.0, 5.0, 6.0)
    assert by_field["t_cycle"].grid == (4.0, 6.0, 8.0)
    single = make_unit().compute(_ctx(_params(n_pool=1.0)))
    assert isinstance(single.dims, dict) and single.dims["v_plant"] > 0.0


def test_main_case_cycle_volumes() -> None:
    """主算例（三表算例 1）周期与容积逐项断言（CA-F1~F5/F12）。"""
    dims = _dims()
    assert dims["n_cycle"] == pytest.approx(6.0, abs=1e-9)  # CA-F1：4h 档
    assert dims["v_draw"] == pytest.approx(1448.3625, abs=1e-3)  # CA-F2：34760.7/(4×6)
    assert dims["v_load"] == pytest.approx(10714.95, abs=1e-2)  # CA-F3：=aao 表 v_o
    assert dims["v_selector"] == pytest.approx(1086.272, abs=1e-2)  # CA-F4
    assert dims["v_bio"] == pytest.approx(11801.22, abs=1e-2)  # CA-F5


def test_main_case_draw_control() -> None:
    """主算例滗水 1/3 池深双控逐项断言（CA-F6~F12）——滗水控制工况。"""
    dims = _dims()
    assert dims["h_draw_max"] == pytest.approx(1.666667, abs=1e-5)  # CA-F6：h2/3
    assert dims["a_draw"] == pytest.approx(869.018, abs=1e-2)  # CA-F7
    assert dims["a_load"] == pytest.approx(590.061, abs=1e-2)  # CA-F8
    assert dims["a_pool"] == pytest.approx(869.018, abs=1e-2)  # CA-F9：max 取大
    assert dims["h_draw"] == pytest.approx(1.666667, abs=1e-5)  # CA-F10：=h2/3
    assert dims["v_pool"] == pytest.approx(4345.088, abs=1e-2)  # CA-F11
    assert dims["v_plant"] == pytest.approx(17380.35, abs=1e-2)  # CA-F12


def test_main_case_decant_sludge_oxygen() -> None:
    """主算例滗水器/剩余污泥/需氧量逐项断言（CA-F13~F22，AAO 同族口径）。"""
    dims = _dims()
    assert dims["t_phase_sum"] == pytest.approx(4.0, abs=1e-9)  # CA-F13：时段和
    assert dims["q_decant"] == pytest.approx(1448.3625, abs=1e-3)  # CA-F14
    assert dims["n_decant_raw"] == pytest.approx(1.810453, abs=1e-4)  # CA-F15
    assert dims["n_decant"] == pytest.approx(2.0, abs=1e-9)  # 整台向上取整
    assert dims["s_y"] == pytest.approx(1928.691, abs=1e-2)  # CA-F16：同 aao
    assert dims["q_wet"] == pytest.approx(321.4485, abs=1e-2)  # CA-F17
    assert dims["theta_c"] == pytest.approx(22.22222, abs=1e-3)  # CA-F18：带内
    assert dims["x_vss"] == pytest.approx(3000.0, abs=1e-9)
    assert dims["o2_carbon"] == pytest.approx(5143.176, abs=1e-1)  # CA-F19：同 aao
    assert dims["o2_nit"] == pytest.approx(4447.979, abs=1e-1)  # CA-F20
    assert dims["o2_denit"] == pytest.approx(2783.637, abs=1e-1)  # CA-F21
    assert dims["o2_total"] == pytest.approx(6807.519, abs=1e-1)  # CA-F22


def test_main_case_geometry() -> None:
    """主算例实际负荷/池体几何/混凝土量逐项断言（CA-F23~F27）。"""
    dims = _dims()
    assert dims["ns_act"] == pytest.approx(0.0679, abs=1e-4)  # CA-F23：滗水控制裕量
    assert dims["h_pool"] == pytest.approx(5.5, abs=1e-9)  # CA-F24
    assert dims["l_pool_raw"] == pytest.approx(46.61055, abs=1e-3)  # CA-F25
    assert dims["l_pool"] == pytest.approx(47.0, abs=1e-9)  # 0.5 m 档取整
    assert dims["b_pool_raw"] == pytest.approx(18.64422, abs=1e-3)  # CA-F26
    assert dims["b_pool"] == pytest.approx(19.0, abs=1e-9)  # 0.5 m 档取整
    assert dims["v_concrete"] == pytest.approx(7647.354, abs=1e-1)  # CA-F27：概算
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例六条校核带均合格


def test_invariant_phase_sum_equals_cycle() -> None:
    """不变性①（business-logic §8 行 8）：时段和=周期——主算例成立，
    破坏配比（t_cycle=6 而时段 2/1/1）= InvalidUnitConfig 域拒。"""
    dims = _dims()
    assert dims["t_phase_sum"] == pytest.approx(4.0, abs=1e-9)
    assert dims["t_phase_sum"] == pytest.approx(_params()["t_cycle"], abs=1e-9)
    with pytest.raises(InvalidUnitConfig, match="时段和=周期不变性破坏"):
        make_unit().compute(_ctx(_params(t_cycle=6.0)))


def test_invariant_draw_within_pool() -> None:
    """不变性②（business-logic §8 行 8）：滗水容积≤池容——h_draw≤h2/3
    双控构造恒成立（含换池数/周期扰动面）。"""
    for overrides in ({}, {"n_pool": 2.0}, {"n_pool": 6.0}):
        dims = _dims(**overrides)
        assert dims["h_draw"] <= dims["h_draw_max"] + 1e-9
        assert dims["v_draw"] <= dims["v_pool"]
        assert dims["a_pool"] >= dims["a_load"] and dims["a_pool"] >= dims["a_draw"] - 1e-9


def test_outflow_and_quality_aao_family() -> None:
    """出流透传（水量不变）+ 出水质=×(1−removal) AAO 同族形态（与 aao 出流同值）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_cass", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    out_conc = out_quality.concentrations
    assert out_conc["BOD5"] == pytest.approx(12.32996, abs=1e-6)  # 123.2996×0.10
    assert out_conc["CODCR"] == pytest.approx(29.99043, abs=1e-6)  # ×0.15
    assert out_conc["SS"] == pytest.approx(9.32121, abs=1e-6)  # ×0.10
    assert out_conc["NH3N"] == pytest.approx(2.6)  # N/P 六键去除[NP1/RATIFY3]
    assert out_conc["TN"] == pytest.approx(12.9)
    assert out_conc["TP"] == pytest.approx(0.455)


def test_band_warnings() -> None:
    """校核带越界产 WARN：ns=0.2（负荷带）/ns=0.05（泥龄带 44.4>25）/
    h2=9.0（滗水带 h_draw=3.0>2.0）。"""
    result = make_unit().compute(_ctx(_params(ns=0.20)))
    ns_warn = [w for w in result.warnings if "ns_band" in w.source and "实际" not in w.message]
    assert ns_warn and ns_warn[0].severity is Severity.WARN
    assert ns_warn[0].param_key == "ns"
    result = make_unit().compute(_ctx(_params(ns=0.05)))
    age_warn = [w for w in result.warnings if "sludge_age_band" in w.source]
    assert age_warn and age_warn[0].severity is Severity.WARN
    result = make_unit().compute(_ctx(_params(h2=9.0)))
    draw_warn = [w for w in result.warnings if "draw_band" in w.source]
    assert draw_warn and draw_warn[0].severity is Severity.WARN
    assert draw_warn[0].param_key == "h2"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["h_draw"] == pytest.approx(3.0, abs=1e-6)  # 9/3 双控取大后


def test_param_domain_rejected() -> None:
    """参数域拒绝：n_pool=0（Ruling ④ 数学有效性守卫）/ns=0/t_cycle=0/
    含水率越 (0,1) → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n_pool=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(ns=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_cycle=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(**{"factor.cass.sludge.moisture": 1.0})))


def test_missing_quality_rejected() -> None:
    """入流缺 BOD5/TN 浓度=InvalidUnitConfig（CA-F3/F20 计算前提）。"""
    ctx = UnitContext(
        unit_id="test_cass",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: WaterQuality({"SS": 93.2121})},
        params=_params(),
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )
    with pytest.raises(InvalidUnitConfig, match="BOD5/TN"):
        make_unit().compute(ctx)


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings
    assert first.formula_ids == second.formula_ids


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"CA-F{index}" for index in range(1, 28))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
