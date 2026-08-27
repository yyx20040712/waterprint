"""sludge_hebing golden 数值测试（期望值来源：docs/norms/sludge_hebing.md 起草表）。

输入:  本包 manifest 与 compute（make_unit）；期望值=表主/副算例逐字（2026-08-27 起草，待追认）
输出:  测试结果（红-绿纪律：先失败一次再通过）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装；数据纪律 §16 A9：期望值禁自编，全部逐字取自
#   docs/norms/sludge_hebing.md 主算例（HB-F1~F13 十三项：q_primary=
#   81.003/q_bio=321.4483333333/q_chem=6.88525/ds_total=5306.515/
#   q_total=409.3365833333/w_water=404030.0683333333/p_merged=
#   0.9870363041/s_y=1928.691182574/k_dt=0.0328770843/dx_bio=
#   2029.0769498099/dev_pct=5.2048647364/ds_check=5306.516182574/
#   dev_close=0.0000222853）与副算例（含水率带内另档+互校中值组合：
#   q_total=312.7739/w_water=307467.385/p_merged=0.9830340223/k_dt=
#   0.05/dx_bio=707.1869190888/dev_pct=63.3333254448——>20% 警告路径）；
#   系数键值逐字取自 data/coefficients 0.6.0 factors.yaml（hebing
#   12 键）——测试区字面量合法。
#   浮点末位注记（照 KT-F10 π 注记先例，M3b1 二审 M1 回填表内）：
#   w_water 主算例表载 …0683333333 系手写循环 3 扩位——DSL 求值序
#   （干基三项各自除后累加）精确值 404030.068333333，差 <1e-8；
#   副算例 307467.385 按本 DSL 求值序恰精确（先算含水率比再乘的
#   别序则得 …49997）——断言容差 abs=1e-6 覆盖，数值零变更。
#
# 【用例面】（十一条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/单口 SLUDGE 出流/removal_refs 空——零
#   removal 键声明面）②主算例三股+汇流逐项（HB-F1~F7）③主算例产量
#   衡算逐项（HB-F8~F13）④主算例互校合格零警告 ⑤副算例逐项（HB-F1~
#   F11 对照）⑥副算例互校偏差越上限恰一 WARN（severity+param_key=
#   yield_syn 归因）⑦出流 SLUDGE 三量（契约口径换算：q_total/86400、
#   ds_total/86400、moisture 直通）⑧参数域拒绝（ds 非正/含水率闭边界/
#   BOD 倒挂三例）⑨纯函数双跑一致 ⑩formula_ids 恰 13 号（HB-F1~F13）
#   且全部可在公式注册表解析 ⑪工况键形态冒烟（condition_key 口径）。
#
# 【锁定流程】本文件写完并由人类复核后执行
#   `python scripts/lock_tests.py core/waterprint/units_lib/sludge/hebing/tests`
#   转为只读（AGENTS.md §11）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

import pytest

from waterprint.contracts.condition import ConditionSet, FlowCase, OperatingCondition
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Severity, UnitContext
from waterprint.registry import formulas
from waterprint.units_lib.sludge.hebing import make_unit, manifest

# ── 主算例入参（表逐字：三股=市政 34760 案例市政表实值 ds 3240.12/
#    1928.690/137.7050 kg/d、含水率 0.96/0.994/0.98；衡算面
#    q_avg_daily=34760.7、s0/se=123.2996/12.32996（aao 衔接式）、
#    v_bio=10714.95、x_vss=3000、t_design=15 ℃）——图源单元无入流 ──
_OUT_REF = PortRef(unit_id="test_sludge_hebing", port_id="out")
_CONDITION = OperatingCondition(flow_case=FlowCase.DESIGN)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议，记录条数供断言）。"""

    def __init__(self) -> None:
        self.count = 0

    def record(self, node: Any) -> None:
        self.count += 1


