"""污泥泵站计算实现：唯一计算源（BZ-F1~BZ-F18 全经 registry.apply 求值）。

输入:  UnitContext（上游 SLUDGE 量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（SLUDGE 出流三量穿流 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】BZ-F1~BZ-F18（docs/norms/sludge_bengzhan.md 起草表；
#   manifest.py 登记）——泵组选型（锚值取整+备用）+ 扬程三分量
#   （静扬程+管损[λ 沿程+ζ 局部×污泥粘度修正]+自由水头）+ 集泥井
#   调节容积/启停校核/概算（wushui_tisheng 泵族先例形态）+ DS/含水率
#   穿流守恒显式。
# 【DSL 收口】泵台数整台向上取整（n_pump_duty=ceil(n_pump_raw)）与
#   出泥管径 0.025 m 档（DN25 步进）ceil 在本文件收口（DSL 无 ceil；
#   离散化后作下游公式输入符号）。零数值字面量。
# 【入流装配】恰一入边且为 SLUDGE（shusong 同款）；入流三量
#   ×SECS_PER_DAY 回工程口径，出流穿流回契约口径。
# 【三量链回显】dims 加 q_in/ds_in/p_in/q_out（ds_out/p_out 即表键）
#   ——进出泥量-含水率-DS 六量全回显。
# 【系数通道】factor.bengzhan.* 17 键经 ctx.params 投影面取值（裸
#   短名投影）；缺键=领域异常。elevation_loss 键归高程链子系统（提升
#   能量由 h_pump 公式承载——表"其他数据键"语义分工注记），本文件
#   不消费。
# 【输出面（D2）】outflows=出流一口 SLUDGE 三量穿流；dims=表结果
#   20 项+回显 4 项；outqualities={}；warnings=五带校核（单泵流量带/
#   出泥管流速带/启停上限/集泥井时间带/水深带；param_key 归因+调节
#   方向）；formula_ids=BZ-F1~F18 全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
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
from waterprint.units_lib.sludge.bengzhan.manifest import (
    FORMULA_IDS,
    PIPE_DISC_STEP,
    SECS_PER_DAY,
    manifest,
)

_UNIT_ID = "sludge_bengzhan"
_GB = "GB 50014-2021 §6.1（泵站集水池容积/备用泵）与 §8（污泥章，条号待核对）"
_HB5 = "给水排水设计手册（第 5 册 城镇排水）污泥泵站章（泵组选型/集泥井常用带）"
_Q_PER_PUMP = "factor.bengzhan.pump.q_per_unit"
_Q_FLOW_BAND = (
    "factor.bengzhan.pump.q_flow_band.min",
    "factor.bengzhan.pump.q_flow_band.max",
)
_FREE_HEAD = "factor.bengzhan.pump.free_head"
_START_MAX = "factor.bengzhan.pump.start_band.max"
_V_BAND = (
    "factor.bengzhan.pipe.velocity_band.min",
    "factor.bengzhan.pipe.velocity_band.max",
)
_ZETA = "factor.bengzhan.pipe.zeta_total"
_LAMBDA = "factor.bengzhan.friction_lambda"
_K_SLUDGE = "factor.bengzhan.k_sludge"
_T_BAND = (
    "factor.bengzhan.well.t_band.min",
    "factor.bengzhan.well.t_band.max",
)
_DEPTH_BAND = (
    "factor.bengzhan.well.depth_band.min",
    "factor.bengzhan.well.depth_band.max",
)
_SUPER = "factor.bengzhan.superheight"
_WALL = "factor.bengzhan.wall_thickness_coef"
_PARAMS_POSITIVE = (
    "n_standby",
    "h_static",
    "l_pipe",
    "v_pipe",
    "t_well",
    "h_well",
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


def _band(params: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(params, keys[0]), _factor(params, keys[1])


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：备用台数/静扬程/管长/名义流速/调节时间/水深非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )


def _inflow(ctx: UnitContext) -> SludgeFlow:
    """入流装配：恰一入边且为 SLUDGE（多入/缺入/水线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], SludgeFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 SLUDGE 入边：得到 {len(refs)} 条"
            "（泵站单入单出语义）"
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


