"""粗格栅计算实现：唯一计算源（CG-F1~F14 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【公式组】CG-F1~F14（docs/norms/cugeshan.md 签字表；manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：n_gap 取整
#   =math.ceil；B/B1/H/L = ceil(raw, length_disc_step)（步长=manifest 参数，
#   出处三表）；sin/tan 预处理值以符号传入公式。零数值字面量（模板 R2）。
# 【系数通道】factor.screen.*/factor.cugeshan.*/removal.cugeshan.* 经
#   ctx.params 投影面取值（app._unit_params，D4 裁决）；缺键=领域异常。
# 【输出面（D5）】outflows=入流透传（WaterFlow 直接构造，图内透传合法）；
#   dims=三表水力结果全量 snake 键；outqualities=入质×(1−removal.mod_default)
#   三指标+NH3N/TN/TP 透传；warnings=流速带越界（factor.screen.velocity_band）；
#   formula_ids=实际求值公式号全量；trace=apply 落迹（sink=ctx.trace）。
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
from waterprint.units_lib.municipal.cugeshan.manifest import FORMULA_IDS, manifest

_BETA_KEYS: tuple[str, str, str] = (
    "factor.screen.beta.rect",
    "factor.screen.beta.semicircle",
    "factor.screen.beta.circle",
)
_V_BAND = ("factor.screen.velocity_band.v.min", "factor.screen.velocity_band.v.max")
_V1_BAND = ("factor.screen.velocity_band.v1.min", "factor.screen.velocity_band.v1.max")
_NORM = "GB 50014-2021 §6.3（条文号待核对原文）"


def _factor(params: dict[str, float], key: str, unit_id: str) -> float:
    """系数投影取值（D4）：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {unit_id!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——D4 装配裁决）"
        )
    return float(value)


