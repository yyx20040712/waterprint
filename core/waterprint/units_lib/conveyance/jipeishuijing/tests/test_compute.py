"""conveyance_jipeishuijing golden 数值测试（期望值来源：conveyance_jipeishuijing.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副/越带算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/conveyance_jipeishuijing.md 主算例（JP-F1~JP-F9 十项：
#   v_well=135.1805000000/a_well=54.0722000000/d_raw=8.2974010021/
#   d=8.5/a_act=56.7450172406/t_act=251.8633260298/q_each=0.2816260417/
#   q_series=0.3097886458/h_total=2.8/v_concrete=55.6101168958——n=2
#   主档）、副算例（t_well=6/h_well=3.0/n=3 长停留深井三路档十项）
#   与越带档（t_well=12：v_well=405.5415/d_raw=14.3715201064/d=14.5/
#   t_act=732.9309937408——t_band 上限+d_band 上限恰两 WARN 路径）；
#   系数键值逐字取自 data/coefficients 0.7.0 factors.yaml
#   （jipeishuijing 12 键）——测试区字面量合法。档值断言 approx
#   口径（wushui_tisheng DN 档 6×0.1 浮点噪声先例）。
#
# 【用例面】（十一条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 WATER 单 OUT 声明/removal_refs 空）
#   ②主算例逐项（JP-F1~F9 十项）③副算例逐项（n=3 档）④主算例零
#   警告 ⑤越带档 t_well=12 恰两 WARN（t_band 面+d_band 面；severity
#   +param_key 归因）⑥动态多口出流面（两口恰键+每口 q_avg=入流/2
#   kz 透传+分流守恒+水质逐指标恒等+每口出流口恒键）⑦参数域拒绝
#   （t_well=0/h_well 非正/n 非整档 2.5 三例）⑧纯函数双跑一致
#   ⑨formula_ids 恰 9 号（JP-F1~F9）且全部可在公式注册表解析
#   ⑩工况键形态冒烟 ⑪n=3 档出流口数恰三口（动态多口参数化实证）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/conveyance/jipeishuijing/tests`
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
from waterprint.units_lib.conveyance.jipeishuijing import make_unit, manifest

# ── 主算例入参（表逐字：入流=市政 34760 案例口径 q_design=0.5632520833
#    m³/s；t_well=4 min/h_well=2.5 m/n=2 路/井径 0.5 m 档）──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_conveyance_jipeishuijing", port_id="in")
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
        # manifest 默认=表主算例逐字（4 参数）
        "t_well": 4.0,
        "h_well": 2.5,
        "n": 2.0,
        "dia_disc_step": 0.5,
        # data/coefficients factors.yaml（0.7.0）jipeishuijing 12 键逐字
        "factor.jipeishuijing.t_band.min": 3.0,
        "factor.jipeishuijing.t_band.max": 10.0,
        "factor.jipeishuijing.depth_band.min": 2.0,
        "factor.jipeishuijing.depth_band.max": 3.5,
        "factor.jipeishuijing.d_band.min": 4.0,
        "factor.jipeishuijing.d_band.max": 12.0,
        "factor.jipeishuijing.k_uneven": 1.10,
        "factor.jipeishuijing.k_uneven_band.min": 1.05,
        "factor.jipeishuijing.k_uneven_band.max": 1.15,
        "factor.jipeishuijing.superheight": 0.3,
        "factor.jipeishuijing.wall_thickness_coef": 0.35,
        "factor.jipeishuijing.elevation_loss": 0.15,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_conveyance_jipeishuijing",
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


def _out_ref(index: int) -> PortRef:
    """动态多口出流引用（out_1~out_n）。"""
    return PortRef(unit_id="test_conveyance_jipeishuijing", port_id=f"out_{index}")


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/两口 WATER 单 OUT 声明/removal_refs 空。"""
    assert manifest.unit_id == "conveyance_jipeishuijing"
    assert manifest.business_line == "conveyance"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_dims() -> None:
    """②主算例逐项断言（JP-F1~F9——汇流→分流→构造十项）。"""
    dims = _dims()
    assert dims["v_well"] == pytest.approx(135.1805000000, abs=1e-9)  # JP-F1
    assert dims["a_well"] == pytest.approx(54.0722000000, abs=1e-9)  # JP-F2
    assert dims["d_raw"] == pytest.approx(8.2974010021, abs=1e-9)  # JP-F3
    assert dims["d"] == pytest.approx(8.5, abs=1e-9)  # 0.5 m 档收口
    assert dims["a_act"] == pytest.approx(56.7450172406, abs=1e-9)  # JP-F4
    assert dims["t_act"] == pytest.approx(251.8633260298, abs=1e-9)  # JP-F5
    assert dims["q_each"] == pytest.approx(0.2816260417, abs=1e-9)  # JP-F6
    assert dims["q_series"] == pytest.approx(0.3097886458, abs=1e-9)  # JP-F7
    assert dims["h_total"] == pytest.approx(2.8, abs=1e-9)  # JP-F8
    assert dims["v_concrete"] == pytest.approx(55.6101168958, abs=1e-9)  # JP-F9


