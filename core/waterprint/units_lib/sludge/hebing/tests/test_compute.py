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
# 【用例面】（十四条，与实际测试函数一一对应——M3a3 yI-1 教训在册）
#   ①清单身份（UNIT_ID/业务线/三 IN 口+单 OUT 口 SLUDGE/removal_refs
#   空——零 removal 键声明面；GOLDEN4a D1 端口翻转）②主算例三股+汇流
#   逐项（HB-F1~F7）③主算例产量衡算逐项（HB-F8~F13）④主算例互校合格
#   零警告 ⑤副算例逐项（HB-F1~F11 对照）⑥副算例互校偏差越上限恰一
#   WARN（severity+param_key=yield_syn 归因）⑦出流 SLUDGE 三量（契约
#   口径换算：q_total/86400、ds_total/86400、moisture 直通）⑧参数域
#   拒绝（ds 非正/含水率闭边界/BOD 倒挂三例）⑨纯函数双跑一致
#   ⑩formula_ids 恰 13 号（HB-F1~F13）且全部可在公式注册表解析
#   ⑪工况键形态冒烟（condition_key 口径）⑫入流模式等价迁移（主算例
#   ——GOLDEN4a D2 双模：三口入流值=注入值→两模式 dims 全等）⑬入流
#   模式等价迁移（矿井三股——手算表 MS-F1~F3 口径直对 MSLUDGE2 锚）
#   ⑭部分边显式拒三例（三股口须全连或全不连——GR-14 族）。
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
from waterprint.contracts.unit_api import Severity, UnitContext, UnitResult
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


