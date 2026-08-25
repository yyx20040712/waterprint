"""municipal_bashi_jiliangcao golden 数值测试（期望值来源：docs/norms/bashi_jiliangcao.md）。

输入:  本包 manifest 与 compute（make_unit）；期望值=三表算例 1 逐字（2026-08-26 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/bashi_jiliangcao.md 算例 1 与 B7 七档系数表；系数键值
#   逐字取自 data/coefficients 0.4.0 数据包 factors/removal_rates
#   yaml——测试区字面量合法。
#
# 【用例面】主算例（b075 档）逐项断言（ha_design/ha_avg/q_meas 往返闭环/
#   b1/l1/b2/l_total/构造常量/sigma/h_loss）+ **巴歇尔七档流量式各一
#   断言**（B7 全档：ha_design=(q_design×1000/C)^(1/n) 反解 + q_meas
#   =C·ha_avg^n 往返闭环，b025 档顺带断言选档校核越界产 WARN）+ 淹没度
#   越临界产 WARN + 非档位喉宽/非正喉宽域拒（Ruling ④：档位面归 grid，
#   compute 只保 b>0+命中）+ 出流=终水零去除穿流 + 纯函数双跑一致 +
#   formula_ids 全部可在公式注册表解析。
# 【口径注记】入流水质=三表衔接式值（BOD5 5.474500/COD 16.50599/
#   SS 0.2272045——紫外出流=全厂终水）；出流=零去除键透传（全指标原样
#   穿流不经 apply——与 M1a ×(1−r) 形态差异记档，ziwai 同款）。
# 【容差注记】三表手算取 Q_design=0.56325（5 位舍入），引擎用精确
#   34760.7/86400×1.4=0.5632520833——水头面差 <2e-5 m，1e-4 容差覆盖。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/municipal/bashi_jiliangcao/tests`
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
from waterprint.units_lib.municipal.bashi_jiliangcao import make_unit, manifest

# ── 算例 1 入参（三表逐字：Q_avg_daily=34760.7 m³/d、Kz=1.4；入流水质=
#    三表衔接式值——紫外出流=全厂终水） ──
_FLOW = WaterFlow(q_avg_daily=34760.7 / 86400, kz=1.4)
_IN_REF = PortRef(unit_id="test_bashi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.474500, "CODCR": 16.50599, "SS": 0.2272045, "NH3N": 26.0, "TN": 43.0, "TP": 6.5}
)

# B7 七档系数面（data/coefficients factors.yaml 0.4.0 逐字：
# 档名 → (喉宽 m, C, n, hmin, hmax, scrit)）。
_GRADES: dict[str, tuple[float, float, float, float, float, float]] = {
    "b025": (0.25, 561.0, 1.513, 0.03, 0.60, 0.6),
    "b045": (0.45, 1038.0, 1.537, 0.03, 0.75, 0.6),
    "b075": (0.75, 1772.0, 1.557, 0.06, 0.75, 0.6),
    "b100": (1.00, 2397.0, 1.569, 0.06, 0.80, 0.7),
    "b120": (1.20, 2904.0, 1.577, 0.06, 0.80, 0.7),
    "b150": (1.50, 3668.0, 1.586, 0.06, 0.80, 0.7),
    "b210": (2.10, 5222.0, 1.599, 0.08, 0.80, 0.7),
}


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(b_throat: float = 0.75, **overrides: float) -> dict[str, float]:
    """算例 1 参数面（b075 主算例选档；factor.*/removal.* 系数投影逐字）。"""
    params: dict[str, float] = {
        "b_throat": b_throat,
        # data/coefficients factors.yaml（0.4.0 M2c 三单元批）逐字——七档全档
        "factor.bashi_jiliangcao.flume.b025.c": 561.0,
        "factor.bashi_jiliangcao.flume.b025.n": 1.513,
        "factor.bashi_jiliangcao.flume.b025.scrit": 0.6,
        "factor.bashi_jiliangcao.flume.b025.hmin": 0.03,
        "factor.bashi_jiliangcao.flume.b025.hmax": 0.60,
        "factor.bashi_jiliangcao.flume.b045.c": 1038.0,
        "factor.bashi_jiliangcao.flume.b045.n": 1.537,
        "factor.bashi_jiliangcao.flume.b045.scrit": 0.6,
        "factor.bashi_jiliangcao.flume.b045.hmin": 0.03,
        "factor.bashi_jiliangcao.flume.b045.hmax": 0.75,
        "factor.bashi_jiliangcao.flume.b075.c": 1772.0,
        "factor.bashi_jiliangcao.flume.b075.n": 1.557,
        "factor.bashi_jiliangcao.flume.b075.scrit": 0.6,
        "factor.bashi_jiliangcao.flume.b075.hmin": 0.06,
        "factor.bashi_jiliangcao.flume.b075.hmax": 0.75,
        "factor.bashi_jiliangcao.flume.b100.c": 2397.0,
        "factor.bashi_jiliangcao.flume.b100.n": 1.569,
        "factor.bashi_jiliangcao.flume.b100.scrit": 0.7,
        "factor.bashi_jiliangcao.flume.b100.hmin": 0.06,
        "factor.bashi_jiliangcao.flume.b100.hmax": 0.80,
        "factor.bashi_jiliangcao.flume.b120.c": 2904.0,
        "factor.bashi_jiliangcao.flume.b120.n": 1.577,
        "factor.bashi_jiliangcao.flume.b120.scrit": 0.7,
        "factor.bashi_jiliangcao.flume.b120.hmin": 0.06,
        "factor.bashi_jiliangcao.flume.b120.hmax": 0.80,
        "factor.bashi_jiliangcao.flume.b150.c": 3668.0,
        "factor.bashi_jiliangcao.flume.b150.n": 1.586,
        "factor.bashi_jiliangcao.flume.b150.scrit": 0.7,
        "factor.bashi_jiliangcao.flume.b150.hmin": 0.06,
        "factor.bashi_jiliangcao.flume.b150.hmax": 0.80,
        "factor.bashi_jiliangcao.flume.b210.c": 5222.0,
        "factor.bashi_jiliangcao.flume.b210.n": 1.599,
        "factor.bashi_jiliangcao.flume.b210.scrit": 0.7,
        "factor.bashi_jiliangcao.flume.b210.hmin": 0.08,
        "factor.bashi_jiliangcao.flume.b210.hmax": 0.80,
        "factor.bashi_jiliangcao.hb_design": 0.25,
        "factor.bashi_jiliangcao.loss_ratio": 0.25,
        "factor.bashi_jiliangcao.geometry.l_throat": 0.60,
        "factor.bashi_jiliangcao.geometry.l_diffuse": 0.92,
        "factor.bashi_jiliangcao.geometry.n_depress": 0.23,
        "factor.bashi_jiliangcao.geometry.k_margin": 0.08,
        "factor.bashi_jiliangcao.elevation_loss": 0.15,
        # removal_rates.yaml mod_default 档逐字（计量单元零去除）
        "removal.bashi_jiliangcao.bod5.mod_default": 0.0,
        "removal.bashi_jiliangcao.cod.mod_default": 0.0,
        "removal.bashi_jiliangcao.ss.mod_default": 0.0,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_bashi",
        inflows={_IN_REF: _FLOW},
        inqualities={_IN_REF: _QUALITY},
        params=params,
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def _dims(b_throat: float = 0.75, **overrides: float) -> dict[str, float]:
    """主算例 dims 面收窄（compute 契约：str→float 全量）。"""
    dims = make_unit().compute(_ctx(_params(b_throat, **overrides))).dims
    assert isinstance(dims, dict)
    return dict(dims)


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包（全 0.0）。"""
    assert manifest.unit_id == "municipal_bashi_jiliangcao"
    assert manifest.business_line == "municipal"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "BOD5": "removal.bashi_jiliangcao.bod5.mod_default",
        "CODCR": "removal.bashi_jiliangcao.cod.mod_default",
        "SS": "removal.bashi_jiliangcao.ss.mod_default",
    }


