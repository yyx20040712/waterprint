"""矿井水调节池计算实现：唯一计算源（KT-F1~F12 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KT-F1~F12（docs/norms/mine_water_tiaojiechi.md 起草表；
#   manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池宽 B/
#   池长 L=ceil(b_raw·l_raw, side_disc_step 0.5 m 档)；出水管 DN=
#   ceil(d_out_raw, length_disc_step 0.05 m 档)；π 经符号 pi 绑定
#   math.pi。零数值字面量。
# 【流量口径】调节容积/搅拌/出水管全部按平均日 flow.q_avg_daily
#   （×86400 换算已内联公式串；表"出水管按平均时均匀输出"口径——
#   均化功能的下游口径，与市政 TJ-F11 最高时溢流管口径差异=主线
#   取纯均化零超越，表单元信息节）。
# 【系数通道】factor.mine_tiaojiechi.*/removal.mine_tiaojiechi.* 经
#   ctx.params 投影面取值（app._unit_params 线感知投影，mine_ 限定
#   键空间）；缺键=领域异常。elevation_loss 键归高程链子系统（后续
#   批），本文件不消费。
# 【输出面（D2）】outflows=入流透传；dims=表水力结果全量 snake 键；
#   outqualities=入质×(1−removal.mod_default) 双指标（零去除键 0.0
#   穿流，乘式形态与市政 tiaojiechi 直接透传记档差异——数值等价）；
#   warnings=校核带越界（实际停留时间带/有效水深带/长宽比带+实际
#   调节容积≥需容积校核；param_key 归因+调节方向）；
#   formula_ids=实际求值公式号全量。
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
from waterprint.units_lib.mine_water.tiaojiechi.manifest import FORMULA_IDS, manifest

_UNIT_ID = "mine_water_tiaojiechi"
_HB = "给水排水设计手册（第 5 册 城镇排水）调节池停留时间法/防沉积搅拌功率密度常用带"
_HRT_BAND = (
    "factor.mine_tiaojiechi.hrt_band.min",
    "factor.mine_tiaojiechi.hrt_band.max",
)
_DEPTH_BAND = (
    "factor.mine_tiaojiechi.depth_band.min",
    "factor.mine_tiaojiechi.depth_band.max",
)
_RATIO_BAND = (
    "factor.mine_tiaojiechi.ratio_lb_band.min",
    "factor.mine_tiaojiechi.ratio_lb_band.max",
)
_STIR_DENSITY = "factor.mine_tiaojiechi.stir.power_density"
_OUT_VELOCITY = "factor.mine_tiaojiechi.overflow_velocity"
_PARAMS_POSITIVE = ("n", "t_reg", "h2", "ratio_lb", "side_disc_step", "length_disc_step")
_FACTORS_POSITIVE = (_STIR_DENSITY, _OUT_VELOCITY)


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
    """构造步长向上取整（KT-F4/F5/F10 的 0.5/0.05 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：分格数/时间/水深/长宽比/步长与搅拌·流速系数非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")
    for key in _FACTORS_POSITIVE:
        if _factor(params, key) <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 系数键 {key!r} 必须 > 0（搅拌功率密度/出水管流速物理域）"
            )


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（调节池单入单出语义）"
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


