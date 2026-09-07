"""高密沉淀池计算实现：唯一计算源（GM-F1~F20 全经 registry.apply_batch
求值——批 13-A 同源向量路径：公式链以 ndarray 流动，标量=N=1 退化）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收；批 13-A 向量化
#   重写：公式链经 _apply_batch 批量正门[AGENTS §13.6 同源向量路径唯一——
#   标量=N=1 退化；守卫层/warnings/ceil=N=1 边界件；N>1=批 D 引擎正门]）
#
# 【公式组】GM-F1~F20（docs/norms/gaomidu.md 起草表；manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池边长 B=
#   ceil(b_raw, side_disc_step 0.5 m 档)/池总高 h_total=ceil(h_total_raw,
#   length_disc_step 0.1 m 档)。零数值字面量。
# 【DSL 单输出导出量】q_design_h（=q1h×n，GM-F11 全厂回流泵 m3/h）与
#   ss_out（=ss_in×(1−removal.gaomidu.ss)，GM-F12 入参）在 compute 以
#   符号算术合成——零字面量、无新工程常数（registry 单输出限制导出面）。
# 【系数通道】factor.gaomidu.*/removal.gaomidu.* 经 ctx.params 投影面
#   取值（app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【流量口径】沉淀区水力与混合/絮凝区容积按最高时 flow.q_design
#   （GM-F1~F11）；药剂耗量与干泥量按平均日 flow.q_avg_daily（GM-F12~
#   F15，×86400 已内联公式串）——四表口径逐字（Densadeg 类，ADR-008 ③）。
# 【输出面（D2）】outflows=入流透传+sludge_out SLUDGE 产股（GOLDEN4a D3
#   无条件产股——GM-F12/F13 全厂口径 ds/q_wet+moisture=1−c_sludge/1000；
#   ÷SECS_PER_DAY 回契约口径）；dims=四表水力结果全量 snake 键（不变——
#   投影非计算，nongsuo sup 先例同构）；
#   outqualities=入质×(1−removal.mod_default) 三指标+NH3N/TN/TP 透传
#   （同 M1a/M2a2 形态）；warnings=校核带越界（液面负荷带/回流比带/
#   快混·絮凝停留带/GT 带+絮凝区布置校核 h_floc_calc<h_settle；
#   param_key 归因+调节方向）；formula_ids=实际求值公式号全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import final

import numpy

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
from waterprint.units_lib._constants import SECS_PER_DAY
from waterprint.units_lib._unit_compute import _apply_batch, _factor, _inflow, _make_ceil_step, _vec
from waterprint.units_lib.municipal.gaomidu.manifest import FORMULA_IDS, WATER_DENSITY, manifest

type _Array = numpy.ndarray  # 向量链注记别名（批 13-A——公式链中间量形态）

_UNIT_ID = "municipal_gaomidu"
_GT = "GB/T 50335-2016 §5.4.3（高密斜管清水区液面负荷）"
_HB = "给水排水设计手册（第 5 册 城镇排水）混合/絮凝 G 值法"
_SURFACE_BAND = (
    "factor.gaomidu.surface_load_band.min",
    "factor.gaomidu.surface_load_band.max",
)
_RSLUDGE_BAND = (
    "factor.gaomidu.r_sludge_band.min",
    "factor.gaomidu.r_sludge_band.max",
)
_TMIX_BAND = ("factor.gaomidu.t_mix_band.min", "factor.gaomidu.t_mix_band.max")
_TFLOC_BAND = ("factor.gaomidu.t_floc_band.min", "factor.gaomidu.t_floc_band.max")
_GT_BAND = ("factor.gaomidu.gt_band.min", "factor.gaomidu.gt_band.max")
_G_MIX = "factor.gaomidu.g_mix"
_G_FLOC = "factor.gaomidu.g_floc"
_C_SLUDGE = "factor.gaomidu.sludge.concentration"
_DOSE_PAC = "factor.gaomidu.dose.pac"
_DOSE_PAM = "factor.gaomidu.dose.pam"
_PARAMS_POSITIVE = (
    "n",
    "q_surface",
    "r_sludge",
    "t_mix",
    "t_floc",
    "l_tube",
    "h_clear",
    "h_buffer",
    "h_thick",
    "side_disc_step",
    "length_disc_step",
)
_FACTORS_POSITIVE = (_G_MIX, _G_FLOC, _C_SLUDGE, _DOSE_PAC, _DOSE_PAM)


_ceil_step = _make_ceil_step(_UNIT_ID, "取整步长", spaced=False)


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/负荷/回流比/停留/构造几何/步长与 G 值·含固率·药剂非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")
    for key in _FACTORS_POSITIVE:
        if _factor(params, key, _UNIT_ID) <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 系数键 {key!r} 必须 > 0（G 值/含固率/药剂投加量物理域）"
            )


def _basin(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, _Array]:
    """GM-F1~F5：单池流量/需蓄斜管区面积/池边长（0.5 m 档）/实际液面负荷。"""
    q1h = _apply_batch(ctx, "GM-F1", {"q_design": _vec(flow.q_design), "n": _vec(p["n"])})
    a_incl_req = _apply_batch(ctx, "GM-F2", {"q1h": q1h, "q_surface": _vec(p["q_surface"])})
    b_raw = _apply_batch(ctx, "GM-F3", {"a_incl_req": a_incl_req})
    b = _vec(_ceil_step(float(b_raw[0]), p["side_disc_step"]))
    a_act = _apply_batch(ctx, "GM-F4", {"B": b})
    return {
        "q1h": q1h,
        "q_design_h": q1h * _vec(p["n"]),  # DSL 单输出导出量（GM-F11 全厂口径）
        "a_incl_req": a_incl_req,
        "b_raw": b_raw,
        "b": b,
        "a_act": a_act,
        "q_surface_act": _apply_batch(ctx, "GM-F5", {"q1h": q1h, "a_act": a_act}),
    }


def _mix_floc(ctx: UnitContext, p: dict[str, float], basin: dict[str, _Array]) -> dict[str, _Array]:
    """GM-F6~F10：快混/絮凝区容积与 G 值法功率、GT 校核（单池）。"""
    g_floc = _vec(_factor(p, _G_FLOC, _UNIT_ID))
    v_mix = _apply_batch(ctx, "GM-F6", {"q1h": basin["q1h"], "t_mix": _vec(p["t_mix"])})
    v_floc = _apply_batch(ctx, "GM-F7", {"q1h": basin["q1h"], "t_floc": _vec(p["t_floc"])})
    return {
        "v_mix": v_mix,
        "v_floc": v_floc,
        "p_mix": _apply_batch(
            ctx, "GM-F8", {"g_mix": _vec(_factor(p, _G_MIX, _UNIT_ID)), "v_mix": v_mix}
        ),
        "p_floc": _apply_batch(ctx, "GM-F9", {"g_floc": g_floc, "v_floc": v_floc}),
        "gt_floc": _apply_batch(ctx, "GM-F10", {"g_floc": g_floc, "t_floc": _vec(p["t_floc"])}),
    }


def _sludge_dose(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, basin: dict[str, _Array], ss_in: float
) -> dict[str, _Array]:
    """GM-F11~F15：污泥回流/干泥量/浓缩排泥/PAC·PAM 药剂耗量（平均日口径）。"""
    q_avg = _vec(flow.q_avg_daily)
    ss_out = _vec(ss_in) * (1 - _vec(_factor(p, "removal.gaomidu.ss.mod_default", _UNIT_ID)))
    s_dry = _apply_batch(
        ctx, "GM-F12", {"q_avg_daily": q_avg, "ss_in": _vec(ss_in), "ss_out": ss_out}
    )
    return {
        "q_return": _apply_batch(
            ctx, "GM-F11", {"r_sludge": _vec(p["r_sludge"]), "q_design_h": basin["q_design_h"]}
        ),
        "ss_out": ss_out,
        "s_dry": s_dry,
        "q_sludge": _apply_batch(
            ctx, "GM-F13", {"s_dry": s_dry, "c_sludge": _vec(_factor(p, _C_SLUDGE, _UNIT_ID))}
        ),
        "m_pac": _apply_batch(
            ctx, "GM-F14", {"q_avg_daily": q_avg, "dose_pac": _vec(_factor(p, _DOSE_PAC, _UNIT_ID))}
        ),
        "m_pam": _apply_batch(
            ctx, "GM-F15", {"q_avg_daily": q_avg, "dose_pam": _vec(_factor(p, _DOSE_PAM, _UNIT_ID))}
        ),
    }


def _depth(
    ctx: UnitContext, p: dict[str, float], basin: dict[str, _Array], mixfloc: dict[str, _Array]
) -> dict[str, _Array]:
    """GM-F16~F20：斜管区高/沉淀区总高/池总高（0.1 m 档）/絮凝水深校核/混凝土量。"""
    h_tube_zone = _apply_batch(ctx, "GM-F16", {"l_tube": _vec(p["l_tube"])})
    h_settle = _apply_batch(
        ctx,
        "GM-F17",
        {
            "h_clear": _vec(p["h_clear"]),
            "h_tube_zone": h_tube_zone,
            "h_buffer": _vec(p["h_buffer"]),
            "h_thick": _vec(p["h_thick"]),
        },
    )
    h_total_raw = _apply_batch(
        ctx,
        "GM-F18",
        {
            "h_super": _vec(_factor(p, "factor.gaomidu.superheight", _UNIT_ID)),
            "h_settle": h_settle,
        },
    )
    h_total = _vec(_ceil_step(float(h_total_raw[0]), p["length_disc_step"]))
    return {
        "h_tube_zone": h_tube_zone,
        "h_settle": h_settle,
        "h_total_raw": h_total_raw,
        "h_total": h_total,
        "h_floc_calc": _apply_batch(
            ctx, "GM-F19", {"v_floc": mixfloc["v_floc"], "a_act": basin["a_act"]}
        ),
        "v_concrete": _apply_batch(
            ctx,
            "GM-F20",
            {
                "a_act": basin["a_act"],
                "h_total": h_total,
                "n": _vec(p["n"]),
                "wall_coef": _vec(_factor(p, "factor.gaomidu.wall_thickness_coef", _UNIT_ID)),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0], _UNIT_ID), _factor(p, keys[1], _UNIT_ID)


def _param_band(p: dict[str, float], keys: tuple[str, str], key: str) -> bool:
    """参数域带检查（单参数值 vs 带键）。"""
    band = _band(p, keys)
    return band[0] <= p[key] <= band[1]


def _warnings(
    p: dict[str, float],
    basin: dict[str, _Array],
    mixfloc: dict[str, _Array],
    depth: dict[str, _Array],
) -> tuple[Warning, ...]:
    """校核带检查：液面负荷/回流比/快混絮凝停留/GT 带+絮凝区布置校核。"""
    found: list[Warning] = []
    surf = _band(p, _SURFACE_BAND)
    q_surface_act = float(basin["q_surface_act"][0])
    if not surf[0] <= q_surface_act <= surf[1]:
        found.append(
            _warn(
                f"{_GT}；{_SURFACE_BAND[0]}~{_SURFACE_BAND[1]}",
                f"实际液面负荷 = {q_surface_act:.4f} 越出建议带"
                f" [{surf[0]}, {surf[1]}]——调节方向：q_surface（负荷）或 n（池数）",
                "q_surface",
            )
        )
    if not _param_band(p, _RSLUDGE_BAND, "r_sludge"):
        band = _band(p, _RSLUDGE_BAND)
        found.append(
            _warn(
                f"{_GT}；{_RSLUDGE_BAND[0]}~{_RSLUDGE_BAND[1]}",
                f"污泥回流比 = {p['r_sludge']:.4f} 越出建议带"
                f" [{band[0]}, {band[1]}]——调节方向：r_sludge（Densadeg 回流档）",
                "r_sludge",
            )
        )
    if not _param_band(p, _TMIX_BAND, "t_mix"):
        band = _band(p, _TMIX_BAND)
        found.append(
            _warn(
                f"{_HB}；{_TMIX_BAND[0]}~{_TMIX_BAND[1]}",
                f"快速混合停留时间 = {p['t_mix']:.4f} min 越出建议带"
                f" [{band[0]}, {band[1]}]——调节方向：t_mix（混合常用档）",
                "t_mix",
            )
        )
    if not _param_band(p, _TFLOC_BAND, "t_floc"):
        band = _band(p, _TFLOC_BAND)
        found.append(
            _warn(
                f"{_HB}；{_TFLOC_BAND[0]}~{_TFLOC_BAND[1]}",
                f"絮凝停留时间 = {p['t_floc']:.4f} min 越出建议带"
                f" [{band[0]}, {band[1]}]——调节方向：t_floc（絮凝常用档）",
                "t_floc",
            )
        )
    gt = _band(p, _GT_BAND)
    gt_floc = float(mixfloc["gt_floc"][0])
    if not gt[0] <= gt_floc <= gt[1]:
        found.append(
            _warn(
                f"{_HB}；{_GT_BAND[0]}~{_GT_BAND[1]}",
                f"絮凝 GT 值 = {gt_floc:.0f} 越出建议带"
                f" [{gt[0]:.0f}, {gt[1]:.0f}]——调节方向：t_floc（历时）或 g_floc（系数键）",
                "t_floc",
            )
        )
    h_floc_calc = float(depth["h_floc_calc"][0])
    h_settle = float(depth["h_settle"][0])
    if h_floc_calc >= h_settle:
        found.append(
            _warn(
                f"{_HB}；GM-F19 絮凝区布置校核（h_floc_calc < h_settle）",
                f"絮凝区计算水深 = {h_floc_calc:.4f} m 不低于沉淀区总高"
                f" {h_settle:.4f} m——布置不可行：t_floc（↓）或 q_surface（↑负荷缩面）",
                "t_floc",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：三指标 ×(1−removal.mod_default)，其余指标透传（同 M1a 形态）。"""
    out: dict[str, float] = {}
    for indicator, ref_key in manifest.removal_refs.items():
        value = inflow.concentrations.get(indicator)
        if value is not None:
            out[indicator] = value * (1 - _factor(p, ref_key, _UNIT_ID))
    for indicator, value in inflow.concentrations.items():
        out.setdefault(indicator, value)
    return WaterQuality(out)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _Gaomidu()


