"""mine_water_ningjiao golden 数值测试（期望值来源：docs/norms/mine_water_ningjiao.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_ningjiao.md 主算例（KN-F1~F15 十五项含 B=4.5
#   离散化项与 p1~p4 四区功率）与副算例（t_floc=4.0 絮凝档上限工况
#   B=5.5/gt=93900）；系数键值逐字取自 data/coefficients 0.5.0
#   factors.yaml（mine_ningjiao 24 键）/removal_rates.yaml（ss/cod 显式
#   0.0 穿流两键——反应无分离，去除挂下游分离单元）——测试区字面量合法。
#
# 【用例面】主算例逐项断言 + 副算例絮凝档上限工况对照 + 校核带越界
#   产 Warning（GT 带/停留带）+ 参数域拒绝（n≤0、t_mix≤0）+ 纯函数
#   双跑一致 + formula_ids 全部可在公式注册表解析 + 出流水质=入质×
#   (1−removal)（SS/COD 零变化穿流）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/ningjiao/tests`
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
from waterprint.units_lib.mine_water.ningjiao import make_unit, manifest

# ── 主算例入参（表逐字：Q_design_h=2739.75 m³/h（Q_avg_daily=43836
#    m³/d、Kz=1.5 上游口径）、n=2 池（q1=1369.875 m³/h）、t=
#    1.0/2.0/3.0/1.5 min、G=600/300/80/30 s⁻¹、h2=3.0 m；入流水质=
#    chenshachi 表出流——SS 680/COD 200） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_ningjiao", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.0, "CODCR": 200.0, "SS": 680.0, "NH3N": 1.0, "TN": 60.0, "TP": 2.0}
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
        "t_mix": 1.0,
        "t_seed": 2.0,
        "t_floc": 3.0,
        "t_ripen": 1.5,
        "h2": 3.0,
        "ratio_lb": 1.2,
        "side_disc_step": 0.5,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_ningjiao.t_mix_band.min": 0.5,
        "factor.mine_ningjiao.t_mix_band.max": 2.0,
        "factor.mine_ningjiao.t_seed_band.min": 1.0,
        "factor.mine_ningjiao.t_seed_band.max": 3.0,
        "factor.mine_ningjiao.t_floc_band.min": 2.0,
        "factor.mine_ningjiao.t_floc_band.max": 4.0,
        "factor.mine_ningjiao.t_ripen_band.min": 1.0,
        "factor.mine_ningjiao.t_ripen_band.max": 2.0,
        "factor.mine_ningjiao.g_mix": 600.0,
        "factor.mine_ningjiao.g_seed": 300.0,
        "factor.mine_ningjiao.g_floc": 80.0,
        "factor.mine_ningjiao.g_ripen": 30.0,
        "factor.mine_ningjiao.gt_band.min": 10000.0,
        "factor.mine_ningjiao.gt_band.max": 100000.0,
        "factor.mine_ningjiao.depth_band.min": 2.5,
        "factor.mine_ningjiao.depth_band.max": 4.0,
        "factor.mine_ningjiao.cell_ratio_lb_band.min": 0.8,
        "factor.mine_ningjiao.cell_ratio_lb_band.max": 1.5,
        "factor.mine_ningjiao.dose.pac": 40.0,
        "factor.mine_ningjiao.dose.pam": 1.0,
        "factor.mine_ningjiao.seed.dose": 500.0,
        "factor.mine_ningjiao.superheight": 0.4,
        "factor.mine_ningjiao.wall_thickness_coef": 0.35,
        "factor.mine_ningjiao.elevation_loss": 0.3,
        # removal_rates.yaml mod_default 档逐字（反应无分离穿流）
        "removal.mine_ningjiao.ss.mod_default": 0.0,
        "removal.mine_ningjiao.cod.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_ningjiao",
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
    assert manifest.unit_id == "mine_water_ningjiao"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_ningjiao.ss.mod_default",
        "CODCR": "removal.mine_ningjiao.cod.mod_default",
    }


def test_main_case_zones() -> None:
    """主算例（表主算例）四分区容积与总停留逐项断言（KN-F1~F5）。"""
    dims = _dims()
    assert dims["v1"] == pytest.approx(22.83125, abs=1e-9)  # KN-F1：1369.875×1/60
    assert dims["v2"] == pytest.approx(45.6625, abs=1e-9)  # KN-F2：×2/60
    assert dims["v3"] == pytest.approx(68.49375, abs=1e-9)  # KN-F3：×3/60
    assert dims["v4"] == pytest.approx(34.246875, abs=1e-9)  # KN-F4：×1.5/60
    assert dims["t_total"] == pytest.approx(7.5, abs=1e-9)  # KN-F5：≤12 合格


def test_main_case_power() -> None:
    """主算例四区搅拌功率与全厂装机逐项断言（KN-F6 泛式四次求值）。"""
    dims = _dims()
    assert dims["p1"] == pytest.approx(8.21925, abs=1e-8)  # 0.001×600²×22.83125/1000
    assert dims["p2"] == pytest.approx(4.109625, abs=1e-8)
    assert dims["p3"] == pytest.approx(0.43836, abs=1e-8)
    assert dims["p4"] == pytest.approx(0.0308221875, abs=1e-10)
    assert dims["p_total"] == pytest.approx(25.5961143750, abs=1e-8)  # Σp×2 池


def test_main_case_layout() -> None:
    """主算例分区面积/池宽（0.5 m 档）/各区池长/总 GT 逐项断言（KN-F7~F10）。"""
    dims = _dims()
    assert dims["a1"] == pytest.approx(7.6104166667, abs=1e-8)  # KN-F7：v1/3.0
    assert dims["a2"] == pytest.approx(15.2208333333, abs=1e-8)
    assert dims["a3"] == pytest.approx(22.83125, abs=1e-9)  # a_max=絮凝区
    assert dims["a4"] == pytest.approx(11.415625, abs=1e-9)
    assert dims["b_raw"] == pytest.approx(4.3618851047, abs=1e-7)  # KN-F8：√(22.83125/1.2)
    assert dims["b"] == pytest.approx(4.5, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["l1"] == pytest.approx(1.6912037037, abs=1e-8)  # KN-F9：a1/4.5
    assert dims["l2"] == pytest.approx(3.3824074074, abs=1e-8)
    assert dims["l3"] == pytest.approx(5.0736111111, abs=1e-8)
    assert dims["l4"] == pytest.approx(2.5368055556, abs=1e-8)
    assert dims["gt_total"] == pytest.approx(89100.0, abs=1e-6)  # KN-F10：带内


def test_main_case_dose_concrete() -> None:
    """主算例药剂耗量（平均日口径）/总高/混凝土量逐项断言（KN-F11~F15）。"""
    dims = _dims()
    assert dims["m_pac"] == pytest.approx(1753.44, abs=1e-6)  # KN-F11：43836×40/1000
    assert dims["m_pam"] == pytest.approx(43.836, abs=1e-8)  # KN-F12
    assert dims["m_seed"] == pytest.approx(21918.0, abs=1e-6)  # KN-F13：21.918 t/d 投加
    assert dims["h_total"] == pytest.approx(3.4, abs=1e-9)  # KN-F14
    assert dims["v_concrete"] == pytest.approx(135.8459375, abs=1e-6)  # KN-F15：概算
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例七条校核面均合格


def test_secondary_case_floc_upper() -> None:
    """副算例（t_floc=4.0 絮凝档上限工况）逐项断言（表副算例）。"""
    dims = _dims(t_floc=4.0)
    assert dims["v3"] == pytest.approx(91.325, abs=1e-9)
    assert dims["t_total"] == pytest.approx(8.5, abs=1e-9)
    assert dims["p3"] == pytest.approx(0.58448, abs=1e-8)
    assert dims["p_total"] == pytest.approx(25.8883543750, abs=1e-8)
    assert dims["b"] == pytest.approx(5.5, abs=1e-9)  # √(30.4417/1.2)→0.5 m 档
    assert dims["l3"] == pytest.approx(5.5348484848, abs=1e-8)
    assert dims["gt_total"] == pytest.approx(93900.0, abs=1e-6)  # 带内合格
    assert dims["v_concrete"] == pytest.approx(153.9587291667, abs=1e-6)
    result = make_unit().compute(_ctx(_params(t_floc=4.0)))
    assert result.warnings == ()  # 副算例各校核面均带内合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal) 零变化穿流。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_ningjiao", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(680.0, abs=1e-9) == out_quality.SS  # ×(1−0.0) 穿流
    assert pytest.approx(200.0, abs=1e-9) == out_quality.CODCR
    assert out_quality.BOD5 == 5.0  # 无去除键穿流不变
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_gt_band_warning() -> None:
    """校核带越界：G 值键投影降档+四区停留贴带下限 → gt=9600 越下带产 WARN。

    构造场景（warning 用例参数面允许合成，模板 chuchenchi q_prime=4.8
    先例）：g_mix=80/g_seed=60/g_floc=25/g_ripen=10（0.5.0 键值降档）
    + t_mix=0.5/t_seed=1.0/t_floc=2.0/t_ripen=1.0（四带下限组合）→
    gt=80×30+60×60+25×120+10×60=2400+3600+3000+600=9600<1×10⁴ 越下带
    （param_key 归因 GT 面无直接参数，归 t 停留组调节方向）。
    """
    result = make_unit().compute(
        _ctx(
            _params(
                t_mix=0.5,
                t_seed=1.0,
                t_floc=2.0,
                t_ripen=1.0,
                **{
                    "factor.mine_ningjiao.g_mix": 80.0,
                    "factor.mine_ningjiao.g_seed": 60.0,
                    "factor.mine_ningjiao.g_floc": 25.0,
                    "factor.mine_ningjiao.g_ripen": 10.0,
                },
            )
        )
    )
    gt = [w for w in result.warnings if "gt_band" in w.source]
    assert gt and gt[0].severity is Severity.WARN
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["gt_total"] == pytest.approx(9600.0, abs=1e-6)  # 越下限实证


def test_retention_band_warning() -> None:
    """校核带越界：t_mix=3.0 越 0.5~2.0 带产 WARN（param_key=t_mix）。"""
    result = make_unit().compute(_ctx(_params(t_mix=3.0)))
    ret = [w for w in result.warnings if "t_mix_band" in w.source]
    assert ret and ret[0].severity is Severity.WARN
    assert ret[0].param_key == "t_mix"


def test_param_domain_rejected() -> None:
    """参数域拒绝：n≤0 / t_mix≤0 / h2≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_mix=0.0)))
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
    assert result.formula_ids == tuple(f"KN-F{index}" for index in range(1, 16))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
