"""辐流二沉池计算实现：唯一计算源（EC-F1~F15 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收；
#   公式路线 = ADR-008 ②清水表面负荷主控+固体负荷校核）
#
# 【公式组】EC-F1~F15（docs/norms/erchunchi.md 起草表；manifest.py 登记）
#   ——清水/固体表面负荷（EC-F1~F9）、回流污泥浓度（EC-F10）、停留时间
#   （t_hrt 校核导出量）、堰负荷与几何（EC-F11~F14）、概算混凝土量
#   （EC-F15）全覆盖；A = max(清水负荷面积, 固体负荷面积) 主控取大。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池径 D=
#   ceil(d_raw, dia_disc_step 0.5 m 档)/d_center/h4/h_total=ceil(raw,
#   length_disc_step 0.1 m 档)；π 经符号 pi 绑定 math.pi。零数值字面量。
# 【DSL 单输出导出量】q1（=q_design/n 清水口径单池秒流量）、v_check（=
#   a_act×h2 校核容积）/t_hrt（=v_check/q1h 校核 HRT）/q_return_sludge
#   （=r_external×q1h 回流污泥量）在 compute 以符号算术合成——零字面量、
#   无新工程常数（registry 单输出限制的导出面）。
# 【流量口径（三表逐字冻结）】清水表面负荷与池径按最高时 flow.q_design
#   （不含回流）；固体负荷按含回流混合液 (1+R)×q1h；R/X 与 AAO 表联动
#   （各包独立声明同值参数）——混合液 MLSS 由参数 x_mlss 承载，不经
#   水质去除链（三表语义注记）。
# 【系数通道】factor.erchunchi.*/removal.erchunchi.* 经 ctx.params 投影
#   面取值（app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D3）】outflows=入流透传；dims=三表水力结果全量 snake 键；
#   outqualities=入质×(1−removal.mod_default) 三指标+NH3N/TN/TP 透传；
#   warnings=校核带越界（清水负荷/固体负荷/堰负荷/水深带/Xr 带[0.2.1]/
#   HRT 带[0.2.1]——param_key 归因+双向调节方向，堰负荷越界归堰构造
#   口径注记）；formula_ids=实际求值公式号全量。
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
from waterprint.units_lib.municipal.erchunchi.manifest import FORMULA_IDS, manifest

_UNIT_ID = "municipal_erchunchi"
_GB = "GB 50014-2021 表 7.5.1+§7.6.15/§7.6.16"
_HB = "给水排水设计手册（第 5 册 城镇排水）"
_SURFACE_BAND = (
    "factor.erchunchi.surface_load_band.min",
    "factor.erchunchi.surface_load_band.max",
)
_SOLID_MAX = "factor.erchunchi.solid_load.center_inlet"
_WEIR_MAX = "factor.erchunchi.weir_load.max"
_DEPTH_BAND = ("factor.erchunchi.depth_band.min", "factor.erchunchi.depth_band.max")
_XR_BAND = ("factor.erchunchi.x_r_band.min", "factor.erchunchi.x_r_band.max")
_HRT_BAND = ("factor.erchunchi.hrt_band.min", "factor.erchunchi.hrt_band.max")
_PARAMS_POSITIVE = (
    "n",
    "q_nom",
    "x_mlss",
    "r_external",
    "h2",
    "r_pit",
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
    """构造步长向上取整（EC-F6/F12/F13/F14 的 0.5/0.1 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/负荷/浓度/回流比/水深/构造/步长非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（二沉池单入单出语义）"
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


