"""V型滤池计算实现：唯一计算源（XL-F1~F19 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【公式组】XL-F1~F19（docs/norms/vxinglvchi.md 起草表；manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：单格宽 B/
#   长 L=ceil(b_raw·l_raw, side_disc_step 0.5 m 档)。零数值字面量。
# 【流量口径】过滤面积与冲洗强度按最高时 flow.q_design（含自用水系数
#   ×1.05 经 factor 键，XL-F1~F15）；冲洗耗水率按平均日 flow.q_avg_daily
#   复核（XL-F16/F17，×86400 已内联公式串）——四表口径逐字。
# 【系数通道】factor.vxinglvchi.*/removal.vxinglvchi.* 经 ctx.params
#   投影面取值（app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D2）】outflows=入流透传；dims=四表水力结果全量 snake 键；
#   outqualities=入质×(1−removal.mod_default) 三指标+NH3N/TN/TP 透传
#   （同 M1a/M2a2 形态）；warnings=校核带越界（正常滤速带/单格长宽比
#   带/滤层厚带/砂上水深带/过滤周期带+强制滤速单向上限——band 11~13
#   为典型带、低于下限=保守合格非越界，四表算例 9.4626<11 注"合格"
#   口径）；反冲耗水率≤5% 无 data 包键且被 selfuse_coef 覆盖（四表
#   XL-F17 注记）——dims 承载不设运行时警告（追认点）；formula_ids=
#   实际求值公式号全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import Final, final

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
from waterprint.units_lib.municipal.vxinglvchi.manifest import FORMULA_IDS, manifest

_UNIT_ID = "municipal_vxinglvchi"
_GB = "GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速）"
_HB = "给水排水设计手册（第 5 册 城镇排水）V 型滤池构造"
_VFILTER_BAND = (
    "factor.vxinglvchi.v_filter_band.min",
    "factor.vxinglvchi.v_filter_band.max",
)
_VFORCED_MAX = "factor.vxinglvchi.v_forced_band.max"
_RATIO_BAND = (
    "factor.vxinglvchi.cell_ratio_lb_band.min",
    "factor.vxinglvchi.cell_ratio_lb_band.max",
)
_DEPTH_BAND = (
    "factor.vxinglvchi.media.depth_band.min",
    "factor.vxinglvchi.media.depth_band.max",
)
_ABOVE_BAND = (
    "factor.vxinglvchi.water_above_band.min",
    "factor.vxinglvchi.water_above_band.max",
)
_CYCLE_BAND = (
    "factor.vxinglvchi.cycle_band.min",
    "factor.vxinglvchi.cycle_band.max",
)
_SELFUSE = "factor.vxinglvchi.selfuse_coef"
_W_AIR = "factor.vxinglvchi.wash.air"
_W_WATER_SIM = "factor.vxinglvchi.wash.water_sim"
_W_WATER = "factor.vxinglvchi.wash.water"
_W_SWEEP = "factor.vxinglvchi.wash.sweep"
_T_AIR = "factor.vxinglvchi.wash.t_air"
_T_SIM = "factor.vxinglvchi.wash.t_sim"
_T_WATER = "factor.vxinglvchi.wash.t_water"
# 强制滤速最小分格数（一格冲洗时其余格过全部流量——XL-F9 分母
# a_total_act−a_cell_act = a_cell_act×(n−1) 需 n≥2；宪法 §3 允许集内字面量）
_MIN_CELLS: Final[int] = 2
_PARAMS_POSITIVE = (
    "n",
    "v_filter",
    "ratio_lb",
    "h_water_above",
    "h_sand",
    "h_bottom",
    "t_cycle",
    "side_disc_step",
)
_FACTORS_POSITIVE = (_SELFUSE, _W_AIR, _W_WATER_SIM, _W_WATER, _W_SWEEP, _T_AIR, _T_SIM, _T_WATER)


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
    """构造步长向上取整（XL-F4/F5 的 0.5 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：分格数（强制滤速需 n≥2）/滤速/几何/周期/步长与
    冲洗强度·历时系数非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")
    if params["n"] < _MIN_CELLS:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'n' 必须 ≥ 2（一格冲洗时其余格过全部流量——"
            f"强制滤速 XL-F9 分母 a_total_act−a_cell_act 需 n≥2）：得到 {params['n']!r}"
        )
    for key in _FACTORS_POSITIVE:
        if _factor(params, key) <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 系数键 {key!r} 必须 > 0（自用水/冲洗强度/历时物理域）"
            )


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条"
            "（V 型滤池单入单出语义）"
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


