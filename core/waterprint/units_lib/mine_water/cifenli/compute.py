"""磁分离计算实现：唯一计算源（KS-F1~F8 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KS-F1~KS-F8（docs/norms/mine_water_cifenli.md 起草表；
#   manifest.py 登记）——磁盘表面负荷主线+磁种回收衡算。
# 【DSL 收口】ceil 在本文件收口（DSL 无 ceil）：盘片数整台向上取整
#   （n_disks_raw 取整前审计面——chenshachi b_raw 先例）。零数值字面量。
# 【流量口径】盘面水力按最高时 flow.q_design（KS-F1~F5，×3600 已内联
#   公式串）；截留泥量/磁泥湿量/磁种净耗按平均日 flow.q_avg_daily
#   （KS-F6~F8，×86400 已内联）——表流量口径逐字。
# 【ss_in 衔接】KS-F6 截留率衡算的进水 SS=入流水质取数（衔接链值，
#   表"衔接式"原文）；入流缺 SS 指标=领域异常（泥量衡算前提失败）。
# 【系数通道】factor.mine_cifenli.*/removal.mine_cifenli.* 经 ctx.params
#   投影面取值（app._unit_params 线感知投影，mine_ 限定键空间）；
#   缺键=领域异常。elevation_loss 键归高程链子系统（后续批），本文件
#   不消费；channel.t_band/channel.v_max 选型校核键不消费（流道几何
#   归厂商样本——表"其他数据键"原文）；superheight/wall_thickness_
#   coef 机室构筑概算面键本批不落公式（表无公式行），仅登记在册。
# 【输出面（D2）】outflows=入流透传+sludge_out SLUDGE 产股（GOLDEN4a D3
#   无条件产股——MS-F1 口径投影，注记见 manifest ports 注）；dims=表结果全量 snake 键（单台
#   流量/单盘面积/需盘面面积/盘片数/线速度/截留泥量/磁泥湿量/磁种
#   净耗）；outqualities=入质×(1−removal.mod_default) 双指标（SS
#   680→68/COD 200→80——衔接下游 gaomidu 表）；warnings=校核带越界
#   （表面负荷带/盘转速上限；param_key 归因+调节方向）；
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
from waterprint.units_lib.mine_water.cifenli.manifest import (
    FORMULA_IDS,
    KG_PER_TON,
    SECS_PER_DAY,
    manifest,
)

_UNIT_ID = "mine_water_cifenli"
_GB = "GB/T 41019-2021（磁加载分离表面负荷/盘转速，条号待核对）"
_LOAD_BAND = (
    "factor.mine_cifenli.surface_load_band.min",
    "factor.mine_cifenli.surface_load_band.max",
)
_SPEED_MAX = "factor.mine_cifenli.disk.speed_max"
_PARAMS_POSITIVE = ("n_units", "omega", "q_surf", "m_seed")


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：台数/转速/表面负荷/磁种投加量非正一律拒。"""
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
            "（磁分离机单入单出语义）"
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


def _ss_in(inflow: WaterQuality) -> float:
    """进水 SS 取数（KS-F6 衔接链值）：缺指标=泥量衡算前提失败。"""
    value = inflow.concentrations.get("SS")
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 入流水质缺 SS 指标（KS-F6 截留率衡算的"
            " 衔接链值——矿井水线水质链 SS 必在，缺=上游装配缺陷）"
        )
    return value


def _disk_face(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow
) -> dict[str, float]:
    """KS-F1~F4：单台流量/单盘面积/需盘面面积/盘片数（整台 ceil）。"""
    q_1h = _apply(ctx, "KS-F1", {"q_design": flow.q_design, "n_units": p["n_units"]})
    a_disk = _apply(
        ctx,
        "KS-F2",
        {
            "pi": math.pi,
            "d_disk": _factor(p, "factor.mine_cifenli.disk.diameter"),
            "eta_im": _factor(p, "factor.mine_cifenli.disk.immersion"),
        },
    )
    a_total_req = _apply(ctx, "KS-F3", {"q_1h": q_1h, "q_surf": p["q_surf"]})
    n_disks_raw = _apply(ctx, "KS-F4", {"a_total_req": a_total_req, "a_disk": a_disk})
    return {
        "q_1h": q_1h,
        "a_disk": a_disk,
        "a_total_req": a_total_req,
        "n_disks_raw": n_disks_raw,
        # 盘片数整台向上取整（表 KS-F4 口径——DSL 无 ceil，本文件收口）
        "n_disks": float(math.ceil(n_disks_raw)),
    }


