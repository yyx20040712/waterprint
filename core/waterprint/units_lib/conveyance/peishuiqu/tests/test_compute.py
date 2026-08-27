"""conveyance_peishuiqu golden 数值测试（期望值来源：conveyance_peishuiqu.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/conveyance_peishuiqu.md 主算例（PQ-F1~PQ-F7 七项：
#   q_each=0.2816260417/a_channel=0.7040651042/h_water=0.5867209201/
#   h_weir=0.1708915267/q_series=0.3097886458/h_total=0.8867209201/
#   v_end=0.4000000000——恰落带下限合）与副算例（n=3/b_channel=1.0/
#   v_channel=0.6/b=2.5 宽浅低流速档七项——v_end=0.2000000000 <0.4
#   越下限恰一 WARN 路径[渠末段淤积风险]）；系数键值逐字取自
#   data/coefficients 0.7.0 factors.yaml（peishuiqu 12 键）——测试区
#   字面量合法。h_weir 按截断指数 0.66666667 手算（xiaohua 0.33333333
#   立方根指数同款注记——DSL 同串同值）。
#
# 【用例面】（十一条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 WATER 单 OUT 声明/removal_refs 空）
#   ②主算例逐项（PQ-F1~F7 七项——含渠末流速恰落带下限）③副算例逐项
#   （三路宽浅档）④主算例零警告 ⑤副算例 v_end 越下限恰一 WARN
#   （severity+param_key=v_channel 归因+淤积风险语义）⑥动态多口出流面
#   （两口恰键+每口 q_avg=入流/2 kz 透传+分流守恒+水质逐指标恒等+
#   每口出流口恒键）⑦参数域拒绝（b_channel=0/n 非整档 2.5/
#   g_gravity=0 三例）⑧纯函数双跑一致 ⑨formula_ids 恰 7 号
#   （PQ-F1~F7）且全部可在公式注册表解析 ⑩工况键形态冒烟
#   ⑪n=3 档出流口数恰三口（动态多口参数化实证）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/conveyance/peishuiqu/tests`
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
from waterprint.units_lib.conveyance.peishuiqu import make_unit, manifest

# ── 主算例入参（表逐字：入流=市政 34760 案例口径 q_design=0.5632520833
#    m³/s；n=2 路/b_channel=1.2 m/v_channel=0.8 m/s/b=2.0 m 堰长/
#    g_gravity=9.81）──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_conveyance_peishuiqu", port_id="in")
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
        # manifest 默认=表主算例逐字（5 参数）
        "n": 2.0,
        "b_channel": 1.2,
        "v_channel": 0.8,
        "b": 2.0,
        "g_gravity": 9.81,
        # data/coefficients factors.yaml（0.7.0）peishuiqu 12 键逐字
        "factor.peishuiqu.v_channel_band.min": 0.6,
        "factor.peishuiqu.v_channel_band.max": 1.0,
        "factor.peishuiqu.v_end_band.min": 0.4,
        "factor.peishuiqu.v_end_band.max": 1.0,
        "factor.peishuiqu.m_weir": 0.45,
        "factor.peishuiqu.h_weir_band.min": 0.10,
        "factor.peishuiqu.h_weir_band.max": 0.30,
        "factor.peishuiqu.k_uneven": 1.10,
        "factor.peishuiqu.k_uneven_band.min": 1.05,
        "factor.peishuiqu.k_uneven_band.max": 1.15,
        "factor.peishuiqu.superheight": 0.3,
        "factor.peishuiqu.elevation_loss": 0.15,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_conveyance_peishuiqu",
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
    return PortRef(unit_id="test_conveyance_peishuiqu", port_id=f"out_{index}")


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/两口 WATER 单 OUT 声明/removal_refs 空。"""
    assert manifest.unit_id == "conveyance_peishuiqu"
    assert manifest.business_line == "conveyance"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_dims() -> None:
    """②主算例逐项断言（PQ-F1~F7——分流→断面→堰→渠末校核七项）。"""
    dims = _dims()
    assert dims["q_each"] == pytest.approx(0.2816260417, abs=1e-9)  # PQ-F1
    assert dims["a_channel"] == pytest.approx(0.7040651042, abs=1e-9)  # PQ-F2
    assert dims["h_water"] == pytest.approx(0.5867209201, abs=1e-9)  # PQ-F3
    assert dims["h_weir"] == pytest.approx(0.1708915267, abs=1e-9)  # PQ-F4
    assert dims["q_series"] == pytest.approx(0.3097886458, abs=1e-9)  # PQ-F5
    assert dims["h_total"] == pytest.approx(0.8867209201, abs=1e-9)  # PQ-F6
    assert dims["v_end"] == pytest.approx(0.4000000000, abs=1e-9)  # PQ-F7 恰落带下限


def test_secondary_case_dims() -> None:
    """③副算例（三路宽浅低流速档）逐项断言（表副算例 PQ-F1~F7 对照）。"""
    dims = _dims(n=3.0, b_channel=1.0, v_channel=0.6, b=2.5)
    assert dims["q_each"] == pytest.approx(0.1877506944, abs=1e-9)
    assert dims["a_channel"] == pytest.approx(0.9387534722, abs=1e-9)
    assert dims["h_water"] == pytest.approx(0.9387534722, abs=1e-9)
    assert dims["h_weir"] == pytest.approx(0.1123879322, abs=1e-9)  # 带内合
    assert dims["q_series"] == pytest.approx(0.2065257639, abs=1e-9)
    assert dims["h_total"] == pytest.approx(1.2387534722, abs=1e-9)
    assert dims["v_end"] == pytest.approx(0.2000000000, abs=1e-9)  # <0.4 越下限


def test_main_case_no_warning() -> None:
    """④主算例三带全合（v_channel/h_weir/v_end 恰落带内或下限）——warnings 全空。"""
    result = _compute()
    assert result.warnings == ()


def test_secondary_v_end_warning() -> None:
    """⑤副算例 v_end=0.2 <0.4 恰一 WARN（渠末段淤积风险；param_key=v_channel）。"""
    result = _compute(n=3.0, b_channel=1.0, v_channel=0.6, b=2.5)
    v_end = [w for w in result.warnings if "v_end_band" in w.source]
    assert len(result.warnings) == 1 and v_end
    assert v_end[0].severity is Severity.WARN
    assert v_end[0].param_key == "v_channel"
    assert "淤积" in v_end[0].message


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
    """⑦参数域拒绝：b_channel=0 / n 非整档 2.5 / g_gravity=0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(b_channel=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=2.5)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(g_gravity=0.0)))


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
    """⑨formula_ids 恰 7 号（PQ-F1~F7）且全部可在公式注册表解析（A1 防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"PQ-F{index}" for index in range(1, 8))
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
