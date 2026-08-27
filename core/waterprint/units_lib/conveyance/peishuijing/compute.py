"""配水井计算实现：唯一计算源（PJ-F1~PJ-F12 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 系数投影 + 迹收集器）
输出:  UnitResult（动态多口出流 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【公式组】PJ-F1~PJ-F12（docs/norms/conveyance_peishuijing.md 起草表；
#   manifest.py 登记）——均匀分流→出流口水力（面积/流速/μ 反解水头）
#   →不均匀余量→井室断面→井径→总深→概算。
# 【多出流口口径（表内冻结）】manifest ports 声明单 OUT 口 "out"
#   （流体/方向声明锚点）；本文件按参数 n 动态产 out_1~out_n 多键
#   出流——每口 WaterFlow(q_avg_daily=入流/n, kz 透传)+水质逐指标
#   恒等透传（穿流）。分流守恒：Σ各口 q_avg_daily=入流 q_avg_daily
#   （D3 探针守恒正门锚）；n 非整值/非正=领域异常拒。
# 【DSL 收口】出流口 0.1 m 档（length_disc_step）与井径 0.5 m 档
#   （dia_disc_step）ceil 在本文件收口（DSL 无 ceil，
#   wushui_tisheng DN 档/ningjiao B 档先例同型）。
# 【流量口径】水力面按最高时 flow.q_design（出流口/井室）；出流每口
#   按平均日 q_avg_daily/n 分流（表头流量口径节逐字）。
# 【系数通道】factor.peishuijing.* 15 键经 ctx.params 投影面取值
#   （app._unit_params 剥 conveyance_ 前缀裸短名投影）；缺键=领域异常。
#   elevation_loss 键归高程链子系统（后续批），本文件不消费；
#   k_uneven_band 双键为数据包自校面，本文件不消费（constraints.py
#   注记同源）。
# 【输出面（D2）】outflows=out_1~out_n 动态多键（n 口分流）；dims=
#   表结果全量 14 键；outqualities=各出流口恒键、值为入流水质恒等
#   透传（WATER 通道穿流——出流口恒键契约，executor 入流装配取上游
#   qualities 池键）；warnings=四带越界（v_band/head_band 结果面+
#   v_channel_band/depth_band 参数面——出警告不阻断；param_key 归因+
#   调节方向）；formula_ids=PJ-F1~F12。
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
from waterprint.units_lib.conveyance.peishuijing.manifest import FORMULA_IDS, manifest

_UNIT_ID = "conveyance_peishuijing"
_HB3 = "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（孔口出流/不均匀系数）"
_HB5 = "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施参照常用带）"
_V_BAND = ("factor.peishuijing.v_band.min", "factor.peishuijing.v_band.max")
_HEAD_BAND = ("factor.peishuijing.head_band.min", "factor.peishuijing.head_band.max")
_V_CHANNEL_BAND = (
    "factor.peishuijing.v_channel_band.min",
    "factor.peishuijing.v_channel_band.max",
)
_DEPTH_BAND = ("factor.peishuijing.depth_band.min", "factor.peishuijing.depth_band.max")
_MU_OUT = "factor.peishuijing.mu_out"
_K_UNEVEN = "factor.peishuijing.k_uneven"
_SUPERHEIGHT = "factor.peishuijing.superheight"
_WALL = "factor.peishuijing.wall_thickness_coef"
_PARAMS_POSITIVE = (
    "v",
    "g_gravity",
    "length_disc_step",
    "v_channel",
    "h_well",
    "dia_disc_step",
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
    """构造档向上取整（步长>0 守卫；ningjiao B 档同型）。"""
    if step <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}"
        )
    return math.ceil(value / step) * step


def _series_count(params: dict[str, float]) -> int:
    """出流口数 n 收口：非正/非整值拒（grid [2,3,4] 档的 compute 侧守卫）。"""
    raw = params.get("n")
    count = int(raw) if raw is not None else 0
    if raw is None or count != raw or count <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'n' 须为正整数（grid 档 [2,3,4]——"
            f"出流口数）：得到 {raw!r}"
        )
    return count


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：流速/重力/档步长/断面流速/水深非正一律拒+n 整档收口。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    _series_count(params)


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（配水井单入多出语义）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 股"
            "（配水井单入多出语义）"
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


def _outlet(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, count: int
) -> dict[str, float]:
    """PJ-F1~F7：均匀分流→出流口水力→不均匀余量。"""
    q_each = _apply(
        ctx, "PJ-F1", {"q_design": flow.q_design, "n": float(count)}
    )
    a_out = _apply(ctx, "PJ-F2", {"q_each": q_each, "v_out": p["v"]})
    d_raw = _apply(ctx, "PJ-F3", {"a_out": a_out})
    d = _ceil_step(d_raw, p["length_disc_step"])
    a_act = _apply(ctx, "PJ-F4", {"d": d})
    v_act = _apply(ctx, "PJ-F5", {"q_each": q_each, "a_act": a_act})
    return {
        "q_each": q_each,
        "a_out": a_out,
        "d_raw": d_raw,
        "d": d,
        "a_act": a_act,
        "v_act": v_act,
        "h_head": _apply(
            ctx,
            "PJ-F6",
            {
                "v_act": v_act,
                "g_gravity": p["g_gravity"],
                "mu_out": _factor(p, _MU_OUT),
            },
        ),
        "q_series": _apply(
            ctx, "PJ-F7", {"q_each": q_each, "k_uneven": _factor(p, _K_UNEVEN)}
        ),
    }


def _chamber(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow
) -> dict[str, float]:
    """PJ-F8~F12：井室断面→井径（0.5 m 档收口）→总深→概算。"""
    a_well = _apply(
        ctx, "PJ-F8", {"q_design": flow.q_design, "v_channel": p["v_channel"]}
    )
    d_well_raw = _apply(ctx, "PJ-F9", {"a_well": a_well})
    d_well = _ceil_step(d_well_raw, p["dia_disc_step"])
    a_well_act = _apply(ctx, "PJ-F10", {"d_well": d_well})
    h_total = _apply(
        ctx,
        "PJ-F11",
        {"h_super": _factor(p, _SUPERHEIGHT), "h_well": p["h_well"]},
    )
    return {
        "a_well": a_well,
        "d_well_raw": d_well_raw,
        "d_well": d_well,
        "a_well_act": a_well_act,
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "PJ-F12",
            {
                "a_well_act": a_well_act,
                "h_total": h_total,
                "wall_coef": _factor(p, _WALL),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(
    p: dict[str, float], outlet: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：流速带/水头带（结果面）+断面流速带/水深带（参数面）。"""
    found: list[Warning] = []
    velocity = _band(p, _V_BAND)
    if not velocity[0] <= outlet["v_act"] <= velocity[1]:
        found.append(
            _warn(
                f"{_HB3}；{_V_BAND[0]}~{_V_BAND[1]}",
                f"出流口实际流速 v_act = {outlet['v_act']:.4f} m/s 越出建议带"
                f" [{velocity[0]}, {velocity[1]}]——调节方向：v（名义出流"
                "流速带内取值）",
                "v",
            )
        )
    head = _band(p, _HEAD_BAND)
    if not head[0] <= outlet["h_head"] <= head[1]:
        found.append(
            _warn(
                f"{_HB3}；{_HEAD_BAND[0]}~{_HEAD_BAND[1]}",
                f"孔口作用水头 h_head = {outlet['h_head']:.4f} m 越出建议带"
                f" [{head[0]}, {head[1]}]——调节方向：v（水头过小对施工"
                "高差敏感——配水均匀性不利）",
                "v",
            )
        )
    channel = _band(p, _V_CHANNEL_BAND)
    if not channel[0] <= p["v_channel"] <= channel[1]:
        found.append(
            _warn(
                f"{_HB5}；{_V_CHANNEL_BAND[0]}~{_V_CHANNEL_BAND[1]}",
                f"井室断面流速 v_channel = {p['v_channel']:.4f} m/s 越出建议带"
                f" [{channel[0]}, {channel[1]}]——调节方向：v_channel（集水"
                "设施断面流速带内取值）",
                "v_channel",
            )
        )
    depth = _band(p, _DEPTH_BAND)
    if not depth[0] <= p["h_well"] <= depth[1]:
        found.append(
            _warn(
                f"{_HB5}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"配水井有效水深 h_well = {p['h_well']:.4f} m 越出建议带"
                f" [{depth[0]}, {depth[1]}]——调节方向：h_well（集水设施"
                "水深带内取值）",
                "h_well",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _ConveyancePeishuijing()


@final
class _ConveyancePeishuijing:
    """配水井 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """PJ-F1~F12 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        count = _series_count(p)
        outlet = _outlet(ctx, p, flow, count)
        chamber = _chamber(ctx, p, flow)
        dims = {**outlet, **chamber}
        # 动态多口（表内冻结口径）：out_1~out_n 每口平均日均分+kz 透传；
        # 水质逐指标恒等透传（穿流——出流口恒键契约）
        outflows = {}
        outqualities = {}
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        for index in range(1, count + 1):
            ref = PortRef(unit_id=ctx.unit_id, port_id=f"out_{index}")
            outflows[ref] = WaterFlow(
                q_avg_daily=flow.q_avg_daily / count, kz=flow.kz
            )
            outqualities[ref] = quality
        return UnitResult(
            outflows=outflows,
            outqualities=outqualities,
            dims=dims,
            warnings=_warnings(p, outlet),
            formula_ids=FORMULA_IDS,
        )
