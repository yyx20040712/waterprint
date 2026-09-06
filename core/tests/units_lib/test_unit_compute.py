"""共享件异常分支最小直测：_unit_compute 四 helper+_ceil_step 三组消息恒等。

输入:  waterprint.units_lib._unit_compute 公开符号（B15 挂账直兑——B8
       「异常分支知情接受」口径解除）
输出:  InvalidUnitConfig 异常分支断言+R-1 运行时消息逐字恒等断言
"""

from __future__ import annotations

import pytest

from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.units_lib._unit_compute import (
    _ceil_step_core,
    _factor,
    _make_ceil_step,
)

# ── _factor：缺键拒（消息含键名——GR-09）──────────────────────────


def test_factor_missing_key_raises() -> None:
    """缺系数键=InvalidUnitConfig（消息含键名+单元语境）。"""
    with pytest.raises(InvalidUnitConfig) as exc:
        _factor({"a": 1.0}, "factor.x.key", "municipal_demo")
    assert "factor.x.key" in str(exc.value)
    assert "municipal_demo" in str(exc.value)


def test_factor_present_key_returns_float() -> None:
    """在册键正常取值（异常分支的对偶面）。"""
    assert _factor({"k": 2}, "k", "u") == 2.0


# ── _inflow/_inflow_sludge：多入/缺入/异流体拒 ────────────────────

def _ctx_with(inflows: dict[object, object]) -> object:
    """最小 UnitContext 替身（入流装配断言面——只消费 inflows/unit_id）。"""
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.quality import WaterQuality
    from waterprint.contracts.unit_api import UnitContext

    return UnitContext(
        unit_id="municipal_demo",
        inflows=inflows,  # type: ignore[arg-type]
        inqualities={
            ref: WaterQuality({}) for ref in inflows
        },  # type: ignore[misc]
        params={},
        condition=build_condition_set([]).iter_all().__next__(),
        assumptions={},
        trace=None,  # type: ignore[arg-type]
    )


def _water(q: float) -> object:
    from waterprint.contracts.flow import WaterFlow

    return WaterFlow(q_avg_daily=q, kz=1.0)


def _sludge(q: float) -> object:
    from waterprint.contracts.sludge import SludgeFlow

    return SludgeFlow(q_wet=q, ds=q * 0.5, moisture=0.9)


def test_inflow_rejects_sludge_inflow() -> None:
    """_inflow 泥线入流拒（异流体分支——KC 族守卫）。"""
    from waterprint.contracts.ports import PortRef
    from waterprint.units_lib._unit_compute import _inflow

    ctx = _ctx_with({PortRef("municipal_demo", "in"): _sludge(1.0)})
    with pytest.raises(InvalidUnitConfig) as exc:
        _inflow(ctx, "演示边注")  # type: ignore[arg-type]
    assert "恰一条 WATER 入边" in str(exc.value)


def test_inflow_rejects_multi_and_missing() -> None:
    """_inflow 多入/缺入拒（条数分支）。"""
    from waterprint.contracts.ports import PortRef
    from waterprint.units_lib._unit_compute import _inflow

    multi = _ctx_with({
        PortRef("a", "out"): _water(1.0),
        PortRef("b", "out"): _water(1.0),
    })
    with pytest.raises(InvalidUnitConfig):
        _inflow(multi, "演示边注")  # type: ignore[arg-type]
    empty = _ctx_with({})
    with pytest.raises(InvalidUnitConfig):
        _inflow(empty, "演示边注")  # type: ignore[arg-type]


def test_inflow_sludge_rejects_water_inflow() -> None:
    """_inflow_sludge 水线入流拒（异流体分支——泥线族守卫）。"""
    from waterprint.contracts.ports import PortRef
    from waterprint.units_lib._unit_compute import _inflow_sludge

    ctx = _ctx_with({PortRef("municipal_demo", "in"): _water(1.0)})
    with pytest.raises(InvalidUnitConfig) as exc:
        _inflow_sludge(ctx, "演示边注")  # type: ignore[arg-type]
    assert "恰一条 SLUDGE 入边" in str(exc.value)


def test_inflow_sludge_rejects_empty() -> None:
    """_inflow_sludge 缺入拒。"""
    from waterprint.units_lib._unit_compute import _inflow_sludge

    with pytest.raises(InvalidUnitConfig):
        _inflow_sludge(_ctx_with({}), "演示边注")  # type: ignore[arg-type]


# ── _ceil_step：三组 R-1 消息逐字恒等（B15 收敛承载面）─────────────


def test_ceil_step_core_group1_message_verbatim() -> None:
    """组1 消息族「取整步长」逐字恒等（18 包绑定形态的共享源）。"""
    step_fn = _make_ceil_step("municipal_cass", "取整步长", spaced=False)
    with pytest.raises(InvalidUnitConfig) as exc:
        step_fn(1.0, 0.0)
    assert str(exc.value) == (
        f"单元 {'municipal_cass'!r} 的取整步长必须 > 0：得到 0.0"
    )
    assert step_fn(0.95, 0.1) == pytest.approx(1.0)


def test_ceil_step_core_group2_message_verbatim() -> None:
    """组2 消息族「length_disc_step」逐字恒等（municipal/chenshachi）。"""
    step_fn = _make_ceil_step("municipal_chenshachi", "length_disc_step", spaced=True)
    with pytest.raises(InvalidUnitConfig) as exc:
        step_fn(1.0, -0.1)
    assert str(exc.value) == (
        f"单元 {'municipal_chenshachi'!r} 的 length_disc_step 必须 > 0：得到 -0.1"
    )


def test_ceil_step_core_group3_message_verbatim() -> None:
    """组3 参数面（cugeshan/xigeshan wrapper——unit_id 调用时传）。"""
    with pytest.raises(InvalidUnitConfig) as exc:
        _ceil_step_core(1.0, 0.0, "municipal_cugeshan", "length_disc_step",
                        spaced=True)
    assert str(exc.value) == (
        f"单元 {'municipal_cugeshan'!r} 的 length_disc_step 必须 > 0：得到 0.0"
    )
    assert _ceil_step_core(0.95, 0.1, "municipal_cugeshan", "length_disc_step",
                           spaced=True) == pytest.approx(1.0)


def test_package_binding_messages_match_original() -> None:
    """包级绑定抽查：绑定产物消息与原 def 逐字同（迁移面恒等抽验）。"""
    from waterprint.units_lib.municipal.chenshachi.compute import _ceil_step as cs
    from waterprint.units_lib.municipal.cugeshan.compute import _ceil_step as cg
    from waterprint.units_lib.sludge.bengzhan.compute import _ceil_step as bz

    with pytest.raises(InvalidUnitConfig) as exc_bz:
        bz(1.0, 0.0)
    assert str(exc_bz.value) == (
        f"单元 {'sludge_bengzhan'!r} 的取整步长必须 > 0：得到 0.0"
    )
    with pytest.raises(InvalidUnitConfig) as exc_cs:
        cs(1.0, 0.0)
    assert str(exc_cs.value) == (
        f"单元 {'municipal_chenshachi'!r} 的 length_disc_step 必须 > 0：得到 0.0"
    )
    with pytest.raises(InvalidUnitConfig) as exc_cg:
        cg(1.0, 0.0, "municipal_cugeshan")
    assert str(exc_cg.value) == (
        f"单元 {'municipal_cugeshan'!r} 的 length_disc_step 必须 > 0：得到 0.0"
    )