def _basin(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """KT-F1~F8：需调节容积/单格几何（B·L 0.5 m 档）/实际容积与停留时间。"""
    v_total = _apply(ctx, "KT-F1", {"q_avg_daily": flow.q_avg_daily, "t_reg": p["t_reg"]})
    v1 = _apply(ctx, "KT-F2", {"v_total": v_total, "n": p["n"]})
    a1 = _apply(ctx, "KT-F3", {"v1": v1, "h2": p["h2"]})
    b_raw = _apply(ctx, "KT-F4", {"a1": a1, "ratio_lb": p["ratio_lb"]})
    b = _ceil_step(b_raw, p["side_disc_step"])
    l_raw = _apply(ctx, "KT-F5", {"a1": a1, "B": b})
    length = _ceil_step(l_raw, p["side_disc_step"])
    a_act = _apply(ctx, "KT-F6", {"B": b, "L": length})
    v_act_total = _apply(ctx, "KT-F7", {"a_act": a_act, "h2": p["h2"], "n": p["n"]})
    return {
        "v_total": v_total,
        "v1": v1,
        "a1": a1,
        "b_raw": b_raw,
        "b": b,
        "l_raw": l_raw,
        "l": length,
        "a_act": a_act,
        "v_act_total": v_act_total,
        "t_reg_act": _apply(
            ctx, "KT-F8", {"v_act_total": v_act_total, "q_avg_daily": flow.q_avg_daily}
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(p: dict[str, float], basin: dict[str, float]) -> tuple[Warning, ...]:
    """校核带检查：实际停留时间/有效水深/长宽比/调节容积充足性。"""
    found: list[Warning] = []
    hrt = _band(p, _HRT_BAND)
    if not hrt[0] <= basin["t_reg_act"] <= hrt[1]:
        found.append(
            _warn(
                f"{_HB}；{_HRT_BAND[0]}~{_HRT_BAND[1]}",
                f"实际调节停留时间 = {basin['t_reg_act']:.4f} h 越出建议带"
                f" [{hrt[0]}, {hrt[1]}]——调节方向：t_reg（↑扩容）或 h2/n（↑加深加格）",
                "t_reg",
            )
        )
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= p["h2"] <= dep[1]:
        found.append(
            _warn(
                f"{_HB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"有效水深 h2 = {p['h2']:.4f} m 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：h2（半地下/地下式布置常用带内取值）",
                "h2",
            )
        )
    ratio = _band(p, _RATIO_BAND)
    if not ratio[0] <= p["ratio_lb"] <= ratio[1]:
        found.append(
            _warn(
                f"{_HB}；{_RATIO_BAND[0]}~{_RATIO_BAND[1]}",
                f"池长宽比 L/B = {p['ratio_lb']:.4f} 越出建议带"
                f" [{ratio[0]}, {ratio[1]}]——调节方向：ratio_lb（矩形池工程常用）",
                "ratio_lb",
            )
        )
    if basin["v_act_total"] < basin["v_total"]:
        found.append(
            _warn(
                f"{_HB}；KT-F7 调节容积校核（v_act_total ≥ v_total）",
                f"实际调节容积 = {basin['v_act_total']:.4f} m³ 低于需容积"
                f" {basin['v_total']:.4f} m³——调节方向：h2（↑加深）或 n（↑加格）",
                "h2",
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
    return _MineTiaojiechi()


@final
class _MineTiaojiechi:
    """矿井水调节池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KT-F1~F12 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        basin = _basin(ctx, p, flow)
        p_stir = _apply(
            ctx,
            "KT-F9",
            {"v_act_total": basin["v_act_total"], "w_stir": _factor(p, _STIR_DENSITY)},
        )
        d_out_raw = _apply(
            ctx,
            "KT-F10",
            {
                "q_avg_daily": flow.q_avg_daily,
                "pi": math.pi,
                "v_out": _factor(p, _OUT_VELOCITY),
            },
        )
        dn_out = _ceil_step(d_out_raw, p["length_disc_step"])
        h_total = _apply(
            ctx,
            "KT-F11",
            {"h_super": _factor(p, "factor.mine_tiaojiechi.superheight"), "h2": p["h2"]},
        )
        v_concrete = _apply(
            ctx,
            "KT-F12",
            {
                "a_act": basin["a_act"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.mine_tiaojiechi.wall_thickness_coef"),
            },
        )
        dims = {
            **basin,
            "p_stir": p_stir,
            "d_out_raw": d_out_raw,  # 离散前原值（DN 档审计面）
            "dn_out": dn_out,
            "h_total": h_total,
            "v_concrete": v_concrete,
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, basin),
            formula_ids=FORMULA_IDS,
        )
