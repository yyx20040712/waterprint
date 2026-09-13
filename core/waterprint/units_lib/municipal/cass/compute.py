"""CASS 生物池计算实现：唯一计算源（CA-F1~F28 全经 registry.apply_batch
求值——批 13-A 同源向量路径：公式链以 ndarray 流动，标量=N=1 退化）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收；批 13-A 向量化重写：
#   公式链经 _apply_batch 批量正门[AGENTS §13.6 同源向量路径唯一——标量
#   =N=1 退化；守卫层/warnings/ceil=N=1 边界件；N>1=批 D 引擎正门]）
#
# 【批 MINOR(2026-09-08)重复清理】type _Array 收口 _unit_compute.Array（import as 保名；四锚恒等）。
# 【公式组】CA-F1~F28（docs/norms/cass.md 起草表+曝气头数据面批；manifest.py 登记）——
#   周期循环主线：周期数/滗水容积（F1~F2）、负荷法主容积+选择区+滗水
#   1/3 池深双控池面积（F3~F12）、时段和=周期不变性（F13，域拒非警告）、
#   滗水器选型（F14~F15，整台 ceil）、剩余污泥/泥龄（F16~F18，AAO 同族
#   口径）、需氧量（F19~F22）、实际负荷校核（F23）、几何与概算（F24~F27）+曝气头选型（F28）。
# 【DSL 收口】ceil 在本文件收口：滗水器台数整台；池长/池宽 0.5 m 档。
#   零数值字面量。流量口径（三表逐字冻结）：生物反应/剩余污泥/需氧量按
#   平均日 flow.q_avg_daily（AAO 同族）；滗水水力按池均摊。
# 【池数守卫（Ruling ④）】compute 只保 n_pool>0 数学有效性（≤0 拒）；
#   池数 ≥2 档位下限经 manifest ParamSpec.grid=[2,3,4,5,6] 声明承载。
# 【系数通道】factor.cass.*/removal.cass.* 经 ctx.params 投影面取值
#   （app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D2）】outflows=入流透传；dims=三表水力结果全量 snake 键；
#   outqualities=入质×(1−removal) removal_refs 命中键（六指标全键，
#   NP2）+其余透传（AAO 同族形态）；warnings=六条校核带越界（ns/mlss/t_selector 参数带+theta_c/
#   h_draw/ns_act 结果带）；formula_ids=实际求值公式号全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import final

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
from waterprint.units_lib._unit_compute import Array as _Array
from waterprint.units_lib._unit_compute import _apply_batch, _factor, _inflow, _make_ceil_step, _vec
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


_ceil_step = _make_ceil_step(_UNIT_ID, "取整步长", spaced=False)


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
    moisture = _factor(params, "factor.cass.sludge.moisture", _UNIT_ID)
    if not 0 < moisture < 1:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 剩余污泥含水率须 ∈ (0,1)：得到 {moisture!r}")


def _cycles(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, _Array]:
    """CA-F1/F2：周期数与单池单周期滗水容积（池均摊口径）。"""
    n_cycle = _apply_batch(ctx, "CA-F1", {"t_cycle": _vec(p["t_cycle"])})
    return {
        "n_cycle": n_cycle,
        "v_draw": _apply_batch(
            ctx,
            "CA-F2",
            {
                "q_avg_daily": _vec(flow.q_avg_daily),
                "n_pool": _vec(p["n_pool"]),
                "n_cycle": n_cycle,
            },
        ),
    }


def _areas(
    ctx: UnitContext, p: dict[str, float], v_bio: _Array, v_draw: _Array
) -> dict[str, _Array]:
    """CA-F6~F12：滗水/负荷双控单池面积、滗水深度与池容（滗水 1/3 池深联动）。"""
    h2 = _vec(p["h2"])
    n_pool = _vec(p["n_pool"])
    h_draw_max = _apply_batch(ctx, "CA-F6", {"h2": h2})
    a_draw = _apply_batch(ctx, "CA-F7", {"v_draw": v_draw, "h_draw_max": h_draw_max})
    a_load = _apply_batch(ctx, "CA-F8", {"v_bio": v_bio, "n_pool": n_pool, "h2": h2})
    a_pool = _apply_batch(ctx, "CA-F9", {"a_load": a_load, "a_draw": a_draw})
    v_pool = _apply_batch(ctx, "CA-F11", {"a_pool": a_pool, "h2": h2})
    return {
        "h_draw_max": h_draw_max,
        "a_draw": a_draw,
        "a_load": a_load,
        "a_pool": a_pool,
        "h_draw": _apply_batch(ctx, "CA-F10", {"v_draw": v_draw, "a_pool": a_pool}),
        "v_pool": v_pool,
        "v_plant": _apply_batch(ctx, "CA-F12", {"v_pool": v_pool, "n_pool": n_pool}),
    }


def _decant(ctx: UnitContext, p: dict[str, float], v_draw: _Array) -> dict[str, _Array]:
    """CA-F13~F15：时段和（不变性载体）+ 滗水器选型（整台 ceil 收口）。"""
    q_decant = _apply_batch(ctx, "CA-F14", {"v_draw": v_draw, "t_draw": _vec(p["t_draw"])})
    n_decant_raw = _apply_batch(
        ctx,
        "CA-F15",
        {
            "q_decant": q_decant,
            "q_per_decant": _vec(_factor(p, "factor.cass.decant.q_per_unit", _UNIT_ID)),
        },
    )
    phases = {"t_react": _vec(p["t_react"]), "t_settle": _vec(p["t_settle"]),
              "t_draw": _vec(p["t_draw"])}
    return {
        "t_phase_sum": _apply_batch(ctx, "CA-F13", phases),
        "q_decant": q_decant,
        "n_decant_raw": n_decant_raw,
        "n_decant": _vec(math.ceil(float(n_decant_raw[0]))),
    }


def _sludge(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, _Array], v_load: _Array
) -> dict[str, _Array]:
    """CA-F16~F18：剩余污泥量（干/湿）与泥龄校核（AAO 同族口径）。"""
    s_y = _apply_batch(
        ctx,
        "CA-F16",
        {
            "q_avg_daily": _vec(flow.q_avg_daily),
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "y_yield": _vec(_factor(p, "factor.cass.yield.y", _UNIT_ID)),
        },
    )
    return {
        "s_y": s_y,
        "q_wet": _apply_batch(
            ctx,
            "CA-F17",
            {
                "s_y": s_y,
                "p_moisture": _vec(_factor(p, "factor.cass.sludge.moisture", _UNIT_ID)),
            },
        ),
        "theta_c": _apply_batch(
            ctx, "CA-F18", {"v_load": v_load, "x_mlss": _vec(p["x_mlss"]), "s_y": s_y}
        ),
    }


def _oxygen(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, _Array], v_load: _Array
) -> dict[str, _Array]:
    """CA-F19~F22：碳化/硝化/反硝化需氧量与设计需氧量（AAO 同族）。"""
    vss_ratio = _factor(p, "factor.cass.vss_ratio", _UNIT_ID)
    x_vss = _vec(vss_ratio) * _vec(p["x_mlss"])
    o2_carbon = _apply_batch(
        ctx,
        "CA-F19",
        {
            "a_prime": _vec(_factor(p, "factor.cass.o2.a_prime", _UNIT_ID)),
            "q_avg_daily": _vec(flow.q_avg_daily),
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "b_prime": _vec(_factor(p, "factor.cass.o2.b_prime", _UNIT_ID)),
            "v_load": v_load,
            "x_vss": x_vss,
        },
    )
    tkn = {"q_avg_daily": _vec(flow.q_avg_daily), "tkn_in": qual["tn_in"],
           "tn_eff": _vec(p["tn_eff"])}
    o2_nit = _apply_batch(ctx, "CA-F20", tkn)
    o2_denit = _apply_batch(ctx, "CA-F21", tkn)
    return {
        "x_vss": x_vss,
        "o2_carbon": o2_carbon,
        "o2_nit": o2_nit,
        "o2_denit": o2_denit,
        "o2_total": _apply_batch(
            ctx, "CA-F22", {"o2_carbon": o2_carbon, "o2_nit": o2_nit, "o2_denit": o2_denit}
        ),
    }


def _geometry(
    ctx: UnitContext, p: dict[str, float], areas: dict[str, _Array], v_selector: _Array
) -> dict[str, _Array]:
    """CA-F24~F28：几何+概算+曝气头选型（CA-F28 主反应区口径——数量唯一
    真源在本字段，几何层只摆放不计数 §10.5 R1）。"""
    h2 = _vec(p["h2"])
    h_pool = _apply_batch(ctx, "CA-F24", {"h_super": _vec(_factor(
        p, "factor.cass.superheight", _UNIT_ID)), "h2": h2})
    binds = {"a_pool": areas["a_pool"], "ratio_lb": _vec(p["ratio_lb"])}
    l_raw = _apply_batch(ctx, "CA-F25", binds)
    b_raw = _apply_batch(ctx, "CA-F26", binds)
    binds28 = {"a_pool": areas["a_pool"], "v_selector": v_selector,
               "n_pool": _vec(p["n_pool"]), "h2": h2, "f_aerator_service": _vec(
        _factor(p, "factor.cass.aerator.service_area", _UNIT_ID))}
    n_aerator_raw = _apply_batch(ctx, "CA-F28", binds28)
    return {
        "h_pool": h_pool,
        "l_pool_raw": l_raw,
        "l_pool": _vec(_ceil_step(float(l_raw[0]), p["side_disc_step"])),
        "b_pool_raw": b_raw,
        "b_pool": _vec(_ceil_step(float(b_raw[0]), p["side_disc_step"])),
        "v_concrete": _apply_batch(
            ctx,
            "CA-F27",
            {
                "a_pool": areas["a_pool"],
                "h_pool": h_pool,
                "n_pool": _vec(p["n_pool"]),
                "wall_coef": _vec(_factor(p, "factor.cass.wall_thickness_coef", _UNIT_ID)),
            },
        ),
        "n_aerator_raw": n_aerator_raw,
        "n_aerator": _vec(math.ceil(float(n_aerator_raw[0]))),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], band_key: str) -> tuple[float, float]:
    """带类系数取值（factor.cass.<band>.min/max 双键）。"""
    return (
        _factor(p, f"factor.cass.{band_key}.min", _UNIT_ID),
        _factor(p, f"factor.cass.{band_key}.max", _UNIT_ID),
    )


# 结果带检查表：(带键短名, dims 键, 量名, 归因参数键)——theta_c/h_draw/ns_act。
_RESULT_BANDS: tuple[tuple[str, str, str, str], ...] = (
    ("sludge_age_band", "theta_c", "泥龄 theta_c d（主反应区口径）", "ns"),
    ("draw_band", "h_draw", "滗水深度 h_draw m（受 h2/3 上限双控）", "h2"),
    ("ns_band", "ns_act", "实际污泥负荷 ns_act（滗水控制裕量）", "ns"),
)


def _warnings(
    p: dict[str, float], areas: dict[str, _Array], sludge: dict[str, _Array], ns_act: _Array
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
    scalars = {key: float(value[0]) for key, value in values.items()}
    band_source = {
        "sludge_age_band": f"{_HB}（CASS 泥龄 15~25d，主反应区口径）",
        "draw_band": f"business-logic §8 行 8；{_HB}（滗水器滗水深度）",
        "ns_band": f"{_GB}；{_HB}（滗水控制裕量口径见起草表追认点 3）",
    }
    for band_key, dim_key, quantity, param_key in _RESULT_BANDS:
        low, high = _band(p, band_key)
        if not low <= scalars[dim_key] <= high:
            found.append(
                _warn(
                    f"{band_source[band_key]}；factor.cass.{band_key}.*",
                    f"{quantity} = {scalars[dim_key]:.4f} 越出建议带 [{low}, {high}]"
                    f"——调节方向：{param_key}",
                    param_key,
                )
            )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：removal_refs 命中键 ×(1−removal.mod_default)，其余透传（AAO 同族形态）。"""
    out: dict[str, float] = {}
    for indicator, ref_key in manifest.removal_refs.items():
        value = inflow.concentrations.get(indicator)
        if value is not None:
            out[indicator] = value * (1 - _factor(p, ref_key, _UNIT_ID))
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
        """CA-F1~F28 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx, "生物池单入单出语义")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        bod5_in, tn_in = quality.BOD5, quality.TN
        if bod5_in is None or tn_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 BOD5/TN 浓度（CA-F3/F20 计算前提，GR-09）"
            )
        removal = _vec(_factor(p, "removal.cass.bod5.mod_default", _UNIT_ID))
        qual = {
            "bod5_in": _vec(bod5_in),
            "tn_in": _vec(tn_in),
            "bod5_out": _vec(bod5_in) * (1 - removal),
        }
        cycles = _cycles(ctx, p, flow)
        v_load = _apply_batch(
            ctx,
            "CA-F3",
            {
                "q_avg_daily": _vec(flow.q_avg_daily),
                "bod5_in": _vec(bod5_in),
                "ns": _vec(p["ns"]),
                "x_mlss": _vec(p["x_mlss"]),
            },
        )
        sel = {"q_avg_daily": _vec(flow.q_avg_daily), "t_selector": _vec(p["t_selector"])}
        v_selector = _apply_batch(ctx, "CA-F4", sel)
        v_bio = _apply_batch(ctx, "CA-F5", {"v_load": v_load, "v_selector": v_selector})
        areas = _areas(ctx, p, v_bio, cycles["v_draw"])
        decant = _decant(ctx, p, cycles["v_draw"])
        sludge = _sludge(ctx, p, flow, qual, v_load)
        oxygen = _oxygen(ctx, p, flow, qual, v_load)
        ns_act = _apply_batch(
            ctx, "CA-F23", {"ns": _vec(p["ns"]), "v_bio": v_bio, "v_plant": areas["v_plant"]}
        )
        geometry = _geometry(ctx, p, areas, v_selector)
        arrays = {
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
        dims = {key: float(value[0]) for key, value in arrays.items()}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, areas, sludge, ns_act),
            formula_ids=FORMULA_IDS,
        )