def test_throat_grid_declared() -> None:
    """B7 七档档位面：manifest grid 声明（0.25~2.10 手册标准档）——
    简报枚举 0.5/1.25/2.0 非手册档按最近标准档映射（起草表追认点 1）。"""
    (spec,) = [s for s in manifest.params if s.field_id == "b_throat"]
    assert spec.grid == (0.25, 0.45, 0.75, 1.0, 1.2, 1.5, 2.1)


def test_main_case_heads() -> None:
    """主算例（b075 档）水头反解与流量读数往返闭环逐项断言（BL-F1~F3）。"""
    dims = _dims()
    assert dims["ha_design"] == pytest.approx(0.478969, abs=1e-4)  # BL-F2
    assert dims["ha_avg"] == pytest.approx(0.385883, abs=1e-4)  # BL-F3
    assert dims["q_meas"] == pytest.approx(402.3229, abs=1e-3)  # BL-F1：往返闭环
    # 5 位舍入口径复核：手算 0.478952 与引擎 0.478969 差 <2e-5 m
    assert dims["ha_design"] == pytest.approx((563.25 / 1772.0) ** (1 / 1.557), abs=5e-5)


def test_main_case_geometry() -> None:
    """主算例标准型构造尺寸逐项断言（BL-F4~F7+构造常量）。"""
    dims = _dims()
    assert dims["b1"] == pytest.approx(1.38, abs=1e-9)  # BL-F4：1.2×0.75+0.48
    assert dims["l1"] == pytest.approx(1.575, abs=1e-9)  # BL-F5：1.2+0.5×0.75
    assert dims["b2"] == pytest.approx(1.05, abs=1e-9)  # BL-F6：0.75+0.3
    assert dims["l_total"] == pytest.approx(3.095, abs=1e-9)  # BL-F7：1.575+0.60+0.92
    assert dims["l_throat"] == pytest.approx(0.60, abs=1e-9)  # 标准型常数
    assert dims["l_diffuse"] == pytest.approx(0.92, abs=1e-9)
    assert dims["n_depress"] == pytest.approx(0.23, abs=1e-9)  # 喉道底跌落 N
    assert dims["k_margin"] == pytest.approx(0.08, abs=1e-9)  # 槽身边距 K


