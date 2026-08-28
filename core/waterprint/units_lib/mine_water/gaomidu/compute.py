"""高密沉淀计算实现：唯一计算源（KG-F1~F10 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KG-F1~KG-F10（docs/norms/mine_water_gaomidu.md 起草表；
#   manifest.py 登记）——无回流斜管高密沉淀主线（低负荷 5~8 保浊度，
#   泥渣直接外排）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池宽
#   B=ceil(b_raw, side_disc_step 0.5 m 档)/池长 L=ceil(l_raw, 同档)。
#   零数值字面量。
# 【流量口径】沉淀区水力与混合/絮凝区容积全按最高时 flow.q_design
#   （KG-F1~F10，×3600 已内联公式串）——表流量口径逐字（全表单口径）。
# 【系数通道】factor.mine_gaomidu.*/removal.mine_gaomidu.* 经
#   ctx.params 投影面取值（app._unit_params 线感知投影，mine_ 限定
#   键空间）；缺键=领域异常。elevation_loss 键归高程链子系统（后续
#   批），本文件不消费；无 r_sludge/q_return 回流键族（与市政
#   Densadeg 回流型物理隔离——表边界差异节）。
# 【输出面（D2）】outflows=入流透传+sludge_out SLUDGE 产股（GOLDEN4a D3
#   无条件产股——MS-F3 口径投影，注记见 manifest ports 注）；dims=表结果全量 snake 键（单池
#   流量/混合絮凝容积/沉淀面积/池宽池长（含取整前审计面）/实际负荷/
#   轴向流速/总高/混凝土）；outqualities=入质×(1−removal.mod_default)
#   双指标（SS 68→6.8/COD 80→56——衔接下游 vxinglvchi 表）；
#   warnings=校核带越界（液面负荷带[参数面+实际面双检查]/轴向流速
#   上限/快混絮凝停留双带；param_key 归因+调节方向）；
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
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)
from waterprint.registry import formulas
from waterprint.units_lib.mine_water.gaomidu.manifest import (
    FORMULA_IDS,
    G_PER_KG,
    MOISTURE_RESIDUE,
    SECS_PER_DAY,
    WATER_DENSITY,
    manifest,
)

_UNIT_ID = "mine_water_gaomidu"
_GB = "GB/T 41019-2021（混凝沉淀液面负荷，条号待核对）"
_HB = "给水排水设计手册（第 3 册 城镇给水）斜管沉淀池轴向流速/构造常用带"
_LOAD_BAND = (
    "factor.mine_gaomidu.surface_load_band.min",
    "factor.mine_gaomidu.surface_load_band.max",
)
_AXIAL_MAX = "factor.mine_gaomidu.axial_velocity.max"
_T_MIX_BAND = (
    "factor.mine_gaomidu.t_mix_band.min",
    "factor.mine_gaomidu.t_mix_band.max",
)
_T_FLOC_BAND = (
    "factor.mine_gaomidu.t_floc_band.min",
    "factor.mine_gaomidu.t_floc_band.max",
)
_PARAMS_POSITIVE = (
    "n",
    "t_mix",
    "t_floc",
    "q_surf",
    "l_tube",
    "h_clear",
    "h_dist",
    "h_thick",
    "side_disc_step",
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
    """构造步长向上取整（KG-F5/F6 的 0.5 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/停留/负荷/斜管长/构造区高/步长非正一律拒。"""
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
            "（沉淀池单入单出语义）"
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


def _volumes(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """KG-F1~F3：单池流量与快混/絮凝区容积（最高时口径）。"""
    q1h = _apply(ctx, "KG-F1", {"q_design": flow.q_design, "n": p["n"]})
    return {
        "q1h": q1h,
        "v_mix": _apply(ctx, "KG-F2", {"q1h": q1h, "t_mix": p["t_mix"]}),
        "v_floc": _apply(ctx, "KG-F3", {"q1h": q1h, "t_floc": p["t_floc"]}),
    }


def _basin(ctx: UnitContext, p: dict[str, float], q1h: float) -> dict[str, float]:
    """KG-F4~F7：沉淀面积/池宽池长（0.5 m 档）/实际液面负荷。"""
    a_settle = _apply(ctx, "KG-F4", {"q1h": q1h, "q_surf": p["q_surf"]})
    b_raw = _apply(
        ctx, "KG-F5", {"a_settle": a_settle, "ratio_lb": _factor(p, "factor.mine_gaomidu.ratio_lb")}
    )
    b = _ceil_step(b_raw, p["side_disc_step"])
    l_raw = _apply(ctx, "KG-F6", {"a_settle": a_settle, "b": b})
    length = _ceil_step(l_raw, p["side_disc_step"])
    return {
        "a_settle": a_settle,
        "b_raw": b_raw,
        "b": b,
        "l_raw": l_raw,
        "l": length,
        "q_surf_act": _apply(ctx, "KG-F7", {"q1h": q1h, "l": length, "b": b}),
    }


def _axial(ctx: UnitContext, p: dict[str, float]) -> float:
    """KG-F8：斜管轴向流速校核（≤ axial_velocity.max）。"""
    return _apply(ctx, "KG-F8", {"q_surf": p["q_surf"]})


def _depth(
    ctx: UnitContext, p: dict[str, float], basin: dict[str, float]
) -> dict[str, float]:
    """KG-F9~F10：池总高与概算混凝土量。"""
    h_total = _apply(
        ctx,
        "KG-F9",
        {
            "h_super": _factor(p, "factor.mine_gaomidu.superheight"),
            "h_clear": p["h_clear"],
            "h_dist": p["h_dist"],
            "h_thick": p["h_thick"],
            "l_tube": p["l_tube"],
        },
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "KG-F10",
            {
                "l": basin["l"],
                "b": basin["b"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.mine_gaomidu.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _retention_warning(
    p: dict[str, float],
    param_key: str,
    band_keys: tuple[str, str],
    zone: str,
) -> Warning | None:
    """单区停留时间带检查（快混/絮凝同型，参数键归因）。"""
    band = _band(p, band_keys)
    value = p[param_key]
    if not band[0] <= value <= band[1]:
        return _warn(
            f"{_HB}；{band_keys[0]}~{band_keys[1]}",
            f"{zone}停留时间 = {value:.4f} min 越出建议带"
            f" [{band[0]}, {band[1]}]——调节方向：{param_key}（带内取值）",
            param_key,
        )
    return None


def _warnings(
    p: dict[str, float], q_surf_act: float, v_axial: float
) -> tuple[Warning, ...]:
    """校核带检查：液面负荷带（参数面+实际面）/轴向流速上限/停留双带。"""
    found: list[Warning] = []
    load = _band(p, _LOAD_BAND)
    if not load[0] <= p["q_surf"] <= load[1]:
        found.append(
            _warn(
                f"{_GB}；{_LOAD_BAND[0]}~{_LOAD_BAND[1]}",
                f"液面负荷 q_surf = {p['q_surf']:.4f} m³/(m²·h) 越出建议带"
                f" [{load[0]}, {load[1]}]——调节方向：q_surf（低负荷保浊度档带内取值）",
                "q_surf",
            )
        )
    if not load[0] <= q_surf_act <= load[1]:
        found.append(
            _warn(
                f"{_GB}；{_LOAD_BAND[0]}~{_LOAD_BAND[1]}",
                f"实际液面负荷 q_surf_act = {q_surf_act:.4f} m³/(m²·h) 越出建议带"
                f" [{load[0]}, {load[1]}]（B/L 0.5 m 档离散放大断面所致）"
                "——调节方向：q_surf",
                "q_surf",
            )
        )
    axial_max = _factor(p, _AXIAL_MAX)
    if v_axial > axial_max:
        found.append(
            _warn(
                f"{_HB}；{_AXIAL_MAX}",
                f"斜管轴向流速 = {v_axial:.7f} m/s 越上限"
                f" {axial_max}——调节方向：q_surf（降负荷）",
                "q_surf",
            )
        )
    for param_key, band_keys, zone in (
        ("t_mix", _T_MIX_BAND, "快速混合区"),
        ("t_floc", _T_FLOC_BAND, "絮凝区"),
    ):
        warning = _retention_warning(p, param_key, band_keys, zone)
        if warning is not None:
            found.append(warning)
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：双指标 ×(1−removal.mod_default)，其余透传。"""
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
    return _MineGaomidu()


