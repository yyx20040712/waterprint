"""AAO 生物池计算实现：唯一计算源（AO-F1~F14 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收；
#   公式路线 = ADR-008 ①负荷法主线+泥龄校核带）
#
# 【公式组】AO-F1~F14（docs/norms/aao.md 起草表；manifest.py 登记）——
#   五项公式清单全覆盖义务：污泥负荷/分区容积（AO-F1~F5）、需氧量
#   （AO-F9~F12）、内外回流比（AO-F13/F14）、剩余污泥量（AO-F6~F8）、
#   污泥龄（AO-F8，校核侧）。
# 【DSL 单输出导出量】delta_n（=TN_in−tn_eff）/x_vss（=vss_ratio×
#   x_mlss）/bod5_out（=bod5_in×(1−removal.aao.bod5)）/v_total（三区
#   容积合成）/t_total（HRT=v_total/q_avg_h）/v_o_series（=v_o/n 单系列）
#   在 compute 以符号算术合成——零字面量、无新工程常数（registry 单
#   输出限制的导出面）。
# 【流量口径（三表逐字冻结）】生物池按平均日 flow.q_avg_daily；外回流
#   泵 AO-F13 按最高时 flow.q_design（×sec_per_hour）、内回流泵 AO-F14
#   按平均时（×sec_per_hour）——双口径待领域专家追认，代码零裁量。
# 【系数通道】factor.aao.*/removal.aao.* 经 ctx.params 投影面取值
#   （app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D3）】outflows=入流透传；dims=三表水力结果全量 snake 键；
#   outqualities=入质×(1−removal.mod_default) 三指标+NH3N/TN/TP 透传；
#   warnings=七条校核带越界（ns/mlss/t_p/R/Ri 参数带+t_n/theta_c 结果带
#   ——好氧泥龄口径，param_key 归因+双向调节方向）；formula_ids 全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

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
from waterprint.units_lib.municipal.aao.manifest import FORMULA_IDS, manifest

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
)
# 参数带检查表：(参数键, 带键短名, 量名)——限值经 factor.aao.* 双键。
_PARAM_BANDS: tuple[tuple[str, str, str], ...] = (
    ("ns", "ns_band", "BOD5 污泥负荷 Ns kgBOD5/(kgMLSS·d)"),
    ("x_mlss", "mlss_band", "设计 MLSS mg/L"),
    ("t_p", "hrt_anaerobic_band", "厌氧区 HRT t_p h"),
    ("r_external", "r_external_band", "外回流比 R"),
    ("r_internal", "r_internal_band", "内回流比 Ri"),
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


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/负荷/浓度/HRT/回流比/出水 TN/时换算非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


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


def _volumes(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, bod5_in: float, tn_in: float
) -> dict[str, float]:
    """AO-F1~F5：好氧/厌氧/缺氧区容积与 HRT 校核（平均日口径）。"""
    v_o = _apply(
        ctx,
        "AO-F1",
        {"q_avg_daily": flow.q_avg_daily, "bod5_in": bod5_in, "ns": p["ns"], "x_mlss": p["x_mlss"]},
    )
    v_anaerobic = _apply(ctx, "AO-F3", {"q_avg_daily": flow.q_avg_daily, "t_p": p["t_p"]})
    delta_n = tn_in - p["tn_eff"]
    if delta_n <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 反硝化脱氮量 delta_n 必须 > 0：TN_in={tn_in!r}，"
            f"tn_eff={p['tn_eff']!r}（进水 TN 须高于设计出水 TN——AO-F4 前提）"
        )
    v_anoxic = _apply(
        ctx,
        "AO-F4",
        {
            "q_avg_daily": flow.q_avg_daily,
            "delta_n": delta_n,
            "k_denit": _factor(p, "factor.aao.k_denit"),
            "x_mlss": p["x_mlss"],
        },
    )
    q_avg_h = flow.q_avg_daily * p["sec_per_hour"]  # 平均时流量 m3/h（AO-F14 同源）
    v_total = v_o + v_anaerobic + v_anoxic  # 三区容积合成（三表 v_total 行）
    return {
        "v_o": v_o,
        "t_o": _apply(ctx, "AO-F2", {"v_o": v_o, "q_avg_daily": flow.q_avg_daily}),
        "v_anaerobic": v_anaerobic,
        "delta_n": delta_n,
        "v_anoxic": v_anoxic,
        "t_n": _apply(ctx, "AO-F5", {"v_anoxic": v_anoxic, "q_avg_daily": flow.q_avg_daily}),
        "v_total": v_total,
        "t_total": v_total / q_avg_h,  # 全池 HRT（三表 v_total 行括注）
        "v_o_series": v_o / p["n"],  # 单系列好氧容积（三表 v_o 行括注）
    }


def _sludge(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, float], v_o: float
) -> dict[str, float]:
    """AO-F6~F8：剩余污泥量（干/湿）与好氧泥龄校核。"""
    s_y = _apply(
        ctx,
        "AO-F6",
        {
            "q_avg_daily": flow.q_avg_daily,
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "y_yield": _factor(p, "factor.aao.yield.y"),
        },
    )
    return {
        "s_y": s_y,
        "q_wet": _apply(
            ctx, "AO-F7", {"s_y": s_y, "p_moisture": _factor(p, "factor.aao.sludge.moisture")}
        ),
        "theta_c": _apply(ctx, "AO-F8", {"v_o": v_o, "x_mlss": p["x_mlss"], "s_y": s_y}),
    }


def _oxygen(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, qual: dict[str, float], v_o: float
) -> dict[str, float]:
    """AO-F9~F12：碳化/硝化/反硝化需氧量与设计需氧量。"""
    x_vss = _factor(p, "factor.aao.vss_ratio") * p["x_mlss"]
    o2_carbon = _apply(
        ctx,
        "AO-F9",
        {
            "a_prime": _factor(p, "factor.aao.o2.a_prime"),
            "q_avg_daily": flow.q_avg_daily,
            "bod5_in": qual["bod5_in"],
            "bod5_out": qual["bod5_out"],
            "b_prime": _factor(p, "factor.aao.o2.b_prime"),
            "v_o": v_o,
            "x_vss": x_vss,
        },
    )
    o2_nit = _apply(
        ctx,
        "AO-F10",
        {"q_avg_daily": flow.q_avg_daily, "tkn_in": qual["tn_in"], "tn_eff": p["tn_eff"]},
    )
    o2_denit = _apply(
        ctx,
        "AO-F11",
        {"q_avg_daily": flow.q_avg_daily, "tkn_in": qual["tn_in"], "tn_eff": p["tn_eff"]},
    )
    return {
        "x_vss": x_vss,
        "o2_carbon": o2_carbon,
        "o2_nit": o2_nit,
        "o2_denit": o2_denit,
        "o2_total": _apply(
            ctx, "AO-F12", {"o2_carbon": o2_carbon, "o2_nit": o2_nit, "o2_denit": o2_denit}
        ),
    }


def _returns(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """AO-F13/F14：外回流（最高时口径）/内回流（平均时口径）泵流量。"""
    return {
        "q_return": _apply(
            ctx,
            "AO-F13",
            {"r_external": p["r_external"], "q_design_h": flow.q_design * p["sec_per_hour"]},
        ),
        "q_internal": _apply(
            ctx,
            "AO-F14",
            {"r_internal": p["r_internal"], "q_avg_h": flow.q_avg_daily * p["sec_per_hour"]},
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _warnings(
    p: dict[str, float], volumes: dict[str, float], sludge: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：五条参数带（ns/mlss/t_p/R/Ri）+两条结果带（t_n/theta_c）。"""
    found: list[Warning] = []
    for param_key, band_key, quantity in _PARAM_BANDS:
        low = _factor(p, f"factor.aao.{band_key}.min")
        high = _factor(p, f"factor.aao.{band_key}.max")
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
        _factor(p, "factor.aao.sludge_age_band.min"),
        _factor(p, "factor.aao.sludge_age_band.max"),
    )
    if not age[0] <= sludge["theta_c"] <= age[1]:
        found.append(
            _warn(
                f"{_GB}（AAO 泥龄 11~23d，好氧泥龄判断口径）；factor.aao.sludge_age_band.*",
                f"好氧泥龄 theta_c = {sludge['theta_c']:.4f} d 越出建议带 [{age[0]}, {age[1]}]"
                "——调节方向：ns（↓泥龄↑）或 x_mlss（↑泥龄↑）；全池口径备考注记见"
                " docs/norms/aao.md（口径待领域专家追认）",
                "ns",
            )
        )
    hrt = (
        _factor(p, "factor.aao.hrt_anoxic_band.min"),
        _factor(p, "factor.aao.hrt_anoxic_band.max"),
    )
    if not hrt[0] <= volumes["t_n"] <= hrt[1]:
        found.append(
            _warn(
                f"{_HB}；factor.aao.hrt_anoxic_band.*",
                f"缺氧区 HRT t_n = {volumes['t_n']:.4f} h 越出建议带 [{hrt[0]}, {hrt[1]}]"
                "——调节方向：x_mlss（↑t_n↓）或反硝化速率 Kde（factor.aao.k_denit，↑t_n↓）",
                "x_mlss",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：三指标 ×(1−removal.mod_default)，其余指标透传。"""
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
    return _Aao()


@final
class _Aao:
    """AAO 生物池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """AO-F1~F14 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        bod5_in, tn_in = quality.BOD5, quality.TN
        if bod5_in is None or tn_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 BOD5/TN 浓度（AO-F1/F4 计算前提，GR-09）"
            )
        qual = {"bod5_in": bod5_in, "tn_in": tn_in,
                "bod5_out": bod5_in * (1 - _factor(p, "removal.aao.bod5.mod_default"))}
        volumes = _volumes(ctx, p, flow, bod5_in, tn_in)
        sludge = _sludge(ctx, p, flow, qual, volumes["v_o"])
        oxygen = _oxygen(ctx, p, flow, qual, volumes["v_o"])
        returns = _returns(ctx, p, flow)
        dims = {**volumes, **sludge, **oxygen, **returns}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, volumes, sludge),
            formula_ids=FORMULA_IDS,
        )