def _load(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """EC-F1~F10：单池流量/双控面积/池径/负荷校核/Xr（含 HRT 导出量）。"""
    q1h = _apply(ctx, "EC-F1", {"q_design": flow.q_design, "n": p["n"]})
    q1 = flow.q_design / p["n"]  # 清水口径单池秒流量（EC-F11/F12 入参）
    a_q = _apply(ctx, "EC-F2", {"q1h": q1h, "q_nom": p["q_nom"]})
    m_solid = _apply(
        ctx,
        "EC-F3",
        {"r_external": p["r_external"], "q1h": q1h, "x_mlss": p["x_mlss"]},
    )
    a_solid = _apply(ctx, "EC-F4", {"m_solid": m_solid, "g_max": _factor(p, _SOLID_MAX)})
    a_tank = _apply(ctx, "EC-F5", {"a_q": a_q, "a_solid": a_solid})
    d_raw = _apply(ctx, "EC-F6", {"a_tank": a_tank, "pi": math.pi})
    d = _ceil_step(d_raw, p["dia_disc_step"])
    a_act = _apply(ctx, "EC-F7", {"pi": math.pi, "D": d})
    v_check = a_act * p["h2"]  # 校核容积（三表校核 HRT 行）
    return {
        "q1": q1,
        "q1h": q1h,
        "a_q": a_q,
        "m_solid": m_solid,
        "a_solid": a_solid,
        "a_tank": a_tank,
        "d_raw": d_raw,
        "d": d,
        "a_act": a_act,
        "q_act": _apply(ctx, "EC-F8", {"q1h": q1h, "a_act": a_act}),
        "g_act": _apply(ctx, "EC-F9", {"m_solid": m_solid, "a_act": a_act}),
        "x_r": _apply(ctx, "EC-F10", {"x_mlss": p["x_mlss"], "r_external": p["r_external"]}),
        "v_check": v_check,
        "t_hrt": v_check / q1h,  # 校核 HRT（三表校核 HRT 行）
        "q_return_sludge": p["r_external"] * q1h,  # 回流污泥量（排泥衔接行）
    }


def _geometry(ctx: UnitContext, p: dict[str, float], load: dict[str, float]) -> dict[str, float]:
    """EC-F11~F15：堰负荷/中心筒/池底坡/总高（含离散）与混凝土量。"""
    h4 = _ceil_step(
        _apply(
            ctx,
            "EC-F13",
            {
                "i_slope": _factor(p, "factor.erchunchi.bottom_slope"),
                "D": load["d"],
                "r_pit": p["r_pit"],
            },
        ),
        p["length_disc_step"],
    )
    h_total = _ceil_step(
        _apply(
            ctx,
            "EC-F14",
            {
                "h_super": _factor(p, "factor.erchunchi.superheight"),
                "h2": p["h2"],
                "h_buf": _factor(p, "factor.erchunchi.buffer_h3"),
                "h4": h4,
            },
        ),
        p["length_disc_step"],
    )
    return {
        "q_weir": _apply(
            ctx, "EC-F11", {"q1": load["q1"], "pi": math.pi, "D": load["d"]}
        ),
        "d_center": _ceil_step(
            _apply(
                ctx,
                "EC-F12",
                {
                    "r_external": p["r_external"],
                    "q1": load["q1"],
                    "pi": math.pi,
                    "v_center": _factor(p, "factor.erchunchi.center_velocity"),
                },
            ),
            p["length_disc_step"],
        ),
        "h4": h4,
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "EC-F15",
            {
                "pi": math.pi,
                "D": load["d"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.erchunchi.wall_thickness_coef"),
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
    p: dict[str, float], load: dict[str, float], geometry: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：清水负荷/固体负荷/堰负荷/水深/Xr/HRT 六条。"""
    found: list[Warning] = []
    surf = _band(p, _SURFACE_BAND)
    if not surf[0] <= load["q_act"] <= surf[1]:
        found.append(
            _warn(
                f"{_GB}；{_SURFACE_BAND[0]}~{_SURFACE_BAND[1]}",
                f"实际清水表面负荷 = {load['q_act']:.4f} 越出建议带"
                f" [{surf[0]}, {surf[1]}]——调节方向：q_nom（负荷）或 n（池数）",
                "q_nom",
            )
        )
    solid = _factor(p, _SOLID_MAX)
    if load["g_act"] > solid:
        found.append(
            _warn(
                f"{_GB}；{_SOLID_MAX}",
                f"实际固体面积负荷 = {load['g_act']:.4f} 超上限 {solid}"
                "——调节方向：x_mlss（↓）或 n（池数 ↑）",
                "x_mlss",
            )
        )
    weir = _factor(p, _WEIR_MAX)
    if geometry["q_weir"] > weir:
        found.append(
            _warn(
                f"GB 50014-2021（沉淀池堰负荷，二沉档）；{_WEIR_MAX}",
                f"出水堰负荷 = {geometry['q_weir']:.4f} 超上限 {weir}——堰构造口径注记："
                "默认周边双侧出水堰（L=2πD），单侧口径敏感性见 docs/norms/erchunchi.md"
                "（堰构造口径待领域专家追认）",
                None,
            )
        )
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= p["h2"] <= dep[1]:
        found.append(
            _warn(
                f"{_HB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"池边有效水深 h2 = {p['h2']:.4f} 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：h2（带内取值）",
                "h2",
            )
        )
    xr = _band(p, _XR_BAND)
    if not xr[0] <= load["x_r"] <= xr[1]:
        found.append(
            _warn(
                f"{_HB}；{_XR_BAND[0]}~{_XR_BAND[1]}（0.2.1 键）",
                f"回流污泥浓度 Xr = {load['x_r']:.4f} mg/L 越出建议带"
                f" [{xr[0]}, {xr[1]}]——调节方向：r_external（↑Xr↓，与 AAO 表联动）",
                "r_external",
            )
        )
    hrt = _band(p, _HRT_BAND)
    if not hrt[0] <= load["t_hrt"] <= hrt[1]:
        found.append(
            _warn(
                f"{_HB}；{_HRT_BAND[0]}~{_HRT_BAND[1]}（0.2.1 键）",
                f"校核 HRT = {load['t_hrt']:.4f} h 越出建议带"
                f" [{hrt[0]}, {hrt[1]}]——调节方向：q_nom（↓池径↑t↑）或 h2（↑t↑）",
                "q_nom",
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
    return _Erchunchi()


@final
class _Erchunchi:
    """辐流二沉池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """EC-F1~F15 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        load = _load(ctx, p, flow)
        geometry = _geometry(ctx, p, load)
        dims = {**load, **geometry}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={
                out_ref: _out_quality(p, ctx.inqualities.get(in_ref, WaterQuality({})))
            },
            dims=dims,
            warnings=_warnings(p, load, geometry),
            formula_ids=FORMULA_IDS,
        )
