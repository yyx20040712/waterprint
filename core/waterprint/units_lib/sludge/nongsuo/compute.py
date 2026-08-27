"""污泥浓缩计算实现：唯一计算源（NS-F1~NS-F12 全经 registry.apply 求值）。

输入:  UnitContext（上游 SLUDGE 量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（SLUDGE 底流出流三量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】NS-F1~NS-F12（docs/norms/sludge_nongsuo.md 起草表；
#   manifest.py 登记）——重力浓缩双主线（固体通量面积式+浓缩时间
#   面积式取大——erchunchi max 先例）+ 截留 DS 守恒链（底流/上清液
#   分流 NS-F7~F10）+ 圆形池构造/概算。
# 【DSL 收口】池径 0.5 m 档 ceil 在本文件收口（SIDE_DISC_STEP=
#   manifest 常量；DSL 无 ceil）。零数值字面量。
# 【入流装配】恰一入边且为 SLUDGE（shusong 同款）；入流三量
#   ×SECS_PER_DAY 回工程口径，底流出流回契约口径。
# 【回流口（Q1 未裁）】sup 上清液端口=声明先行（manifest ports
#   recycle=True），默认关=不连边——compute 不产 sup 股（打开后
#   双向守恒入图迭代归追认批），上清液量走 dims q_sup/ds_sup 回显。
# 【三量链回显】dims 加 q_in/ds_in/p_in/q_out/p_out（ds_out 即表键；
#   q_out=底流 q_thick、p_out=参数值）——进出六量全回显。
# 【系数通道】factor.nongsuo.* 12 键经 ctx.params 投影面取值（裸
#   短名投影）；缺键=领域异常。elevation_loss 键归高程链子系统，
#   本文件不消费。
# 【输出面（D2）】outflows=底流一口 SLUDGE 三量（q_thick/ds_out/
#   p_out）；dims=表结果 13 项+回显 5 项；outqualities={}；warnings=
#   四带校核（实际固体负荷带/浓缩时间带/有效水深带/底流含水率带；
#   param_key 归因+调节方向）；formula_ids=NS-F1~F12 全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import final

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)
from waterprint.registry import formulas
from waterprint.units_lib.sludge.nongsuo.manifest import (
    FORMULA_IDS,
    SECS_PER_DAY,
    SIDE_DISC_STEP,
    manifest,
)

_UNIT_ID = "sludge_nongsuo"
_GB = "GB 50014-2021 §8（污泥章——重力浓缩，条号待核对）"
_HB5 = "给水排水设计手册（第 5 册 城镇排水）污泥浓缩章（常用带）"
_SOLID_BAND = (
    "factor.nongsuo.solid_load_band.min",
    "factor.nongsuo.solid_load_band.max",
)
_TIME_BAND = (
    "factor.nongsuo.time_band.min",
    "factor.nongsuo.time_band.max",
)
_DEPTH_BAND = (
    "factor.nongsuo.depth_band.min",
    "factor.nongsuo.depth_band.max",
)
_MOISTURE_BAND = (
    "factor.nongsuo.moisture_out_band.min",
    "factor.nongsuo.moisture_out_band.max",
)
_ETA_CAPTURE = "factor.nongsuo.eta_capture"
_SUPER = "factor.nongsuo.superheight"
_WALL = "factor.nongsuo.wall_thickness_coef"
_PARAMS_POSITIVE = (
    "q_solid",
    "t_thicken",
    "h_eff",
    "n",
    "h_cone",
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


def _band(params: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(params, keys[0]), _factor(params, keys[1])


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：负荷/时间/水深/池数/锥底非正一律拒；p_out 开域 (0,1)。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    p_out = params.get("p_out")
    if p_out is None or not 0 < p_out < 1:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'p_out' 必须在开区间 (0,1)"
            f"（小数含水率——闭边界 1 使底流换算除零）：得到 {p_out!r}"
        )


def _inflow(ctx: UnitContext) -> SludgeFlow:
    """入流装配：恰一入边且为 SLUDGE（多入/缺入/水线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], SludgeFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 SLUDGE 入边：得到 {len(refs)} 条"
            "（浓缩池单入单出语义——上清液口为出流非入流）"
        )
    flow = ctx.inflows[refs[0]]
    assert isinstance(flow, SludgeFlow)  # 上行守卫已收窄，窄化供类型面
    return flow


def _apply(ctx: UnitContext, formula_id: str, bindings: dict[str, float]) -> float:
    """apply 薄封装：统一携带 (unit_id, condition_key) 与 trace sink。"""
    return formulas.apply(
        formula_id,
        bindings,
        (ctx.unit_id, ConditionSet.key(ctx.condition)),
        sink=ctx.trace,
    )


def _area(
    ctx: UnitContext, p: dict[str, float], q_wet: float, ds_in: float
) -> dict[str, float]:
    """NS-F1~F6：双主线面积取大+单池面积+池径（0.5 m 档）+实际负荷校核。"""
    a_load = _apply(ctx, "NS-F1", {"ds_in": ds_in, "q_solid": p["q_solid"]})
    a_time = _apply(
        ctx,
        "NS-F2",
        {"q_wet": q_wet, "t_thicken": p["t_thicken"], "h_eff": p["h_eff"]},
    )
    a_req = _apply(ctx, "NS-F3", {"a_load": a_load, "a_time": a_time})
    a_single = _apply(ctx, "NS-F4", {"a_req": a_req, "n": p["n"]})
    d_raw = _apply(ctx, "NS-F5", {"a_single": a_single, "pi": math.pi})
    if SIDE_DISC_STEP <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {SIDE_DISC_STEP!r}"
        )
    return {
        "a_load": a_load,
        "a_time": a_time,
        "a_req": a_req,
        "a_single": a_single,
        "d_raw": d_raw,
        # 池径 0.5 m 档向上取整（表 NS-F5 口径——DSL 无 ceil，本文件收口）
        "d": math.ceil(d_raw / SIDE_DISC_STEP) * SIDE_DISC_STEP,
        "q_solid_act": _apply(ctx, "NS-F6", {"ds_in": ds_in, "a_req": a_req}),
    }


