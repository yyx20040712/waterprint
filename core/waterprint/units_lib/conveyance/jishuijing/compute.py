"""集水井计算实现：唯一计算源（JS-F1~JS-F7 全经 registry.apply 求值）。

输入:  UnitContext（上游汇流量 + 参数 + 系数投影 + 迹收集器）
输出:  UnitResult（WATER 出流穿流透传 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【公式组】JS-F1~JS-F7（docs/norms/conveyance_jishuijing.md 起草表；
#   manifest.py 登记）——汇流集水容积（最高时停留法）→面积→井径→
#   实际面积→停留校核→总深→概算。
# 【汇流形态】多股来水经图入边到 in 口（propagate 按 dst 分组加权
#   合并——本单元只见合并后单股 WATER；多入/缺入/非水=领域异常）。
# 【DSL 收口】井径 0.5 m 构造档 ceil 在本文件收口（DSL 无 ceil，
#   ningjiao/wushui_tisheng 先例同型；步长=参数 dia_disc_step）。
# 【穿流口径】出流=入流双量透传（q_avg_daily/kz 恒等——零去除穿流，
#   不经公式面）；出流水质=入流水质逐指标恒等（穿流单元）。
# 【系数通道】factor.jishuijing.* 9 键经 ctx.params 投影面取值
#   （app._unit_params 剥 conveyance_ 前缀裸短名投影）；缺键=领域异常。
#   elevation_loss 键归高程链子系统（后续批），本文件不消费。
# 【输出面（D2）】outflows=出流一口穿流透传；dims=表结果全量 8 键
#   （v_well/a_well/d_raw/d/a_act/t_act/h_total/v_concrete）；
#   outqualities=出流口恒键、值为入流水质恒等透传（WATER 通道穿流
#   ——出流口恒键契约，executor 入流装配取上游 qualities 池键）；
#   warnings=三带越界（t_band 参数面/depth_band 参数面/d_band 结果面
#   ——出警告不阻断；param_key 归因+调节方向）；formula_ids=JS-F1~F7。
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
from waterprint.units_lib.conveyance.jishuijing.manifest import FORMULA_IDS, manifest

_UNIT_ID = "conveyance_jishuijing"
_HB = "给水排水设计手册（第 5 册 城镇排水）泵站章（集水设施常用带）"
_GB61 = "GB 50014-2021 §6.1（集水池容积参照口径，条号随追认核对）"
_T_BAND = ("factor.jishuijing.t_band.min", "factor.jishuijing.t_band.max")
_DEPTH_BAND = ("factor.jishuijing.depth_band.min", "factor.jishuijing.depth_band.max")
_D_BAND = ("factor.jishuijing.d_band.min", "factor.jishuijing.d_band.max")
_SUPERHEIGHT = "factor.jishuijing.superheight"
_WALL = "factor.jishuijing.wall_thickness_coef"
_PARAMS_POSITIVE = ("t_well", "h_well", "dia_disc_step")


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
    """井径构造档向上取整（步长>0 守卫；ningjiao B 档同型）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：停留时间/有效水深/井径档非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（propagate 汇流后单股）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边（propagate 汇流后"
            f"单股）：得到 {len(refs)} 股（集水井单入单出语义）"
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


def _well(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow
) -> dict[str, float]:
    """JS-F1~F5：汇流容积→面积→井径（0.5 m 档收口）→实际面积→停留校核。"""
    v_well = _apply(
        ctx, "JS-F1", {"q_design": flow.q_design, "t_well": p["t_well"]}
    )
    a_well = _apply(ctx, "JS-F2", {"v_well": v_well, "h_well": p["h_well"]})
    d_raw = _apply(ctx, "JS-F3", {"a_well": a_well})
    d = _ceil_step(d_raw, p["dia_disc_step"])
    a_act = _apply(ctx, "JS-F4", {"d": d})
    return {
        "v_well": v_well,
        "a_well": a_well,
        "d_raw": d_raw,
        "d": d,
        "a_act": a_act,
        "t_act": _apply(
            ctx,
            "JS-F5",
            {"a_act": a_act, "h_well": p["h_well"], "q_design": flow.q_design},
        ),
    }


def _shell(ctx: UnitContext, p: dict[str, float], a_act: float) -> dict[str, float]:
    """JS-F6~F7：井总深（超高键）+概算混凝土量（壁厚系数键）。"""
    h_total = _apply(
        ctx,
        "JS-F6",
        {"h_super": _factor(p, _SUPERHEIGHT), "h_well": p["h_well"]},
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "JS-F7",
            {
                "a_act": a_act,
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


def _warnings(p: dict[str, float], d: float) -> tuple[Warning, ...]:
    """校核带检查：停留带（参数面）/水深带（参数面）/井径带（结果面）。"""
    found: list[Warning] = []
    band = _band(p, _T_BAND)
    if not band[0] <= p["t_well"] <= band[1]:
        found.append(
            _warn(
                f"{_GB61}；{_T_BAND[0]}~{_T_BAND[1]}",
                f"汇流停留时间 t_well = {p['t_well']:.4f} min 越出建议带"
                f" [{band[0]}, {band[1]}]——调节方向：t_well（集水容积带内取值）",
                "t_well",
            )
        )
    depth = _band(p, _DEPTH_BAND)
    if not depth[0] <= p["h_well"] <= depth[1]:
        found.append(
            _warn(
                f"{_HB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"有效水深 h_well = {p['h_well']:.4f} m 越出建议带"
                f" [{depth[0]}, {depth[1]}]——调节方向：h_well（集水设施水深带内取值）",
                "h_well",
            )
        )
    diameter = _band(p, _D_BAND)
    if not diameter[0] <= d <= diameter[1]:
        found.append(
            _warn(
                f"{_HB}；{_D_BAND[0]}~{_D_BAND[1]}",
                f"井径 d = {d:.4f} m 越出建议带"
                f" [{diameter[0]}, {diameter[1]}]——调节方向：t_well/h_well"
                "（超上限宜分座或改矩形——构造合理性）",
                "t_well",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _ConveyanceJishuijing()


@final
class _ConveyanceJishuijing:
    """集水井 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """JS-F1~F7 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        well = _well(ctx, p, flow)
        shell = _shell(ctx, p, well["a_act"])
        dims = {**well, **shell}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            # 穿流透传：q_avg_daily/kz 双量恒等（零去除——不经公式面）
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            # 出流水质=入流水质逐指标恒等（穿流单元——出流口恒键契约）
            outqualities={out_ref: quality},
            dims=dims,
            warnings=_warnings(p, dims["d"]),
            formula_ids=FORMULA_IDS,
        )
