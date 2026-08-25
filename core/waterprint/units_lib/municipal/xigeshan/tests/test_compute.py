"""municipal_xigeshan golden 数值测试（期望值来源：docs/norms/xigeshan.md 签字表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-23 签字）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/xigeshan.md 算例 1；系数键值逐字取自 data/coefficients
#   0.1.0 数据包 factors/removal_rates yaml——测试区字面量合法）
#
# 【用例面】主算例逐项断言（q/n_gap/B/B1/v_checked/v1_checked/ξ/h₁/
#   H/L/W/清渣方式/DS）+ 校核带越界产 Warning（v 带/v₁ 带）+ 参数域拒绝
#   （n<1）+ 纯函数双跑一致 + formula_ids 全部可在公式注册表解析。
# 【红绿实录】红=skeleton 期 no tests ran（本文件未含测试函数）→
#   实装后 9 passed。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/xigeshan/tests`
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
from waterprint.units_lib.municipal.xigeshan import make_unit, manifest

# ── 算例 1 入参（三表逐字：q_avg_daily=34760.7 m³/d、Kz=1.4；参数取
#    resources/yyx.ddesign.json 实际值；系数=data 包 yaml 键值逐字） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_xigeshan", port_id="in")
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
        "n": 3.0,
        "b": 0.008,
        "alpha": 70.0,
        "h": 0.6,
        "v": 0.8,
        "v1": 0.7,
        "s": 0.003,
        "bar_shape": 0.0,
        "g_gravity": 9.81,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.1.0 生效）逐字（格栅共用 factor.screen.*）
        "factor.screen.beta.rect": 2.42,
        "factor.screen.beta.semicircle": 1.97,
        "factor.screen.beta.circle": 1.83,
        "factor.screen.headloss.k": 3.0,
        "factor.screen.superheight": 0.3,
        "factor.screen.trough_width_margin": 0.2,
        "factor.screen.trough_length.l3_fixed": 1.0,
        "factor.screen.trough_length.l4_fixed": 0.5,
        "factor.screen.trough_length.drop_constant": 0.2,
        "factor.screen.slag.moisture": 0.80,
        "factor.screen.mech_clean_threshold": 0.2,
        "factor.screen.velocity_band.v.min": 0.6,
        "factor.screen.velocity_band.v.max": 1.0,
        "factor.screen.velocity_band.v1.min": 0.4,
        "factor.screen.velocity_band.v1.max": 0.9,
        "factor.screen.wall_thickness_coef": 0.3,
        "factor.xigeshan.w1_slag": 0.08,
        # removal_rates.yaml mod_default 档逐字
        "removal.xigeshan.bod5.mod_default": 0.08,
        "removal.xigeshan.cod.mod_default": 0.08,
        "removal.xigeshan.ss.mod_default": 0.08,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float], quality: WaterQuality | None = None) -> UnitContext:
    return UnitContext(
        unit_id="test_xigeshan",
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
    assert manifest.unit_id == "municipal_xigeshan"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.xigeshan.bod5.mod_default",
        "CODCR": "removal.xigeshan.cod.mod_default",
        "SS": "removal.xigeshan.ss.mod_default",
    }


def test_main_case_hydraulics() -> None:
    """主算例（三表算例 1）水力结果逐项断言。"""
    result = make_unit().compute(_ctx(_params()))
    dims = _dims(result.dims)
    assert dims["q"] == pytest.approx(0.18775, abs=1e-5)  # XG-F1：0.56325/3
    assert dims["n_gap"] == pytest.approx(48.0)  # XG-F2：47.40 → ceil
    assert dims["B"] == pytest.approx(0.8, abs=1e-9)  # XG-F3：0.725 → 0.8
    assert dims["B1"] == pytest.approx(0.5, abs=1e-9)  # XG-F4：0.44702 → 0.5
    assert dims["v_checked"] == pytest.approx(0.790, abs=1e-3)  # XG-F5：0.7899
    assert dims["v1_checked"] == pytest.approx(0.626, abs=1e-3)  # XG-F6：0.6258
    assert dims["xi"] == pytest.approx(0.6544, abs=1e-4)  # XG-F7：0.65442
    assert dims["h1"] == pytest.approx(0.0587, abs=1e-4)  # XG-F8：0.05867
    assert dims["H"] == pytest.approx(1.0, abs=1e-9)  # XG-F9：0.95867 → 1.0
    assert dims["L"] == pytest.approx(1.9, abs=1e-9)  # XG-F10：1.87309 → 1.9
    assert dims["w_slag"] == pytest.approx(2.7809, abs=1e-4)  # XG-F11：2.780856
    assert dims["mech_clean"] == pytest.approx(1.0)  # XG-F12：2.7809>0.2 机械清渣
    assert dims["ds_slag"] == pytest.approx(556.2, abs=0.1)  # XG-F13：556.171
    # XG-F14：V_c = L·B·H·n·0.3 = 1.9×0.8×1.0×3×0.3 = 1.368
    assert dims["v_concrete"] == pytest.approx(1.368, abs=1e-6)
    assert result.warnings == ()  # 主算例两流速带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal.mod_default)，NH3N 透传。"""
    quality = WaterQuality(
        {"BOD5": 200.0, "CODCR": 400.0, "SS": 250.0, "NH3N": 30.0, "TN": 40.0, "TP": 5.0}
    )
    result = make_unit().compute(_ctx(_params(), quality))
    out_ref = PortRef(unit_id="test_xigeshan", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(200.0 * (1 - 0.08)) == out_quality.BOD5
    assert pytest.approx(400.0 * (1 - 0.08)) == out_quality.CODCR
    assert pytest.approx(250.0 * (1 - 0.08)) == out_quality.SS
    assert out_quality.NH3N == 30.0  # 无去除逻辑不建条目，透传
    assert out_quality.TN == 40.0
    assert out_quality.TP == 5.0


def test_velocity_band_warning() -> None:
    """校核带越界：v 带下界（v=0.45 → n_gap=86，v_checked≈0.441<0.6）产 WARN。"""
    result = make_unit().compute(_ctx(_params(v=0.45)))
    v_warnings = [w for w in result.warnings if w.param_key == "v"]
    assert v_warnings and v_warnings[0].severity is Severity.WARN
    assert "factor.screen.velocity_band.v" in v_warnings[0].source


def test_v1_band_warning() -> None:
    """校核带越界：v₁ 带下界（v1=0.2 → v1_checked≈0.196<0.4）产 WARN。"""
    result = make_unit().compute(_ctx(_params(v1=0.2)))
    v1_warnings = [w for w in result.warnings if w.param_key == "v1"]
    assert v1_warnings and v1_warnings[0].severity is Severity.WARN
    assert "factor.screen.velocity_band.v1" in v1_warnings[0].source


def test_param_domain_rejected() -> None:
    """参数域拒绝：n<1（台数非法）→ InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = _dims(unit.compute(_ctx(_params())).dims)
    second = _dims(unit.compute(_ctx(_params())).dims)
    assert first == second


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"XG-F{index}" for index in range(1, 15))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
