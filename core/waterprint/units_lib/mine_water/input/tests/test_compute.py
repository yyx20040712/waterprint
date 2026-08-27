"""mine_water_input golden 数值测试（期望值来源：docs/norms/mine_water_input.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_input.md 主算例（KI-F1~F7 七项）；系数键值
#   逐字取自 data/coefficients 0.5.0 factors.yaml（mine_input 两键，
#   无去除键——输入源单元不建 removal.mine_input.*）——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q_design/q_avg_h/v_inlet/z_pipe_bottom/
#   z_water/z_bottom/freeboard）+ 超高校核带越界产 Warning（freeboard
#   < freeboard.min）+ 参数域拒绝（kz≤0、kz<1、q_avg_daily≤0、
#   非零入边=注入点语义拒）+ 纯函数双跑一致 + formula_ids 全部可在
#   公式注册表解析 + 出流水质=参数注入六指标（GB/T 19223-2015 含
#   悬浮物类典型值面）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/input/tests`
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
from waterprint.units_lib.mine_water.input import make_unit, manifest

# ── 主算例入参（表逐字：Q_avg_daily=43836.0 m³/d、Kz=1.5 井下脉动独立
#    口径、z_water_inlet=100.0、z_ground=102.0、DN=800 mm；进水水质=
#    GB/T 19223-2015 含悬浮物类典型值——SS 800/COD 200/BOD5 5.0/
#    NH3N 1.0/TN 60/TP 2.0 mg/L） ──
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；factor.* 系数投影逐字 0.5.0）。"""
    params: dict[str, float] = {
        "q_avg_daily": 43836.0,
        "kz": 1.5,
        "dn_inlet": 800.0,
        "z_water_inlet": 100.0,
        "z_ground": 102.0,
        "h_pool": 3.0,
        "ss_in": 800.0,
        "cod_in": 200.0,
        "bod5_in": 5.0,
        "nh3n_in": 1.0,
        "tn_in": 60.0,
        "tp_in": 2.0,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_input.elevation_loss": 0.2,
        "factor.mine_input.freeboard.min": 0.3,
    }
    params.update(overrides)
    return params


def _ctx(
    params: dict[str, float],
    inflows: dict[PortRef, WaterFlow] | None = None,
    inqualities: dict[PortRef, WaterQuality] | None = None,
) -> UnitContext:
    """测试上下文：默认零入边（注入点语义），入边面可覆盖。"""
    return UnitContext(
        unit_id="test_mine_input",
        inflows={} if inflows is None else inflows,
        inqualities={} if inqualities is None else inqualities,
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
    """清单身份：UNIT_ID/业务线/两口 WATER/零去除率引用（源单元不建键）。"""
    assert manifest.unit_id == "mine_water_input"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {}  # 输入源单元无处理功能不建键


def test_main_case_flow_and_elevation() -> None:
    """主算例（表主算例）流量口径与高程链逐项断言（KI-F1~F7）。"""
    dims = _dims()
    assert dims["q_design"] == pytest.approx(0.7610416667, abs=1e-9)  # KI-F1
    assert dims["q_avg_h"] == pytest.approx(1826.5, abs=1e-9)  # KI-F2：43836/24
    # KI-F3：DN800（表 π 截断 3.14159265 差 ~1e-9，容差覆盖）
    assert dims["v_inlet"] == pytest.approx(1.0093628607, abs=1e-8)
    assert dims["z_pipe_bottom"] == pytest.approx(99.2, abs=1e-9)  # KI-F4
    assert dims["z_water"] == pytest.approx(99.8, abs=1e-9)  # KI-F5：−h_loss 0.2
    assert dims["z_bottom"] == pytest.approx(96.8, abs=1e-9)  # KI-F6：−h_pool 3.0
    assert dims["freeboard"] == pytest.approx(2.2, abs=1e-9)  # KI-F7
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例超高校核合格（2.2 ≥ 0.3）


def test_outflow_injection_and_quality() -> None:
    """出流注入：水量=参数面（q_avg_daily=Q_design/kz 口径）+ 水质=六指标注入。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_input", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == pytest.approx(43836.0 / 86400, abs=1e-12)
    assert out_flow.kz == 1.5
    assert out_flow.q_design == pytest.approx(0.7610416667, abs=1e-9)
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(800.0, abs=1e-9) == out_quality.SS
    assert pytest.approx(200.0, abs=1e-9) == out_quality.CODCR
    assert pytest.approx(5.0, abs=1e-9) == out_quality.BOD5
    assert pytest.approx(1.0, abs=1e-9) == out_quality.NH3N
    assert pytest.approx(60.0, abs=1e-9) == out_quality.TN
    assert pytest.approx(2.0, abs=1e-9) == out_quality.TP


def test_freeboard_band_warning() -> None:
    """校核带越界：z_ground=100.0 → freeboard=0.2 < 0.3 产 WARN（param_key=z_ground）。"""
    result = make_unit().compute(_ctx(_params(z_ground=100.0)))
    free = [w for w in result.warnings if "freeboard" in w.source]
    assert free and free[0].severity is Severity.WARN
    assert free[0].param_key == "z_ground"


def test_param_domain_rejected() -> None:
    """参数域拒绝：kz≤0 / kz<1（厂界口径）/ q_avg_daily≤0 / 非零入边=注入点语义拒。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(kz=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(kz=0.5)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(q_avg_daily=0.0)))
    upstream = PortRef(unit_id="upstream", port_id="out")
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(
            _ctx(
                _params(),
                inflows={upstream: WaterFlow(q_avg_daily=0.5, kz=1.5)},
            )
        )


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
    assert result.formula_ids == tuple(f"KI-F{index}" for index in range(1, 8))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
