"""AAO 能耗计算段：_oxygen（自 compute 迁入）+ _energy（AO-F21~F25）。

输入:  UnitContext + 参数 + 需氧量/容积数组（compute 主链产物）
输出:  oxygen/energy 两段数组（compute 并组合成 dims）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（ADR-024 D1；compute.py 400 行墙拆件——需氧量函数随能耗链
#   同迁（O2→供气→风机功率主题连续性）；公式声明住 manifest+
#   formulas_energy，本件纯求值（R1 公式经注册表/R4 纯函数/R5 禁
#   import 其他单元与 L3——单元包内兄弟件不在此列）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.unit_api import UnitContext
from waterprint.units_lib._unit_compute import Array as _Array
from waterprint.units_lib._unit_compute import _apply_batch, _factor, _vec

_UNIT_ID = "municipal_aao"


def _oxygen(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, _Array], v_o: _Array
) -> dict[str, _Array]:
    """AO-F9~F12：碳化/硝化/反硝化需氧量与设计需氧量。"""
    vss_ratio = _factor(p, "factor.aao.vss_ratio", _UNIT_ID)
    x_vss = _vec(vss_ratio) * _vec(p["x_mlss"])
    o2_carbon = _apply_batch(
        ctx,
        "AO-F9",
        {
            "a_prime": _vec(_factor(p, "factor.aao.o2.a_prime", _UNIT_ID)),
            "q_avg_daily": _vec(flow.q_avg_daily),
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "b_prime": _vec(_factor(p, "factor.aao.o2.b_prime", _UNIT_ID)),
            "v_o": v_o,
            "x_vss": x_vss,
        },
    )
    tkn = {"q_avg_daily": _vec(flow.q_avg_daily), "tkn_in": qual["tn_in"],
           "tn_eff": _vec(p["tn_eff"])}
    o2_nit = _apply_batch(ctx, "AO-F10", tkn)
    o2_denit = _apply_batch(ctx, "AO-F11", tkn)
    return {
        "x_vss": x_vss,
        "o2_carbon": o2_carbon,
        "o2_nit": o2_nit,
        "o2_denit": o2_denit,
        "o2_total": _apply_batch(
            ctx, "AO-F12", {"o2_carbon": o2_carbon, "o2_nit": o2_nit, "o2_denit": o2_denit}
        ),
    }


def _energy(
    ctx: UnitContext, p: dict[str, float], oxygen: dict[str, _Array], volumes: dict[str, _Array]
) -> dict[str, _Array]:
    """AO-F21~F25：供气量→风机轴功率→日耗电+缺氧/厌氧搅拌（ADR-024）。"""
    q_air = _apply_batch(
        ctx,
        "AO-F21",
        {
            "o2_total": oxygen["o2_total"],
            "f_sor": _vec(_factor(p, "factor.aao.blower.sor_factor", _UNIT_ID)),
            "o2_per_air": _vec(_factor(p, "factor.aao.blower.o2_per_air", _UNIT_ID)),
            "ea": _vec(_factor(p, "factor.aao.blower.oxygen_transfer_eff", _UNIT_ID)),
        },
    )
    p_blower = _apply_batch(
        ctx,
        "AO-F22",
        {
            "q_air": q_air,
            "p_pressure": _vec(_factor(p, "factor.aao.blower.pressure_kpa", _UNIT_ID)),
            "eta_blower": _vec(_factor(p, "factor.aao.blower.efficiency", _UNIT_ID)),
        },
    )
    e_aeration = _apply_batch(ctx, "AO-F23", {"p_blower": p_blower})
    p_stir = _apply_batch(
        ctx,
        "AO-F24",
        {
            "v_anoxic": volumes["v_anoxic"],
            "v_anaerobic": volumes["v_anaerobic"],
            "w_stir_bio": _vec(_factor(p, "factor.aao.stir.power_density", _UNIT_ID)),
        },
    )
    e_stir = _apply_batch(ctx, "AO-F25", {"p_stir": p_stir})
    return {
        "q_air": q_air,
        "p_blower": p_blower,
        "e_aeration": e_aeration,
        "p_stir": p_stir,
        "e_stir": e_stir,
    }
