"""app_energy 镜像测试：能耗药耗全厂聚合投影（B4-2a，ADR-024）。

输入:  构造 PlantResult（逐工况单元快照 dims——e_*/m_* 键面）
输出:  energy_summary_of 行为断言（sparse 键族/同键多单元叠加/power_total
       合成律/空工况空映射/纯函数双跑恒等）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：ADR-024 D2/D3——键名约定聚合（e_aeration/e_pump/e_stir→power_*；
# m_pac/m_pam/w_pam/m_seed_net→dose_*；w_pam 并 PAM 族；m_seed 毛耗
# 不聚合）；sparse 有则录无则略；power_total=在场分项之和（无分项不立）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

from waterprint.app_energy import energy_summary_of
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    UnitResultSnapshot,
)


def _snapshot(dims: dict[str, float]) -> UnitResultSnapshot:
    """最小单元快照（能耗聚合只消费 dims——其余面空构造）。"""
    return UnitResultSnapshot(
        unit_id="u", outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _plant(conditions: dict[str, dict[str, dict[str, float]]]) -> PlantResult:
    return PlantResult(
        conditions={
            ck: {uid: _snapshot(dims) for uid, dims in units.items()}
            for ck, units in conditions.items()
        },
        summary={}, trace=(),
        repro=ReproTriple(design_hash="", engine_version="", data_version=""),
    )


def test_sparse_projection_and_power_total() -> None:
    """R1/R3：键有则录无则略；power_total=在场分项之和（无分项不立）。"""
    plant = _plant({
        "design": {
            "aao": {"e_aeration": 100.0, "e_stir": 40.0},
            "pump": {"e_pump": 60.0, "m_pac": 12.5},
        },
        "sludge_line": {"ganhua": {"ds_out": 3.0}},  # 无能耗键——空映射
    })
    view = energy_summary_of(plant)
    assert view["design"] == {
        "power_aeration_kwh_d": 100.0,
        "power_pump_kwh_d": 60.0,
        "power_stir_kwh_d": 40.0,
        "power_total_kwh_d": 200.0,
        "dose_pac_kg_d": 12.5,
    }
    assert view["sludge_line"] == {}  # sparse：无分项无合计


def test_multi_unit_same_key_accumulates() -> None:
    """R3：同键多单元叠加（gaomidu+ningjiao 双 m_pac 场景）。"""
    plant = _plant({
        "design": {
            "gaomidu": {"m_pac": 10.0, "m_pam": 1.0},
            "ningjiao": {"m_pac": 15.5, "m_seed": 99.0},  # m_seed 毛耗不聚合
            "tuoshui": {"w_pam": 2.0},  # w_pam 并入 PAM 族
            "cifenli": {"m_seed_net": 5.0},  # 磁种净耗
        },
    })
    assert energy_summary_of(plant)["design"] == {
        "dose_pac_kg_d": 25.5,
        "dose_pam_kg_d": 3.0,
        "dose_seed_kg_d": 5.0,
    }


def test_pure_function_double_run_identical() -> None:
    """R2：纯投影同输入同输出（双跑恒等）。"""
    plant = _plant({"avg": {"a": {"e_stir": 7.25}}})
    first: Any = energy_summary_of(plant)
    second = energy_summary_of(plant)
    assert first == second
    assert first["avg"]["power_stir_kwh_d"] == 7.25
