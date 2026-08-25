"""municipal_chenshachi golden 数值测试（期望值来源：docs/norms/chenshachi.md 签字表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-23 签字）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/chenshachi.md 算例 1；系数键值逐字取自 data/coefficients
#   0.1.0 数据包 factors/removal_rates yaml——测试区字面量合法）
#
# 【用例面】主算例逐项断言（Q₁/Q₁h/D/h₂/径深比/V_eff/t_actual/V_sand/
#   V_hopper/d_upper/h₄/V_cone/h_cyl/V_storage/H/A渠/h渠/宽深比/L直/B出/
#   Q_wet/DS）+ 校核带越界产 Warning（表面负荷带/有效水深带/径深比带/
#   停留时间带）+ 参数域拒绝（n<1、q_surf≤0）+ 纯函数双跑一致 +
#   formula_ids 全部可在公式注册表解析。
# 【矛盾 3 注记】t=30（三表参数）与校核带 25~60 s 的 mod.json min=30
#   不一致——"待领域专家裁定"挂账保留（30 在带内，不阻塞）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/chenshachi/tests`
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
from waterprint.units_lib.municipal.chenshachi import make_unit, manifest

# ── 算例 1 入参（三表逐字：q_avg_daily=34760.7 m³/d、Kz=1.4；参数取
#    resources/yyx.ddesign.json 实际值；系数=data 包 yaml 键值逐字） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_chenshachi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)


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
        "q_surf": 150.0,
        "t_retention": 30.0,
        "t_clean": 2.0,
        "theta": 55.0,
        "d_r": 0.5,
        "b_channel": 0.8,
        "v_channel": 1.0,
        "length_disc_step": 0.1,
        "sec_per_hour": 3600.0,
        # data/coefficients factors.yaml（0.1.0 生效）逐字
        "factor.chenshachi.sand_yield_x": 30.0,
        "factor.chenshachi.hopper.safety": 1.5,
        "factor.chenshachi.buffer_h3": 0.5,
        "factor.chenshachi.superheight": 0.3,
        "factor.chenshachi.grit.moisture": 0.60,
        "factor.chenshachi.grit.vs": 0.05,
        "factor.chenshachi.grit.density": 1600.0,
        "factor.chenshachi.channel.straight_mult": 7.0,
        "factor.chenshachi.channel.straight_min": 4.5,
        "factor.chenshachi.channel.outlet_mult": 2.0,
        "factor.chenshachi.surface_load_band.min": 150.0,
        "factor.chenshachi.surface_load_band.max": 200.0,
        "factor.chenshachi.retention_band.min": 25.0,
        "factor.chenshachi.retention_band.max": 60.0,
        "factor.chenshachi.h2_band.min": 1.0,
        "factor.chenshachi.h2_band.max": 2.0,
        "factor.chenshachi.ratio_dh2_band.min": 2.0,
        "factor.chenshachi.ratio_dh2_band.max": 2.5,
        "factor.chenshachi.wall_thickness_coef": 0.4,
        "factor.chenshachi.hopper_upper_ratio": 0.5,
        # removal_rates.yaml mod_default 档逐字
        "removal.chenshachi.bod5.mod_default": 0.05,
        "removal.chenshachi.cod.mod_default": 0.05,
        "removal.chenshachi.ss.mod_default": 0.10,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float], quality: WaterQuality | None = None) -> UnitContext:
    return UnitContext(
        unit_id="test_chenshachi",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: quality if quality is not None else WaterQuality({})},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims(dims: object) -> dict[str, float]:
    """dims 面收窄为 dict[str, float]（compute 契约：str→float 全量）。"""
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包。"""
    assert manifest.unit_id == "municipal_chenshachi"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.chenshachi.bod5.mod_default",
        "CODCR": "removal.chenshachi.cod.mod_default",
        "SS": "removal.chenshachi.ss.mod_default",
    }


def test_main_case_basin() -> None:
    """主算例（三表算例 1）池体水力结果逐项断言（CS-F1~F6）。"""
    dims = _dims(make_unit().compute(_ctx(_params())).dims)
    assert dims["q1"] == pytest.approx(0.28163, abs=1e-5)  # CS-F1：0.56325/2
    assert dims["q1h"] == pytest.approx(1013.85, abs=0.1)  # Q₁×3600
    assert dims["d"] == pytest.approx(3.0, abs=1e-9)  # CS-F2：2.9336 → 3.0
    assert dims["h2"] == pytest.approx(1.25, abs=1e-9)  # CS-F3：150×30/3600
    assert dims["ratio_dh2"] == pytest.approx(2.40, abs=1e-3)  # CS-F4：3.0/1.25
    assert dims["v_eff"] == pytest.approx(8.836, abs=1e-3)  # CS-F5：π×1.5²×1.25
    assert dims["t_actual"] == pytest.approx(31.4, abs=0.05)  # CS-F6：31.37