@final
class _MineGaomidu:
    """高密沉淀 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KG-F1~F10 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        volumes = _volumes(ctx, p, flow)
        basin = _basin(ctx, p, volumes["q1h"])
        axial = _axial(ctx, p)
        dims = {**volumes, **basin, "v_axial": axial, **_depth(ctx, p, basin)}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        sludge_ref = PortRef(unit_id=ctx.unit_id, port_id="sludge_out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        # GOLDEN4a D3 产股前提：MS-F3 泥渣衡算需 SS（矿井水线 SS 必在——
        # 缺=上游装配缺陷，municipal gaomidu GM-F12 同款守卫）
        ss_in = quality.SS
        if ss_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 SS 浓度（MS-F3 泥渣干基衡算前提，GR-09）"
            )
        # MS-F3 链级衔接式（投影非计算不注册）：ds=q_avg×ΔSS 去除衡算
        ss_residue = (
            flow.q_avg_daily
            * SECS_PER_DAY
            * (ss_in - ss_in * (1 - _factor(p, "removal.mine_gaomidu.ss.mod_default")))
            / G_PER_KG
        )
        return UnitResult(
            outflows={
                out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz),
                # GOLDEN4a D3 产股：无条件产股（nongsuo sup 先例同构）——
                # ds=MS-F3 干基（hebing 注入 ds_chem 位链路同源）；q_wet=
                # ds/((1−p)×ρ) HB-F3 口径（ρ=1000 简化——manifest 常量
                # 直值注记，系数键化归后续批呈报不扩 coefficients）。
                sludge_ref: SludgeFlow(
                    q_wet=ss_residue
                    / ((1 - MOISTURE_RESIDUE) * WATER_DENSITY)
                    / SECS_PER_DAY,
                    ds=ss_residue / SECS_PER_DAY,
                    moisture=MOISTURE_RESIDUE,
                ),
            },
            outqualities={
                out_ref: _out_quality(p, quality),
                sludge_ref: WaterQuality({}),  # 空 WaterQuality 单位元（R5/GR-04）
            },
            dims=dims,
            warnings=_warnings(p, basin["q_surf_act"], axial),
            formula_ids=FORMULA_IDS,
        )