def _params(**overrides: float) -> dict[str, float]:
    """主算例参数面（manifest 默认即算例值；系数投影逐字 0.6.0）。"""
    params: dict[str, float] = {
        # manifest 默认=表主算例逐字（12 参数）
        "ds_primary": 3240.12,
        "p_primary": 0.96,
        "ds_bio": 1928.690,
        "p_bio": 0.994,
        "ds_chem": 137.7050,
        "p_chem": 0.98,
        "q_avg_daily": 34760.7,
        "s0_bod": 123.2996,
        "se_bod": 12.32996,
        "v_bio": 10714.95,
        "x_vss": 3000.0,
        "t_design": 15.0,
        # data/coefficients factors.yaml（0.6.0）hebing 12 键逐字
        "factor.hebing.yield.y": 0.5,
        "factor.hebing.yield.y_band.min": 0.4,
        "factor.hebing.yield.y_band.max": 0.6,
        "factor.hebing.yield_syn": 0.8,
        "factor.hebing.yield_syn_band.min": 0.4,
        "factor.hebing.yield_syn_band.max": 0.8,
        "factor.hebing.k_decay20": 0.04,
        "factor.hebing.k_decay_band.min": 0.04,
        "factor.hebing.k_decay_band.max": 0.075,
        "factor.hebing.theta_kd": 1.04,
        "factor.hebing.dev_band.max": 20.0,
        "factor.hebing.elevation_loss": 0.15,
    }
    params.update(overrides)
    return params


def _ctx(params: dict[str, float]) -> UnitContext:
    return UnitContext(
        unit_id="test_sludge_hebing",
        inflows={},
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


def _secondary_overrides() -> dict[str, float]:
    """副算例覆盖面（表副算例：p 三档另取+互校中值组合）。"""
    return {
        "p_primary": 0.95,
        "p_bio": 0.992,
        "p_chem": 0.98,
        "factor.hebing.yield_syn": 0.6,
        "factor.hebing.k_decay20": 0.05,
        "t_design": 20.0,
    }


def test_manifest_identity() -> None:
    """①清单身份：UNIT_ID/业务线/单口 SLUDGE 出流/removal_refs 空（零 removal 键）。"""
    assert manifest.unit_id == "sludge_hebing"
    assert manifest.business_line == "sludge"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("out", "SLUDGE", "OUT"),
    ]
    assert manifest.removal_refs == {}


def test_main_case_stocks() -> None:
    """②主算例三股湿泥量+汇流四量逐项断言（HB-F1~F7——mix P4 镜像）。"""
    dims = _dims()
    assert dims["q_primary"] == pytest.approx(81.003, abs=1e-9)  # HB-F1
    assert dims["q_bio"] == pytest.approx(321.4483333333, abs=1e-9)  # HB-F2
    assert dims["q_chem"] == pytest.approx(6.88525, abs=1e-9)  # HB-F3
    assert dims["ds_total"] == pytest.approx(5306.515, abs=1e-9)  # HB-F4：DS 守恒
    assert dims["q_total"] == pytest.approx(409.3365833333, abs=1e-9)  # HB-F5
    # HB-F6：表载末位手写循环 3 扩位（浮点末位注记）——容差 1e-6
    assert dims["w_water"] == pytest.approx(404030.0683333333, abs=1e-6)
    assert dims["p_merged"] == pytest.approx(0.9870363041, abs=1e-9)  # HB-F7 干基反解


def test_main_case_yield() -> None:
    """③主算例产量衡算逐项断言（HB-F8~F13——ADR-008 ④ 主线+互校+闭合）。"""
    dims = _dims()
    assert dims["s_y"] == pytest.approx(1928.691182574, abs=1e-9)  # HB-F8 经验产率
    assert dims["k_dt"] == pytest.approx(0.0328770843, abs=1e-9)  # HB-F9 Kd 修正
    assert dims["dx_bio"] == pytest.approx(2029.0769498099, abs=1e-9)  # HB-F10 机理
    assert dims["dev_pct"] == pytest.approx(5.2048647364, abs=1e-9)  # HB-F11 ≤20 合格
    assert dims["ds_check"] == pytest.approx(5306.516182574, abs=1e-9)  # HB-F12
    assert dims["dev_close"] == pytest.approx(0.0000222853, abs=1e-10)  # HB-F13 ≈0


