"""紫外消毒计算实现：唯一计算源（ZW-F1~F13 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【公式组】ZW-F1~F13（docs/norms/ziwai.md 起草表；manifest.py 登记）。
# 【DSL 收口】ceil 离散在本文件收口（DSL 无 ceil）：渠内水深 h_w=ceil(
#   h_w_raw, length_disc_step 0.1 m 档)；灯管数 n_lamp=整支 ceil；模块
#   数 n_module=整模块 ceil；每渠串列 n_module_series=ceil(n_module/
#   n_channel)——模块不足整渠串列时按整列布置（灯区按渠放大，dims
#   双值承载）。零数值字面量。
# 【流量口径】消毒按最高时 flow.q_design（峰值流量下仍需保证剂量）——
#   四表口径逐字；ZW-F4 灯管概算链承载剂量校核语义（选型剂量≥设计
#   剂量，无独立公式）。
# 【系数通道】factor.ziwai.*/removal.ziwai.* 经 ctx.params 投影面取值
#   （app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D2）】outflows=入流透传；dims=四表水力结果全量 snake 键；
#   outqualities=零去除键透传（removal.ziwai.*.mod_default 全 0.0——
#   物理消毒无去除，透传分支不经 apply、formula_ids 不含去除式，与
#   M1a 三单元一律乘 (1−r) 的形态差异记档；紫外只改变粪大肠指标=
#   dims 的 c_fecal_out）；warnings=校核带越界（渠内流速带/有效接触
#   时间带+灯管淹没校核 h_submerge<0——实际过流态口径）；单渠事故
#   0.78 m/s 超带为表内注记非运行时警告（R1 微修后口径：运行时不
#   枚举事故态）；formula_ids=实际求值公式号全量。
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
from waterprint.units_lib.municipal.ziwai.manifest import FORMULA_IDS, manifest

_UNIT_ID = "municipal_ziwai"
_HB = "给水排水设计手册（第 5 册 城镇排水）紫外渠道设计"
_VELOCITY_BAND = (
    "factor.ziwai.velocity_band.min",
    "factor.ziwai.velocity_band.max",
)
_TEXP_BAND = (
    "factor.ziwai.t_exp_band.min",
    "factor.ziwai.t_exp_band.max",
)
_Q_PER_LAMP = "factor.ziwai.q_per_lamp"
_F_AGING = "factor.ziwai.f_aging"
_C_FECAL_IN = "factor.ziwai.fecal.c_in_design"
_N_LOG = "factor.ziwai.fecal.log_removal"
_PARAMS_POSITIVE = (
    "n_channel",
    "v_channel",
    "b_c",
    "n_lamp_module",
    "l_module",
    "l_stab",
    "h_module",
    "length_disc_step",
)
_FACTORS_POSITIVE = (_Q_PER_LAMP, _F_AGING, _C_FECAL_IN, _N_LOG)


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
    """构造步长向上取整（ZW-F2 的 0.1 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：渠道数/流速/渠宽/模块几何/步长与灯管·粪大肠系数非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")
    for key in _FACTORS_POSITIVE:
        if _factor(params, key) <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 系数键 {key!r} 必须 > 0"
                "（单灯处理量/老化系数/粪大肠设计值物理域）"
            )


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条"
            "（紫外消毒渠单入单出语义）"
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


