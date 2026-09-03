"""municipal_aao golden 数值测试（期望值来源：docs/norms/aao.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/aao.md 算例 1；系数键值逐字取自 data/coefficients 0.2.0
#   数据包 factors/removal_rates yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（v_o/t_o/v_anaerobic/delta_n/v_anoxic/t_n/
#   v_total/t_total/v_o_series/s_y/q_wet/theta_c/x_vss/o2_carbon/o2_nit/
#   o2_denit/o2_total/q_return/q_internal）+ 池体几何 8 键（L7 批：
#   h2/a_pool/l_pool/b_pool/h_pool/l_pool_raw/b_pool_raw/v_pool——期望值=
#   v_total 锚独立手算，AO-F15~F19 CASS 公式族平移）+ 校核带越界产
#   Warning（ns 带/t_p 带/缺氧 HRT 带/泥龄带[好氧口径]）+ 参数域拒绝
#   （ns≤0/delta_n≤0）+ 纯函数双跑一致 + formula_ids 全部可在公式注册表解析。
# 【口径注记】入流水质=三表衔接式值（BOD5 123.2996/COD 199.9362/
#   SS 93.2121，上游=初沉池出流）；出流=衔接 erchunchi 表值；q_return
#   按最高时口径（引擎精确 Q_design 与表 5 位舍入差 <0.01，容差覆盖）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/aao/tests`
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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.municipal.aao import make_unit, manifest

# ── 算例 1 入参（三表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    三表衔接式值——初沉池出流逐项） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_aao", port_id="in")
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
        "n": 2.0,
        "ns": 0.10,
        "x_mlss": 4000.0,
        "t_p": 1.5,
        "r_external": 1.0,
        "r_internal": 2.0,
        "tn_eff": 15.0,
        "sec_per_hour": 3600.0,
        # L7 池体图元批几何形态参数（CASS 同值同 range 平移——manifest 声明面）
        "h2": 5.0,
        "ratio_lb": 2.5,
        "side_disc_step": 0.5,
        # data/coefficients factors.yaml（0.2.0 生效）逐字
        "factor.aao.ns_band.min": 0.05,
        "factor.aao.ns_band.max": 0.15,
        "factor.aao.mlss_band.min": 3500.0,
        "factor.aao.mlss_band.max": 4500.0,
        "factor.aao.sludge_age_band.min": 11.0,
        "factor.aao.sludge_age_band.max": 23.0,
        "factor.aao.hrt_anaerobic_band.min": 1.0,
        "factor.aao.hrt_anaerobic_band.max": 2.0,
        "factor.aao.hrt_anoxic_band.min": 2.0,
        "factor.aao.hrt_anoxic_band.max": 4.0,
        "factor.aao.k_denit": 0.05,
        "factor.aao.o2.a_prime": 0.5,
        "factor.aao.o2.b_prime": 0.1,
        "factor.aao.vss_ratio": 0.75,
        "factor.aao.yield.y": 0.5,
        "factor.aao.r_external_band.min": 0.5,
        "factor.aao.r_external_band.max": 1.0,
        "factor.aao.r_internal_band.min": 1.0,
        "factor.aao.r_internal_band.max": 3.0,
        "factor.aao.sludge.moisture": 0.994,
        "factor.aao.elevation_loss": 0.5,
        "factor.aao.superheight": 0.3,
        # removal_rates.yaml mod_default 档逐字（N/P 三键 0.8.0 NP1/RATIFY3）
        "removal.aao.bod5.mod_default": 0.90,
        "removal.aao.cod.mod_default": 0.85,
        "removal.aao.ss.mod_default": 0.90,
        "removal.aao.nh3n.mod_default": 0.90,
        "removal.aao.tn.mod_default": 0.75,
        "removal.aao.tp.mod_default": 0.93,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float], quality: WaterQuality | None = None) -> UnitContext:
    return UnitContext(
        unit_id="test_aao",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: quality if quality is not None else _QUALITY},
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
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包。"""
    assert manifest.unit_id == "municipal_aao"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
        ("sludge_out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {  # 六指标全键（N/P 三键 NP1/RATIFY3）
        "BOD5": "removal.aao.bod5.mod_default",
        "CODCR": "removal.aao.cod.mod_default",
        "SS": "removal.aao.ss.mod_default",
        "NH3N": "removal.aao.nh3n.mod_default",
        "TN": "removal.aao.tn.mod_default",
        "TP": "removal.aao.tp.mod_default",
    }


