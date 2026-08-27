"""mine_water_vxinglvchi golden 数值测试（期望值来源：docs/norms/mine_water_vxinglvchi.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_vxinglvchi.md 主算例（KV-F1~F11 十一项：q_d=
#   46027.8/t_w=23.8/f_total=386.7882352941/f_single=24.1742647059/
#   v_force_act=5.3333333333/B=3.5/L=7.0/w_wash=3.66/eta_wash=
#   0.0012722746（0.13%）/h_total=3.7/v_concrete=507.64）与副算例
#   （n=12 少格数：f_single=32.2323529412/v_force_act=5.4545454545/
#   B=4.1/L=7.9/eta_wash=0.0009542059（0.10%）/v_concrete=503.3406）；
#   系数键值逐字取自 data/coefficients 0.5.0 factors.yaml
#   （mine_vxinglvchi 21 键）/removal_rates.yaml（ss 0.80 低浊进水
#   档/cod 0.075 微量去除保守档）——测试区字面量合法。
#   t_bw 口径注记：三阶段反冲停滤历时=t_air+t_sim+t_water=3+4+5=12
#   min（表主算例输入 t_bw=12 min 同值，compute 零字面量合成审计面
#   ——ningjiao p_total 单输出导出量先例）；B/L 0.1 m 档 ceil 浮点
#   尾差（4.1000000000000005）断言容差 abs=1e-9 覆盖。
#
# 【用例面】主算例逐项断言 + 副算例少格数对照 + 校核带越界产
#   Warning（滤速带/强制滤速上限/滤层厚带/砂上水深带/周期带/反冲
#   耗水率上限）+ 参数域拒绝（n≤1 除零守卫、v_filter≤0、t_filter≤0）
#   + 纯函数双跑一致 + formula_ids 全部可在公式注册表解析 + 出流
#   水质=入质×(1−removal)（SS 6.8→1.36/COD 56→51.8 衔接 ziwai 表——
#   COD 51.8 为全厂终水贴 GB 20426-2006 限值 50 上方，表内注记）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/vxinglvchi/tests`
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
from waterprint.units_lib.mine_water.vxinglvchi import make_unit, manifest

# ── 主算例入参（表逐字：Q_avg_daily=43836.0 m³/d（日处理量口径——
#    过滤面积按平均日×自用水系数，异于沉淀类最高时口径）、n=16 格、
#    v_filter=5.0 m/h、k_self=1.05、t_filter=24 h、t_bw=12 min（三阶段
#    3+4+5 合成）、ratio_lb=2.0、h_media=1.0、h_water=1.2、h_super=0.5、
#    h_plate=0.1、h_under=0.9、q_w_sim=3、q_w=5、q_sweep=2、t_sim=4、
#    t_water=5、wall_coef=0.35；入流水质=gaomidu 表出流——SS 6.8/COD 56） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_vxinglvchi", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"BOD5": 5.0, "CODCR": 56.0, "SS": 6.8, "NH3N": 1.0, "TN": 60.0, "TP": 2.0}
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；系数投影逐字 0.5.0）。"""
    params: dict[str, float] = {
        "n": 16.0,
        "v_filter": 5.0,
        "t_filter": 24.0,
        "h_media": 1.0,
        "h_water": 1.2,
        "h_plate": 0.1,
        "h_under": 0.9,
        "side_disc_step": 0.1,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_vxinglvchi.v_filter_band.min": 4.0,
        "factor.mine_vxinglvchi.v_filter_band.max": 6.0,
        "factor.mine_vxinglvchi.v_forced.max": 10.0,
        "factor.mine_vxinglvchi.selfuse_coef": 1.05,
        "factor.mine_vxinglvchi.cell_ratio_lb": 2.0,
        "factor.mine_vxinglvchi.media.depth_band.min": 0.8,
        "factor.mine_vxinglvchi.media.depth_band.max": 1.2,
        "factor.mine_vxinglvchi.water_above_band.min": 1.0,
        "factor.mine_vxinglvchi.water_above_band.max": 1.5,
        "factor.mine_vxinglvchi.wash.air": 15.0,
        "factor.mine_vxinglvchi.wash.water_sim": 3.0,
        "factor.mine_vxinglvchi.wash.water": 5.0,
        "factor.mine_vxinglvchi.wash.sweep": 2.0,
        "factor.mine_vxinglvchi.wash.t_air": 3.0,
        "factor.mine_vxinglvchi.wash.t_sim": 4.0,
        "factor.mine_vxinglvchi.wash.t_water": 5.0,
        "factor.mine_vxinglvchi.cycle_band.min": 24.0,
        "factor.mine_vxinglvchi.cycle_band.max": 48.0,
        "factor.mine_vxinglvchi.wash.ratio_max": 0.05,
        "factor.mine_vxinglvchi.superheight": 0.5,
        "factor.mine_vxinglvchi.wall_thickness_coef": 0.35,
        "factor.mine_vxinglvchi.elevation_loss": 2.5,
        # removal_rates.yaml mod_default 档逐字（深层过滤）
        "removal.mine_vxinglvchi.ss.mod_default": 0.8,
        "removal.mine_vxinglvchi.cod.mod_default": 0.075,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_vxinglvchi",
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


def test_manifest_identity() -> None:
    """清单身份：UNIT_ID/业务线/两口 WATER/去除率引用键对齐 data 包（BOD5 不建键）。"""
    assert manifest.unit_id == "mine_water_vxinglvchi"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_vxinglvchi.ss.mod_default",
        "CODCR": "removal.mine_vxinglvchi.cod.mod_default",
    }