@final
class _Gaomidu:
    """高密沉淀池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """GM-F1~F20 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx, "高密沉淀池单入单出语义")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        ss_in = quality.SS
        if ss_in is None:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流缺 SS 浓度（GM-F12 干泥量计算前提，GR-09）"
            )
        basin = _basin(ctx, p, flow)
        mixfloc = _mix_floc(ctx, p, basin)
        sludge = _sludge_dose(ctx, p, flow, basin, ss_in)
        depth = _depth(ctx, p, basin, mixfloc)
        arrays = {**basin, **mixfloc, **sludge, **depth}
        dims = {key: float(value[0]) for key, value in arrays.items()}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        sludge_ref = PortRef(unit_id=ctx.unit_id, port_id="sludge_out")
        return UnitResult(
            outflows={
                out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz),
                # GOLDEN4a D3 产股：无条件产股（nongsuo sup 先例同构）——
                # ds=GM-F12 s_dry 全厂（hebing 注入 ds_chem 链路同源）、
                # q_wet=GM-F13 q_sludge 直用（与 HB-F3 同式）；moisture=
                # 1−c_sludge/WATER_DENSITY（=0.98 与 hebing p_chem 默认
                # 同源——含固率↔含水率 ρ=1000 口径互推，manifest 注记）。
                sludge_ref: SludgeFlow(
                    q_wet=float(sludge["q_sludge"][0]) / SECS_PER_DAY,
                    ds=float(sludge["s_dry"][0]) / SECS_PER_DAY,
                    moisture=1 - _factor(p, _C_SLUDGE, _UNIT_ID) / WATER_DENSITY,
                ),
            },
            outqualities={
                out_ref: _out_quality(p, quality),
                # SLUDGE 通道无水质指标——空 WaterQuality 单位元（R5/GR-04）
                sludge_ref: WaterQuality({}),
            },
            dims=dims,
            warnings=_warnings(p, basin, mixfloc, depth),
            formula_ids=FORMULA_IDS,
        )