def _filter(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """XL-F1~F9：过滤流量/需面积/分格几何（B·L 0.5 m 档）/正常·强制滤速校核。"""
    q_filter = _apply(
        ctx, "XL-F1", {"q_design": flow.q_design, "selfuse_coef": _factor(p, _SELFUSE)}
    )
    a_total_req = _apply(ctx, "XL-F2", {"q_filter": q_filter, "v_filter": p["v_filter"]})
    a_cell = _apply(ctx, "XL-F3", {"a_total_req": a_total_req, "n": p["n"]})
    b_raw = _apply(ctx, "XL-F4", {"a_cell": a_cell, "ratio_lb": p["ratio_lb"]})
    b = _ceil_step(b_raw, p["side_disc_step"])
    l_raw = _apply(ctx, "XL-F5", {"a_cell": a_cell, "B": b})
    length = _ceil_step(l_raw, p["side_disc_step"])
    a_cell_act = _apply(ctx, "XL-F6", {"B": b, "L": length})
    a_total_act = _apply(ctx, "XL-F7", {"a_cell_act": a_cell_act, "n": p["n"]})
    return {
        "q_filter": q_filter,
        "a_total_req": a_total_req,
        "a_cell": a_cell,
        "b_raw": b_raw,
        "b": b,
        "l_raw": l_raw,
        "l": length,
        "a_cell_act": a_cell_act,
        "a_total_act": a_total_act,
        "v_filter_act": _apply(ctx, "XL-F8", {"q_filter": q_filter, "a_total_act": a_total_act}),
        "v_forced_act": _apply(
            ctx,
            "XL-F9",
            {"q_filter": q_filter, "a_total_act": a_total_act, "a_cell_act": a_cell_act},
        ),
    }


def _wash(
    ctx: UnitContext,
    p: dict[str, float],
    flow: WaterFlow,
    filt: dict[str, float],
) -> dict[str, float]:
    """XL-F10~F17：气水反冲洗三阶段强度/单格次耗气耗水/日耗水率（平均日复核）。"""
    q_air = _apply(ctx, "XL-F10", {"a_cell_act": filt["a_cell_act"], "w_air": _factor(p, _W_AIR)})
    q_wash_sim = _apply(
        ctx, "XL-F11", {"a_cell_act": filt["a_cell_act"], "w_water_sim": _factor(p, _W_WATER_SIM)}
    )
    q_wash = _apply(
        ctx, "XL-F12", {"a_cell_act": filt["a_cell_act"], "w_water": _factor(p, _W_WATER)}
    )
    q_sweep = _apply(
        ctx, "XL-F13", {"a_cell_act": filt["a_cell_act"], "w_sweep": _factor(p, _W_SWEEP)}
    )
    v_air_per = _apply(
        ctx, "XL-F14", {"q_air": q_air, "t_air": _factor(p, _T_AIR), "t_sim": _factor(p, _T_SIM)}
    )
    v_wash_per = _apply(
        ctx,
        "XL-F15",
        {
            "q_wash_sim": q_wash_sim,
            "q_wash": q_wash,
            "q_sweep": q_sweep,
            "t_air": _factor(p, _T_AIR),
            "t_sim": _factor(p, _T_SIM),
            "t_water": _factor(p, _T_WATER),
        },
    )
    v_wash_daily = _apply(
        ctx, "XL-F16", {"v_wash_per": v_wash_per, "n": p["n"], "t_cycle": p["t_cycle"]}
    )
    return {
        "q_air": q_air,
        "q_wash_sim": q_wash_sim,
        "q_wash": q_wash,
        "q_sweep": q_sweep,
        "v_air_per": v_air_per,
        "v_wash_per": v_wash_per,
        "v_wash_daily": v_wash_daily,
        "ratio_wash": _apply(
            ctx, "XL-F17", {"v_wash_daily": v_wash_daily, "q_avg_daily": flow.q_avg_daily}
        ),
    }


def _depth(ctx: UnitContext, p: dict[str, float], filt: dict[str, float]) -> dict[str, float]:
    """XL-F18/F19：滤池总高（池深组成四段）与概算口径混凝土量。"""
    h_total = _apply(
        ctx,
        "XL-F18",
        {
            "h_super": _factor(p, "factor.vxinglvchi.superheight"),
            "h_water_above": p["h_water_above"],
            "h_sand": p["h_sand"],
            "h_bottom": p["h_bottom"],
        },
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "XL-F19",
            {
                "a_total_act": filt["a_total_act"],
                "h_total": h_total,
                "wall_coef": _factor(p, "factor.vxinglvchi.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(p: dict[str, float], filt: dict[str, float]) -> tuple[Warning, ...]:
    """校核带检查：正常滤速/长宽比/滤层厚/砂上水深/过滤周期带+强制滤速上限。"""
    found: list[Warning] = []
    vf = _band(p, _VFILTER_BAND)
    if not vf[0] <= filt["v_filter_act"] <= vf[1]:
        found.append(
            _warn(
                f"{_GB}；{_VFILTER_BAND[0]}~{_VFILTER_BAND[1]}",
                f"实际正常滤速 = {filt['v_filter_act']:.4f} 越出建议带"
                f" [{vf[0]}, {vf[1]}]——调节方向：v_filter（滤速）或 n（分格数）",
                "v_filter",
            )
        )
    vfm = _factor(p, _VFORCED_MAX)
    if filt["v_forced_act"] > vfm:
        found.append(
            _warn(
                f"{_GB}；{_VFORCED_MAX}（单向上限——带 11~13 为典型带，低于下限=保守合格）",
                f"一格冲洗时强制滤速 = {filt['v_forced_act']:.4f} 超上限 {vfm}"
                "——调节方向：n（↑加格）或 v_filter（↓滤速）",
                "n",
            )
        )
    ratio = _band(p, _RATIO_BAND)
    if not ratio[0] <= p["ratio_lb"] <= ratio[1]:
        found.append(
            _warn(
                f"{_HB}；{_RATIO_BAND[0]}~{_RATIO_BAND[1]}",
                f"单格长宽比 L/B = {p['ratio_lb']:.4f} 越出建议带"
                f" [{ratio[0]}, {ratio[1]}]——调节方向：ratio_lb（V 滤单格工程常用）",
                "ratio_lb",
            )
        )
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= p["h_sand"] <= dep[1]:
        found.append(
            _warn(
                f"{_GB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"均质滤料层厚 = {p['h_sand']:.4f} m 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：h_sand（GB 50013-2018 §9.5 均质滤料）",
                "h_sand",
            )
        )
    above = _band(p, _ABOVE_BAND)
    if not above[0] <= p["h_water_above"] <= above[1]:
        found.append(
            _warn(
                f"{_HB}；{_ABOVE_BAND[0]}~{_ABOVE_BAND[1]}",
                f"砂上水深 = {p['h_water_above']:.4f} m 越出建议带"
                f" [{above[0]}, {above[1]}]——调节方向：h_water_above（恒水位过滤）",
                "h_water_above",
            )
        )
    cyc = _band(p, _CYCLE_BAND)
    if not cyc[0] <= p["t_cycle"] <= cyc[1]:
        found.append(
            _warn(
                f"{_HB}；{_CYCLE_BAND[0]}~{_CYCLE_BAND[1]}",
                f"过滤周期 = {p['t_cycle']:.4f} h 越出建议带"
                f" [{cyc[0]}, {cyc[1]}]——调节方向：t_cycle（V 滤长周期档）",
                "t_cycle",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：三指标 ×(1−removal.mod_default)，其余指标透传（同 M1a 形态）。"""
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
    return _Vxinglvchi()


@final
class _Vxinglvchi:
    """V 型滤池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """XL-F1~F19 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        filt = _filter(ctx, p, flow)
        wash = _wash(ctx, p, flow, filt)
        depth = _depth(ctx, p, filt)
        dims = {**filt, **wash, **depth}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, filt),
            formula_ids=FORMULA_IDS,
        )