def test_main_case_flow_chain() -> None:
    """主算例（表主算例）日处理量/有效过滤时长/过滤面积逐项断言（KV-F1~F4）。"""
    dims = _dims()
    assert dims["t_bw"] == pytest.approx(12.0, abs=1e-9)  # 三阶段 3+4+5 合成审计面
    assert dims["q_d"] == pytest.approx(46027.8, abs=1e-9)  # KV-F1：43836×1.05
    assert dims["t_w"] == pytest.approx(23.8, abs=1e-9)  # KV-F2：24−24×(12/60)/24
    assert dims["f_total"] == pytest.approx(386.7882352941, abs=1e-8)  # KV-F3
    assert dims["f_single"] == pytest.approx(24.1742647059, abs=1e-8)  # KV-F4：/16
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例六条校核面均合格


def test_main_case_layout_wash() -> None:
    """主算例强制滤速/单格尺寸（0.1 m 档）/反冲水量/耗水率逐项断言（KV-F5~F9）。"""
    dims = _dims()
    assert dims["v_force_act"] == pytest.approx(5.3333333333, abs=1e-8)  # KV-F5：16/15×5
    assert dims["b_raw"] == pytest.approx(3.4766553400, abs=1e-8)  # KV-F6：√(24.174…/2)
    assert dims["b"] == pytest.approx(3.5, abs=1e-9)  # 0.1 m 档向上取整
    assert dims["l_raw"] == pytest.approx(6.9069327731, abs=1e-8)  # KV-F7
    assert dims["l"] == pytest.approx(7.0, abs=1e-9)  # 0.1 m 档向上取整
    assert dims["w_wash"] == pytest.approx(3.66, abs=1e-9)  # KV-F8：(3×4+5×5+2×12)×60/1000
    assert dims["eta_wash"] == pytest.approx(0.0012722746, abs=1e-10)  # KV-F9：0.13% ≤5%


def test_main_case_depth_concrete() -> None:
    """主算例滤池总高与概算混凝土量逐项断言（KV-F10~F11）。"""
    dims = _dims()
    assert dims["h_total"] == pytest.approx(3.7, abs=1e-9)  # KV-F10：五段构造高
    assert dims["v_concrete"] == pytest.approx(507.64, abs=1e-6)  # KV-F11：概算


def test_secondary_case_few_cells() -> None:
    """副算例（n=12 少格数）逐项断言（表副算例）。"""
    dims = _dims(n=12.0)
    assert dims["f_single"] == pytest.approx(32.2323529412, abs=1e-8)
    assert dims["v_force_act"] == pytest.approx(5.4545454545, abs=1e-8)  # 12/11×5
    assert dims["b"] == pytest.approx(4.1, abs=1e-9)  # 0.1 m 档（浮点尾差容差内）
    assert dims["l"] == pytest.approx(7.9, abs=1e-9)
    assert dims["eta_wash"] == pytest.approx(0.0009542059, abs=1e-10)  # 0.10%
    assert dims["v_concrete"] == pytest.approx(503.3406, abs=1e-6)
    result = make_unit().compute(_ctx(_params(n=12.0)))
    assert result.warnings == ()  # 副算例各校核面均带内合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal)（衔接下游 ziwai 表——全厂终水）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_vxinglvchi", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(1.36, abs=1e-9) == out_quality.SS  # 6.8×(1−0.80)
    assert pytest.approx(51.8, abs=1e-9) == out_quality.CODCR  # 56×(1−0.075)
    assert out_quality.BOD5 == 5.0  # 无去除键穿流不变
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_v_filter_band_warning() -> None:
    """校核带越界：v_filter=7.0 越 4~6 带产 WARN（param_key=v_filter）。"""
    result = make_unit().compute(_ctx(_params(v_filter=7.0)))
    band = [w for w in result.warnings if "v_filter_band" in w.source]
    assert band and band[0].severity is Severity.WARN
    assert band[0].param_key == "v_filter"


