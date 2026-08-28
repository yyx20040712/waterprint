"""辐流初沉池计算实现：唯一计算源（CC-F1~F18 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【公式组】CC-F1~F18（docs/norms/chuchenchi.md 起草表；manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池径 D=
#   ceil(d_raw, dia_disc_step 0.5 m 档)/d_center/h4/h_total=ceil(raw,
#   length_disc_step 0.1 m 档)；π 经符号 pi 绑定 math.pi。零数值字面量。
# 【DSL 单输出导出量】q1（=q_design/n，CC-F8/F9 单池秒流量）与
#   ss_out（=ss_in×(1−removal.chuchenchi.ss)，CC-F10 入参）在 compute
#   以符号算术合成——零字面量、无新工程常数（registry 单输出限制导出面）。
# 【系数通道】factor.chuchenchi.*/removal.chuchenchi.* 经 ctx.params
#   投影面取值（app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【流量口径】池体水力按最高时 flow.q_design（CC-F1~F9）；排泥按平均日
#   flow.q_avg_daily（CC-F10~F12，×86400 已内联公式串）——三表口径逐字。
# 【输出面（D3）】outflows=入流透传+sludge_out SLUDGE 产股（GOLDEN4a D3——
#   全厂口径投影与 moisture 同源注记见 manifest ports 注）；
#   outqualities=入质×(1−removal.mod_default) 三指标+NH3N/TN/TP 透传；
#   warnings=校核带越界（表面负荷/有效水深/径深比/堰负荷/排泥周期带
#   [0.2.1 键]+贮泥容积 v_storage≥v_need；param_key 归因+双向调节方向，
#   堰负荷越界归堰构造口径注记）；formula_ids=实际求值公式号全量。
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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)
from waterprint.registry import formulas
from waterprint.units_lib.municipal.chuchenchi.manifest import (
    FORMULA_IDS,
    SECS_PER_DAY,
    manifest,
)

_UNIT_ID = "municipal_chuchenchi"
_NORM = "GB 50014-2021 §6.5（沉淀池）"
_SURFACE_BAND = (
    "factor.chuchenchi.surface_load_band.min",
    "factor.chuchenchi.surface_load_band.max",
)
_DEPTH_BAND = ("factor.chuchenchi.depth_band.min", "factor.chuchenchi.depth_band.max")
_RATIO_BAND = (
    "factor.chuchenchi.ratio_dh2_band.min",
    "factor.chuchenchi.ratio_dh2_band.max",
)
_WEIR_MAX = "factor.chuchenchi.weir_load.max"
_CYCLE_BAND = (
    "factor.chuchenchi.sludge_cycle_band.min",
    "factor.chuchenchi.sludge_cycle_band.max",
)
_PARAMS_POSITIVE = (
    "n",
    "q_prime",
    "t_settle",
    "t_sludge",
    "r1",
    "r2",
    "h5",
    "dia_disc_step",
    "length_disc_step",
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
    """构造步长向上取整（CC-F3/F8/F14/F17 的 0.5/0.1 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/负荷/时间/泥斗几何/步长非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（初沉池单入单出语义）"
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
    """CC-F1~F7：单池流量/需蓄面积/池径/实际负荷/有效水深/径深比。"""
    q1h = _apply(ctx, "CC-F1", {"q_design": flow.q_design, "n": p["n"]})
    f_req = _apply(ctx, "CC-F2", {"q1h": q1h, "q_prime": p["q_prime"]})
    d_raw = _apply(ctx, "CC-F3", {"f_req": f_req, "pi": math.pi})
    d = _ceil_step(d_raw, p["dia_disc_step"])
    f_act = _apply(ctx, "CC-F4", {"pi": math.pi, "D": d})
    q_prime_act = _apply(ctx, "CC-F5", {"q1h": q1h, "f_act": f_act})
    h2 = _apply(ctx, "CC-F6", {"q_prime_act": q_prime_act, "t_settle": p["t_settle"]})
    return {
        "q1": flow.q_design / p["n"],  # DSL 单输出导出量（CC-F8/F9 入参）
        "q1h": q1h,
        "f_req": f_req,
        "d_raw": d_raw,
        "d": d,
        "f_act": f_act,
        "q_prime_act": q_prime_act,
        "h2": h2,
        "ratio_dh2": _apply(ctx, "CC-F7", {"D": d, "h2": h2}),
    }