def test_secondary_case_dims() -> None:
    """③副算例（长停留深井三路档）逐项断言（表副算例 JP-F1~F9 对照）。"""
    dims = _dims(t_well=6.0, h_well=3.0, n=3.0)
    assert dims["v_well"] == pytest.approx(202.7707500000, abs=1e-9)
    assert dims["a_well"] == pytest.approx(67.5902500000, abs=1e-9)
    assert dims["d_raw"] == pytest.approx(9.2767763386, abs=1e-9)
    assert dims["d"] == pytest.approx(9.5, abs=1e-9)
    assert dims["a_act"] == pytest.approx(70.8821841656, abs=1e-9)
    assert dims["t_act"] == pytest.approx(377.5335392253, abs=1e-9)
    assert dims["q_each"] == pytest.approx(0.1877506944, abs=1e-9)
    assert dims["q_series"] == pytest.approx(0.2065257639, abs=1e-9)
    assert dims["h_total"] == pytest.approx(3.3, abs=1e-9)
    assert dims["v_concrete"] == pytest.approx(81.8689227113, abs=1e-9)


def test_main_case_no_warning() -> None:
    """④主算例三带全合（4∈[3,10]/2.5∈[2,3.5]/8.5∈[4,12]）——warnings 全空。"""
    result = _compute()
    assert result.warnings == ()


def test_over_band_warnings() -> None:
    """⑤越带档 t_well=12 恰两 WARN（t_band 上限+d_band 上限 14.5>12）。"""
    dims = _dims(t_well=12.0)
    assert dims["v_well"] == pytest.approx(405.5415, abs=1e-9)
    assert dims["d_raw"] == pytest.approx(14.3715201064, abs=1e-9)
    assert dims["d"] == pytest.approx(14.5, abs=1e-9)
    assert dims["t_act"] == pytest.approx(732.9309937408, abs=1e-9)
    result = _compute(t_well=12.0)
    sources = tuple(w.source for w in result.warnings)
    assert len(result.warnings) == 2
    assert any("t_band" in s for s in sources) and any("d_band" in s for s in sources)
    assert all(w.severity is Severity.WARN for w in result.warnings)


def test_multi_outlet_flow_face() -> None:
    """⑥动态多口出流面：两口恰键+每口均分+kz 透传+分流守恒+水质恒等。"""
    result = _compute()
    assert set(result.outflows) == {_out_ref(1), _out_ref(2)}
    total = 0.0
    for ref in sorted(result.outflows, key=lambda r: r.port_id):
        out = result.outflows[ref]
        assert isinstance(out, WaterFlow)
        assert out.q_avg_daily == pytest.approx(_FLOW.q_avg_daily / 2, abs=1e-15)
        assert out.kz == pytest.approx(1.4, abs=0.0)
        total += out.q_avg_daily
    assert total == pytest.approx(_FLOW.q_avg_daily, abs=1e-15)  # 分流守恒
    assert set(result.outqualities) == {_out_ref(1), _out_ref(2)}  # 每口恒键
    for ref in result.outqualities:
        assert result.outqualities[ref].concentrations == _QUALITY.concentrations


def test_param_domain_rejected() -> None:
    """⑦参数域拒绝：t_well=0 / h_well 非正 / n 非整档 2.5 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_well=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(h_well=-1.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=2.5)))


def test_pure_function_double_run() -> None:
    """⑧纯函数断言：同 ctx 双跑 dims/warnings/outflows 三面逐项相同。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings
    assert set(first.outflows) == set(second.outflows)
    out_first = first.outflows[_out_ref(1)]
    out_second = second.outflows[_out_ref(1)]
    assert isinstance(out_first, WaterFlow) and isinstance(out_second, WaterFlow)
    assert (out_first.q_avg_daily, out_first.kz) == (out_second.q_avg_daily, out_second.kz)


def test_formula_ids_registered() -> None:
    """⑨formula_ids 恰 9 号（JP-F1~F9）且全部可在公式注册表解析（A1 防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"JP-F{index}" for index in range(1, 10))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """⑩工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"


def test_n3_outlet_count() -> None:
    """⑪n=3 档出流口数恰三口（动态多口参数化实证——表内冻结口径）。"""
    result = _compute(n=3.0)
    assert set(result.outflows) == {_out_ref(1), _out_ref(2), _out_ref(3)}
    total = 0.0
    for ref in sorted(result.outflows, key=lambda r: r.port_id):
        out = result.outflows[ref]
        assert isinstance(out, WaterFlow)
        total += out.q_avg_daily
    assert total == pytest.approx(_FLOW.q_avg_daily, abs=1e-15)  # 三路守恒
