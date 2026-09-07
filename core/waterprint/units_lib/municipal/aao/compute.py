"""AAO 生物池计算实现：唯一计算源（AO-F1~F19 全经 registry.apply_batch
求值——批 13-A 同源向量路径：公式链以 ndarray 流动，标量=N=1 退化）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收；
#   公式路线 = ADR-008 ①负荷法主线+泥龄校核带；批 13-A 向量化重写：
#   公式链经 _apply_batch 批量正门（AGENTS §13.6 同源向量路径唯一——
#   标量=N=1 退化；守卫层/warnings/ceil=N=1 边界件；N>1=批 D 引擎正门）
#
# 【公式组】AO-F1~F19（docs/norms/aao.md 起草表+L7 池体图元批几何族；
#   manifest.py 登记）——
#   五项公式清单全覆盖义务：污泥负荷/分区容积（AO-F1~F5）、需氧量
#   （AO-F9~F12）、内外回流比（AO-F13/F14）、剩余污泥量（AO-F6~F8）、
#   污泥龄（AO-F8，校核侧）；L7 池体几何（AO-F15~F19——CASS 公式族
#   平移：容积折水面/超高叠加/长宽比定形/圆整容积，连续流无滗水支项）。
# 【DSL 单输出导出量】delta_n（=TN_in−tn_eff）/x_vss（=vss_ratio×
#   x_mlss）/bod5_out（=bod5_in×(1−removal.aao.bod5)）/v_total（三区
#   容积合成）/t_total（HRT=v_total/q_avg_h）/v_o_series（=v_o/n 单系列）
#   在 compute 以符号算术合成（数组链——IEEE 元素运算位恒等）——零字面量、
#   无新工程常数（registry 单输出限制的导出面）。
# 【池体几何段（L7）】AO-F15~F19——ceil 在本文件收口（池长/池宽
#   side_disc_step 档，沿 CASS；步长>0 已由 _validate 参数域守卫承载）；
#   h2 参数复用键随水面声明入 dims（表 section_keys.water_depth 取数
#   要求）；v_pool=圆整边长×h2≥v_total 圆整裕量诚实呈现（D12）。
# 【流量口径（三表逐字冻结）】生物池按平均日 flow.q_avg_daily；外回流
#   泵 AO-F13 按最高时 flow.q_design（×sec_per_hour）、内回流泵 AO-F14
#   按平均时（×sec_per_hour）——双口径待领域专家追认，代码零裁量。
# 【系数通道】factor.aao.*/removal.aao.* 经 ctx.params 投影面取值
#   （app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D3）】outflows=入流透传+sludge_out SLUDGE 产股（GOLDEN4a D3
#   无条件产股——AO-F6/F7 全厂口径 ds/q_wet+moisture 系数键；÷SECS_
#   PER_DAY 回契约口径）；dims=三表水力结果全量 snake 键（不变——
#   投影非计算，nongsuo sup 先例同构）；
#   outqualities=入质×(1−removal.mod_default) removal_refs 命中键
#   （六指标全键，NP2）+其余透传；
#   warnings=七条校核带越界（ns/mlss/t_p/R/Ri 参数带+t_n/theta_c 结果带
#   ——好氧泥龄口径，param_key 归因+双向调节方向）；formula_ids 全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import final

import numpy

from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)
from waterprint.units_lib._constants import SECS_PER_DAY
from waterprint.units_lib._unit_compute import _apply_batch, _factor, _inflow, _vec
from waterprint.units_lib.municipal.aao.manifest import FORMULA_IDS, manifest

type _Array = numpy.ndarray  # 向量链注记别名（批 13-A——公式链中间量形态）

_UNIT_ID = "municipal_aao"
_HB = "给水排水设计手册（第 5 册 城镇排水）"
_GB = "GB 50014-2021 §7.6"
_PARAMS_POSITIVE = (
    "n",
    "ns",
    "x_mlss",
    "t_p",
    "r_external",
    "r_internal",
    "tn_eff",
    "sec_per_hour",
    "h2",
    "ratio_lb",
    "side_disc_step",
)
# 参数带检查表：(参数键, 带键短名, 量名)——限值经 factor.aao.* 双键。
_PARAM_BANDS: tuple[tuple[str, str, str], ...] = (
    ("ns", "ns_band", "BOD5 污泥负荷 Ns kgBOD5/(kgMLSS·d)"),
    ("x_mlss", "mlss_band", "设计 MLSS mg/L"),
    ("t_p", "hrt_anaerobic_band", "厌氧区 HRT t_p h"),
    ("r_external", "r_external_band", "外回流比 R"),
    ("r_internal", "r_internal_band", "内回流比 Ri"),
)


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/负荷/浓度/HRT/回流比/出水 TN/时换算非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _volumes(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, bod5_in: float, tn_in: float
) -> dict[str, _Array]:
    """AO-F1~F5：好氧/厌氧/缺氧区容积与 HRT 校核（平均日口径——数组链）。"""
    q_avg = _vec(flow.q_avg_daily)
    x_mlss = _vec(p["x_mlss"])
    v_o = _apply_batch(
        ctx,
        "AO-F1",
        {
            "q_avg_daily": q_avg,
            "bod5_in": _vec(bod5_in),
            "ns": _vec(p["ns"]),
            "x_mlss": x_mlss,
        },
    )
    v_anaerobic = _apply_batch(ctx, "AO-F3", {"q_avg_daily": q_avg, "t_p": _vec(p["t_p"])})
    if tn_in - p["tn_eff"] <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 反硝化脱氮量 delta_n 必须 > 0：TN_in={tn_in!r}，"
            f"tn_eff={p['tn_eff']!r}（进水 TN 须高于设计出水 TN——AO-F4 前提）"
        )
    delta_n = _vec(tn_in) - _vec(p["tn_eff"])
    v_anoxic = _apply_batch(
        ctx,
        "AO-F4",
        {
            "q_avg_daily": q_avg,
            "delta_n": delta_n,
            "k_denit": _vec(_factor(p, "factor.aao.k_denit", _UNIT_ID)),
            "x_mlss": x_mlss,
        },
    )
    q_avg_h = q_avg * _vec(p["sec_per_hour"])  # 平均时流量 m3/h（AO-F14 同源）
    v_total = v_o + v_anaerobic + v_anoxic  # 三区容积合成（三表 v_total 行）
    return {
        "v_o": v_o,
        "t_o": _apply_batch(ctx, "AO-F2", {"v_o": v_o, "q_avg_daily": q_avg}),
        "v_anaerobic": v_anaerobic,
        "delta_n": delta_n,
        "v_anoxic": v_anoxic,
        "t_n": _apply_batch(ctx, "AO-F5", {"v_anoxic": v_anoxic, "q_avg_daily": q_avg}),
        "v_total": v_total,
        "t_total": v_total / q_avg_h,  # 全池 HRT（三表 v_total 行括注）
        "v_o_series": v_o / _vec(p["n"]),  # 单系列好氧容积（三表 v_o 行括注）
    }


def _sludge(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, _Array], v_o: _Array
) -> dict[str, _Array]:
    """AO-F6~F8：剩余污泥量（干/湿）与好氧泥龄校核。"""
    s_y = _apply_batch(
        ctx,
        "AO-F6",
        {
            "q_avg_daily": _vec(flow.q_avg_daily),
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "y_yield": _vec(_factor(p, "factor.aao.yield.y", _UNIT_ID)),
        },
    )
    return {
        "s_y": s_y,
        "q_wet": _apply_batch(
            ctx,
            "AO-F7",
            {
                "s_y": s_y,
                "p_moisture": _vec(_factor(p, "factor.aao.sludge.moisture", _UNIT_ID)),
            },
        ),
        "theta_c": _apply_batch(
            ctx, "AO-F8", {"v_o": v_o, "x_mlss": _vec(p["x_mlss"]), "s_y": s_y}
        ),
    }


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


def _returns(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, _Array]:
    """AO-F13/F14：外回流（最高时口径）/内回流（平均时口径）泵流量。"""
    return {
        "q_return": _apply_batch(
            ctx,
            "AO-F13",
            {
                "r_external": _vec(p["r_external"]),
                "q_design_h": _vec(flow.q_design) * _vec(p["sec_per_hour"]),
            },
        ),
        "q_internal": _apply_batch(
            ctx,
            "AO-F14",
            {
                "r_internal": _vec(p["r_internal"]),
                "q_avg_h": _vec(flow.q_avg_daily) * _vec(p["sec_per_hour"]),
            },
        ),
    }


def _geometry(ctx: UnitContext, p: dict[str, float], v_total: _Array) -> dict[str, _Array]:
    """AO-F15~F19：池体几何——容积折水面/超高/长宽比定形（0.5 m 档 ceil 收口）。

    h2 参数复用键随水面声明入 dims（表 section_keys.water_depth 取数）；
    ceil 边长×h2=v_pool≥v_total 圆整裕量诚实呈现（沿 CASS，D12）。
    """
    h2 = _vec(p["h2"])
    a_pool = _apply_batch(ctx, "AO-F15", {"v_total": v_total, "h2": h2})
    h_pool = _apply_batch(
        ctx,
        "AO-F16",
        {"h_super": _vec(_factor(p, "factor.aao.superheight", _UNIT_ID)), "h2": h2},
    )
    binds = {"a_pool": a_pool, "ratio_lb": _vec(p["ratio_lb"])}
    l_raw = _apply_batch(ctx, "AO-F17", binds)
    b_raw = _apply_batch(ctx, "AO-F18", binds)
    step = p["side_disc_step"]
    l_pool = math.ceil(float(l_raw[0]) / step) * step
    b_pool = math.ceil(float(b_raw[0]) / step) * step
    return {
        "h2": h2,
        "a_pool": a_pool,
        "h_pool": h_pool,
        "l_pool_raw": l_raw,
        "b_pool_raw": b_raw,
        "l_pool": _vec(l_pool),
        "b_pool": _vec(b_pool),
        "v_pool": _apply_batch(
            ctx, "AO-F19", {"l_pool": _vec(l_pool), "b_pool": _vec(b_pool), "h2": h2}
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _warnings(
    p: dict[str, float], volumes: dict[str, _Array], sludge: dict[str, _Array]
) -> tuple[Warning, ...]:
    """校核带检查：五条参数带（ns/mlss/t_p/R/Ri）+两条结果带（t_n/theta_c）。"""
    found: list[Warning] = []
    for param_key, band_key, quantity in _PARAM_BANDS:
        low = _factor(p, f"factor.aao.{band_key}.min", _UNIT_ID)
        high = _factor(p, f"factor.aao.{band_key}.max", _UNIT_ID)
        value = p[param_key]
        if not low <= value <= high:
            found.append(
                _warn(
                    f"{_GB}；{_HB}；factor.aao.{band_key}.*",
                    f"{quantity} = {value:.4f} 越出建议带 [{low}, {high}]"
                    f"——调节方向：{param_key}（带内取值）",
                    param_key,
                )
            )
    age = (
        _factor(p, "factor.aao.sludge_age_band.min", _UNIT_ID),
        _factor(p, "factor.aao.sludge_age_band.max", _UNIT_ID),
    )
    theta_c = float(sludge["theta_c"][0])
    if not age[0] <= theta_c <= age[1]:
        found.append(
            _warn(
                f"{_GB}（AAO 泥龄 11~23d，好氧泥龄判断口径）；factor.aao.sludge_age_band.*",
                f"好氧泥龄 theta_c = {theta_c:.4f} d 越出建议带 [{age[0]}, {age[1]}]"
                "——调节方向：ns（↓泥龄↑）或 x_mlss（↑泥龄↑）；全池口径备考注记见"
                " docs/norms/aao.md（口径待领域专家追认）",
                "ns",
            )
        )
    hrt = (
        _factor(p, "factor.aao.hrt_anoxic_band.min", _UNIT_ID),
        _factor(p, "factor.aao.hrt_anoxic_band.max", _UNIT_ID),
    )
    t_n = float(volumes["t_n"][0])
    if not hrt[0] <= t_n <= hrt[1]:
        found.append(
            _warn(
                f"{_HB}；factor.aao.hrt_anoxic_band.*",
                f"缺氧区 HRT t_n = {t_n:.4f} h 越出建议带 [{hrt[0]}, {hrt[1]}]"
                "——调节方向：x_mlss（↑t_n↓）或反硝化速率 Kde（factor.aao.k_denit，↑t_n↓）",
                "x_mlss",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：removal_refs 命中键 ×(1−removal.mod_default)，其余透传。"""
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
    return _Aao()