def _center_weir(
    ctx: UnitContext, p: dict[str, float], basin: dict[str, float]
) -> dict[str, float]:
    """CC-F8/F9：中心配水筒径（0.1 m 档）与周边双侧出水堰负荷。"""
    d_center = _ceil_step(
        _apply(
            ctx,
            "CC-F8",
            {
                "q1": basin["q1"],
                "pi": math.pi,
                "v_center": _factor(p, "factor.chuchenchi.center_velocity"),
            },
        ),
        p["length_disc_step"],
    )
    return {
        "d_center": d_center,
        "q_weir": _apply(ctx, "CC-F9", {"q1": basin["q1"], "pi": math.pi, "D": basin["d"]}),
    }


def _sludge(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, ss_in: float
) -> dict[str, float]:
    """CC-F10~F12：单池干泥量/湿泥量/贮泥需容积（平均日口径）。"""
    ss_out = ss_in * (1 - _factor(p, "removal.chuchenchi.ss.mod_default"))
    s_dry_1 = _apply(
        ctx,
        "CC-F10",
        {"q_avg_daily": flow.q_avg_daily, "ss_in": ss_in, "ss_out": ss_out, "n": p["n"]},
    )
    s_wet_1 = _apply(
        ctx,
        "CC-F11",
        {"s_dry_1": s_dry_1, "p_moisture": _factor(p, "factor.chuchenchi.sludge.moisture")},
    )
    return {
        "ss_out": ss_out,
        "s_dry_1": s_dry_1,
        "s_wet_1": s_wet_1,
        "v_need": _apply(ctx, "CC-F12", {"s_wet_1": s_wet_1, "t_sludge": p["t_sludge"]}),
    }


def _hopper(ctx: UnitContext, p: dict[str, float], basin: dict[str, float]) -> dict[str, float]:
    """CC-F13~F16：泥斗/池底坡锥台/污泥区总容积（h4 0.1 m 档）。"""
    v1 = _apply(ctx, "CC-F13", {"pi": math.pi, "h5": p["h5"], "r1": p["r1"], "r2": p["r2"]})
    h4 = _ceil_step(
        _apply(
            ctx,
            "CC-F14",
            {
                "i_slope": _factor(p, "factor.chuchenchi.bottom_slope"),
                "D": basin["d"],
                "r1": p["r1"],
            },
        ),
        p["length_disc_step"],
    )
    v2 = _apply(ctx, "CC-F15", {"pi": math.pi, "h4": h4, "D": basin["d"], "r1": p["r1"]})
    return {
        "v1_hopper": v1,
        "h4": h4,
        "v2_cone": v2,
        "v_storage": _apply(ctx, "CC-F16", {"v1_hopper": v1, "v2_cone": v2}),
    }