def test_main_case_hopper_and_channel() -> None:
    """主算例砂斗组/总高/进出水渠逐项断言（CS-F7~F16）。"""
    dims = _dims(make_unit().compute(_ctx(_params())).dims)
    assert dims["v_sand"] == pytest.approx(0.5214, abs=1e-4)  # CS-F7：单池
    assert dims["v_hopper"] == pytest.approx(1.5642, abs=1e-4)  # CS-F8：×2×1.5
    assert dims["d_upper"] == pytest.approx(1.5, abs=1e-9)  # CS-F9：0.5×3.0
    assert dims["h4"] == pytest.approx(0.3501, abs=1e-4)  # CS-F10
    assert dims["v_cone"] == pytest.approx(0.2979, abs=1e-4)  # CS-F11：圆台
    assert dims["h_cyl"] == pytest.approx(0.8, abs=1e-9)  # CS-F12：0.7166 → 0.8
    assert dims["v_storage"] == pytest.approx(1.7116, abs=1e-4)  # 0.2979+1.4137
    assert dims["h_total"] == pytest.approx(3.3, abs=1e-9)  # CS-F13：3.2001 → 3.3
    assert dims["a_channel"] == pytest.approx(0.2816, abs=1e-4)  # CS-F14：Q₁/v渠
    assert dims["h_channel"] == pytest.approx(0.352, abs=1e-4)  # CS-F14：≥0.2 合格
    assert dims["ratio_bh"] == pytest.approx(2.27, abs=1e-2)  # 0.8/0.352
    assert dims["l_straight"] == pytest.approx(5.6, abs=1e-9)  # CS-F15：max(5.6,4.5)
    assert dims["b_outlet"] == pytest.approx(1.6, abs=1e-9)  # CS-F16：2×0.8


def test_main_case_sludge() -> None:
    """主算例沉砂污泥口与混凝土量断言（CS-F17/F18）。"""
    dims = _dims(make_unit().compute(_ctx(_params())).dims)
    assert dims["q_wet"] == pytest.approx(1.0428, abs=1e-4)  # V_sand×n（全厂）
    assert dims["ds_grit"] == pytest.approx(667.4, abs=0.1)  # CS-F17：667.389
    # CS-F18：π×1.5²×3.3×2×0.4 = 18.656
    assert dims["v_concrete"] == pytest.approx(18.656, abs=1e-2)
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例四条校核带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal.mod_default)，NH3N 透传。"""
    quality = WaterQuality(
        {"BOD5": 200.0, "CODCR": 400.0, "SS": 250.0, "NH3N": 30.0, "TN": 40.0, "TP": 5.0}
    )
    result = make_unit().compute(_ctx(_params(), quality))
    out_ref = PortRef(unit_id="test_chenshachi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(200.0 * (1 - 0.05)) == out_quality.BOD5
    assert pytest.approx(400.0 * (1 - 0.05)) == out_quality.CODCR
    assert pytest.approx(250.0 * (1 - 0.10)) == out_quality.SS
    assert out_quality.NH3N == 30.0  # 无去除逻辑不建条目，透传
    assert out_quality.TN == 40.0
    assert out_quality.TP == 5.0


def test_h2_and_retention_band_warnings() -> None:
    """校核带越界：t_retention=90 → h₂=3.75 越 1.0~2.0 带 + t_actual 越 25~60 带。"""
    result = make_unit().compute(_ctx(_params(t_retention=90.0)))
    keys = {w.param_key for w in result.warnings}
    assert "t_retention" in keys
    h2_warnings = [w for w in result.warnings if "h2_band" in w.source]
    assert h2_warnings and h2_warnings[0].severity is Severity.WARN


def test_surface_load_band_warning() -> None:
    """校核带越界：q_surf=250 越 150~200 m³/(m²·h) 带产 WARN。"""
    result = make_unit().compute(_ctx(_params(q_surf=250.0)))
    surf_warnings = [w for w in result.warnings if w.param_key == "q_surf"]
    assert surf_warnings and surf_warnings[0].severity is Severity.WARN
    assert "surface_load_band" in surf_warnings[0].source


def test_param_domain_rejected() -> None:
    """参数域拒绝：n<1 / q_surf≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(q_surf=0.0)))


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = _dims(unit.compute(_ctx(_params())).dims)
    second = _dims(unit.compute(_ctx(_params())).dims)
    assert first == second


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"CS-F{index}" for index in range(1, 19))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