def test_main_case_volumes() -> None:
    """主算例（三表算例 1）分区容积/HRT 逐项断言（AO-F1~F5+导出量）。"""
    dims = _dims()
    assert dims["v_o"] == pytest.approx(10714.95, abs=0.01)  # AO-F1
    assert dims["t_o"] == pytest.approx(7.397973, abs=1e-4)  # AO-F2
    assert dims["v_anaerobic"] == pytest.approx(2172.544, abs=1e-2)  # AO-F3
    assert dims["delta_n"] == pytest.approx(28.0, abs=1e-9)  # 43−15
    assert dims["v_anoxic"] == pytest.approx(4866.498, abs=1e-2)  # AO-F4
    assert dims["t_n"] == pytest.approx(3.360000, abs=1e-4)  # AO-F5
    assert dims["v_total"] == pytest.approx(17753.99, abs=0.01)  # 三区合成
    assert dims["t_total"] == pytest.approx(12.25797, abs=1e-4)  # 全池 HRT
    assert dims["v_o_series"] == pytest.approx(5357.473, abs=1e-2)  # 单系列


def test_main_case_sludge_and_oxygen() -> None:
    """主算例剩余污泥/泥龄/需氧量逐项断言（AO-F6~F12）。"""
    dims = _dims()
    assert dims["s_y"] == pytest.approx(1928.690, abs=0.01)  # AO-F6
    assert dims["q_wet"] == pytest.approx(321.4484, abs=1e-3)  # AO-F7
    assert dims["theta_c"] == pytest.approx(22.22222, abs=1e-4)  # AO-F8（带内）
    assert dims["x_vss"] == pytest.approx(3000.0, abs=1e-9)  # 0.75×4000
    assert dims["o2_carbon"] == pytest.approx(5143.174, abs=0.02)  # AO-F9
    assert dims["o2_nit"] == pytest.approx(4447.979, abs=0.02)  # AO-F10
    assert dims["o2_denit"] == pytest.approx(2783.637, abs=0.02)  # AO-F11
    assert dims["o2_total"] == pytest.approx(6807.517, abs=0.05)  # AO-F12
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例七条校核带均合格


def test_main_case_returns() -> None:
    """主算例内外回流泵流量断言（AO-F13 最高时/F14 平均时双口径）。"""
    dims = _dims()
    assert dims["q_return"] == pytest.approx(2027.700, abs=0.1)  # AO-F13：×Q_design_h
    assert dims["q_internal"] == pytest.approx(2896.725, abs=1e-2)  # AO-F14：×Q_avg_h


def test_main_case_geometry() -> None:
    """主算例池体几何 8 键断言（AO-F15~F19——L7 CASS 公式族平移）。

    期望值=独立手算（非引擎回抄）：基值 v_total=17753.99（算例 1 锚，
    test_main_case_volumes）→ a_pool=v_total/h2=3550.798 →
    l_raw=sqrt(a_pool×2.5)≈94.2178 / b_raw=sqrt(a_pool÷2.5)≈37.6871 →
    0.5 m 档 ceil：l_pool=94.5 / b_pool=38.0；h_pool=0.3+5.0=5.3；
    v_pool=94.5×38×5=17955.0（圆整裕量 >v_total 诚实呈现，沿 CASS）。
    """
    dims = _dims()
    assert dims["h2"] == pytest.approx(5.0, abs=1e-12)  # 参数复用键入 dims
    assert dims["a_pool"] == pytest.approx(3550.798, abs=0.01)  # AO-F15
    assert dims["l_pool_raw"] == pytest.approx(94.2178, abs=1e-3)  # AO-F17
    assert dims["b_pool_raw"] == pytest.approx(37.6871, abs=1e-3)  # AO-F18
    assert dims["l_pool"] == pytest.approx(94.5, abs=1e-9)  # ceil 0.5 m 档
    assert dims["b_pool"] == pytest.approx(38.0, abs=1e-9)  # ceil 0.5 m 档
    assert dims["h_pool"] == pytest.approx(5.3, abs=1e-9)  # AO-F16：0.3+5.0
    assert dims["v_pool"] == pytest.approx(17955.0, abs=0.01)  # AO-F19
    assert dims["v_pool"] > dims["v_total"]  # 圆整裕量诚实呈现（D12）