def _line_speed(ctx: UnitContext, p: dict[str, float]) -> float:
    """KS-F5：盘缘线速度（盘径×转速，≤0.3 m/s 校核）。"""
    return _apply(
        ctx,
        "KS-F5",
        {
            "pi": math.pi,
            "d_disk": _factor(p, "factor.mine_cifenli.disk.diameter"),
            "omega": p["omega"],
        },
    )


def _balance(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, ss_in: float
) -> dict[str, float]:
    """KS-F6~F8：截留泥量/磁泥湿量（平均日口径）+磁种净耗衡算。"""
    w_ss = _apply(
        ctx,
        "KS-F6",
        {
            "q_avg_daily": flow.q_avg_daily,
            "ss_in": ss_in,
            "eta_ss": _factor(p, "removal.mine_cifenli.ss.mod_default"),
        },
    )
    q_sludge = _apply(
        ctx,
        "KS-F7",
        {
            "w_ss": w_ss,
            "p_sludge": _factor(p, "factor.mine_cifenli.sludge.moisture"),
            "rho_sludge": _factor(p, "factor.mine_cifenli.sludge.density"),
        },
    )
    m_seed_net = _apply(
        ctx,
        "KS-F8",
        {
            "m_seed": p["m_seed"],
            "eta_recover": _factor(p, "factor.mine_cifenli.seed.recovery"),
        },
    )
    return {"w_ss": w_ss, "q_sludge": q_sludge, "m_seed_net": m_seed_net}


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(p: dict[str, float]) -> tuple[Warning, ...]:
    """校核带检查：盘面表面负荷带/盘转速上限（omega 对 speed_max 键）。"""
    found: list[Warning] = []
    load = _band(p, _LOAD_BAND)
    if not load[0] <= p["q_surf"] <= load[1]:
        found.append(
            _warn(
                f"{_GB}；{_LOAD_BAND[0]}~{_LOAD_BAND[1]}",
                f"盘面表面负荷 q_surf = {p['q_surf']:.4f} m³/(m²·h) 越出建议带"
                f" [{load[0]}, {load[1]}]——调节方向：q_surf（磁加载分离主控参数带内取值）",
                "q_surf",
            )
        )
    speed_max = _factor(p, _SPEED_MAX)
    if p["omega"] > speed_max:
        found.append(
            _warn(
                f"{_GB}；{_SPEED_MAX}",
                f"盘转速 omega = {p['omega']:.4f} rpm 越转速上限"
                f" {speed_max}（盘缘线速度 ≤0.3 m/s 折算口径）——调节方向：omega",
                "omega",
            )
        )
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
    return _MineCifenli()


@final
class _MineCifenli:
    """磁分离 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KS-F1~F8 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        face = _disk_face(ctx, p, flow)
        dims = {
            **face,
            "v_line": _line_speed(ctx, p),
            **_balance(ctx, p, flow, _ss_in(quality)),
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        sludge_ref = PortRef(unit_id=ctx.unit_id, port_id="sludge_out")
        return UnitResult(
            outflows={
                out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz),
                # GOLDEN4a D3 产股：无条件产股（nongsuo sup 先例同构）——
                # MS-F1 口径 ds=w_ss×KG_PER_TON（干基 kg/d——hebing 注入
                # ds_primary 位链路同源）；q_wet=KS-F7 直用（ρ=1100 直算
                # 口径）；moisture 与 hebing p_primary 注入位同源（系数键）。
                sludge_ref: SludgeFlow(
                    q_wet=dims["q_sludge"] / SECS_PER_DAY,
                    ds=dims["w_ss"] * KG_PER_TON / SECS_PER_DAY,
                    moisture=_factor(p, "factor.mine_cifenli.sludge.moisture"),
                ),
            },
            outqualities={
                out_ref: _out_quality(p, quality),
                sludge_ref: WaterQuality({}),  # 空 WaterQuality 单位元（R5/GR-04）
            },
            dims=dims,
            warnings=_warnings(p),
            formula_ids=FORMULA_IDS,
        )
