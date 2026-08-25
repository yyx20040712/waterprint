"""municipal_erchunchi golden 数值测试（期望值来源：docs/norms/erchunchi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-25 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/erchunchi.md 算例 1（含 D=41.0 固体负荷主控/d_center=1.6/
#   h4=1.0/h_total=4.6 离散化项）；系数键值逐字取自 data/coefficients
#   0.2.0+0.2.1 数据包 factors/removal_rates yaml——测试区字面量合法。
#
# 【用例面】主算例逐项断言（q1h/a_q/m_solid/a_solid/a_tank/d_raw/D/
#   a_act/q_act/g_act/x_r/v_check/t_hrt/q_return_sludge/q_weir/
#   d_center/h4/h_total/v_concrete）+ 校核带越界产 Warning（清水负荷带/
#   堰负荷[堰构造注记]/Xr 带[0.2.1 键]/水深带/HRT 带[0.2.1 键]）+
#   参数域拒绝（n<1、q_nom≤0）+ 纯函数双跑一致 + formula_ids 全部可在
#   公式注册表解析。
# 【口径注记】入流水质=三表衔接式值（BOD5 12.32996/COD 29.99043/
#   SS 9.32121，上游=AAO 出流）；出流=全厂出水（BOD 9.864/COD 25.49/
#   SS 4.66，一级 A 三指标合格）；m_solid 等最高时口径量与表 5 位舍入
#   Q_design 差 <0.01%，容差覆盖。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/erchunchi/tests`
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
from waterprint.units_lib.municipal.erchunchi import make_unit, manifest

# ── 算例 1 入参（三表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    三表衔接式值——AAO 生物池出流逐项） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_erchunchi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 12.32996, "CODCR": 29.99043, "SS": 9.32121, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
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
        "q_nom": 1.2,
        "x_mlss": 4000.0,
        "r_external": 1.0,
        "h2": 3.0,
        "r_pit": 1.0,
        "dia_disc_step": 0.5,
        "length_disc_step": 0.1,
        # data/coefficients factors.yaml（0.2.0 生效 + 0.2.1 前置键）逐字
        "factor.erchunchi.surface_load_band.min": 0.6,
        "factor.erchunchi.surface_load_band.max": 1.5,
        "factor.erchunchi.solid_load.center_inlet": 150.0,
        "factor.erchunchi.solid_load.peripheral_inlet": 200.0,
        "factor.erchunchi.weir_load.max": 1.7,
        "factor.erchunchi.depth_band.min": 2.5,
        "factor.erchunchi.depth_band.max": 3.5,
        "factor.erchunchi.superheight": 0.3,
        "factor.erchunchi.buffer_h3": 0.3,
        "factor.erchunchi.bottom_slope": 0.05,
        "factor.erchunchi.center_velocity": 0.3,
        "factor.erchunchi.wall_thickness_coef": 0.4,
        "factor.erchunchi.elevation_loss": 0.6,
        "factor.erchunchi.x_r_band.min": 6000.0,  # 0.2.1 前置键
        "factor.erchunchi.x_r_band.max": 12000.0,
        "factor.erchunchi.hrt_band.min": 1.5,  # 0.2.1 前置键
        "factor.erchunchi.hrt_band.max": 4.0,
        # removal_rates.yaml mod_default 档逐字
        "removal.erchunchi.bod5.mod_default": 0.20,
        "removal.erchunchi.cod.mod_default": 0.15,
        "removal.erchunchi.ss.mod_default": 0.50,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_erchunchi",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims(**overrides: float) -> dict[str, float]:
    """主算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params(**overrides))).dims
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包。"""
    assert manifest.unit_id == "municipal_erchunchi"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.erchunchi.bod5.mod_default",
        "CODCR": "removal.erchunchi.cod.mod_default",
        "SS": "removal.erchunchi.ss.mod_default",
    }


def test_main_case_load() -> None:
    """主算例（三表算例 1）双控面积/池径/负荷校核逐项断言（EC-F1~F10）。"""
    dims = _dims()
    assert dims["q1"] == pytest.approx(0.281625, abs=1e-5)  # EC-F1 子式
    assert dims["q1h"] == pytest.approx(1013.85, abs=0.1)  # EC-F1：×3600
    assert dims["a_q"] == pytest.approx(844.8750, abs=1e-2)  # EC-F2
    assert dims["m_solid"] == pytest.approx(194659.2, abs=1.0)  # EC-F3：(1+1)×q1h×24×4
    assert dims["a_solid"] == pytest.approx(1297.728, abs=1e-2)  # EC-F4
    assert dims["a_tank"] == pytest.approx(1297.728, abs=1e-2)  # EC-F5：固体负荷主控
    assert dims["d_raw"] == pytest.approx(40.6501, abs=1e-2)  # EC-F6：√1652.45
    assert dims["d"] == pytest.approx(41.0, abs=1e-9)  # 0.5 m 档向上取整
    assert dims["a_act"] == pytest.approx(1320.254, abs=1e-2)  # EC-F7：π×420.25
    assert dims["q_act"] == pytest.approx(0.7679202, abs=1e-5)  # EC-F8：带内
    assert dims["g_act"] == pytest.approx(147.4407, abs=1e-2)  # EC-F9：≤150 合格
    assert dims["x_r"] == pytest.approx(8000.0, abs=1e-9)  # EC-F10：带内
    assert dims["v_check"] == pytest.approx(3960.763, abs=1e-2)  # a_act×3.0
    assert dims["t_hrt"] == pytest.approx(3.906656, abs=1e-3)  # 校核 HRT：带内
    assert dims["q_return_sludge"] == pytest.approx(1013.85, abs=0.1)  # R×q1h


def test_main_case_geometry() -> None:
    """主算例堰负荷/中心筒/池底坡/总高/混凝土量逐项断言（EC-F11~F15）。"""
    dims = _dims()
    assert dims["q_weir"] == pytest.approx(1.093220, abs=1e-5)  # EC-F11：L=2π×41
    assert dims["d_center"] == pytest.approx(1.6, abs=1e-9)  # EC-F12：1.54615 → 0.1 档
    assert dims["h4"] == pytest.approx(1.0, abs=1e-9)  # EC-F13：0.975 → 0.1 档
    assert dims["h_total"] == pytest.approx(4.6, abs=1e-9)  # EC-F14：整值无需取整
    assert dims["v_concrete"] == pytest.approx(4858.536, abs=1e-1)  # EC-F15
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例六条校核带均合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传 + 出水质=入质×(1−removal.mod_default)——全厂出水三指标。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_erchunchi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(12.32996 * (1 - 0.20)) == out_quality.BOD5  # 9.863964 ≤10
    assert pytest.approx(29.99043 * (1 - 0.15)) == out_quality.CODCR  # 25.49187 ≤50
    assert pytest.approx(9.32121 * (1 - 0.50)) == out_quality.SS  # 4.660605 ≤10
    assert out_quality.NH3N == 26.0  # 氮磷去除归后续批，穿流不变
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_surface_and_weir_band_warnings() -> None:
    """清水负荷带/堰负荷越界：q_nom=2.0+固体上限放大 → 水力主控 q_act≈1.91、
    堰负荷≈1.72 双越界（堰构造注记随警告，param_key=None）。"""
    result = make_unit().compute(
        _ctx(_params(q_nom=2.0, **{"factor.erchunchi.solid_load.center_inlet": 10000.0}))
    )
    surf = [w for w in result.warnings if "surface_load_band" in w.source]
    assert surf and surf[0].severity is Severity.WARN
    assert surf[0].param_key == "q_nom"
    weir = [w for w in result.warnings if "weir_load" in w.source]
    assert weir and weir[0].param_key is None  # 归堰构造口径注记
    assert "单侧" in weir[0].message


def test_x_r_band_warning() -> None:
    """Xr 带越界（0.2.1 键）：r_external=0.4 → Xr=14000 越 6000~12000 带。"""
    result = make_unit().compute(_ctx(_params(r_external=0.4)))
    xr = [w for w in result.warnings if "x_r_band" in w.source]
    assert xr and xr[0].severity is Severity.WARN
    assert xr[0].param_key == "r_external"
    assert "0.2.1" in xr[0].source


def test_depth_and_hrt_band_warnings() -> None:
    """水深带/HRT 带越界（0.2.1 键）：h2=2.0 越水深带；再放大固体上限
    收小池径 → 校核 HRT≈1.35 越 1.5~4 带。"""
    result = make_unit().compute(_ctx(_params(h2=2.0)))
    dep = [w for w in result.warnings if "depth_band" in w.source]
    assert dep and dep[0].param_key == "h2"
    result2 = make_unit().compute(
        _ctx(
            _params(
                h2=2.0,
                q_nom=1.5,
                **{"factor.erchunchi.solid_load.center_inlet": 10000.0},
            )
        )
    )
    hrt = [w for w in result2.warnings if "hrt_band" in w.source]
    assert hrt and hrt[0].severity is Severity.WARN
    assert hrt[0].param_key == "q_nom"
    assert "0.2.1" in hrt[0].source


def test_param_domain_rejected() -> None:
    """参数域拒绝：n<1 / q_nom≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(q_nom=0.0)))


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
    assert result.formula_ids == tuple(f"EC-F{index}" for index in range(1, 16))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