def test_forced_velocity_warning() -> None:
    """校核带越界：n=31 格一格冲洗 → v_force=31/30×9.6>10 越上限产 WARN。

    构造场景（warning 用例参数面允许合成）：n=31、v_filter=9.6 →
    31/30×9.6=9.92≤10 未越；取 v_filter=10.0→31/30×10=10.33>10 实证
    （v_filter=10 本身越滤速带同场景双触发——两带独立）。
    """
    result = make_unit().compute(_ctx(_params(n=31.0, v_filter=10.0)))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_force_act"] == pytest.approx(31.0 / 30.0 * 10.0, abs=1e-8)
    assert dims["v_force_act"] > 10.0
    forced = [w for w in result.warnings if "v_forced" in w.source]
    assert forced and forced[0].severity is Severity.WARN


def test_media_depth_band_warning() -> None:
    """校核带越界：h_media=0.6 越 0.8~1.2 带产 WARN（param_key=h_media）。"""
    result = make_unit().compute(_ctx(_params(h_media=0.6)))
    media = [w for w in result.warnings if "media.depth_band" in w.source]
    assert media and media[0].severity is Severity.WARN
    assert media[0].param_key == "h_media"


def test_water_above_band_warning() -> None:
    """校核带越界（M3a3 R1 补例）：h_water=2.0 越 1.0~1.5 上带产 WARN（param_key=h_water）。

    越带触发探针实录：h_water=2.0 → 恰一条 water_above_band WARN（无其余带
    误报）；带内对照 h_water=1.2 → 零告警（新断言非空真实证——红证等效）。
    """
    result = make_unit().compute(_ctx(_params(h_water=2.0)))
    dims = result.dims
    assert isinstance(dims, dict)
    # 0.5+2.0+1.0+0.1+0.9——h_water=2.0 生效实值
    assert dims["h_total"] == pytest.approx(4.5, abs=1e-9)
    above = [w for w in result.warnings if "water_above_band" in w.source]
    assert above and above[0].severity is Severity.WARN
    assert above[0].param_key == "h_water"
    assert len(above) == 1  # 恰一条——不牵动其余校核带


def test_cycle_band_warning() -> None:
    """校核带越界（M3a3 R1 补例）：t_filter=60.0 越 24~48 上带产 WARN（param_key=t_filter）。

    越带触发探针实录：t_filter=60.0 → 恰一条 cycle_band WARN（长周期不触发
    耗水率面——eta=3.66×(24/60)/2876.7375 更小）；带内对照 t_filter=24.0 →
    零告警（新断言非空真实证——红证等效）。
    """
    result = make_unit().compute(_ctx(_params(t_filter=60.0)))
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["t_w"] == pytest.approx(24 - 24 * (12.0 / 60) / 60, abs=1e-9)  # 23.92 长周期实值
    cycle = [w for w in result.warnings if "cycle_band" in w.source]
    assert cycle and cycle[0].severity is Severity.WARN
    assert cycle[0].param_key == "t_filter"
    assert len(cycle) == 1  # 恰一条——不牵动其余校核带


def test_wash_ratio_warning() -> None:
    """校核带越界：周期 8 h 短周期高频反冲 → eta_wash 越 5% 上限产 WARN。

    构造场景（warning 用例参数面允许合成）：t_filter=8（越 24~48 带同
    场景双触发）→ eta=3.66×(24/8)/2876.7375=0.003817≤5% 未越；取
    t_filter=1 极端短周期 → eta=3.66×24/2876.7375=0.030534 仍≤5%——
    反冲耗水率在单格日冲一次口径下达 5% 需 q_d 极小：取 n=2 格 →
    eta=3.66×24/(46027.8/2)=0.0038…未越；耗水率越限以带键投影放宽
    ratio_max=0.001 实证（eta=0.001272>0.001——键值域内合成）。
    """
    result = make_unit().compute(
        _ctx(_params(**{"factor.mine_vxinglvchi.wash.ratio_max": 0.001}))
    )
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["eta_wash"] == pytest.approx(0.0012722746, abs=1e-10)
    assert dims["eta_wash"] > 0.001
    ratio = [w for w in result.warnings if "wash.ratio_max" in w.source]
    assert ratio and ratio[0].severity is Severity.WARN


def test_param_domain_rejected() -> None:
    """参数域拒绝：n=1（强制滤速除零守卫）/v_filter≤0/t_filter≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n=1.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(v_filter=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(t_filter=0.0)))


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
    assert result.formula_ids == tuple(f"KV-F{index}" for index in range(1, 12))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