def _depth(
    ctx: UnitContext, p: dict[str, float], basin: dict[str, float], hopper: dict[str, float]
) -> dict[str, float]:
    """CC-F17/F18：池总高（0.1 m 档）与概算口径混凝土量。"""
    h_total = _ceil_step(
        _apply(
            ctx,
            "CC-F17",
            {
                "h_super": _factor(p, "factor.chuchenchi.superheight"),
                "h2": basin["h2"],
                "h_buf": _factor(p, "factor.chuchenchi.buffer_h3"),
                "h4": hopper["h4"],
                "h5": p["h5"],
            },
        ),
        p["length_disc_step"],
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "CC-F18",
            {
                "pi": math.pi,
                "D": basin["d"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.chuchenchi.wall_thickness_coef"),
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
    p: dict[str, float],
    basin: dict[str, float],
    center: dict[str, float],
    sludge: dict[str, float],
    hopper: dict[str, float],
) -> tuple[Warning, ...]:
    """校核带检查：表面负荷/有效水深/径深比/堰负荷/排泥周期/贮泥容积。"""
    found: list[Warning] = []
    surf = _band(p, _SURFACE_BAND)
    if not surf[0] <= basin["q_prime_act"] <= surf[1]:
        found.append(
            _warn(
                f"{_NORM}；{_SURFACE_BAND[0]}~{_SURFACE_BAND[1]}",
                f"实际表面水力负荷 = {basin['q_prime_act']:.4f} 越出建议带"
                f" [{surf[0]}, {surf[1]}]——调节方向：q_prime（负荷）或 n（池数）",
                "q_prime",
            )
        )
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= basin["h2"] <= dep[1]:
        found.append(
            _warn(
                f"{_NORM}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"有效水深 h2 = {basin['h2']:.4f} 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：t_settle（↑加深）或 q_prime（↓加深）",
                "t_settle",
            )
        )
    ratio = _band(p, _RATIO_BAND)
    if not ratio[0] <= basin["ratio_dh2"] <= ratio[1]:
        found.append(
            _warn(
                f"给水排水设计手册（第 5 册）；{_RATIO_BAND[0]}~{_RATIO_BAND[1]}",
                f"径深比 D/h2 = {basin['ratio_dh2']:.4f} 越出建议带"
                f" [{ratio[0]}, {ratio[1]}]——调节方向：q_prime（影响 D）或 t_settle（影响 h2）",
                "q_prime",
            )
        )
    weir = _factor(p, _WEIR_MAX)
    if center["q_weir"] > weir:
        found.append(
            _warn(
                f"{_NORM}；{_WEIR_MAX}",
                f"出水堰负荷 = {center['q_weir']:.4f} 超上限 {weir}——堰构造口径注记："
                "默认周边双侧出水堰（L=2π(D−1)），单侧口径敏感性见 docs/norms/chuchenchi.md"
                "（堰构造口径待领域专家追认）",
                None,
            )
        )
    cycle = _band(p, _CYCLE_BAND)
    if not cycle[0] <= p["t_sludge"] <= cycle[1]:
        found.append(
            _warn(
                f"{_NORM}；{_CYCLE_BAND[0]}~{_CYCLE_BAND[1]}（0.2.1 键）",
                f"排泥周期 = {p['t_sludge']:.4f} 越出建议带"
                f" [{cycle[0]}, {cycle[1]}]——调节方向：t_sludge（↑泥量增大/↓贮泥更频）",
                "t_sludge",
            )
        )
    if hopper["v_storage"] < sludge["v_need"]:
        found.append(
            _warn(
                "给水排水设计手册（第 5 册）；CC-F16 贮泥容积校核（v_storage ≥ v_need）",
                f"污泥区容积 = {hopper['v_storage']:.4f} m³ 低于需容积"
                f" {sludge['v_need']:.4f} m³——调节方向：t_sludge（↓）或泥斗构造 h5/r1（↑）",
                "t_sludge",
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
    return _Chuchenchi()


@final
class _Chuchenchi:
    """辐流初沉池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """CC-F1~F18 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        ss_in = quality.SS
        if ss_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 SS 浓度（CC-F10 排泥量计算前提，GR-09）"
            )
        basin = _basin(ctx, p, flow)
        center = _center_weir(ctx, p, basin)
        sludge = _sludge(ctx, p, flow, ss_in)
        hopper = _hopper(ctx, p, basin)
        depth = _depth(ctx, p, basin, hopper)
        dims = {**basin, **center, **sludge, **hopper, **depth}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        sludge_ref = PortRef(unit_id=ctx.unit_id, port_id="sludge_out")
        return UnitResult(
            outflows={
                out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz),
                # GOLDEN4a D3 产股：无条件产股（nongsuo sup 先例同构）——
                # 全厂口径注记见 manifest ports 注。
                sludge_ref: SludgeFlow(
                    q_wet=sludge["s_wet_1"] * p["n"] / SECS_PER_DAY,
                    ds=sludge["s_dry_1"] * p["n"] / SECS_PER_DAY,
                    moisture=_factor(p, "factor.chuchenchi.sludge.moisture"),
                ),
            },
            outqualities={
                out_ref: _out_quality(p, quality),
                sludge_ref: WaterQuality({}),  # 空 WaterQuality 单位元（R5/GR-04）
            },
            dims=dims,
            warnings=_warnings(p, basin, center, sludge, hopper),
            formula_ids=FORMULA_IDS,
        )
