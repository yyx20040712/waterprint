"""旋流沉砂池计算实现：唯一计算源（CS-F1~F18 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【公式组】CS-F1~F18（docs/norms/chenshachi.md 签字表；manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池径 D/
#   h_cyl/总高 H = ceil(raw, length_disc_step)（步长=manifest 参数）；
#   tanθ 预处理值以符号传入；π 经符号 pi 绑定 math.pi。零数值字面量。
# 【DSL 单输出导出量】Q₁h（=Q₁×sec_per_hour，参数化时换算）/A渠（=Q₁/
#   v渠，4-26 子式）/Q_wet（=V_sand×n）/V_storage（=V_cone+A_upper·h_cyl，
#   F12 容积合成校核量）/宽深比（=B渠/h渠）在 compute 以符号算术合成
#   ——零字面量、无新工程常数（记档：registry 单输出限制的导出面）。
# 【系数通道】factor.chenshachi.*/removal.chenshachi.* 经 ctx.params
#   投影面取值（app._unit_params，D4 裁决）；缺键=领域异常。
# 【输出面（D5）】outflows=入流透传；dims=三表水力结果全量 snake 键；
#   outqualities=入质×(1−removal.mod_default) 三指标+NH3N/TN/TP 透传；
#   warnings=四条校核带越界（surface_load/h2/ratio_dh2/retention，
#   factor.chenshachi.*_band；h渠≥0.2 与 B/h 带 1.0~3.0 无 data 包键
#   ——挂账不实现）；formula_ids=实际求值公式号全量；trace=apply 落迹。
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
from waterprint.units_lib.municipal.chenshachi.manifest import FORMULA_IDS, manifest

_UNIT_ID = "municipal_chenshachi"
_NORM = "GB 50014-2021 §6.4（条文号待核对原文）"
_SURFACE_BAND = (
    "factor.chenshachi.surface_load_band.min",
    "factor.chenshachi.surface_load_band.max",
)
_H2_BAND = ("factor.chenshachi.h2_band.min", "factor.chenshachi.h2_band.max")
_RATIO_BAND = (
    "factor.chenshachi.ratio_dh2_band.min",
    "factor.chenshachi.ratio_dh2_band.max",
)
_RETENTION_BAND = (
    "factor.chenshachi.retention_band.min",
    "factor.chenshachi.retention_band.max",
)


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值（D4）：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——D4 装配裁决）"
        )
    return float(value)


def _ceil_step(value: float, step: float) -> float:
    """构造步长向上取整（三表 CS-F2/F12/F13 的 0.1m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的 length_disc_step 必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/负荷/停留/流速/渠宽/步长非正一律拒。"""
    for key in ("n", "q_surf", "t_retention", "t_clean", "theta", "b_channel", "v_channel"):
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（沉砂池单入单出语义）"
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
    """CS-F1~F6：单池流量/池径/有效水深/径深比/有效容积/实际停留时间。"""
    q1 = _apply(ctx, "CS-F1", {"q_design": flow.q_design, "n": p["n"]})
    d = _ceil_step(
        _apply(
            ctx,
            "CS-F2",
            {
                "q1": q1,
                "sec_per_hour": p["sec_per_hour"],
                "pi": math.pi,
                "q_surf": p["q_surf"],
            },
        ),
        p["length_disc_step"],
    )
    h2 = _apply(ctx, "CS-F3", {"q_surf": p["q_surf"], "t_retention": p["t_retention"]})
    v_eff = _apply(ctx, "CS-F5", {"pi": math.pi, "d": d, "h2": h2})
    return {
        "q1": q1,
        "q1h": q1 * p["sec_per_hour"],  # DSL 单输出导出量（F1 第二等式）
        "d": d,
        "h2": h2,
        "ratio_dh2": _apply(ctx, "CS-F4", {"d": d, "h2": h2}),
        "v_eff": v_eff,
        "t_actual": _apply(ctx, "CS-F6", {"v_eff": v_eff, "q1": q1}),
    }


def _hopper(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, basin: dict[str, float]
) -> dict[str, float]:
    """CS-F7~F13：沉砂量/砂斗组容积/圆柱段/总高（含 V_storage 导出量）。"""
    v_sand = _apply(
        ctx,
        "CS-F7",
        {
            "q_avg_daily": flow.q_avg_daily,
            "x_sand": _factor(p, "factor.chenshachi.sand_yield_x"),
            "n": p["n"],
        },
    )
    v_hopper = _apply(
        ctx,
        "CS-F8",
        {
            "v_sand": v_sand,
            "t_clean": p["t_clean"],
            "safety": _factor(p, "factor.chenshachi.hopper.safety"),
        },
    )
    d = basin["d"]
    d_upper = _apply(
        ctx,
        "CS-F9",
        {"upper_ratio": _factor(p, "factor.chenshachi.hopper_upper_ratio"), "d": d},
    )
    tan_theta = math.tan(math.radians(p["theta"]))
    h4 = _apply(ctx, "CS-F10", {"d_upper": d_upper, "d_r": p["d_r"], "tan_theta": tan_theta})
    v_cone = _apply(
        ctx,
        "CS-F11",
        {"pi": math.pi, "h4": h4, "d_upper": d_upper, "d_r": p["d_r"]},
    )
    h_cyl = _ceil_step(
        _apply(
            ctx,
            "CS-F12",
            {"v_hopper": v_hopper, "v_cone": v_cone, "pi": math.pi, "d_upper": d_upper},
        ),
        p["length_disc_step"],
    )
    h_total = _ceil_step(
        _apply(
            ctx,
            "CS-F13",
            {
                "h1_super": _factor(p, "factor.chenshachi.superheight"),
                "h2": basin["h2"],
                "h3_buffer": _factor(p, "factor.chenshachi.buffer_h3"),
                "h4": h4,
                "h_cyl": h_cyl,
            },
        ),
        p["length_disc_step"],
    )
    upper_area = math.pi * (d_upper / 2) ** 2
    return {
        "v_sand": v_sand,
        "v_hopper": v_hopper,
        "d_upper": d_upper,
        "h4": h4,
        "v_cone": v_cone,
        "h_cyl": h_cyl,
        "v_storage": v_cone + upper_area * h_cyl,  # F12 容积合成校核量
        "h_total": h_total,
    }


def _channel(ctx: UnitContext, p: dict[str, float], basin: dict[str, float]) -> dict[str, float]:
    """CS-F14~F16：进水渠水深/直段长/出水渠宽（含 A渠/宽深比导出量）。"""
    h_channel = _apply(
        ctx,
        "CS-F14",
        {"q1": basin["q1"], "v_channel": p["v_channel"], "b_channel": p["b_channel"]},
    )
    return {
        "a_channel": basin["q1"] / p["v_channel"],  # 4-26 子式导出量
        "h_channel": h_channel,
        "ratio_bh": p["b_channel"] / h_channel,
        "l_straight": _apply(
            ctx,
            "CS-F15",
            {
                "straight_mult": _factor(p, "factor.chenshachi.channel.straight_mult"),
                "b_channel": p["b_channel"],
                "straight_min": _factor(p, "factor.chenshachi.channel.straight_min"),
            },
        ),
        "b_outlet": _apply(
            ctx,
            "CS-F16",
            {
                "outlet_mult": _factor(p, "factor.chenshachi.channel.outlet_mult"),
                "b_channel": p["b_channel"],
            },
        ),
    }


def _sludge(
    ctx: UnitContext, p: dict[str, float], hopper: dict[str, float], h_total: float
) -> dict[str, float]:
    """CS-F17/F18：沉砂污泥口 DS（含 Q_wet 导出量）与混凝土量。"""
    return {
        "q_wet": hopper["v_sand"] * p["n"],  # F17 全厂湿砂量导出量
        "ds_grit": _apply(
            ctx,
            "CS-F17",
            {
                "v_sand": hopper["v_sand"],
                "moisture": _factor(p, "factor.chenshachi.grit.moisture"),
                "grit_density": _factor(p, "factor.chenshachi.grit.density"),
                "n": p["n"],
            },
        ),
        "v_concrete": _apply(
            ctx,
            "CS-F18",
            {
                "pi": math.pi,
                "d": hopper["d"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.chenshachi.wall_thickness_coef"),
            },
        ),
    }


def _band_warning(
    param_key: str,
    source: str,
    quantity: str,
    value: float,
    band: tuple[float, float],
) -> Warning:
    """单条校核带越界警告（severity=WARN，param_key=field_id，GR 口径）。"""
    return Warning(
        severity=Severity.WARN,
        source=source,
        message=(
            f"{quantity} = {value:.4f} 越出建议带 [{band[0]}, {band[1]}]"
            f"（参数 {param_key}——调节表面负荷/停留时间设计值）"
        ),
        param_key=param_key,
    )


def _warnings(p: dict[str, float], basin: dict[str, float]) -> tuple[Warning, ...]:
    """校核带检查：表面负荷/有效水深/径深比/实际停留时间（三表 CS 带）。"""
    found: list[Warning] = []
    q_low = _factor(p, _SURFACE_BAND[0])
    q_high = _factor(p, _SURFACE_BAND[1])
    h2_low = _factor(p, _H2_BAND[0])
    h2_high = _factor(p, _H2_BAND[1])
    r_low = _factor(p, _RATIO_BAND[0])
    r_high = _factor(p, _RATIO_BAND[1])
    t_low = _factor(p, _RETENTION_BAND[0])
    t_high = _factor(p, _RETENTION_BAND[1])
    if not q_low <= p["q_surf"] <= q_high:
        found.append(
            _band_warning(
                "q_surf",
                f"{_NORM}；{_SURFACE_BAND[0]}~{_SURFACE_BAND[1]}",
                "表面负荷 m3/(m2.h)",
                p["q_surf"],
                (q_low, q_high),
            )
        )
    if not h2_low <= basin["h2"] <= h2_high:
        found.append(
            _band_warning(
                "t_retention",
                f"{_NORM}；{_H2_BAND[0]}~{_H2_BAND[1]}",
                "有效水深 m",
                basin["h2"],
                (h2_low, h2_high),
            )
        )
    if not r_low <= basin["ratio_dh2"] <= r_high:
        found.append(
            Warning(
                severity=Severity.WARN,
                source=f"{_NORM}；{_RATIO_BAND[0]}~{_RATIO_BAND[1]}",
                message=(
                    f"径深比 D/h2 = {basin['ratio_dh2']:.4f} 越出建议带"
                    f" [{r_low}, {r_high}]（参数 q_surf——"
                    "调节方向：表面负荷 q_surf（影响 D）或停留时间"
                    " t_retention（影响 h2））"
                ),
                param_key="q_surf",
            )
        )
    if not t_low <= basin["t_actual"] <= t_high:
        found.append(
            _band_warning(
                "t_retention",
                f"{_NORM}；{_RETENTION_BAND[0]}~{_RETENTION_BAND[1]}",
                "实际停留时间 s",
                basin["t_actual"],
                (t_low, t_high),
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：三指标 ×(1−removal.mod_default)，其余指标透传。"""
    out: dict[str, float] = {}
    for indicator, ref_key in manifest.removal_refs.items():
        value = inflow.concentrations.get(indicator)
        if value is not None:
            out[indicator] = value * (1 - p[ref_key])
    for indicator, value in inflow.concentrations.items():
        out.setdefault(indicator, value)
    return WaterQuality(out)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _Chenshachi()


@final
class _Chenshachi:
    """旋流沉砂池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """CS-F1~F18 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        basin = _basin(ctx, p, flow)
        hopper = _hopper(ctx, p, flow, basin)
        hopper["d"] = basin["d"]
        channel = _channel(ctx, p, basin)
        sludge = _sludge(ctx, p, hopper, hopper["h_total"])
        dims = {**basin, **hopper, **channel, **sludge}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, ctx.inqualities.get(in_ref, WaterQuality({})))},
            dims=dims,
            warnings=_warnings(p, basin),
            formula_ids=FORMULA_IDS,
        )