def _channel(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """ZW-F1~F3：单渠流量（双渠各半）/渠内水深（0.1 m 档）/实际流速校核。"""
    q_c = _apply(ctx, "ZW-F1", {"q_design": flow.q_design, "n_channel": p["n_channel"]})
    h_w_raw = _apply(
        ctx, "ZW-F2", {"q_c": q_c, "v_channel": p["v_channel"], "b_c": p["b_c"]}
    )
    h_w = _ceil_step(h_w_raw, p["length_disc_step"])
    return {
        "q_c": q_c,
        "h_w_raw": h_w_raw,
        "h_w": h_w,
        "v_channel_act": _apply(ctx, "ZW-F3", {"q_c": q_c, "b_c": p["b_c"], "h_w": h_w}),
    }


def _lamps(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """ZW-F4~F8：灯管概算（整支）/模块分置（整模块·每渠串列 ceil）/渠长。"""
    n_lamp_raw = _apply(
        ctx,
        "ZW-F4",
        {
            "q_design": flow.q_design,
            "q_per_lamp": _factor(p, _Q_PER_LAMP),
            "f_aging": _factor(p, _F_AGING),
        },
    )
    n_lamp = float(math.ceil(n_lamp_raw))
    n_module_raw = _apply(
        ctx, "ZW-F5", {"n_lamp": n_lamp, "n_lamp_module": p["n_lamp_module"]}
    )
    n_module = float(math.ceil(n_module_raw))
    series_raw = _apply(
        ctx, "ZW-F6", {"n_module": n_module, "n_channel": p["n_channel"]}
    )
    n_module_series = float(math.ceil(series_raw))
    l_lamp_zone = _apply(
        ctx, "ZW-F7", {"n_module_series": n_module_series, "l_module": p["l_module"]}
    )
    return {
        "n_lamp_raw": n_lamp_raw,
        "n_lamp": n_lamp,
        "n_module_raw": n_module_raw,
        "n_module": n_module,
        "n_module_series": n_module_series,
        "l_lamp_zone": l_lamp_zone,
        "l_channel": _apply(ctx, "ZW-F8", {"l_stab": p["l_stab"], "l_lamp_zone": l_lamp_zone}),
    }


def _check(
    ctx: UnitContext, p: dict[str, float], channel: dict[str, float], lamps: dict[str, float]
) -> dict[str, float]:
    """ZW-F9~F11：有效接触时间/粪大肠 log 去除/灯管淹没校核。"""
    return {
        "t_exp": _apply(
            ctx,
            "ZW-F9",
            {
                "b_c": p["b_c"],
                "h_w": channel["h_w"],
                "l_lamp_zone": lamps["l_lamp_zone"],
                "q_c": channel["q_c"],
            },
        ),
        "c_fecal_out": _apply(
            ctx, "ZW-F10", {"c_fecal_in": _factor(p, _C_FECAL_IN), "n_log": _factor(p, _N_LOG)}
        ),
        "h_submerge": _apply(ctx, "ZW-F11", {"h_w": channel["h_w"], "h_module": p["h_module"]}),
    }


def _depth(
    ctx: UnitContext, p: dict[str, float], channel: dict[str, float], lamps: dict[str, float]
) -> dict[str, float]:
    """ZW-F12/F13：渠总高与概算口径混凝土量（双渠）。"""
    h_channel = _apply(
        ctx, "ZW-F12", {"h_super": _factor(p, "factor.ziwai.superheight"), "h_w": channel["h_w"]}
    )
    return {
        "h_channel": h_channel,
        "v_concrete": _apply(
            ctx,
            "ZW-F13",
            {
                "l_channel": lamps["l_channel"],
                "b_c": p["b_c"],
                "h_channel": h_channel,
                "n_channel": p["n_channel"],
                "wall_coef": _factor(p, "factor.ziwai.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(
    p: dict[str, float], channel: dict[str, float], check: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：渠内流速带/有效接触时间带/灯管淹没校核（实际过流态）。"""
    found: list[Warning] = []
    vel = _band(p, _VELOCITY_BAND)
    if not vel[0] <= channel["v_channel_act"] <= vel[1]:
        found.append(
            _warn(
                f"{_HB}；{_VELOCITY_BAND[0]}~{_VELOCITY_BAND[1]}"
                "（实际过流态——单渠事故 0.78 m/s 超带为表内注记非运行时）",
                f"实际渠内流速 = {channel['v_channel_act']:.4f} m/s 越出建议带"
                f" [{vel[0]}, {vel[1]}]——调节方向：v_channel（↑加深渠）或 b_c（渠宽）",
                "v_channel",
            )
        )
    texp = _band(p, _TEXP_BAND)
    if not texp[0] <= check["t_exp"] <= texp[1]:
        found.append(
            _warn(
                f"{_HB}；{_TEXP_BAND[0]}~{_TEXP_BAND[1]}",
                f"有效接触时间 = {check['t_exp']:.4f} s 越出建议带"
                f" [{texp[0]}, {texp[1]}]——调节方向：n_lamp_module（↑灯区加长）"
                "或 v_channel/b_c（过流断面）",
                "n_lamp_module",
            )
        )
    if check["h_submerge"] < 0:
        found.append(
            _warn(
                f"{_HB}；ZW-F11 灯管淹没校核（h_submerge ≥ 0）",
                f"灯管顶淹没裕量 = {check['h_submerge']:.4f} m < 0（灯管露出水面）"
                "——调节方向：v_channel（↓加深渠）或 h_module（模块高构造）",
                "v_channel",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _Ziwai()


@final
class _Ziwai:
    """紫外消毒 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """ZW-F1~F13 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        channel = _channel(ctx, p, flow)
        lamps = _lamps(ctx, p, flow)
        check = _check(ctx, p, channel, lamps)
        depth = _depth(ctx, p, channel, lamps)
        dims = {**channel, **lamps, **check, **depth}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            # 零去除键透传：removal.ziwai.*.mod_default 全 0.0（物理消毒
            # 无去除）——出水质=入水质逐键原样（不经 apply，简报 D2 裁决）；
            # 消毒指标=粪大肠（dims 的 c_fecal_out 承载）
            outqualities={out_ref: WaterQuality(dict(quality.concentrations))},
            dims=dims,
            warnings=_warnings(p, channel, check),
            formula_ids=FORMULA_IDS,
        )