def _ceil_step(value: float, step: float, unit_id: str) -> float:
    """构造步长向上取整（三表 CG-F3/F4/F9/F10 的 0.1m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {unit_id!r} 的 length_disc_step 必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float], unit_id: str) -> None:
    """参数域守卫：台数/几何/步长非正一律拒（GR-02 输入即拒精神）。"""
    for key in ("n", "b", "h", "s", "alpha"):
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {unit_id!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（格栅单入单出语义）"
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


def _geometry(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """CG-F1~F6：单台流量/间隙数/栅槽宽/渠宽/两流速校核值。"""
    sin_alpha = math.sin(math.radians(p["alpha"]))
    sqrt_sin_alpha = math.sqrt(sin_alpha)
    tan_alpha = math.tan(math.radians(p["alpha"]))
    q = _apply(ctx, "CG-F1", {"q_design": flow.q_design, "n": p["n"]})
    n_gap = float(
        math.ceil(
            _apply(
                ctx,
                "CG-F2",
                {
                    "q": q,
                    "sqrt_sin_alpha": sqrt_sin_alpha,
                    "b": p["b"],
                    "h": p["h"],
                    "v": p["v"],
                },
            )
        )
    )
    step = p["length_disc_step"]
    b_width = _ceil_step(
        _apply(
            ctx,
            "CG-F3",
            {
                "s": p["s"],
                "n_gap": n_gap,
                "b": p["b"],
                "margin": _factor(p, "factor.screen.trough_width_margin", ctx.unit_id),
            },
        ),
        step,
        ctx.unit_id,
    )
    b1_width = _ceil_step(
        _apply(ctx, "CG-F4", {"q": q, "h": p["h"], "v1": p["v1"]}),
        step,
        ctx.unit_id,
    )
    return {
        "q": q,
        "n_gap": n_gap,
        "B": b_width,
        "B1": b1_width,
        "v_checked": _apply(
            ctx,
            "CG-F5",
            {
                "q": q,
                "sqrt_sin_alpha": sqrt_sin_alpha,
                "b": p["b"],
                "h": p["h"],
                "n_gap": n_gap,
            },
        ),
        "v1_checked": _apply(ctx, "CG-F6", {"q": q, "h": p["h"], "b1": b1_width}),
        "_sin_alpha": sin_alpha,
        "_tan_alpha": tan_alpha,
    }


def _losses(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, geo: dict[str, float]
) -> dict[str, float]:
    """CG-F7~F14：阻力/水头损失/总高总长/栅渣量/清渣判别/DS/混凝土量。"""
    unit_id = ctx.unit_id
    beta_key = _BETA_KEYS[int(p["bar_shape"])]
    xi = _apply(
        ctx,
        "CG-F7",
        {"beta": _factor(p, beta_key, unit_id), "s_over_b": p["s"] / p["b"]},
    )
    h1 = _apply(
        ctx,
        "CG-F8",
        {
            "k_headloss": _factor(p, "factor.screen.headloss.k", unit_id),
            "xi": xi,
            "v_checked": geo["v_checked"],
            "g": p["g_gravity"],
            "sin_alpha": geo["_sin_alpha"],
        },
    )
    step = p["length_disc_step"]
    h_total = _ceil_step(
        _apply(
            ctx,
            "CG-F9",
            {
                "h": p["h"],
                "h1": h1,
                "superheight": _factor(p, "factor.screen.superheight", unit_id),
            },
        ),
        step,
        unit_id,
    )
    l_total = _ceil_step(
        _apply(
            ctx,
            "CG-F10",
            {
                "B": geo["B"],
                "b1": geo["B1"],
                "tan_alpha": geo["_tan_alpha"],
                "l3_fixed": _factor(p, "factor.screen.trough_length.l3_fixed", unit_id),
                "l4_fixed": _factor(p, "factor.screen.trough_length.l4_fixed", unit_id),
                "drop_constant": _factor(p, "factor.screen.trough_length.drop_constant", unit_id),
                "h": p["h"],
            },
        ),
        step,
        unit_id,
    )
    w_slag = _apply(
        ctx,
        "CG-F11",
        {
            "q_design": flow.q_design,
            "w1": _factor(p, "factor.cugeshan.w1_slag", unit_id),
            "kz": flow.kz,
        },
    )
    mech_margin = _apply(
        ctx,
        "CG-F12",
        {
            "w_slag": w_slag,
            "mech_clean_threshold": _factor(p, "factor.screen.mech_clean_threshold", unit_id),
        },
    )
    ds_slag = _apply(
        ctx,
        "CG-F13",
        {
            "w_slag": w_slag,
            "moisture": _factor(p, "factor.screen.slag.moisture", unit_id),
        },
    )
    v_concrete = _apply(
        ctx,
        "CG-F14",
        {
            "L": l_total,
            "B": geo["B"],
            "H": h_total,
            "n": p["n"],
            "wall_coef": _factor(p, "factor.screen.wall_thickness_coef", unit_id),
        },
    )
    return {
        "xi": xi,
        "h1": h1,
        "H": h_total,
        "L": l_total,
        "w_slag": w_slag,
        "mech_clean": float(mech_margin > 0),
        "ds_slag": ds_slag,
        "v_concrete": v_concrete,
    }


def _band_warning(param_key: str, source: str, value: float, lower: float, upper: float) -> Warning:
    """单条校核带越界警告（severity=WARN，param_key=field_id，GR 口径）。"""
    return Warning(
        severity=Severity.WARN,
        source=source,
        message=(
            f"校核流速 {value:.4f} m/s 越出建议带 [{lower}, {upper}] m/s"
            f"（参数 {param_key}——调节过栅/栅前流速设计值）"
        ),
        param_key=param_key,
    )


def _warnings(p: dict[str, float], geo: dict[str, float]) -> tuple[Warning, ...]:
    """校核带检查：过栅流速带 + 栅前流速带（三表 CG-F5/F6 约束带）。"""
    found: list[Warning] = []
    v_low = _factor(p, _V_BAND[0], "municipal_cugeshan")
    v_high = _factor(p, _V_BAND[1], "municipal_cugeshan")
    v1_low = _factor(p, _V1_BAND[0], "municipal_cugeshan")
    v1_high = _factor(p, _V1_BAND[1], "municipal_cugeshan")
    if not v_low <= geo["v_checked"] <= v_high:
        found.append(
            _band_warning(
                "v", f"{_NORM}；{_V_BAND[0]}~{_V_BAND[1]}", geo["v_checked"], v_low, v_high
            )
        )
    if not v1_low <= geo["v1_checked"] <= v1_high:
        found.append(
            _band_warning(
                "v1",
                f"{_NORM}；{_V1_BAND[0]}~{_V1_BAND[1]}",
                geo["v1_checked"],
                v1_low,
                v1_high,
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
    return _Cugeshan()


@final
class _Cugeshan:
    """粗格栅 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """CG-F1~F14 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p, ctx.unit_id)
        in_ref, flow = _inflow(ctx)
        geo = _geometry(ctx, p, flow)
        loss = _losses(ctx, p, flow, geo)
        dims = {name: value for name, value in {**geo, **loss}.items() if not name.startswith("_")}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, ctx.inqualities.get(in_ref, WaterQuality({})))},
            dims=dims,
            warnings=_warnings(p, geo),
            formula_ids=FORMULA_IDS,
        )
