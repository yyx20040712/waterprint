"""紫外消毒计算实现：唯一计算源（KZ-F1~F11 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KZ-F1~KZ-F11（docs/norms/mine_water_ziwai.md 起草表；
#   manifest.py 登记）——灯管布置实算剂量主线（辐照强度→单排剂量
#   →排数 ceil→实算剂量校核），含结垢系数 f_fouling 特征键。
# 【DSL 收口】ceil 在本文件收口（DSL 无 ceil）：灯管排数向上取整
#   （n_rows_raw 取整前审计面——cifenli n_disks 同型）。零数值字面量。
# 【流量口径】渠内水力按最高时 flow.q_design（KZ-F1~F3/KZ-F6/KZ-F9，
#   ×3600 已内联公式串）——表流量口径逐字（n 渠并联均分）。
# 【合格面】KZ-F8 实算剂量 ≥ 设计剂量由排数 ceil 结构保证（数学上
#   恒成立），constraints 声明式承载不产运行时 Warning。
# 【系数通道】factor.mine_ziwai.*/removal.mine_ziwai.* 经 ctx.params
#   投影面取值（app._unit_params 线感知投影，mine_ 限定键空间）；
#   缺键=领域异常。elevation_loss 键归高程链子系统（与 KZ-F10 渠内
#   公式水损双轨语义——公式值走校核面/经验值走高程链，表追认点 14），
#   本文件不消费；wall_thickness_coef 键本表无混凝土公式行仅登记
#   在册。
# 【输出面（D2）】outflows=入流透传；dims=表结果全量 snake 键（单渠
#   流量/断面积/流速/穿透率/辐照强度/单排剂量/排数（含取整前审计
#   面）/实算剂量/接触时间/渠道水损/渠总高）；outqualities=入质×
#   (1−removal.mod_default) 双指标（零去除键 0.0 穿流——SS 1.36/
#   COD 51.8 全厂终水零变化）；warnings=校核带越界（渠内流速带/
#   穿透率带；param_key 归因+调节方向）；formula_ids=实际求值公式号
#   全量。
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
from waterprint.units_lib.mine_water.ziwai.manifest import FORMULA_IDS, manifest

_UNIT_ID = "mine_water_ziwai"
_GT = "GB/T 31392-2022（回用消毒剂量，条号待核对）"
_HB = "给水排水设计手册（第 3 册 城镇给水）紫外消毒渠内流速/穿透率常用带"
_VELOCITY_BAND = (
    "factor.mine_ziwai.velocity_band.min",
    "factor.mine_ziwai.velocity_band.max",
)
_T254_BAND = (
    "factor.mine_ziwai.t254_band.min",
    "factor.mine_ziwai.t254_band.max",
)
_PARAMS_POSITIVE = (
    "n",
    "b_channel",
    "h_channel",
    "p_lamp",
    "n_layer",
    "d_long",
    "xi_total",
    "n_t",
    "t254",
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
    """参数域守卫：渠数/断面/灯功率/排数/排距/指数/穿透率非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条"
            "（消毒渠单入单出语义）"
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


def _channel(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow
) -> dict[str, float]:
    """KZ-F1~F3：单渠流量/渠断面积/渠内流速（最高时口径）。"""
    q_ch = _apply(ctx, "KZ-F1", {"q_design": flow.q_design, "n": p["n"]})
    a_ch = _apply(
        ctx, "KZ-F2", {"b_channel": p["b_channel"], "h_channel": p["h_channel"]}
    )
    return {
        "q_ch": q_ch,
        "a_ch": a_ch,
        "v_ch": _apply(ctx, "KZ-F3", {"q_ch": q_ch, "a_ch": a_ch}),
    }


