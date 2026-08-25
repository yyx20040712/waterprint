"""CASS 生物池计算实现：唯一计算源（CA-F1~F27 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【公式组】CA-F1~F27（docs/norms/cass.md 起草表；manifest.py 登记）——
#   周期循环主线：周期数/滗水容积（F1~F2）、负荷法主容积+选择区+滗水
#   1/3 池深双控池面积（F3~F12）、时段和=周期不变性（F13，域拒非警告）、
#   滗水器选型（F14~F15，整台 ceil）、剩余污泥/泥龄（F16~F18，AAO 同族
#   口径）、需氧量（F19~F22）、实际负荷校核（F23）、几何与概算（F24~F27）。
# 【DSL 收口】ceil 在本文件收口：滗水器台数整台；池长/池宽 0.5 m 档。
#   零数值字面量。流量口径（三表逐字冻结）：生物反应/剩余污泥/需氧量按
#   平均日 flow.q_avg_daily（AAO 同族）；滗水水力按池均摊。
# 【池数守卫（Ruling ④）】compute 只保 n_pool>0 数学有效性（≤0 拒）；
#   池数 ≥2 档位下限经 manifest ParamSpec.grid=[2,3,4,5,6] 声明承载。
# 【系数通道】factor.cass.*/removal.cass.* 经 ctx.params 投影面取值
#   （app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D2）】outflows=入流透传；dims=三表水力结果全量 snake 键；
#   outqualities=入质×(1−removal) 三指标+NH3N/TN/TP 透传（AAO 同族
#   形态）；warnings=六条校核带越界（ns/mlss/t_selector 参数带+theta_c/
#   h_draw/ns_act 结果带）；formula_ids=实际求值公式号全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import final

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)
from waterprint.registry import formulas
from waterprint.units_lib.municipal.cass.manifest import FORMULA_IDS, manifest

_UNIT_ID = "municipal_cass"
_GB = "GB 50014-2021 §7.6"
_HB = "给水排水设计手册（第 5 册 城镇排水）"
_PARAMS_POSITIVE = (
    "n_pool",
    "t_cycle",
    "t_react",
    "t_settle",
    "t_draw",
    "ns",
    "x_mlss",
    "t_selector",
    "h2",
    "ratio_lb",
    "tn_eff",
    "side_disc_step",
)
# 参数带检查表：(参数键, 带键短名, 量名)——限值经 factor.cass.* 双键。
_PARAM_BANDS: tuple[tuple[str, str, str], ...] = (
    ("ns", "ns_band", "BOD5 污泥负荷 Ns kgBOD5/(kgMLSS·d)"),
    ("x_mlss", "mlss_band", "设计 MLSS mg/L（SBR 变体档）"),
    ("t_selector", "selector_band", "生物选择区 HRT h"),
)


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


def _ceil_step(value: float, step: float) -> float:
    """构造步长向上取整（池长/池宽 0.5 m 档；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/周期/时段/负荷/浓度/水深等非正一律拒 + 时段和=周期。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")
    phase_sum = params["t_react"] + params["t_settle"] + params["t_draw"]
    if phase_sum != params["t_cycle"]:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 时段和=周期不变性破坏：t_react+t_settle+t_draw ="
            f" {phase_sum!r} ≠ t_cycle = {params['t_cycle']!r}"
            "（business-logic §8/CA-F13——时段分配须与周期档一致）"
        )
    moisture = _factor(params, "factor.cass.sludge.moisture")
    if not 0 < moisture < 1:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 剩余污泥含水率须 ∈ (0,1)：得到 {moisture!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（生物池单入单出语义）"
        )
    flow = ctx.inflows[refs[0]]
    assert isinstance(flow, WaterFlow)  # 上行守卫已收窄，窄化供类型面
    return refs[0], flow


def _apply(ctx: UnitContext, formula_id: str, bindings: dict[str, float]) -> float:
    """apply 薄封装：统一携带 (unit_id, condition_key) 与 trace sink。"""
    return formulas.apply(
        formula_id,
        bindings,
        (ctx.unit_id, ConditionSet.key(ctx.condition)),
        sink=ctx.trace,
    )


