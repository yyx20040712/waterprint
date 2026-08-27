"""conveyance_jishuijing golden 数值测试（期望值来源：docs/norms/conveyance_jishuijing.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副/越带算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/conveyance_jishuijing.md 主算例（JS-F1~F7 八项：
#   v_well=168.9756250000/a_well=56.3252083333/d_raw=8.4684994360/
#   d=8.5/a_act=56.7450172406/t_act=302.2359912358/h_total=3.3/
#   v_concrete=65.5404949129）、副算例（t_well=3/h_well=2.5 档：
#   v_well=101.3853750000/a_well=40.5541500000/d=7.5/
#   a_act=44.1786466406/t_act=196.0873645561/v_concrete=43.2950737078）
#   与越带档（t_well=1.5：v_well=50.6926875/d=5.0/
#   t_act=104.5799277632——t_band 下限恰一 WARN 路径）；系数键值逐字
#   取自 data/coefficients 0.7.0 factors.yaml（jishuijing 9 键）——
#   测试区字面量合法。档值断言 approx 口径（wushui_tisheng DN 档
#   6×0.1 浮点噪声先例——0.5 m 档值 8.5/7.5 二进制恰值，仍按
#   abs=1e-9 统一容差）。
#
# 【用例面】（十条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 WATER/removal_refs 空——零 removal
#   键声明面）②主算例逐项（JS-F1~F7 八项）③副算例逐项 ④主算例零
#   警告 ⑤越带档 t_well=1.5 恰一 WARN（severity+param_key=t_well
#   归因）⑥出流穿流透传（q_avg_daily/kz 双量恒等+水质逐指标恒等+
#   outqualities 出流口恒键）⑦参数域拒绝（t_well/h_well/dia_disc_step
#   非正三例）⑧纯函数双跑一致 ⑨formula_ids 恰 7 号（JS-F1~F7）且
#   全部可在公式注册表解析 ⑩工况键形态冒烟（condition_key 口径）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/conveyance/jishuijing/tests`
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
from waterprint.contracts.unit_api import Severity, UnitContext, UnitResult
from waterprint.registry import formulas
from waterprint.units_lib.conveyance.jishuijing import make_unit, manifest

# ── 主算例入参（表逐字：入流=市政 34760 案例口径 Q_avg_daily=
#    34760.7 m³/d、Kz=1.4——q_design=0.5632520833 m³/s；t_well=5 min/
#    h_well=3.0 m/井径 0.5 m 档）——多股汇流经 propagate 合并后单股 ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_conveyance_jishuijing", port_id="in")
_OUT_REF = PortRef(unit_id="test_conveyance_jishuijing", port_id="out")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 198.0, "CODCR": 344.0, "SS": 237.0, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；系数投影逐字 0.7.0）。"""
    params: dict[str, float] = {
        # manifest 默认=表主算例逐字（3 参数）
        "t_well": 5.0,
        "h_well": 3.0,
        "dia_disc_step": 0.5,
        # data/coefficients factors.yaml（0.7.0）jishuijing 9 键逐字
        "factor.jishuijing.t_band.min": 2.0,
        "factor.jishuijing.t_band.max": 10.0,
        "factor.jishuijing.depth_band.min": 2.0,
        "factor.jishuijing.depth_band.max": 4.0,
        "factor.jishuijing.d_band.min": 4.0,
        "factor.jishuijing.d_band.max": 12.0,
        "factor.jishuijing.superheight": 0.3,
        "factor.jishuijing.wall_thickness_coef": 0.35,
        "factor.jishuijing.elevation_loss": 0.15,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_conveyance_jishuijing",
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


def _compute(**overrides: float) -> UnitResult:
    """主算例（或覆盖档）单跑结果。"""
    return make_unit().compute(_ctx(_params(**overrides)))


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/两口 WATER/removal_refs 空（零 removal 键）。"""
    assert manifest.unit_id == "conveyance_jishuijing"
    assert manifest.business_line == "conveyance"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_dims() -> None:
    """②主算例逐项断言（JS-F1~F7——汇流容积→构造→概算八项）。"""
    dims = _dims()
    assert dims["v_well"] == pytest.approx(168.9756250000, abs=1e-9)  # JS-F1
    assert dims["a_well"] == pytest.approx(56.3252083333, abs=1e-9)  # JS-F2
    assert dims["d_raw"] == pytest.approx(8.4684994360, abs=1e-9)  # JS-F3
    assert dims["d"] == pytest.approx(8.5, abs=1e-9)  # 0.5 m 档收口
    assert dims["a_act"] == pytest.approx(56.7450172406, abs=1e-9)  # JS-F4
    assert dims["t_act"] == pytest.approx(302.2359912358, abs=1e-9)  # JS-F5 停留校核
    assert dims["h_total"] == pytest.approx(3.3, abs=1e-9)  # JS-F6
    assert dims["v_concrete"] == pytest.approx(65.5404949129, abs=1e-9)  # JS-F7 概算


def test_secondary_case_dims() -> None:
    """③副算例（短停留浅井档）逐项断言（表副算例 JS-F1~F7 对照）。"""
    dims = _dims(t_well=3.0, h_well=2.5)
    assert dims["v_well"] == pytest.approx(101.3853750000, abs=1e-9)
    assert dims["a_well"] == pytest.approx(40.5541500000, abs=1e-9)
    assert dims["d_raw"] == pytest.approx(7.1857600532, abs=1e-9)
    assert dims["d"] == pytest.approx(7.5, abs=1e-9)
    assert dims["a_act"] == pytest.approx(44.1786466406, abs=1e-9)
    assert dims["t_act"] == pytest.approx(196.0873645561, abs=1e-9)
    assert dims["h_total"] == pytest.approx(2.8, abs=1e-9)
    assert dims["v_concrete"] == pytest.approx(43.2950737078, abs=1e-9)


def test_main_case_no_warning() -> None:
    """④主算例三带全合（5∈[2,10]/3.0∈[2,4]/8.5∈[4,12]）——warnings 全空。"""
    result = _compute()
    assert result.warnings == ()


def test_over_band_warning() -> None:
    """⑤越带档 t_well=1.5 恰一 WARN（t_band 下限；severity+param_key 归因）。"""
    dims = _dims(t_well=1.5)
    assert dims["v_well"] == pytest.approx(50.6926875, abs=1e-9)
    assert dims["d"] == pytest.approx(5.0, abs=1e-9)
    assert dims["t_act"] == pytest.approx(104.5799277632, abs=1e-9)
    result = _compute(t_well=1.5)
    t_warn = [w for w in result.warnings if "t_band" in w.source]
    assert len(result.warnings) == 1 and t_warn
    assert t_warn[0].severity is Severity.WARN
    assert t_warn[0].param_key == "t_well"


def test_outflow_passthrough() -> None:
    """⑥出流穿流透传：q_avg_daily/kz 双量恒等+水质逐指标恒等+出流口恒键。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, WaterFlow)
    assert out.q_avg_daily == pytest.approx(_FLOW.q_avg_daily, abs=0.0)
    assert out.kz == pytest.approx(1.4, abs=0.0)
    assert out.q_design == pytest.approx(_FLOW.q_design, abs=1e-15)
    assert set(result.outqualities) == {_OUT_REF}  # 出流口恒键（executor 入流装配前提）
    assert result.outqualities[_OUT_REF].concentrations == _QUALITY.concentrations  # 穿流恒等


def test_param_domain_rejected() -> None:
    """⑦参数域拒绝：t_well=0 / h_well 非正 / dia_disc_step=0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_well=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(h_well=-1.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(dia_disc_step=0.0)))


def test_pure_function_double_run() -> None:
    """⑧纯函数断言：同 ctx 双跑 dims/warnings/outflows 三面逐项相同。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings
    out_first = first.outflows[_OUT_REF]
    out_second = second.outflows[_OUT_REF]
    assert isinstance(out_first, WaterFlow) and isinstance(out_second, WaterFlow)
    assert (out_first.q_avg_daily, out_first.kz) == (out_second.q_avg_daily, out_second.kz)


def test_formula_ids_registered() -> None:
    """⑨formula_ids 恰 7 号（JS-F1~F7）且全部可在公式注册表解析（A1 防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"JS-F{index}" for index in range(1, 8))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """⑩工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