def _dose_chain(
    ctx: UnitContext, p: dict[str, float], a_ch: float, v_ch: float
) -> dict[str, float]:
    """KZ-F4~F9：穿透率/辐照强度/单排剂量/排数（ceil）/实算剂量/接触时间。"""
    t_eff = _apply(ctx, "KZ-F4", {"t254": p["t254"], "n_t": p["n_t"]})
    i_avg = _apply(
        ctx,
        "KZ-F5",
        {
            "p_lamp": p["p_lamp"],
            "n_layer": p["n_layer"],
            "eta_geo": _factor(p, "factor.mine_ziwai.eta_geo"),
            "t_eff": t_eff,
            "f_aging": _factor(p, "factor.mine_ziwai.f_aging"),
            "f_fouling": _factor(p, "factor.mine_ziwai.f_fouling"),
            "a_ch": a_ch,
        },
    )
    dose_row = _apply(
        ctx, "KZ-F6", {"i_avg": i_avg, "d_long": p["d_long"], "v_ch": v_ch}
    )
    n_rows_raw = _apply(
        ctx,
        "KZ-F7",
        {"dose": _factor(p, "factor.mine_ziwai.dose"), "dose_row": dose_row},
    )
    # 灯管排数向上取整（表 KZ-F7 口径——DSL 无 ceil，本文件收口）
    n_rows = float(math.ceil(n_rows_raw))
    return {
        "t_eff": t_eff,
        "i_avg": i_avg,
        "dose_row": dose_row,
        "n_rows_raw": n_rows_raw,
        "n_rows": n_rows,
        "dose_act": _apply(ctx, "KZ-F8", {"n_rows": n_rows, "dose_row": dose_row}),
        "t_contact": _apply(
            ctx, "KZ-F9", {"n_rows": n_rows, "d_long": p["d_long"], "v_ch": v_ch}
        ),
    }


def _loss_depth(ctx: UnitContext, p: dict[str, float], v_ch: float) -> dict[str, float]:
    """KZ-F10~F11：渠道水损（公式面 max(ξv²/2g, 构造下限)）与渠总高。"""
    h_loss = _apply(
        ctx,
        "KZ-F10",
        {
            "xi_total": p["xi_total"],
            "v_ch": v_ch,
            "loss_min": _factor(p, "factor.mine_ziwai.loss_min"),
        },
    )
    return {
        "h_loss": h_loss,
        "h_total": _apply(
            ctx,
            "KZ-F11",
            {
                "h_super": _factor(p, "factor.mine_ziwai.superheight"),
                "h_channel": p["h_channel"],
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(p: dict[str, float], v_ch: float) -> tuple[Warning, ...]:
    """校核带检查：渠内流速带（宽下限——检修工况可贴限）/穿透率带。"""
    found: list[Warning] = []
    velocity = _band(p, _VELOCITY_BAND)
    if not velocity[0] <= v_ch <= velocity[1]:
        found.append(
            _warn(
                f"{_HB}；{_VELOCITY_BAND[0]}~{_VELOCITY_BAND[1]}",
                f"渠内流速 = {v_ch:.4f} m/s 越出建议带"
                f" [{velocity[0]}, {velocity[1]}]——调节方向：n/h_channel"
                "（渠数与断面构造，剂量达标为准）",
                "n",
            )
        )
    t254_band = _band(p, _T254_BAND)
    if not t254_band[0] <= p["t254"] <= t254_band[1]:
        found.append(
            _warn(
                f"{_HB}；{_T254_BAND[0]}~{_T254_BAND[1]}",
                f"254 nm 穿透率 = {p['t254']:.1f} % 越出建议带"
                f" [{t254_band[0]}, {t254_band[1]}]——调节方向：t254"
                "（滤后清矿井水带内取值；越带下限需增排数保剂量）",
                "t254",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：双指标 ×(1−removal.mod_default)（零去除键 0.0 穿流），其余透传。"""
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
    return _MineZiwai()


@final
class _MineZiwai:
    """紫外消毒 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KZ-F1~F11 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        channel = _channel(ctx, p, flow)
        dims = {
            **channel,
            **_dose_chain(ctx, p, channel["a_ch"], channel["v_ch"]),
            **_loss_depth(ctx, p, channel["v_ch"]),
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, channel["v_ch"]),
            formula_ids=FORMULA_IDS,
        )