def test_main_case_check() -> None:
    """主算例淹没度/水头损失断言（BL-F8/F9）——σ=0.522 ≤0.6 自由流合格。"""
    result = make_unit().compute(_ctx(_params()))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["sigma"] == pytest.approx(0.521954, abs=1e-4)  # BL-F8：自由流
    assert dims["h_loss"] == pytest.approx(0.119742, abs=1e-4)  # BL-F9：估算口径
    assert result.warnings == ()  # 主算例选档带内+自由流（b025 档才越带）


def test_all_seven_grades_flow_formula() -> None:
    """巴歇尔七档流量式各一断言（B7 全档）：ha_design 反解式 +
    q_meas=C·ha_avg^n 往返闭环；b025 档 ha_design=1.0027 越带产选档 WARN。"""
    q_design_ls = _FLOW.q_design * 1000.0
    q_avg_ls = _FLOW.q_avg_daily * 1000.0
    for grade, (b, c, n, hmin, hmax, scrit) in _GRADES.items():
        result = make_unit().compute(_ctx(_params(b_throat=b)))
        dims = result.dims
        assert isinstance(dims, dict)
        # BL-F2 反解式（流量式 Q=C·h^n 的逆，逐档断言）
        assert dims["ha_design"] == pytest.approx(
            (q_design_ls / c) ** (1 / n), abs=1e-6
        ), grade
        # BL-F1 流量式正向（平均时水头读数=平均时流量，往返闭环）
        assert dims["q_meas"] == pytest.approx(c * dims["ha_avg"] ** n, rel=1e-9), grade
        assert dims["ha_avg"] == pytest.approx((q_avg_ls / c) ** (1 / n), abs=1e-6), grade
        # BL-F8 淹没度档临界（σ = 0.25/ha_design——小水头档 σ 超临界=淹没流
        # 警报随档成立；主算例 hb_design=0.25 假定下 b120+ 档水深不足）
        assert dims["sigma"] == pytest.approx(0.25 / dims["ha_design"], abs=1e-9), grade
        sub_warnings = [w for w in result.warnings if "scrit" in w.source]
        assert (dims["sigma"] > scrit) == bool(sub_warnings), grade
        in_band = hmin <= dims["ha_design"] <= hmax
        band_warnings = [w for w in result.warnings if "hmin/hmax" in w.source]
        assert in_band == (not band_warnings), grade  # 选档校核与带一致
        # b025 档：563 L/s 反解水头 1.0027 m 越 0.60 上限（选档不当示例）
        if grade == "b025":
            assert dims["ha_design"] == pytest.approx(1.002651, abs=1e-4)
            assert band_warnings and band_warnings[0].severity is Severity.WARN
            assert band_warnings[0].param_key == "b_throat"


def test_submergence_warning() -> None:
    """淹没度越临界：hb_design=0.45 → σ≈0.94 > 0.6（淹没流）产 WARN。"""
    result = make_unit().compute(
        _ctx(_params(**{"factor.bashi_jiliangcao.hb_design": 0.45}))
    )
    sub = [w for w in result.warnings if "scrit" in w.source]
    assert sub and sub[0].severity is Severity.WARN
    assert sub[0].param_key == "b_throat"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["sigma"] == pytest.approx(0.939480, abs=1e-4)


def test_grade_domain_rejected() -> None:
    """档位域拒：非手册档喉宽 0.5/非正喉宽 → InvalidUnitConfig
    （Ruling ④ 同精神：compute 只保 b>0+档位命中，档位面归 grid 声明）。"""
    with pytest.raises(InvalidUnitConfig, match="非 B7 七档标准档位"):
        make_unit().compute(_ctx(_params(b_throat=0.5)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(b_throat=0.0)))


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=零去除键透传（全厂终水原样穿流）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_bashi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.4
    out_quality = result.outqualities[out_ref]
    assert out_quality.BOD5 == 5.474500  # 透传（removal 全 0.0，不经 apply）
    assert out_quality.CODCR == 16.50599
    assert out_quality.SS == 0.2272045
    assert out_quality.NH3N == 26.0
    assert out_quality.TN == 43.0
    assert out_quality.TP == 6.5


def test_pure_function_double_run() -> None:
    """纯函数断言：同 ctx 双跑 dims/warnings 逐键相同（unit_api R1）。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings
    assert first.formula_ids == second.formula_ids


def test_formula_ids_registered() -> None:
    """formula_ids 非空且全部可在公式注册表解析（§16 A1 漂移防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"BL-F{index}" for index in range(1, 10))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
