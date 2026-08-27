"""污泥干化计算实现：唯一计算源（GH-F1~GH-F8 全经 registry.apply 求值）。

输入:  UnitContext（上游 SLUDGE 量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（SLUDGE 出流三量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】GH-F1~GH-F8（docs/norms/sludge_ganhua.md 起草表；
#   manifest.py 登记）——热干化热量衡算主线：进泥湿质量（三量链
#   质量基）→蒸发水量（干基水量差式——与旧系统湿质量差式同值
#   异形[DS 项相消]）→出泥三量链（体积基）→质量守恒校核（差 0）
#   →热量衡算（潜热/热效率）→燃料耗量（天然气基热值档）→传热
#   面积校核。
# 【机档口径】method 枚举 v1 不进参数面（thermal 单线无分支——
#   solar 档蒸发速率参数归档位重定义，表交叉对照"追认点"注记）。
# 【入流装配】恰一入边且为 SLUDGE（shusong 同款）；入流三量
#   ×SECS_PER_DAY 回工程口径，出流三量（q_out/ds 不变/p_out）回
#   契约口径。
# 【三量链回显】dims 加 q_in/ds_in/p_in/ds_out/p_out（q_out 即表键；
#   ds_out=ds_in 不变——DS 守恒）——进出六量全回显。
# 【系数通道】factor.ganhua.* 8 键经 ctx.params 投影面取值（裸
#   短名投影）；缺键=领域异常。elevation_loss 键归高程链子系统，
#   本文件不消费（车间设备单元不建 wall_thickness_coef——bashi/
#   tuoshui 先例口径）。
# 【输出面（D2）】outflows=出流一口 SLUDGE 三量；dims=表结果 8 项
#   +回显 5 项；outqualities=出流口恒键、值为空
#   WaterQuality 单元（SLUDGE 通道无水质指标——R5 单位元语义，GR-04）；
#   warnings=两带校核（干化后含水率带/蒸发强度带；param_key 归因+调节方向）；
#   带/蒸发强度带；param_key 归因+调节方向）；formula_ids=GH-F1~F8
#   全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import final

from waterprint.contracts.condition import ConditionSet
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
from waterprint.units_lib.sludge.ganhua.manifest import FORMULA_IDS, SECS_PER_DAY, manifest

_UNIT_ID = "sludge_ganhua"
_GB = "GB 50014-2021 §8（污泥章——干化后含水率档，条号待核对）"
_HB5 = "给水排水设计手册（第 5 册 城镇排水）污泥干化章（常用带）"
_MOISTURE_BAND = (
    "factor.ganhua.moisture_out_band.min",
    "factor.ganhua.moisture_out_band.max",
)
_EVAP_BAND = (
    "factor.ganhua.evap_rate_band.min",
    "factor.ganhua.evap_rate_band.max",
)
_H_EVAP = "factor.ganhua.h_evap"
_ETA_THERMAL = "factor.ganhua.eta_thermal"
_FUEL = "factor.ganhua.fuel_calorific"
_PARAMS_POSITIVE = ("t_op", "r_evap")


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


def _band(params: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(params, keys[0]), _factor(params, keys[1])


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：运行时/蒸发强度非正拒；p_out 开域 (0,1)。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    p_out = params.get("p_out")
    if p_out is None or not 0 < p_out < 1:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'p_out' 必须在开区间 (0,1)"
            f"（小数含水率——闭边界使干基换算除零）：得到 {p_out!r}"
        )


def _inflow(ctx: UnitContext) -> SludgeFlow:
    """入流装配：恰一入边且为 SLUDGE（多入/缺入/水线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], SludgeFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 SLUDGE 入边：得到 {len(refs)} 条"
            "（干化机单入单出语义）"
        )
    flow = ctx.inflows[refs[0]]
    assert isinstance(flow, SludgeFlow)  # 上行守卫已收窄，窄化供类型面
    return flow