def _cycles(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """CA-F1/F2：周期数与单池单周期滗水容积（池均摊口径）。"""
    n_cycle = _apply(ctx, "CA-F1", {"t_cycle": p["t_cycle"]})
    return {
        "n_cycle": n_cycle,
        "v_draw": _apply(
            ctx,
            "CA-F2",
            {"q_avg_daily": flow.q_avg_daily, "n_pool": p["n_pool"], "n_cycle": n_cycle},
        ),
    }


def _areas(ctx: UnitContext, p: dict[str, float], v_bio: float, v_draw: float) -> dict[str, float]:
    """CA-F6~F12：滗水/负荷双控单池面积、滗水深度与池容（滗水 1/3 池深联动）。"""
    h_draw_max = _apply(ctx, "CA-F6", {"h2": p["h2"]})
    a_draw = _apply(ctx, "CA-F7", {"v_draw": v_draw, "h_draw_max": h_draw_max})
    a_load = _apply(ctx, "CA-F8", {"v_bio": v_bio, "n_pool": p["n_pool"], "h2": p["h2"]})
    a_pool = _apply(ctx, "CA-F9", {"a_load": a_load, "a_draw": a_draw})
    v_pool = _apply(ctx, "CA-F11", {"a_pool": a_pool, "h2": p["h2"]})
    return {
        "h_draw_max": h_draw_max,
        "a_draw": a_draw,
        "a_load": a_load,
        "a_pool": a_pool,
        "h_draw": _apply(ctx, "CA-F10", {"v_draw": v_draw, "a_pool": a_pool}),
        "v_pool": v_pool,
        "v_plant": _apply(ctx, "CA-F12", {"v_pool": v_pool, "n_pool": p["n_pool"]}),
    }


def _decant(ctx: UnitContext, p: dict[str, float], v_draw: float) -> dict[str, float]:
    """CA-F13~F15：时段和（不变性载体）+ 滗水器选型（整台 ceil 收口）。"""
    q_decant = _apply(ctx, "CA-F14", {"v_draw": v_draw, "t_draw": p["t_draw"]})
    n_decant_raw = _apply(
        ctx,
        "CA-F15",
        {"q_decant": q_decant, "q_per_decant": _factor(p, "factor.cass.decant.q_per_unit")},
    )
    phases = {"t_react": p["t_react"], "t_settle": p["t_settle"], "t_draw": p["t_draw"]}
    return {
        "t_phase_sum": _apply(ctx, "CA-F13", phases),
        "q_decant": q_decant,
        "n_decant_raw": n_decant_raw,
        "n_decant": float(math.ceil(n_decant_raw)),
    }


def _sludge(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, float], v_load: float
) -> dict[str, float]:
    """CA-F16~F18：剩余污泥量（干/湿）与泥龄校核（AAO 同族口径）。"""
    s_y = _apply(
        ctx,
        "CA-F16",
        {
            "q_avg_daily": flow.q_avg_daily,
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "y_yield": _factor(p, "factor.cass.yield.y"),
        },
    )
    return {
        "s_y": s_y,
        "q_wet": _apply(
            ctx, "CA-F17", {"s_y": s_y, "p_moisture": _factor(p, "factor.cass.sludge.moisture")}
        ),
        "theta_c": _apply(ctx, "CA-F18", {"v_load": v_load, "x_mlss": p["x_mlss"], "s_y": s_y}),
    }


def _oxygen(
    ctx: UnitContext,
    p: dict[str, float],
    flow: WaterFlow,
    qual: dict[str, float],
    v_load: float,
) -> dict[str, float]:
    """CA-F19~F22：碳化/硝化/反硝化需氧量与设计需氧量（AAO 同族）。"""
    x_vss = _factor(p, "factor.cass.vss_ratio") * p["x_mlss"]
    o2_carbon = _apply(
        ctx,
        "CA-F19",
        {
            "a_prime": _factor(p, "factor.cass.o2.a_prime"),
            "q_avg_daily": flow.q_avg_daily,
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "b_prime": _factor(p, "factor.cass.o2.b_prime"),
            "v_load": v_load,
            "x_vss": x_vss,
        },
    )
    tkn = {"q_avg_daily": flow.q_avg_daily, "tkn_in": qual["tn_in"], "tn_eff": p["tn_eff"]}
    o2_nit = _apply(ctx, "CA-F20", tkn)
    o2_denit = _apply(ctx, "CA-F21", tkn)
    return {
        "x_vss": x_vss,
        "o2_carbon": o2_carbon,
        "o2_nit": o2_nit,
        "o2_denit": o2_denit,
        "o2_total": _apply(
            ctx, "CA-F22", {"o2_carbon": o2_carbon, "o2_nit": o2_nit, "o2_denit": o2_denit}
        ),
    }


