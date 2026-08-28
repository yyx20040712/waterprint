"""mine_water_cifenli golden 数值测试（期望值来源：docs/norms/mine_water_cifenli.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/mine_water_cifenli.md 主算例（KS-F1~F8 八项：q_1h=684.9375/
#   a_disk=1.2370021059/a_total_req=27.3975/n_disks=23/v_line=
#   0.2356194488/w_ss=26.827632/q_sludge=304.8594545455/m_seed_net=
#   1.0959 t/d）与副算例（n_units=2、q_surf=20 少台数低负荷：q_1h=
#   1369.875/a_total_req=68.49375/n_disks=56）；系数键值逐字取自
#   data/coefficients 0.5.0 factors.yaml（mine_cifenli 14 键）/
#   removal_rates.yaml（ss 0.90/cod 0.60——磁絮体磁盘截留，颗粒态
#   COD 随絮体带出）——测试区字面量合法。
#   π 口径注记：表 KS-F2/KS-F5 内联 3.14159265 按模板惯例经符号 pi
#   绑定 math.pi（KI/KT 先例同型）——a_disk 差 1.45e-9/v_line 差
#   2.2e-10，断言容差 abs=1e-8 覆盖；m_seed_net 表期望列 1.0959 t/d
#   为显示口径，DSL 逐字输出 kg/d=1095.9（同量 ×1000）。
#
# 【用例面】主算例逐项断言 + 副算例少台数低负荷对照 + 校核带越界
#   产 Warning（表面负荷带/盘转速上限）+ 参数域拒绝（n_units≤0、
#   omega≤0、m_seed≤0）+ 纯函数双跑一致 + formula_ids 全部可在公式
#   注册表解析 + 出流水质=入质×(1−removal)（SS 680→68/COD 200→80
#   衔接 gaomidu 表）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/mine_water/cifenli/tests`
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
from waterprint.units_lib.mine_water.cifenli import make_unit, manifest

# ── 主算例入参（表逐字：Q_design_h=2739.75 m³/h（Q_avg_daily=43836
#    m³/d、Kz=1.5 上游口径）、n_units=4 台、d_disk=1.5 m、eta_im=0.35、
#    omega=3 rpm、q_surf=25、ss_in=680.0、eta_ss=0.90、p_sludge=0.92、
#    rho_sludge=1100、m_seed=21918.0 kg/d（ningjiao KN-F13 口径）、
#    eta_recover=0.95；入流水质=ningjiao 表出流——SS 680/COD 200） ──
_FLOW = WaterFlow(q_avg_daily=43836.0 / 86400, kz=1.5)
_IN_REF = PortRef(unit_id="test_mine_cifenli", port_id="in")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)
_QUALITY = WaterQuality(
    {"CODCR": 200.0, "SS": 680.0, "NH3N": 1.0, "TN": 60.0, "TP": 2.0}
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
        "n_units": 4.0,
        "omega": 3.0,
        "q_surf": 25.0,
        "m_seed": 21918.0,
        # data/coefficients factors.yaml（0.5.0）逐字
        "factor.mine_cifenli.surface_load_band.min": 20.0,
        "factor.mine_cifenli.surface_load_band.max": 40.0,
        "factor.mine_cifenli.disk.diameter": 1.5,
        "factor.mine_cifenli.disk.immersion": 0.35,
        "factor.mine_cifenli.disk.speed_max": 3.0,
        "factor.mine_cifenli.seed.recovery": 0.95,
        "factor.mine_cifenli.sludge.moisture": 0.92,
        "factor.mine_cifenli.sludge.density": 1100.0,
        "factor.mine_cifenli.superheight": 0.3,
        "factor.mine_cifenli.wall_thickness_coef": 0.35,
        "factor.mine_cifenli.elevation_loss": 0.2,
        # removal_rates.yaml mod_default 档逐字（KS-F6 截留率=SS 去除键）
        "removal.mine_cifenli.ss.mod_default": 0.9,
        "removal.mine_cifenli.cod.mod_default": 0.6,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_mine_cifenli",
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
    assert manifest.unit_id == "mine_water_cifenli"
    assert manifest.business_line == "mine_water"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
        ("sludge_out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {
        "SS": "removal.mine_cifenli.ss.mod_default",
        "CODCR": "removal.mine_cifenli.cod.mod_default",
    }


def test_main_case_disk_chain() -> None:
    """主算例（表主算例）单台流量/单盘面积/需盘面总面积逐项断言（KS-F1~F3）。"""
    dims = _dims()
    assert dims["q_1h"] == pytest.approx(684.9375, abs=1e-9)  # KS-F1：2739.75/4
    assert dims["a_disk"] == pytest.approx(1.2370021059, abs=1e-8)  # KS-F2：π 差 1.45e-9
    assert dims["a_total_req"] == pytest.approx(27.3975, abs=1e-9)  # KS-F3：/25 带内
    result = make_unit().compute(_ctx(_params()))
    assert result.warnings == ()  # 主算例两条校核面均合格


def test_main_case_disks_and_speed() -> None:
    """主算例盘片数（取整）与盘缘线速度逐项断言（KS-F4/F5）。"""
    dims = _dims()
    assert dims["n_disks_raw"] == pytest.approx(22.1483050329, abs=1e-8)  # 取整前审计面
    assert dims["n_disks"] == pytest.approx(23.0, abs=1e-9)  # KS-F4：22.148… ceil 23 盘/台
    assert dims["v_line"] == pytest.approx(0.2356194488, abs=1e-8)  # KS-F5：≤0.3 合格


def test_main_case_mass_balance() -> None:
    """主算例截留泥量/磁泥湿量/磁种净耗逐项断言（KS-F6~F8，平均日口径）。"""
    dims = _dims()
    assert dims["w_ss"] == pytest.approx(26.827632, abs=1e-9)  # KS-F6：43836×680×0.90/10⁶
    assert dims["q_sludge"] == pytest.approx(304.8594545455, abs=1e-8)  # KS-F7：全厂湿量
    # KS-F8：DSL 逐字输出 kg/d=1095.9（表期望列 1.0959 t/d 显示口径，同量）
    assert dims["m_seed_net"] == pytest.approx(1095.9, abs=1e-8)
    assert dims["m_seed_net"] == pytest.approx(1.0959 * 1000, abs=1e-6)


def test_secondary_case_few_units() -> None:
    """副算例（n_units=2、q_surf=20 少台数低负荷）逐项断言（表副算例）。"""
    dims = _dims(n_units=2.0, q_surf=20.0)
    assert dims["q_1h"] == pytest.approx(1369.875, abs=1e-9)
    assert dims["a_total_req"] == pytest.approx(68.49375, abs=1e-9)  # 带边缘——单台盘量放大
    assert dims["n_disks_raw"] == pytest.approx(55.3707625824, abs=1e-8)
    assert dims["n_disks"] == pytest.approx(56.0, abs=1e-9)  # 56 盘/台（贴限记录归追认点 9）
    result = make_unit().compute(_ctx(_params(n_units=2.0, q_surf=20.0)))
    assert result.warnings == ()  # q_surf=20 恰带下限内合格


def test_outflow_passthrough_and_quality() -> None:
    """出流透传（水量不变）+ 出水质=入质×(1−removal)（衔接下游 gaomidu 表）。"""
    result = make_unit().compute(_ctx(_params()))
    out_ref = PortRef(unit_id="test_mine_cifenli", port_id="out")
    out_flow = result.outflows[out_ref]
    assert isinstance(out_flow, WaterFlow)
    assert out_flow.q_avg_daily == _FLOW.q_avg_daily
    assert out_flow.kz == 1.5
    out_quality = result.outqualities[out_ref]
    assert pytest.approx(68.0, abs=1e-9) == out_quality.SS  # 680×(1−0.90)
    assert pytest.approx(80.0, abs=1e-9) == out_quality.CODCR  # 200×(1−0.60)
    assert out_quality.BOD5 is None  # 不建键缺项=None（P6 契约）
    assert out_quality.NH3N == 1.0
    assert out_quality.TN == 60.0
    assert out_quality.TP == 2.0


def test_surface_load_band_warning() -> None:
    """校核带越界：q_surf=45 越 20~40 带产 WARN（param_key=q_surf）。"""
    result = make_unit().compute(_ctx(_params(q_surf=45.0)))
    band = [w for w in result.warnings if "surface_load_band" in w.source]
    assert band and band[0].severity is Severity.WARN
    assert band[0].param_key == "q_surf"


def test_disk_speed_warning() -> None:
    """校核带越界：omega=5 越盘转速上限 disk.speed_max=3 产 WARN（param_key=omega）。"""
    result = make_unit().compute(_ctx(_params(omega=5.0)))
    speed = [w for w in result.warnings if "disk.speed_max" in w.source]
    assert speed and speed[0].severity is Severity.WARN
    assert speed[0].param_key == "omega"
    dims = result.dims
    assert isinstance(dims, dict)
    assert dims["v_line"] == pytest.approx(0.3926990817, abs=1e-8)  # 5 rpm 越限实证


def test_param_domain_rejected() -> None:
    """参数域拒绝：n_units≤0 / omega≤0 / m_seed≤0 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(n_units=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(omega=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(m_seed=0.0)))


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
    # GOLDEN4b R1（2026-08-28）：MS-F1 磁泥股衔接式收编（sludge_out 产股消费）
    assert result.formula_ids == (*tuple(f"KS-F{index}" for index in range(1, 9)), "MS-F1")
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"