def _compute(**overrides: float) -> UnitResult:
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
    """①清单身份：UNIT_ID/业务线/三 IN 口+单 OUT 口 SLUDGE/removal_refs 空（零 removal 键）。"""
    assert manifest.unit_id == "sludge_hebing"
    assert manifest.business_line == "sludge"
    assert [(p.port_id, p.fluid.name, p.direction.name) for p in manifest.ports] == [
        ("in_primary", "SLUDGE", "IN"),
        ("in_bio", "SLUDGE", "IN"),
        ("in_chem", "SLUDGE", "IN"),
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
    assert set(result.outqualities) == {_OUT_REF}  # 空水质单位元面（executor 入流装配前提）
    assert result.outqualities[_OUT_REF].concentrations == {}  # SLUDGE 通道无水质面


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
    assert isinstance(out_first, SludgeFlow) and isinstance(out_second, SludgeFlow)
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


# ── GOLDEN4a D2 双模（2026-08-28）：三 IN 口（in_primary/in_bio/in_chem）
#    入流直值模式——入流值=案例注入值时两模式 dims 全等（等价迁移断言，
#    GOLDEN4b 真边接通的锚保真前提）。注：入流 q_wet 以 HB-F1~F3 派生值
#    ÷86400 构造（回契约口径），×86400 回显已实证位级精确（六值全验）──
_IN_PRIMARY = PortRef(unit_id="test_sludge_hebing", port_id="in_primary")
_IN_BIO = PortRef(unit_id="test_sludge_hebing", port_id="in_bio")
_IN_CHEM = PortRef(unit_id="test_sludge_hebing", port_id="in_chem")


def _ctx_inflows(
    inflows: dict[PortRef, SludgeFlow], **overrides: float
) -> UnitContext:
    """入流模式 ctx（参数面可携冲突值——入流直值优先，双源冲突面实证）。"""
    return UnitContext(
        unit_id="test_sludge_hebing",
        inflows=inflows,
        inqualities={},
        params=_params(**overrides),
        condition=_CONDITION,
        assumptions={},
        trace=_Sink(),
    )


def test_inflow_mode_equivalence_main() -> None:
    """⑫入流模式等价迁移（主算例）：三口入流值=注入值→两模式 dims 全等。"""
    params_result = _compute()
    stocks = params_result.dims  # HB-F1~F3 派生值（q 三股）=入流 q_wet 工程口径
    inflows = {
        _IN_PRIMARY: SludgeFlow(
            q_wet=stocks["q_primary"] / 86400, ds=3240.12 / 86400, moisture=0.96
        ),
        _IN_BIO: SludgeFlow(
            q_wet=stocks["q_bio"] / 86400, ds=1928.690 / 86400, moisture=0.994
        ),
        _IN_CHEM: SludgeFlow(
            q_wet=stocks["q_chem"] / 86400, ds=137.7050 / 86400, moisture=0.98
        ),
    }
    # 参数面携冲突 ds/p 六键（≠入流值）——入流直值优先（D2 避免双源冲突）
    flow_result = make_unit().compute(
        _ctx_inflows(
            inflows,
            ds_primary=1.0,
            p_primary=0.5,
            ds_bio=2.0,
            p_bio=0.5,
            ds_chem=3.0,
            p_chem=0.5,
        )
    )
    assert flow_result.dims == params_result.dims  # 13 键全等（等价迁移）
    assert flow_result.warnings == params_result.warnings
    assert flow_result.outflows == params_result.outflows  # 出流三量同步全等
    # 审计口径：HB-F1~F3 入流模式不重算（入流即真值）——formula_ids 收窄
    assert flow_result.formula_ids == tuple(
        f"HB-F{index}" for index in range(4, 14)
    )


def test_inflow_mode_equivalence_mine() -> None:
    """⑬入流模式等价迁移（矿井三股）：MS-F1~F3 注入值直对 MSLUDGE2 锚。"""
    mine_overrides = {
        "ds_primary": 26827.632,
        "p_primary": 0.92,
        "ds_bio": 3787.4304,
        "p_bio": 0.10,
        "ds_chem": 2682.7632,
        "p_chem": 0.97,
    }
    params_result = _compute(**mine_overrides)
    stocks = params_result.dims
    assert stocks["q_total"] == pytest.approx(428.979096, abs=1e-9)  # MSLUDGE2 锚
    assert stocks["ds_total"] == pytest.approx(33297.8256, abs=1e-9)
    assert stocks["p_merged"] == pytest.approx(0.9223789086, abs=1e-9)
    inflows = {
        _IN_PRIMARY: SludgeFlow(
            q_wet=stocks["q_primary"] / 86400, ds=26827.632 / 86400, moisture=0.92
        ),
        _IN_BIO: SludgeFlow(
            q_wet=stocks["q_bio"] / 86400, ds=3787.4304 / 86400, moisture=0.10
        ),
        _IN_CHEM: SludgeFlow(
            q_wet=stocks["q_chem"] / 86400, ds=2682.7632 / 86400, moisture=0.97
        ),
    }
    # ctx 参数面=市政默认（≠矿井注入值）——入流直值优先后 dims 仍全等
    flow_result = make_unit().compute(_ctx_inflows(inflows))
    assert flow_result.dims == params_result.dims  # 等价迁移（矿井锚保真前提）


def test_partial_inflow_rejected() -> None:
    """⑭部分边显式拒三例（三股口须全连或全不连——GR-14 族部分注入态非法）。"""
    one = {
        _IN_PRIMARY: SludgeFlow(
            q_wet=81.003 / 86400, ds=3240.12 / 86400, moisture=0.96
        )
    }
    with pytest.raises(InvalidUnitConfig, match="全连或全不连"):
        make_unit().compute(_ctx_inflows(one))
    only_bio = {
        _IN_BIO: SludgeFlow(
            q_wet=321.4483333333 / 86400, ds=1928.690 / 86400, moisture=0.994
        )
    }
    with pytest.raises(InvalidUnitConfig, match="全连或全不连"):
        make_unit().compute(_ctx_inflows(only_bio))
    two = {
        **one,
        _IN_CHEM: SludgeFlow(
            q_wet=6.88525 / 86400, ds=137.7050 / 86400, moisture=0.98
        ),
    }
    with pytest.raises(InvalidUnitConfig, match="全连或全不连"):
        make_unit().compute(_ctx_inflows(two))