def test_outflow_passthrough_and_quality() -> None:
    """出流透传 + 出水质=入质×(1−removal.mod_default)，NH3N/TN/TP 六键真实去除[NP1/RATIFY3]。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_aao", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(123.2996 * (1 - 0.90)) == out_quality.BOD5  # 12.32996
    assert pytest.approx(199.9362 * (1 - 0.85)) == out_quality.CODCR  # 29.99043
    assert pytest.approx(93.2121 * (1 - 0.90)) == out_quality.SS  # 9.32121
    assert pytest.approx(2.6) == out_quality.NH3N  # N/P 六键去除[NP1/RATIFY3]
    assert pytest.approx(10.75) == out_quality.TN
    assert pytest.approx(0.455) == out_quality.TP


def test_ns_band_warning() -> None:
    """校核带越界：ns=0.04 越 0.05~0.15 带（param_key=ns）。"""
    result = make_unit().compute(_ctx(_params(ns=0.04)))
    ns_warn = [w for w in result.warnings if "ns_band" in w.source]
    assert ns_warn and ns_warn[0].severity is Severity.WARN
    assert ns_warn[0].param_key == "ns"


def test_anaerobic_band_warning() -> None:
    """校核带越界：t_p=0.5 越 1~2 h 带（param_key=t_p）。"""
    result = make_unit().compute(_ctx(_params(t_p=0.5)))
    tp_warn = [w for w in result.warnings if "hrt_anaerobic_band" in w.source]
    assert tp_warn and tp_warn[0].param_key == "t_p"


def test_anoxic_band_warning() -> None:
    """校核带越界：x_mlss=8000 → t_n≈1.68 越 2~4 h 带（param_key=x_mlss）。"""
    result = make_unit().compute(_ctx(_params(x_mlss=8000.0)))
    tn_warn = [w for w in result.warnings if "hrt_anoxic_band" in w.source]
    assert tn_warn and tn_warn[0].param_key == "x_mlss"


def test_sludge_age_band_warning() -> None:
    """泥龄带越界：ns=0.30 → theta_c≈7.4 越 11~23 d 带（好氧泥龄口径）。"""
    result = make_unit().compute(_ctx(_params(ns=0.30)))
    age_warn = [w for w in result.warnings if "sludge_age_band" in w.source]
    assert age_warn and age_warn[0].severity is Severity.WARN
    assert age_warn[0].param_key == "ns"
    assert "好氧泥龄" in age_warn[0].message  # 口径注记随警告（待追认）


def test_param_domain_rejected() -> None:
    """参数域拒绝：ns≤0 / tn_eff≥TN_in（delta_n≤0）→ InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(ns=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(tn_eff=50.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(), WaterQuality({"BOD5": 120.0})))


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
    assert result.formula_ids == tuple(f"AO-F{index}" for index in range(1, 20))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"


def test_sludge_out_port() -> None:
    """GOLDEN4a D3 产股口：sludge_out 无条件产股（nongsuo sup 先例同构）。

    值链：ds=AO-F6 s_y 全厂（位级同式投影）；q_wet=AO-F7 dims 直用；
    moisture=factor.aao.sludge.moisture（0.994 与 sludge_hebing p_bio
    默认同源声明）。链路同源对照：工程值 1928.690=hebing 注入 ds_bio
    （表载舍入面——容差同表 s_y 行 abs=0.01）。"""
    result = make_unit().compute(_ctx(_params()))
    dims = result.dims
    assert isinstance(dims, dict)
    ref = PortRef(unit_id="test_aao", port_id="sludge_out")
    stock = result.outflows[ref]
    assert isinstance(stock, SludgeFlow)
    assert stock.ds == pytest.approx(dims["s_y"] / 86400, abs=1e-15)  # AO-F6 全厂
    assert stock.ds * 86400 == pytest.approx(1928.690, abs=0.01)  # hebing 注入链路
    assert stock.q_wet == pytest.approx(dims["q_wet"] / 86400, abs=1e-15)  # AO-F7 直用
    assert stock.q_wet * 86400 == pytest.approx(321.4483333333, abs=1e-3)  # =HB-F2 口径
    assert stock.moisture == pytest.approx(0.994, abs=1e-12)
    assert result.outqualities[ref].concentrations == {}  # 空 WaterQuality（GR-04）