def test_sludge_out_port() -> None:
    """GOLDEN4a D3 产股口：sludge_out 无条件产股（nongsuo sup 先例同构）。

    值链（手算表 MS-F1 口径）：ds=w_ss×1000（KS-F6 干基 t/d→kg/d——
    26827.632 直对 MSLUDGE2 锚）；q_wet=q_sludge 直用（KS-F7 ρ=1100
    直算口径 304.8594545455——映射表"上游直算口径"列）；moisture=
    factor.mine_cifenli.sludge.moisture（0.92 hebing p_primary 注入位
    同源）；契约口径=工程值/86400。"""
    result = make_unit().compute(_ctx(_params()))
    dims = result.dims
    assert isinstance(dims, dict)
    ref = PortRef(unit_id="test_mine_cifenli", port_id="sludge_out")
    stock = result.outflows[ref]
    assert isinstance(stock, SludgeFlow)
    assert stock.ds == pytest.approx(dims["w_ss"] * 1000 / 86400, abs=1e-15)  # MS-F1
    assert stock.ds * 86400 == pytest.approx(26827.632, abs=1e-9)  # MSLUDGE2 锚
    assert stock.q_wet == pytest.approx(dims["q_sludge"] / 86400, abs=1e-15)  # KS-F7 直用
    assert stock.q_wet * 86400 == pytest.approx(304.8594545455, abs=1e-8)
    assert stock.moisture == pytest.approx(0.92, abs=1e-12)
    assert result.outqualities[ref].concentrations == {}  # 空 WaterQuality（GR-04）