@final
class _Aao:
    """AAO 生物池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """AO-F1~F19 主算路径（纯函数：同 ctx 必同 UnitResult——向量路径 N=1）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx, "生物池单入单出语义")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        bod5_in, tn_in = quality.BOD5, quality.TN
        if bod5_in is None or tn_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 BOD5/TN 浓度（AO-F1/F4 计算前提，GR-09）"
            )
        qual = {
            "bod5_in": _vec(bod5_in),
            "tn_in": _vec(tn_in),
            "bod5_out": _vec(bod5_in)
            * (1 - _vec(_factor(p, "removal.aao.bod5.mod_default", _UNIT_ID))),
        }
        volumes = _volumes(ctx, p, flow, bod5_in, tn_in)
        sludge = _sludge(ctx, p, flow, qual, volumes["v_o"])
        oxygen = _oxygen(ctx, p, flow, qual, volumes["v_o"])
        returns = _returns(ctx, p, flow)
        geometry = _geometry(ctx, p, volumes["v_total"])
        arrays = {**volumes, **sludge, **oxygen, **returns, **geometry}
        dims = {key: float(value[0]) for key, value in arrays.items()}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        sludge_ref = PortRef(unit_id=ctx.unit_id, port_id="sludge_out")
        return UnitResult(
            outflows={
                out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz),
                # GOLDEN4a D3 产股：无条件产股（nongsuo sup 先例同构）——
                # ds=AO-F6 s_y 全厂（hebing 注入 ds_bio 链路同源）、q_wet=
                # AO-F7 dims 直用（与 HB-F2 同式）；moisture 与 hebing
                # p_bio 默认同源（factor.aao.sludge.moisture）。
                sludge_ref: SludgeFlow(
                    q_wet=float(sludge["q_wet"][0]) / SECS_PER_DAY,
                    ds=float(sludge["s_y"][0]) / SECS_PER_DAY,
                    moisture=_factor(p, "factor.aao.sludge.moisture", _UNIT_ID),
                ),
            },
            outqualities={
                out_ref: _out_quality(p, quality),
                # SLUDGE 通道无水质指标——空 WaterQuality 单位元（R5/GR-04）
                sludge_ref: WaterQuality({}),
            },
            dims=dims,
            warnings=_warnings(p, volumes, sludge),
            formula_ids=FORMULA_IDS,
        )