def _geometry(ctx: UnitContext, p: dict[str, float], areas: dict[str, float]) -> dict[str, float]:
    """CA-F24~F27：池体几何（0.5 m 档 ceil 收口）与概算混凝土量。"""
    h_super = _factor(p, "factor.cass.superheight")
    h_pool = _apply(ctx, "CA-F24", {"h_super": h_super, "h2": p["h2"]})
    binds = {"a_pool": areas["a_pool"], "ratio_lb": p["ratio_lb"]}
    l_raw = _apply(ctx, "CA-F25", binds)
    b_raw = _apply(ctx, "CA-F26", binds)
    return {
        "h_pool": h_pool,
        "l_pool_raw": l_raw,
        "l_pool": _ceil_step(l_raw, p["side_disc_step"]),
        "b_pool_raw": b_raw,
        "b_pool": _ceil_step(b_raw, p["side_disc_step"]),
        "v_concrete": _apply(
            ctx,
            "CA-F27",
            {
                "a_pool": areas["a_pool"],
                "h_pool": h_pool,
                "n_pool": p["n_pool"],
                "wall_coef": _factor(p, "factor.cass.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], band_key: str) -> tuple[float, float]:
    """带类系数取值（factor.cass.<band>.min/max 双键）。"""
    return _factor(p, f"factor.cass.{band_key}.min"), _factor(p, f"factor.cass.{band_key}.max")


# 结果带检查表：(带键短名, dims 键, 量名, 归因参数键)——theta_c/h_draw/ns_act。
_RESULT_BANDS: tuple[tuple[str, str, str, str], ...] = (
    ("sludge_age_band", "theta_c", "泥龄 theta_c d（主反应区口径）", "ns"),
    ("draw_band", "h_draw", "滗水深度 h_draw m（受 h2/3 上限双控）", "h2"),
    ("ns_band", "ns_act", "实际污泥负荷 ns_act（滗水控制裕量）", "ns"),
)


def _warnings(
    p: dict[str, float], areas: dict[str, float], sludge: dict[str, float], ns_act: float
) -> tuple[Warning, ...]:
    """校核带检查：三参数带（ns/mlss/t_selector）+三结果带（theta_c/h_draw/ns_act）。"""
    found: list[Warning] = []
    for param_key, band_key, quantity in _PARAM_BANDS:
        low, high = _band(p, band_key)
        if not low <= p[param_key] <= high:
            found.append(
                _warn(
                    f"{_GB}；{_HB}；factor.cass.{band_key}.*",
                    f"{quantity} = {p[param_key]:.4f} 越出建议带 [{low}, {high}]"
                    f"——调节方向：{param_key}（带内取值）",
                    param_key,
                )
            )
    values = {**areas, **sludge, "ns_act": ns_act}
    band_source = {
        "sludge_age_band": f"{_HB}（CASS 泥龄 15~25d，主反应区口径）",
        "draw_band": f"business-logic §8 行 8；{_HB}（滗水器滗水深度）",
        "ns_band": f"{_GB}；{_HB}（滗水控制裕量口径见起草表追认点 3）",
    }
    for band_key, dim_key, quantity, param_key in _RESULT_BANDS:
        low, high = _band(p, band_key)
        if not low <= values[dim_key] <= high:
            found.append(
                _warn(
                    f"{band_source[band_key]}；factor.cass.{band_key}.*",
                    f"{quantity} = {values[dim_key]:.4f} 越出建议带 [{low}, {high}]"
                    f"——调节方向：{param_key}",
                    param_key,
                )
            )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：三指标 ×(1−removal.mod_default)，其余指标透传（AAO 同族形态）。"""
    out: dict[str, float] = {}
    for indicator, ref_key in manifest.removal_refs.items():
        value = inflow.concentrations.get(indicator)
        if value is not None:
            out[indicator] = value * (1 - _factor(p, ref_key))
    for indicator, value in inflow.concentrations.items():
        out.setdefault(indicator, value)
    return WaterQuality(out)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _Cass()


@final
class _Cass:
    """CASS 生物池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """CA-F1~F27 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        bod5_in, tn_in = quality.BOD5, quality.TN
        if bod5_in is None or tn_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 BOD5/TN 浓度（CA-F3/F20 计算前提，GR-09）"
            )
        bod5_out = bod5_in * (1 - _factor(p, "removal.cass.bod5.mod_default"))
        qual = {"bod5_in": bod5_in, "tn_in": tn_in, "bod5_out": bod5_out}
        cycles = _cycles(ctx, p, flow)
        v_load = _apply(
            ctx,
            "CA-F3",
            {
                "q_avg_daily": flow.q_avg_daily,
                "bod5_in": bod5_in,
                "ns": p["ns"],
                "x_mlss": p["x_mlss"],
            },
        )
        sel = {"q_avg_daily": flow.q_avg_daily, "t_selector": p["t_selector"]}
        v_selector = _apply(ctx, "CA-F4", sel)
        v_bio = _apply(ctx, "CA-F5", {"v_load": v_load, "v_selector": v_selector})
        areas = _areas(ctx, p, v_bio, cycles["v_draw"])
        decant = _decant(ctx, p, cycles["v_draw"])
        sludge = _sludge(ctx, p, flow, qual, v_load)
        oxygen = _oxygen(ctx, p, flow, qual, v_load)
        ns_act = _apply(
            ctx, "CA-F23", {"ns": p["ns"], "v_bio": v_bio, "v_plant": areas["v_plant"]}
        )
        geometry = _geometry(ctx, p, areas)
        dims = {
            **cycles,
            "v_load": v_load,
            "v_selector": v_selector,
            "v_bio": v_bio,
            **areas,
            **decant,
            **sludge,
            **oxygen,
            "ns_act": ns_act,
            **geometry,
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, areas, sludge, ns_act),
            formula_ids=FORMULA_IDS,
        )
