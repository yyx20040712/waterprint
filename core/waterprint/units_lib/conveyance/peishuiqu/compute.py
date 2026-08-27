"""配水渠计算实现：唯一计算源（PQ-F1~PQ-F7 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 系数投影 + 迹收集器）
输出:  UnitResult（动态多口出流 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【公式组】PQ-F1~PQ-F7（docs/norms/conveyance_peishuiqu.md 起草表；
#   manifest.py 登记）——均匀分流→渠道过流断面→渠内水深→堰顶水头
#   （m·b·√(2g) 反解 H^(2/3)）→不均匀余量→渠深→渠末段流速校核
#   （变流量渠末段仅输最后一路——防淤积）。
# 【多出流口口径（表内冻结）】与 peishuijing 同款——manifest ports
#   声明单 OUT 口 "out"（声明锚点）；本文件按参数 n 动态产
#   out_1~out_n 多键出流（每口 WaterFlow(q_avg_daily=入流/n, kz 透传)
#   +水质逐指标恒等透传）。分流守恒：Σ各口 q_avg_daily=入流
#   q_avg_daily（D3 探针守恒正门锚）；n 非整值/非正=领域异常拒。
# 【DSL 收口】无构造档取整（渠道断面/堰顶水头连续值——表口径）。
# 【流量口径】断面/堰水力面按最高时 flow.q_design；出流每口按平均日
#   q_avg_daily/n 分流（表头流量口径节逐字）。
# 【系数通道】factor.peishuiqu.* 12 键经 ctx.params 投影面取值
#   （app._unit_params 剥 conveyance_ 前缀裸短名投影）；缺键=领域异常。
#   elevation_loss 键归高程链子系统（后续批），本文件不消费；
#   k_uneven_band 双键为数据包自校面，m_weir/k_uneven 消费值键
#   （PQ-F4/PQ-F5），带键不消费（constraints.py 注记同源）。
# 【输出面（D2）】outflows=out_1~out_n 动态多键；dims=表结果全量
#   7 键（q_each/a_channel/h_water/h_weir/q_series/h_total/v_end）；
#   outqualities=各出流口恒键、值为入流水质恒等透传（WATER 通道
#   穿流——executor 入流装配取上游 qualities 池键）；warnings=三带
#   越界（v_channel_band 参数面+h_weir_band/v_end_band 结果面——
#   出警告不阻断；param_key 归因+调节方向）；formula_ids=PQ-F1~F7。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

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
from waterprint.units_lib.conveyance.peishuiqu.manifest import FORMULA_IDS, manifest

_UNIT_ID = "conveyance_peishuiqu"
_HB3 = "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（薄壁堰/不均匀系数）"
_GB4V = "GB 50014-2021 §4（最小流速防淤积，条号随追认核对）"
_V_CHANNEL_BAND = (
    "factor.peishuiqu.v_channel_band.min",
    "factor.peishuiqu.v_channel_band.max",
)
_H_WEIR_BAND = ("factor.peishuiqu.h_weir_band.min", "factor.peishuiqu.h_weir_band.max")
_V_END_BAND = ("factor.peishuiqu.v_end_band.min", "factor.peishuiqu.v_end_band.max")
_M_WEIR = "factor.peishuiqu.m_weir"
_K_UNEVEN = "factor.peishuiqu.k_uneven"
_SUPERHEIGHT = "factor.peishuiqu.superheight"
_PARAMS_POSITIVE = ("b_channel", "v_channel", "b", "g_gravity")


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


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
    """参数域守卫：渠宽/渠内流速/堰长/重力非正一律拒+n 整档收口。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    _series_count(params)


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（配水渠单入多出语义）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 股"
            "（配水渠单入多出语义）"
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


def _channel(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, count: int
) -> dict[str, float]:
    """PQ-F1~F7：分流→渠道断面/水深→堰顶水头→余量→渠深→渠末流速。"""
    q_each = _apply(
        ctx, "PQ-F1", {"q_design": flow.q_design, "n": float(count)}
    )
    a_channel = _apply(
        ctx, "PQ-F2", {"q_design": flow.q_design, "v_channel": p["v_channel"]}
    )
    h_water = _apply(
        ctx, "PQ-F3", {"a_channel": a_channel, "b_channel": p["b_channel"]}
    )
    h_weir = _apply(
        ctx,
        "PQ-F4",
        {
            "q_each": q_each,
            "m_weir": _factor(p, _M_WEIR),
            "b": p["b"],
            "g_gravity": p["g_gravity"],
        },
    )
    return {
        "q_each": q_each,
        "a_channel": a_channel,
        "h_water": h_water,
        "h_weir": h_weir,
        "q_series": _apply(
            ctx, "PQ-F5", {"q_each": q_each, "k_uneven": _factor(p, _K_UNEVEN)}
        ),
        "h_total": _apply(
            ctx, "PQ-F6", {"h_super": _factor(p, _SUPERHEIGHT), "h_water": h_water}
        ),
        "v_end": _apply(
            ctx, "PQ-F7", {"q_each": q_each, "a_channel": a_channel}
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _warnings(
    p: dict[str, float], channel: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：渠内流速带（参数面）+堰顶水头带/渠末流速带（结果面）。"""
    found: list[Warning] = []
    velocity = _band(p, _V_CHANNEL_BAND)
    if not velocity[0] <= p["v_channel"] <= velocity[1]:
        found.append(
            _warn(
                f"{_HB3}；{_V_CHANNEL_BAND[0]}~{_V_CHANNEL_BAND[1]}",
                f"渠内设计流速 v_channel = {p['v_channel']:.4f} m/s 越出建议带"
                f" [{velocity[0]}, {velocity[1]}]——调节方向：v_channel（渠道"
                "设计流速带内取值）",
                "v_channel",
            )
        )
    head = _band(p, _H_WEIR_BAND)
    if not head[0] <= channel["h_weir"] <= head[1]:
        found.append(
            _warn(
                f"{_HB3}；{_H_WEIR_BAND[0]}~{_H_WEIR_BAND[1]}",
                f"堰顶水头 h_weir = {channel['h_weir']:.4f} m 越出建议带"
                f" [{head[0]}, {head[1]}]——调节方向：b（堰长带内取值；"
                "水头过小对堰顶施工高差敏感——配水均匀性不利）",
                "b",
            )
        )
    end = _band(p, _V_END_BAND)
    if not end[0] <= channel["v_end"] <= end[1]:
        found.append(
            _warn(
                f"{_GB4V}；{_V_END_BAND[0]}~{_V_END_BAND[1]}",
                f"渠末段流速 v_end = {channel['v_end']:.4f} m/s 越出建议带"
                f" [{end[0]}, {end[1]}]——渠末段淤积风险（变流量渠末段仅输"
                "最后一路）；调节方向：v_channel↑或 n↓（提高末段单路流量）",
                "v_channel",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _ConveyancePeishuiqu()


@final
class _ConveyancePeishuiqu:
    """配水渠 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """PQ-F1~F7 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        count = _series_count(p)
        channel = _channel(ctx, p, flow, count)
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
            dims=channel,
            warnings=_warnings(p, channel),
            formula_ids=FORMULA_IDS,
        )