def _balance(
    ctx: UnitContext, p: dict[str, float], q_wet: float, ds_in: float
) -> dict[str, float]:
    """NS-F7~F10：截留 DS 守恒链（底流三量链+上清液分流）。"""
    ds_out = _apply(ctx, "NS-F7", {"ds_in": ds_in, "eta_capture": _factor(p, _ETA_CAPTURE)})
    q_thick = _apply(ctx, "NS-F8", {"ds_out": ds_out, "p_out": p["p_out"]})
    return {
        "ds_out": ds_out,
        "q_thick": q_thick,
        "q_sup": _apply(ctx, "NS-F9", {"q_wet": q_wet, "q_thick": q_thick}),
        "ds_sup": _apply(ctx, "NS-F10", {"ds_in": ds_in, "ds_out": ds_out}),
    }


def _structure(ctx: UnitContext, p: dict[str, float], a_single: float) -> dict[str, float]:
    """NS-F11~F12：池总高与概算混凝土量。"""
    h_total = _apply(
        ctx,
        "NS-F11",
        {
            "h_super": _factor(p, _SUPER),
            "h_eff": p["h_eff"],
            "h_cone": p["h_cone"],
        },
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "NS-F12",
            {
                "a_single": a_single,
                "h_total": h_total,
                "wall_coef": _factor(p, _WALL),
                "n": p["n"],
            },
        ),
    }


def _warnings(
    p: dict[str, float], area: dict[str, float]
) -> tuple[Warning, ...]:
    """四带校核：实际固体负荷带/浓缩时间带/有效水深带/底流含水率带。"""
    found: list[Warning] = []
    solid = _band(p, _SOLID_BAND)
    if not solid[0] <= area["q_solid_act"] <= solid[1]:
        found.append(
            Warning(
                severity=Severity.WARN,
                source=f"{_GB}；{_SOLID_BAND[0]}~{_SOLID_BAND[1]}",
                message=(
                    f"实际固体负荷 q_solid_act = {area['q_solid_act']:.4f}"
                    f" kgDS/(m²·d) 越出建议带 [{solid[0]}, {solid[1]}]"
                    "——调节方向：q_solid（双主线取大后负荷复核）"
                ),
                param_key="q_solid",
            )
        )
    time_band = _band(p, _TIME_BAND)
    if not time_band[0] <= p["t_thicken"] <= time_band[1]:
        found.append(
            Warning(
                severity=Severity.WARN,
                source=f"{_GB}；{_TIME_BAND[0]}~{_TIME_BAND[1]}",
                message=(
                    f"浓缩时间 t_thicken = {p['t_thicken']:.4f} h 越出建议带"
                    f" [{time_band[0]}, {time_band[1]}]——调节方向：t_thicken（带内取值）"
                ),
                param_key="t_thicken",
            )
        )
    depth = _band(p, _DEPTH_BAND)
    if not depth[0] <= p["h_eff"] <= depth[1]:
        found.append(
            Warning(
                severity=Severity.WARN,
                source=f"{_GB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                message=(
                    f"有效水深 h_eff = {p['h_eff']:.4f} m 越出建议带"
                    f" [{depth[0]}, {depth[1]}]——调节方向：h_eff（带内取值）"
                ),
                param_key="h_eff",
            )
        )
    moisture = _band(p, _MOISTURE_BAND)
    if not moisture[0] <= p["p_out"] <= moisture[1]:
        found.append(
            Warning(
                severity=Severity.WARN,
                source=f"{_HB5}；{_MOISTURE_BAND[0]}~{_MOISTURE_BAND[1]}",
                message=(
                    f"底流含水率 p_out = {p['p_out']:.4f} 越出建议带"
                    f" [{moisture[0]}, {moisture[1]}]——调节方向：p_out（带内取值）"
                ),
                param_key="p_out",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _SludgeNongsuo()


@final
class _SludgeNongsuo:
    """污泥浓缩 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """NS-F1~F12 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        inflow = _inflow(ctx)
        q_wet = inflow.q_wet * SECS_PER_DAY
        ds_in = inflow.ds * SECS_PER_DAY
        p_in = inflow.moisture
        area = _area(ctx, p, q_wet, ds_in)
        balance = _balance(ctx, p, q_wet, ds_in)
        structure = _structure(ctx, p, area["a_single"])
        dims = {
            "q_in": q_wet,
            "ds_in": ds_in,
            "p_in": p_in,
            **area,
            **balance,
            **structure,
            "q_out": balance["q_thick"],
            "p_out": p["p_out"],
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={
                out_ref: SludgeFlow(
                    q_wet=balance["q_thick"] / SECS_PER_DAY,
                    ds=balance["ds_out"] / SECS_PER_DAY,
                    moisture=p["p_out"],
                )
            },
            outqualities={},
            dims=dims,
            warnings=_warnings(p, area),
            formula_ids=FORMULA_IDS,
        )
