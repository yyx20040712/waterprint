"""平流沉砂池计算实现：唯一计算源（KC-F1~F10 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KC-F1~F10（docs/norms/mine_water_chenshachi.md 起草表；
#   manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池长
#   l_cell=ceil(l_cell_raw, side_disc_step 0.5 m 档)/池宽 B=ceil(
#   b_raw, length_disc_step 0.1 m 档)。零数值字面量。
# 【流量口径】池体水力按最高时 flow.q_design（KC-F1~F4/F7/F8）；
#   沉砂量按平均日 flow.q_avg_daily（KC-F5~F6，×86400 已内联公式串）
#   ——表流量口径逐字。
# 【系数通道】factor.mine_chenshachi.*/removal.mine_chenshachi.* 经
#   ctx.params 投影面取值（app._unit_params 线感知投影，mine_ 限定
#   键空间）；缺键=领域异常。elevation_loss 键归高程链子系统（后续
#   批），本文件不消费。
# 【输出面（D2）】outflows=入流透传+sludge_out SLUDGE 产股（GOLDEN4a D3
#   无条件产股——MS-F2 口径投影，注记见 manifest ports 注）；dims=表水力结果全量 snake 键；
#   outqualities=入质×(1−removal.mod_default) 单指标（SS×0.85，
#   COD 无键透传）；warnings=校核带越界（实际水平流速带/停留时间
#   带/有效水深带/单格宽下限/堰负荷上限；param_key 归因+调节方向）；
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
from waterprint.units_lib.mine_water.chenshachi.manifest import (
    FORMULA_IDS,
    KG_PER_TON,
    MOISTURE_SAND,
    RHO_SAND_WET,
    SECS_PER_DAY,
    manifest,
)

_UNIT_ID = "mine_water_chenshachi"
_HB = "给水排水设计手册（第 5 册 城镇排水）平流沉砂池水平流速/停留时间/砂斗常用带"
_VELOCITY_BAND = (
    "factor.mine_chenshachi.velocity_band.min",
    "factor.mine_chenshachi.velocity_band.max",
)
_RETENTION_BAND = (
    "factor.mine_chenshachi.retention_band.min",
    "factor.mine_chenshachi.retention_band.max",
)
_DEPTH_BAND = (
    "factor.mine_chenshachi.depth_band.min",
    "factor.mine_chenshachi.depth_band.max",
)
_CELL_WIDTH_MIN = "factor.mine_chenshachi.cell_width.min"
_WEIR_MAX = "factor.mine_chenshachi.weir_load.max"
_PARAMS_POSITIVE = ("n", "v_h", "t_stay", "h2", "t_clean", "side_disc_step", "length_disc_step")


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
    """构造步长向上取整（KC-F1/F3 的 0.5/0.1 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：格数/流速/停留/水深/清砂周期/步长非正一律拒。"""
    for key in _PARAMS_POSITIVE:
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


def _channel(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """KC-F1~F4：池长（0.5 m 档）/单格断面/池宽（0.1 m 档）/实际流速。"""
    l_cell_raw = _apply(ctx, "KC-F1", {"v_h": p["v_h"], "t_stay": p["t_stay"]})
    l_cell = _ceil_step(l_cell_raw, p["side_disc_step"])
    a_cross = _apply(
        ctx, "KC-F2", {"q_design": flow.q_design, "n": p["n"], "v_h": p["v_h"]}
    )
    b_raw = _apply(ctx, "KC-F3", {"a_cross": a_cross, "h2": p["h2"]})
    b = _ceil_step(b_raw, p["length_disc_step"])
    return {
        "l_cell_raw": l_cell_raw,
        "l_cell": l_cell,
        "a_cross": a_cross,
        "b_raw": b_raw,
        "b": b,
        "v_h_act": _apply(
            ctx, "KC-F4", {"q_design": flow.q_design, "n": p["n"], "b": b, "h2": p["h2"]}
        ),
    }


def _sand(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """KC-F5~F6：每日沉砂量与清砂周期贮砂需容积（平均日口径）。"""
    v_sand = _apply(
        ctx,
        "KC-F5",
        {
            "q_avg_daily": flow.q_avg_daily,
            "x_sand": _factor(p, "factor.mine_chenshachi.sand_yield_x"),
        },
    )
    v_hopper = _apply(
        ctx,
        "KC-F6",
        {
            "v_sand": v_sand,
            "t_clean": p["t_clean"],
            "safety": _factor(p, "factor.mine_chenshachi.hopper.safety"),
        },
    )
    return {"v_sand": v_sand, "v_hopper": v_hopper}


def _weir_and_concrete(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, channel: dict[str, float]
) -> dict[str, float]:
    """KC-F7~F10：出水堰长/堰负荷/池总高/概算混凝土量。"""
    l_weir = _apply(
        ctx,
        "KC-F7",
        {"n": p["n"], "l_cell": channel["l_cell"], "b": channel["b"]},
    )
    h_total = _apply(
        ctx,
        "KC-F9",
        {"h_super": _factor(p, "factor.mine_chenshachi.superheight"), "h2": p["h2"]},
    )
    return {
        "l_weir": l_weir,
        "q_weir": _apply(ctx, "KC-F8", {"q_design": flow.q_design, "l_weir": l_weir}),
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "KC-F10",
            {
                "l_cell": channel["l_cell"],
                "b": channel["b"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.mine_chenshachi.wall_thickness_coef"),
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
    p: dict[str, float], channel: dict[str, float], weir: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：实际流速/停留时间/有效水深/单格宽下限/堰负荷。"""
    found: list[Warning] = []
    vel = _band(p, _VELOCITY_BAND)
    if not vel[0] <= channel["v_h_act"] <= vel[1]:
        found.append(
            _warn(
                f"{_HB}；{_VELOCITY_BAND[0]}~{_VELOCITY_BAND[1]}",
                f"实际水平流速 = {channel['v_h_act']:.4f} m/s 越出建议带"
                f" [{vel[0]}, {vel[1]}]——调节方向：v_h（↑缩短池长↓断面）或 h2（↓收窄断面提流速）",
                "v_h",
            )
        )
    ret = _band(p, _RETENTION_BAND)
    if not ret[0] <= p["t_stay"] <= ret[1]:
        found.append(
            _warn(
                f"{_HB}；{_RETENTION_BAND[0]}~{_RETENTION_BAND[1]}",
                f"停留时间 = {p['t_stay']:.4f} s 越出建议带"
                f" [{ret[0]}, {ret[1]}]——调节方向：t_stay（沉砂效率与占地权衡带内取值）",
                "t_stay",
            )
        )
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= p["h2"] <= dep[1]:
        found.append(
            _warn(
                f"{_HB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"有效水深 h2 = {p['h2']:.4f} m 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：h2（浅池沉砂常用带内取值）",
                "h2",
            )
        )
    floor = _factor(p, _CELL_WIDTH_MIN)
    if channel["b_raw"] < floor:
        found.append(
            _warn(
                f"{_HB}；{_CELL_WIDTH_MIN}",
                f"理论单格宽 b_raw = {channel['b_raw']:.4f} m 低于下限"
                f" {floor}（0.1 m 档取整前校核）——调节方向：h2（↓加深收窄）"
                "或 n（↓减格展宽）",
                "h2",
            )
        )
    weir_max = _factor(p, _WEIR_MAX)
    if weir["q_weir"] > weir_max:
        found.append(
            _warn(
                f"{_HB}；{_WEIR_MAX}",
                f"出水堰负荷 = {weir['q_weir']:.4f} L/(s·m) 超上限"
                f" {weir_max}——调节方向：t_stay（↑增长延长堰长）或 n（↑加格）",
                "t_stay",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：单指标 ×(1−removal.mod_default)（SS 砂粒组分），其余透传。"""
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
    return _MineChenshachi()


@final
class _MineChenshachi:
    """平流沉砂池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KC-F1~F10 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        channel = _channel(ctx, p, flow)
        sand = _sand(ctx, p, flow)
        weir = _weir_and_concrete(ctx, p, flow, channel)
        dims = {**channel, **sand, **weir}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        sludge_ref = PortRef(unit_id=ctx.unit_id, port_id="sludge_out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            outflows={
                out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz),
                # GOLDEN4a D3 产股：无条件产股（nongsuo sup 先例同构）——
                # MS-F2 链级衔接式 ds=v_sand×ρ湿砂×(1−p_sand)×1000（投影
                # 非计算不注册——hebing 注入 ds_bio 位链路同源）；q_wet=
                # v_sand 湿砂体积直算口径；moisture=p_sand（manifest 常量
                # 直值注记，系数键化归后续批呈报不扩 coefficients）。
                sludge_ref: SludgeFlow(
                    q_wet=sand["v_sand"] / SECS_PER_DAY,
                    ds=sand["v_sand"]
                    * RHO_SAND_WET
                    * (1 - MOISTURE_SAND)
                    * KG_PER_TON
                    / SECS_PER_DAY,
                    moisture=MOISTURE_SAND,
                ),
            },
            outqualities={
                out_ref: _out_quality(p, quality),
                sludge_ref: WaterQuality({}),  # 空 WaterQuality 单位元（R5/GR-04）
            },
            dims=dims,
            warnings=_warnings(p, channel, weir),
            formula_ids=FORMULA_IDS,
        )
