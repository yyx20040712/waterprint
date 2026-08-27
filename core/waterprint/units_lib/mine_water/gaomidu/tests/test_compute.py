"""mine_water_gaomidu golden 数值测试（期望值来源：docs/norms/mine_water_gaomidu.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_gaomidu.md 主算例（KG-F1~F10 十项：q1h=
#   1369.875/v_mix=11.415625/v_floc=273.975/a_settle=228.3125/B=12.5/
#   L=18.5/q_surf_act=5.9237837838/v_axial=0.0019245009/h_total=
#   4.3660254/v_concrete=706.750361625）与副算例（t_mix=1.0、q_surf=8.0
#   负荷带上限工况：B=11.0/L=16.0/q_surf_act=7.7833806818/v_concrete=
#   537.89432928）；系数键值逐字取自 data/coefficients 0.5.0
#   factors.yaml（mine_gaomidu 12 键）/removal_rates.yaml（ss 0.90/
#   cod 0.30 低浓度进水保安段）——测试区字面量合法。
#   sin60° 口径注记：KG-F8/KG-F9 内联 0.86602540=表串原文（斜管倾角
#   60° 构造常量），断言逐位一致（无 π 级截断差）。
#
# 【用例面】主算例逐项断言 + 副算例负荷带上限工况对照 + 校核带越界
#   产 Warning（实际液面负荷带/轴向流速上限/絮凝停留带）+ 参数域拒绝
#   （n≤0、t_mix≤0、q_surf≤0）+ 纯函数双跑一致 + formula_ids 全部可
#   在公式注册表解析 + 出流水质=入质×(1−removal)（SS 68→6.8/COD
#   80→56.0 衔接 vxinglvchi 表）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/gaomidu/tests`
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
from waterprint.units_lib.mine_water.gaomidu import make_unit, manifest

# ── 主算例入参（表逐字：Q_design_h=2739.75 m³/h（Q_avg_daily=43836
#    m³/d、Kz=1.5 上游口径）、n=2 池、t_mix=0.5 min、t_floc=12.0 min、
#    q_surf=6.0 m³/(m²·h)、ratio_lb=1.5、h_super=0.5、h_clear=1.0、
#    h_dist=1.5、h_thick=0.5、l_tube=1.0 m 倾角 60°、wall_coef=0.35；
#    入流水质=cifenli 表出流——SS 68/COD 80） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_gaomidu", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.0, "CODCR": 80.0, "SS": 68.0, "NH3N": 1.0, "TN": 60.0, "TP": 2.0}
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
        "n": 2.0,
        "t_mix": 0.5,
        "t_floc": 12.0,
        "q_surf": 6.0,
        "l_tube": 1.0,
        "h_clear": 1.0,
        "h_dist": 1.5,
        "h_thick": 0.5,
        "side_disc_step": 0.5,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_gaomidu.surface_load_band.min": 5.0,
        "factor.mine_gaomidu.surface_load_band.max": 8.0,
        "factor.mine_gaomidu.t_mix_band.min": 0.5,
        "factor.mine_gaomidu.t_mix_band.max": 2.0,
        "factor.mine_gaomidu.t_floc_band.min": 8.0,
        "factor.mine_gaomidu.t_floc_band.max": 15.0,
        "factor.mine_gaomidu.ratio_lb": 1.5,
        "factor.mine_gaomidu.axial_velocity.max": 0.005,
        "factor.mine_gaomidu.superheight": 0.5,
        "factor.mine_gaomidu.wall_thickness_coef": 0.35,
        "factor.mine_gaomidu.elevation_loss": 0.5,
        # removal_rates.yaml mod_default 档逐字（保安沉淀段）
        "removal.mine_gaomidu.ss.mod_default": 0.9,
        "removal.mine_gaomidu.cod.mod_default": 0.3,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_gaomidu",
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
    assert manifest.unit_id == "mine_water_gaomidu"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_gaomidu.ss.mod_default",
        "CODCR": "removal.mine_gaomidu.cod.mod_default",
    }


def test_main_case_volumes() -> None:
    """主算例（表主算例）单池流量与混合/絮凝容积逐项断言（KG-F1~F3）。"""
    dims = _dims()
    assert dims["q1h"] == pytest.approx(1369.875, abs=1e-9)  # KG-F1：2739.75/2
    assert dims["v_mix"] == pytest.approx(11.415625, abs=1e-9)  # KG-F2：×0.5/60
    assert dims["v_floc"] == pytest.approx(273.975, abs=1e-9)  # KG-F3：×12/60
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例五条校核面均合格


def test_main_case_settle_layout() -> None:
    """主算例沉淀面积/池宽池长（0.5 m 档）/实际负荷/轴向流速逐项断言（KG-F4~F8）。"""
    dims = _dims()
    assert dims["a_settle"] == pytest.approx(228.3125, abs=1e-9)  # KG-F4：1369.875/6
    assert dims["b_raw"] == pytest.approx(12.3372741452, abs=1e-8)  # KG-F5：√(228.3125/1.5)
    assert dims["b"] == pytest.approx(12.5, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["l_raw"] == pytest.approx(18.265, abs=1e-9)  # KG-F6：228.3125/12.5
    assert dims["l"] == pytest.approx(18.5, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["q_surf_act"] == pytest.approx(5.9237837838, abs=1e-9)  # KG-F7：带内
    assert dims["v_axial"] == pytest.approx(0.0019245009, abs=1e-10)  # KG-F8：≤0.005 合格


def test_main_case_depth_concrete() -> None:
    """主算例池总高与概算混凝土量逐项断言（KG-F9~F10）。"""
    dims = _dims()
    assert dims["h_total"] == pytest.approx(4.3660254, abs=1e-9)  # KG-F9：含 l_tube·sin60°
    assert dims["v_concrete"] == pytest.approx(706.750361625, abs=1e-6)  # KG-F10：概算


def test_secondary_case_load_upper() -> None:
    """副算例（t_mix=1.0、q_surf=8.0 负荷带上限工况）逐项断言（表副算例）。"""
    dims = _dims(t_mix=1.0, q_surf=8.0)
    assert dims["v_mix"] == pytest.approx(22.83125, abs=1e-9)
    assert dims["a_settle"] == pytest.approx(171.234375, abs=1e-9)
    assert dims["b"] == pytest.approx(11.0, abs=1e-9)  # √(171.234375/1.5)→0.5 m 档
    assert dims["l"] == pytest.approx(16.0, abs=1e-9)
    assert dims["q_surf_act"] == pytest.approx(7.7833806818, abs=1e-9)  # 带内
    assert dims["v_axial"] == pytest.approx(0.0025660012, abs=1e-10)  # ≤0.005 合格
    assert dims["v_concrete"] == pytest.approx(537.89432928, abs=1e-6)
    result = make_unit().compute(_ctx(_params(t_mix=1.0, q_surf=8.0)))
    assert result.warnings == ()  # 副算例各校核面均带内合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal)（衔接下游 vxinglvchi 表）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_gaomidu", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(6.8, abs=1e-9) == out_quality.SS  # 68×(1−0.90)
    assert pytest.approx(56.0, abs=1e-9) == out_quality.CODCR  # 80×(1−0.30)
    assert out_quality.BOD5 == 5.0  # 无去除键穿流不变
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_surface_load_act_warning() -> None:
    """校核带越界：n=5 池离散放大断面 → q_surf_act 越下带产 WARN（KG-F7 实际负荷面）。

    构造场景（warning 用例参数面允许合成，模板 chuchenchi q_prime=4.8
    先例）：n=5 → q1h=547.95/a_settle=91.325/B=8.0 档/L=11.5 档 →
    q_surf_act=547.95/92=5.9559782609（离散放大断面折减）；带键投影
    收紧 min=6.0（0.5.0 键值域内合成）→ 参数面 6.0 恰带下限合格、
    实际面 5.956<6.0 越下带实证（参数面与实际面双检查独立）。
    """
    result = make_unit().compute(
        _ctx(_params(n=5.0, **{"factor.mine_gaomidu.surface_load_band.min": 6.0}))
    )
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["q_surf_act"] == pytest.approx(547.95 / 92.0, abs=1e-9)
    assert dims["q_surf_act"] < 6.0
    act = [
        w
        for w in result.warnings
        if "surface_load_band" in w.source and "q_surf_act" in w.message
    ]
    assert act and act[0].severity is Severity.WARN
    assert act[0].param_key == "q_surf"


def test_axial_velocity_warning() -> None:
    """校核带越界：q_surf=20 越带且 v_axial=0.006417>0.005 双 WARN（双带独立实证）。

    构造场景（warning 用例参数面允许合成）：q_surf=20（越 5~8 带）→
    v_axial=20/(3600×0.86602540)=0.0064168…>0.005 越轴向上限——
    负荷带与轴向流速两带同场景双触发（两带独立声明）。
    """
    result = make_unit().compute(_ctx(_params(q_surf=20.0)))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_axial"] == pytest.approx(20.0 / (3600 * 0.8660254), abs=1e-10)
    assert dims["v_axial"] > 0.005
    axial = [w for w in result.warnings if "axial_velocity" in w.source]
    assert axial and axial[0].severity is Severity.WARN
    load = [
        w
        for w in result.warnings
        if "surface_load_band" in w.source and "q_surf_act" not in w.message
    ]
    assert load and load[0].severity is Severity.WARN  # 参数面越带同场景触发


def test_floc_retention_band_warning() -> None:
    """校核带越界：t_floc=18.0 越 8~15 带产 WARN（param_key=t_floc）。"""
    result = make_unit().compute(_ctx(_params(t_floc=18.0)))
    floc = [w for w in result.warnings if "t_floc_band" in w.source]
    assert floc and floc[0].severity is Severity.WARN
    assert floc[0].param_key == "t_floc"


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0 / t_mix≤0 / q_surf≤0 / l_tube≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_mix=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(q_surf=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(l_tube=0.0)))


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
    assert result.formula_ids == tuple(f"KG-F{index}" for index in range(1, 11))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