def _ceil_step(value: float, step: float) -> float:
    """构造步长向上取整（BZ-F6 的 DN25 档离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}"
        )
    return math.ceil(value / step) * step


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _pumps(ctx: UnitContext, p: dict[str, float], q_wet: float) -> dict[str, float]:
    """BZ-F1~F5：泵组选型（锚值整台取整+均分反算+备用合成）。"""
    q_h = _apply(ctx, "BZ-F1", {"q_wet": q_wet})
    n_pump_raw = _apply(
        ctx, "BZ-F2", {"q_h": q_h, "q_per_pump": _factor(p, _Q_PER_PUMP)}
    )
    n_pump_duty = float(math.ceil(n_pump_raw))
    q_pump_h = _apply(ctx, "BZ-F3", {"q_h": q_h, "n_pump_duty": n_pump_duty})
    return {
        "q_h": q_h,
        "n_pump_raw": n_pump_raw,
        "n_pump_duty": n_pump_duty,
        "q_pump_h": q_pump_h,
        "q_pump_si": _apply(ctx, "BZ-F4", {"q_pump_h": q_pump_h}),
        "n_total": _apply(
            ctx, "BZ-F5", {"n_pump_duty": n_pump_duty, "n_standby": p["n_standby"]}
        ),
    }


def _pipe(ctx: UnitContext, p: dict[str, float], pumps: dict[str, float]) -> dict[str, float]:
    """BZ-F6~F7：出泥管径（DN25 档取整）与实际流速。"""
    d_raw = _apply(
        ctx,
        "BZ-F6",
        {"q_pump_si": pumps["q_pump_si"], "pi": math.pi, "v_pipe": p["v_pipe"]},
    )
    d_pipe = _ceil_step(d_raw, PIPE_DISC_STEP)
    return {
        "d_raw": d_raw,
        "d_pipe": d_pipe,
        "v_act": _apply(
            ctx,
            "BZ-F7",
            {"q_pump_si": pumps["q_pump_si"], "pi": math.pi, "d_pipe": d_pipe},
        ),
    }


def _head(ctx: UnitContext, p: dict[str, float], pipe: dict[str, float]) -> dict[str, float]:
    """BZ-F8~F11：扬程三分量（λ 沿程+ζ 局部×污泥粘度修正+自由水头）。"""
    h_friction = _apply(
        ctx,
        "BZ-F8",
        {
            "lambda_f": _factor(p, _LAMBDA),
            "l_pipe": p["l_pipe"],
            "d_pipe": pipe["d_pipe"],
            "v_act": pipe["v_act"],
        },
    )
    h_local = _apply(
        ctx, "BZ-F9", {"zeta_total": _factor(p, _ZETA), "v_act": pipe["v_act"]}
    )
    h_loss = _apply(
        ctx,
        "BZ-F10",
        {
            "h_friction": h_friction,
            "h_local": h_local,
            "k_sludge": _factor(p, _K_SLUDGE),
        },
    )
    return {
        "h_friction": h_friction,
        "h_local": h_local,
        "h_loss": h_loss,
        "h_pump": _apply(
            ctx,
            "BZ-F11",
            {
                "h_static": p["h_static"],
                "h_loss": h_loss,
                "h_free": _factor(p, _FREE_HEAD),
            },
        ),
    }


def _well(
    ctx: UnitContext, p: dict[str, float], pumps: dict[str, float]
) -> dict[str, float]:
    """BZ-F12~F16：集泥井调节容积/面积/启停校核/总高/概算。"""
    v_well = _apply(
        ctx, "BZ-F12", {"q_pump_si": pumps["q_pump_si"], "t_well": p["t_well"]}
    )
    a_well = _apply(ctx, "BZ-F13", {"v_well": v_well, "h_well": p["h_well"]})
    h_well_total = _apply(
        ctx, "BZ-F15", {"h_super": _factor(p, _SUPER), "h_well": p["h_well"]}
    )
    return {
        "v_well": v_well,
        "a_well": a_well,
        "n_start": _apply(
            ctx, "BZ-F14", {"q_pump_si": pumps["q_pump_si"], "v_well": v_well}
        ),
        "h_well_total": h_well_total,
        "v_concrete": _apply(
            ctx,
            "BZ-F16",
            {
                "a_well": a_well,
                "h_well_total": h_well_total,
                "wall_coef": _factor(p, _WALL),
            },
        ),
    }


def _warnings(
    p: dict[str, float],
    pumps: dict[str, float],
    pipe: dict[str, float],
    well: dict[str, float],
) -> tuple[Warning, ...]:
    """五带校核：单泵流量带/出泥管流速带/启停上限/集泥井时间带/水深带。"""
    found: list[Warning] = []
    flow_band = _band(p, _Q_FLOW_BAND)
    if not flow_band[0] <= pumps["q_pump_h"] <= flow_band[1]:
        found.append(
            _warn(
                f"{_HB5}；{_Q_FLOW_BAND[0]}~{_Q_FLOW_BAND[1]}",
                f"单泵流量 q_pump_h = {pumps['q_pump_h']:.4f} m³/h 越出常用带"
                f" [{flow_band[0]}, {flow_band[1]}]——调节方向：泵组锚键"
                "（factor.bengzhan.pump.q_per_unit 换档）",
                "n_pump_duty",
            )
        )
    v_band = _band(p, _V_BAND)
    if not v_band[0] <= pipe["v_act"] <= v_band[1]:
        found.append(
            _warn(
                f"{_GB}；{_V_BAND[0]}~{_V_BAND[1]}",
                f"出泥管实际流速 v_act = {pipe['v_act']:.4f} m/s 越出建议带"
                f" [{v_band[0]}, {v_band[1]}]（取整后实流速）——调节方向："
                "v_pipe（名义流速改档使取整管径落带）",
                "v_pipe",
            )
        )
    start_max = _factor(p, _START_MAX)
    if well["n_start"] > start_max:
        found.append(
            _warn(
                f"{_HB5}；{_START_MAX}",
                f"启停频率 n_start = {well['n_start']:.4f} 次/h 超上限"
                f" {start_max}——调节方向：t_well（延长调节时间增大井容）",
                "t_well",
            )
        )
    t_band = _band(p, _T_BAND)
    if not t_band[0] <= p["t_well"] <= t_band[1]:
        found.append(
            _warn(
                f"{_GB}；{_T_BAND[0]}~{_T_BAND[1]}",
                f"集泥井调节时间 t_well = {p['t_well']:.4f} min 越出建议带"
                f" [{t_band[0]}, {t_band[1]}]——调节方向：t_well（带内取值）",
                "t_well",
            )
        )
    depth_band = _band(p, _DEPTH_BAND)
    if not depth_band[0] <= p["h_well"] <= depth_band[1]:
        found.append(
            _warn(
                f"{_HB5}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"集泥井有效水深 h_well = {p['h_well']:.4f} m 越出建议带"
                f" [{depth_band[0]}, {depth_band[1]}]——调节方向：h_well"
                "（带内取值）",
                "h_well",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _SludgeBengzhan()


@final
class _SludgeBengzhan:
    """污泥泵站 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """BZ-F1~F18 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        inflow = _inflow(ctx)
        q_wet = inflow.q_wet * SECS_PER_DAY
        ds_in = inflow.ds * SECS_PER_DAY
        p_in = inflow.moisture
        pumps = _pumps(ctx, p, q_wet)
        pipe = _pipe(ctx, p, pumps)
        head = _head(ctx, p, pipe)
        well = _well(ctx, p, pumps)
        ds_out = _apply(ctx, "BZ-F17", {"ds_in": ds_in})
        p_out = _apply(ctx, "BZ-F18", {"p_in": p_in})
        dims = {
            "q_in": q_wet,
            "ds_in": ds_in,
            "p_in": p_in,
            **pumps,
            **pipe,
            **head,
            **well,
            "ds_out": ds_out,
            "p_out": p_out,
            "q_out": q_wet,
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={
                out_ref: SludgeFlow(
                    q_wet=q_wet / SECS_PER_DAY, ds=ds_out / SECS_PER_DAY,
                    moisture=p_out,
                )
            },
            # 出流水质面=空 WaterQuality 单位元（R5/GR-04——SLUDGE 通道
            # 无水质指标，但出流面两 Mapping 口恒有键：executor 入流
            # 装配取上游 qualities 池键的纯污泥图前提，builtin 三节点
            # 同款形态）
            outqualities={out_ref: WaterQuality({})},
            dims=dims,
            warnings=_warnings(p, pumps, pipe, well),
            formula_ids=FORMULA_IDS,
        )