def test_main_case_no_warning() -> None:
    """④主算例互校偏差 5.20% ≤ 上限 20%——warnings 全空。"""
    result = _compute()
    assert result.warnings == ()


def test_secondary_case() -> None:
    """⑤副算例（互校中值组合）逐项断言（表副算例 HB-F1~F11 对照）。"""
    dims = _dims(**_secondary_overrides())
    assert dims["q_primary"] == pytest.approx(64.8024, abs=1e-9)
    assert dims["q_bio"] == pytest.approx(241.08625, abs=1e-9)
    assert dims["q_chem"] == pytest.approx(6.88525, abs=1e-9)
    assert dims["q_total"] == pytest.approx(312.7739, abs=1e-9)
    assert dims["w_water"] == pytest.approx(307467.385, abs=1e-9)
    assert dims["p_merged"] == pytest.approx(0.9830340223, abs=1e-9)
    assert dims["k_dt"] == pytest.approx(0.05, abs=1e-12)  # 20 ℃ 无修正
    assert dims["dx_bio"] == pytest.approx(707.1869190888, abs=1e-9)
    assert dims["dev_pct"] == pytest.approx(63.3333254448, abs=1e-9)  # >20 警告路径


def test_secondary_dev_warning() -> None:
    """⑥副算例互校偏差 63.33% > 上限 20%——恰一 WARN+severity+param_key 归因。"""
    result = _compute(**_secondary_overrides())
    dev = [w for w in result.warnings if "dev_band.max" in w.source]
    assert len(result.warnings) == 1 and dev
    assert dev[0].severity is Severity.WARN
    assert dev[0].param_key == "yield_syn"


def test_outflow_sludge_triple() -> None:
    """⑦出流 SLUDGE 三量：q_total/ds_total 换算契约口径 + moisture 直通。"""
    result = _compute()
    out = result.outflows[_OUT_REF]
    assert isinstance(out, SludgeFlow)
    assert out.q_wet == pytest.approx(409.3365833333 / 86400, abs=1e-15)
    assert out.ds == pytest.approx(5306.515 / 86400, abs=1e-15)
    assert out.moisture == pytest.approx(0.9870363041, abs=1e-9)
    assert result.outqualities == {}  # SLUDGE 通道无水质面


def test_param_domain_rejected() -> None:
    """⑧参数域拒绝：ds_bio 非正 / p_bio 闭边界 1 / BOD 倒挂 → InvalidUnitConfig。"""
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(ds_bio=0.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(p_bio=1.0)))
    with pytest.raises(InvalidUnitConfig):
        make_unit().compute(_ctx(_params(se_bod=123.2996)))


def test_pure_function_double_run() -> None:
    """⑨纯函数断言：同 ctx 双跑 dims/warnings/outflows 三量逐项相同。"""
    unit = make_unit()
    first = unit.compute(_ctx(_params()))
    second = unit.compute(_ctx(_params()))
    assert first.dims == second.dims
    assert first.warnings == second.warnings
    out_first = first.outflows[_OUT_REF]
    out_second = second.outflows[_OUT_REF]
    assert (out_first.q_wet, out_first.ds, out_first.moisture) == (
        out_second.q_wet,
        out_second.ds,
        out_second.moisture,
    )


def test_formula_ids_registered() -> None:
    """⑩formula_ids 恰 13 号（HB-F1~F13）且全部可在公式注册表解析（A1 防线）。"""
    result = make_unit().compute(_ctx(_params()))
    assert result.formula_ids == tuple(f"HB-F{index}" for index in range(1, 14))
    for formula_id in result.formula_ids:
        assert formulas.by_id(formula_id).formula_id == formula_id


def test_condition_key_form() -> None:
    """⑪工况键形态冒烟（apply 第二参 ctx 的 condition_key 口径）。"""
    assert ConditionSet.key(_CONDITION) == "design"