def _apply(ctx: UnitContext, formula_id: str, bindings: dict[str, float]) -> float:
    """apply 薄封装：统一携带 (unit_id, condition_key) 与 trace sink。"""
    return formulas.apply(
        formula_id,
        bindings,
        (ctx.unit_id, ConditionSet.key(ctx.condition)),
        sink=ctx.trace,
    )


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _SludgeGanhua()


@final
class _SludgeGanhua:
    """污泥干化 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """GH-F1~F8 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        inflow = _inflow(ctx)
        q_wet = inflow.q_wet * SECS_PER_DAY
        ds_in = inflow.ds * SECS_PER_DAY
        p_in = inflow.moisture
        m_in = _apply(ctx, "GH-F1", {"ds_in": ds_in, "p_in": p_in})
        w_evap = _apply(
            ctx, "GH-F2", {"ds_in": ds_in, "p_in": p_in, "p_out": p["p_out"]}
        )
        q_out = _apply(ctx, "GH-F3", {"ds_in": ds_in, "p_out": p["p_out"]})
        m_out = _apply(ctx, "GH-F4", {"ds_in": ds_in, "p_out": p["p_out"]})
        m_check = _apply(ctx, "GH-F5", {"m_in": m_in, "w_evap": w_evap})
        q_heat = _apply(
            ctx,
            "GH-F6",
            {
                "w_evap": w_evap,
                "h_evap": _factor(p, _H_EVAP),
                "eta_thermal": _factor(p, _ETA_THERMAL),
            },
        )
        w_fuel = _apply(ctx, "GH-F7", {"q_heat": q_heat, "q_cal_fuel": _factor(p, _FUEL)})
        a_dry = _apply(
            ctx, "GH-F8", {"w_evap": w_evap, "r_evap": p["r_evap"], "t_op": p["t_op"]}
        )
        dims = {
            "q_in": q_wet,
            "ds_in": ds_in,
            "p_in": p_in,
            "m_in": m_in,
            "w_evap": w_evap,
            "q_out": q_out,
            "m_out": m_out,
            "m_check": m_check,
            "q_heat": q_heat,
            "w_fuel": w_fuel,
            "a_dry": a_dry,
            "ds_out": ds_in,  # DS 不变（干化不改干基）
            "p_out": p["p_out"],
        }
        warnings: list[Warning] = []
        moisture_band = _band(p, _MOISTURE_BAND)
        if not moisture_band[0] <= p["p_out"] <= moisture_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_GB}；{_MOISTURE_BAND[0]}~{_MOISTURE_BAND[1]}",
                    message=(
                        f"干化后含水率 p_out = {p['p_out']:.4f} 越出建议带"
                        f" [{moisture_band[0]}, {moisture_band[1]}]——调节方向："
                        "p_out（半干化档带内取值，全干化 <0.20 归设备批）"
                    ),
                    param_key="p_out",
                )
            )
        evap_band = _band(p, _EVAP_BAND)
        if not evap_band[0] <= p["r_evap"] <= evap_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_HB5}；{_EVAP_BAND[0]}~{_EVAP_BAND[1]}",
                    message=(
                        f"传热面积蒸发强度 r_evap = {p['r_evap']:.4f} kg/(m²·h)"
                        f" 越出建议带 [{evap_band[0]}, {evap_band[1]}]——调节"
                        "方向：r_evap（间接式干化设备带内取值）"
                    ),
                    param_key="r_evap",
                )
            )
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={
                out_ref: SludgeFlow(
                    q_wet=q_out / SECS_PER_DAY,
                    ds=ds_in / SECS_PER_DAY,
                    moisture=p["p_out"],
                )
            },
            # 出流水质面=空 WaterQuality 单位元（R5/GR-04——SLUDGE 通道
            # 无水质指标，但出流面两 Mapping 口恒有键：executor 入流
            # 装配取上游 qualities 池键的纯污泥图前提，builtin 三节点
            # 同款形态）
            outqualities={out_ref: WaterQuality({})},
            dims=dims,
            warnings=tuple(warnings),
            formula_ids=FORMULA_IDS,
        )
