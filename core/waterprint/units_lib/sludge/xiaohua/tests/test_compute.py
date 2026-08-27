"""sludge_xiaohua golden 数值测试（期望值来源：docs/norms/sludge_xiaohua.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_xiaohua.md 主算例（XH-F1~F11：w_vs=3104.311275/
#   v_total=2387.93175/v_single=1193.965875/w_vs_deg=1396.94007375/
#   v_biogas=1257.246066375/l_vs=1.3 带内/ds_out=3378.92342625 消化
#   减量/q_out=117.9996474262/p_out=0.9713649702 三量链/d_raw=11.4983
#   →d=11.5 m/v_concrete=835.7761125）与副算例（长周期+高降解+低产
#   气率档：w_vs=2865.5181/v_total=2984.9146875/v_single=1492.45734375/
#   w_vs_deg=1576.034955/v_biogas=1260.827964/l_vs=0.96/ds_out=
#   3199.828545/q_out=117.820552545/p_out=0.9728415079/d=12.5 m/
#   v_concrete=1044.720140625）；系数键值逐字取自 data/coefficients
#   0.6.0 factors.yaml（xiaohua 13 键）——测试区字面量合法。
#   π 口径注记：表 XH-F10 内联 3.14159265 经符号 pi 绑 math.pi
#   （KI/KT/KS 先例同型）——d_raw 差 <1e-9，容差 abs=1e-8 覆盖。
#   入流口径：nongsuo 主算例底流出流三量（ds 4775.8635 kg/d /
#   q 119.3965875 m³/d / p 0.96）。
#
# 【用例面】（十二条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/两口 SLUDGE/removal_refs 空）②主算例
#   挥发分与容积逐项（XH-F1~F3+池径 0.5 m 档取整）③主算例降解/产气/
#   负荷逐项（XH-F4~F6）④主算例消化减量 DS 守恒链逐项（XH-F7~F9——
#   出泥三量链联立）⑤主算例概算+四带校核零警告+三量链回显 ⑥副
#   算例（长周期高降解低产气档）逐项 ⑦越带 Warning——消化时间带
#   （t_digest 越带）⑧越带 Warning——VS 容积负荷带（短周期超负荷
#   实证）⑨出流 SLUDGE 三量（契约口径）⑩参数域拒绝（t_digest 非正/
#   eta_vs≥1）⑪纯函数双跑一致 ⑫formula_ids 恰 11 号（XH-F1~F11）
#   全部可解析+工况键冒烟。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/xiaohua/tests`
#   转为只读（AGENTS.md §11）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.sludge import SludgeFlow, make_sludge
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.sludge.xiaohua import make_unit, manifest

# ── 主算例入流（表逐字：nongsuo 主算例底流出流三量——衔接链口径）──
_IN_REF = PortRef(unit_id="upstream_nongsuo", port_id="out")
_OUT_REF = PortRef(unit_id="test_sludge_xiaohua", port_id="out")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_INFLOW = make_sludge(q_wet=119.3965875 / 86400, ds=4775.8635 / 86400, moisture=0.96)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；系数投影逐字 0.6.0）。"""
    params: dict[str, float] = {
        # manifest 默认=表主算例逐字（5 参数——t_digest_temp=UF-09 承载）
        "t_digest": 20.0,
        "n": 2.0,
        "t_digest_temp": 35.0,
        "eta_vs": 0.45,
        "r_biogas": 0.9,
        # data/coefficients factors.yaml（0.6.0）xiaohua 13 键逐字
        # （temp 键本批不消费——UF-09 注记，投影面照列）
        "factor.xiaohua.time_band.min": 15.0,
        "factor.xiaohua.time_band.max": 30.0,
        "factor.xiaohua.temp": 35.0,
        "factor.xiaohua.f_vs": 0.65,
        "factor.xiaohua.eta_vs_band.min": 0.3,
        "factor.xiaohua.eta_vs_band.max": 0.6,
        "factor.xiaohua.biogas_rate_band.min": 0.8,
        "factor.xiaohua.biogas_rate_band.max": 1.1,
        "factor.xiaohua.vs_load_band.min": 0.5,
        "factor.xiaohua.vs_load_band.max": 1.5,
        "factor.xiaohua.ratio_dh": 1.0,
        "factor.xiaohua.wall_thickness_coef": 0.35,
        "factor.xiaohua.elevation_loss": 0.4,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_xiaohua",
        inflows={_IN_REF: _INFLOW},
        inqualities={},
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


def _compute(**overrides: float):
    """主算例（或覆盖档）单跑结果。"""
    return make_unit().compute(_ctx(_params(**overrides)))


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/两口 SLUDGE/removal_refs 空（零 removal 键）。"""
    assert manifest.unit_id == "sludge_xiaohua"
    assert manifest.business_line == "sludge"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "SLUDGE", "IN"),
        ("out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_vs_and_volume() -> None:
    """②主算例挥发分与容积逐项断言（XH-F1~F3+XH-F10 池径 0.5 m 档）。"""
    dims = _dims()
    assert dims["w_vs"] == pytest.approx(3104.311275, abs=1e-9)  # XH-F1 ×0.65
    assert dims["v_total"] == pytest.approx(2387.93175, abs=1e-9)  # XH-F2 ×20 d
    assert dims["v_single"] == pytest.approx(1193.965875, abs=1e-9)  # XH-F3 /2
    assert dims["d_raw"] == pytest.approx(11.4983, abs=1e-4)  # XH-F10（表 4 位截断）
    assert dims["d"] == pytest.approx(11.5, abs=1e-12)  # 0.5 m 档向上取整


def test_main_case_degradation() -> None:
    """③主算例降解/产气/负荷逐项断言（XH-F4~F6）。"""
    dims = _dims()
    assert dims["w_vs_deg"] == pytest.approx(1396.94007375, abs=1e-9)  # XH-F4 ×0.45
    assert dims["v_biogas"] == pytest.approx(1257.246066375, abs=1e-9)  # XH-F5 ×0.9
    assert dims["l_vs"] == pytest.approx(1.3, abs=1e-9)  # XH-F6 带 0.5~1.5 内


def test_main_case_ds_chain() -> None:
    """④主算例消化减量 DS 守恒链逐项断言（XH-F7~F9——出泥三量链联立）。"""
    dims = _dims()
    assert dims["ds_out"] == pytest.approx(3378.92342625, abs=1e-9)  # XH-F7 减量
    assert dims["q_out"] == pytest.approx(117.9996474262, abs=1e-9)  # XH-F8 体积折减
    assert dims["p_out"] == pytest.approx(0.9713649702, abs=1e-9)  # XH-F9 三量链


def test_main_case_structure_no_warning_echo() -> None:
    """⑤主算例概算+四带校核零警告+进出三量链回显。"""
    dims = _dims()
    assert dims["v_concrete"] == pytest.approx(835.7761125, abs=1e-9)  # XH-F11
    result = _compute()
    assert result.warnings == ()
    assert dims["q_in"] == pytest.approx(119.3965875, abs=1e-9)
    assert dims["ds_in"] == pytest.approx(4775.8635, abs=1e-9)
    assert dims["p_in"] == pytest.approx(0.96, abs=1e-12)


def test_secondary_case() -> None:
    """⑥副算例（t=25 d/eta 0.55/r_biogas 0.8/f_vs 0.60 档）逐项断言。"""
    dims = _dims(
        t_digest=25.0, eta_vs=0.55, r_biogas=0.8, **{"factor.xiaohua.f_vs": 0.60}
    )
    assert dims["w_vs"] == pytest.approx(2865.5181, abs=1e-9)
    assert dims["v_total"] == pytest.approx(2984.9146875, abs=1e-9)
    assert dims["v_single"] == pytest.approx(1492.45734375, abs=1e-9)
    assert dims["w_vs_deg"] == pytest.approx(1576.034955, abs=1e-9)
    assert dims["v_biogas"] == pytest.approx(1260.827964, abs=1e-9)
    assert dims["l_vs"] == pytest.approx(0.96, abs=1e-9)  # 带内
    assert dims["ds_out"] == pytest.approx(3199.828545, abs=1e-9)
    assert dims["q_out"] == pytest.approx(117.820552545, abs=1e-9)
    assert dims["p_out"] == pytest.approx(0.9728415079, abs=1e-9)
    assert dims["d"] == pytest.approx(12.5, abs=1e-12)  # 12.3862 → 0.5 m 档
    assert dims["v_concrete"] == pytest.approx(1044.720140625, abs=1e-9)


def test_time_band_warning() -> None:
    """⑦越带 Warning：t_digest=10 越消化时间带下限（param_key=t_digest）。"""
    result = _compute(t_digest=10.0)
    time_w = [w for w in result.warnings if "time_band" in w.source]
    assert time_w and time_w[0].severity is Severity.WARN
    assert time_w[0].param_key == "t_digest"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_total"] == pytest.approx(1193.965875, abs=1e-8)  # 越带实值生效


def test_vs_load_band_warning() -> None:
    """⑧越带 Warning：t_digest=10 短周期使 l_vs 越负荷带上限（结果校核实证）。"""
    result = _compute(t_digest=10.0)
    load = [w for w in result.warnings if "vs_load_band" in w.source]
    assert load and load[0].severity is Severity.WARN
    assert load[0].param_key == "t_digest"  # 调节方向归因消化时间
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["l_vs"] == pytest.approx(2.6, abs=1e-9)  # 3104.311275/1193.965875


def test_outflow_sludge_triple() -> None:
    """⑨出流 SLUDGE 三量（契约口径：q_out/ds_out 换算+p_out 直通）。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(117.9996474262 / 86400, abs=1e-15)  # 往返噪声+表 10 位截断
    assert out.ds == pytest.approx(3378.92342625 / 86400, abs=1e-16)
    assert out.moisture == pytest.approx(0.9713649702, abs=1e-9)
    assert result.outqualities == {}


def test_param_domain_rejected() -> None:
    """⑩参数域拒绝：t_digest≤0 / eta_vs≥1 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_digest=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(eta_vs=1.0)))


def test_pure_function_double_run() -> None:
    """⑪纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings


def test_formula_ids_registered_and_condition_key() -> None:
    """⑫formula_ids 恰 11 号（XH-F1~XH-F11）全部可解析+工况键形态冒烟。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"XH-F{index}" for index in range(1, 12))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id
    assert ConditionSet.key(_CONDITION) == "design"
