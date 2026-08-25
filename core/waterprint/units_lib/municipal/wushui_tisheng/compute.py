"""污水提升泵房计算实现：唯一计算源（TS-F1~F14 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【公式组】TS-F1~F14（docs/norms/wushui_tisheng.md 起草表；manifest.py
#   登记）——集水井调节容积法+泵扬程三分量主线：选泵（F1~F3，整台
#   ceil 收口）、压力管水力（F4~F6，DN 0.1 m 档 ceil+比阻档表键命中）、
#   局部损失与管路总损（F7~F8）、泵扬程三分量（F9，M2b1 追认点 14
#   承接）、集水井与启停校核（F10~F12）、井体几何与概算（F13~F14）。
# 【DSL 收口】ceil 离散在本文件收口（DSL 无 ceil）：工作泵台数
#   n_pump_duty=ceil(n_pump_raw) 整台；出水管径 d_pipe=ceil(d_pipe_raw,
#   dia_disc_step 0.1 m 档=DN 档)。DN 档命中比阻表键（dn300~dn800），
#   越表=领域异常（档表覆盖面显式声明）。q_design_h/q_pump_si 经
#   sec_per_hour 参数符号合成（AO-F13 同款，零换算字面量）。
# 【流量口径（三表逐字冻结）】水泵与压力管按最高时 flow.q_design
#   （峰值提升能力）；集水井调节容积按最大一台泵出水量（工作泵均分）。
# 【系数通道】factor.wushui_tisheng.*/removal.wushui_tisheng.* 经
#   ctx.params 投影面取值（app._unit_params，M1a 现状对齐）；缺键=
#   领域异常。
# 【输出面（D2）】outflows=入流透传；dims=三表水力/设备结果全量 snake
#   键（h_pump 扬程=本表核心产出，elevation 面消费归出图批 UF-32 契约）；
#   outqualities=零去除键透传（removal.wushui_tisheng.*.mod_default 全
#   0.0——提升单元无处理，透传分支不经 apply、formula_ids 不含去除式，
#   ziwai/bashi 零去除形态同款记档）；warnings=四条校核带越界（实际
#   流速带/单泵流量带/启停上限/调节时间带——param_key 归因+调节方向）；
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
from waterprint.contracts.unit_api import (
    Severity,
    Unit,
    UnitContext,
    UnitResult,
    Warning,
)
from waterprint.registry import formulas
from waterprint.units_lib.municipal.wushui_tisheng.manifest import (
    DN_RESISTANCE,
    FORMULA_IDS,
    manifest,
)

_UNIT_ID = "municipal_wushui_tisheng"
_GB = "GB 50014-2021 §6.1"
_HB = "给水排水设计手册（第 5 册 城镇排水）泵站章"
_HB1 = "给水排水设计手册（第 1 册 常用资料）水管比阻表"
_PARAMS_POSITIVE = (
    "h_static",
    "v_pipe",
    "l_pipe",
    "n_standby",
    "h_well",
    "t_well",
    "dia_disc_step",
    "g_gravity",
    "sec_per_hour",
)
# DN 档→比阻表键段（DN_RESISTANCE 真源区取值：d_pipe 按 0.1 m 档
# ceil 后的档值命中，越表=领域异常）。
_DN_KEYS: dict[float, str] = dict(DN_RESISTANCE)
_Q_PER_PUMP = "factor.wushui_tisheng.pump.q_per_unit"
_FREE_HEAD = "factor.wushui_tisheng.pump.free_head"
_ZETA = "factor.wushui_tisheng.pipe.zeta_total"


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
    """构造步长向上取整（DN 0.1 m 档；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：静扬程/流速/管长/备用台数/井几何/步长/换算非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（泵房单入单出语义）"
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


def _pumps(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """TS-F1~F3：选泵（整台 ceil 收口）与泵组配置（2 用 1 备档）。"""
    q_design_h = flow.q_design * p["sec_per_hour"]
    n_pump_raw = _apply(
        ctx, "TS-F1", {"q_design_h": q_design_h, "q_per_pump": _factor(p, _Q_PER_PUMP)}
    )
    n_pump_duty = float(math.ceil(n_pump_raw))
    return {
        "q_design_h": q_design_h,
        "n_pump_raw": n_pump_raw,
        "n_pump_duty": n_pump_duty,
        "q_pump": _apply(ctx, "TS-F2", {"q_design_h": q_design_h, "n_pump_duty": n_pump_duty}),
        "n_pump_total": _apply(
            ctx, "TS-F3", {"n_pump_duty": n_pump_duty, "n_standby": p["n_standby"]}
        ),
    }


def _a_pipe_of(p: dict[str, float], d_pipe: float) -> float:
    """比阻档表命中：d_pipe 档值 → dnXXX 键取值（越表=领域异常）。"""
    segment = _DN_KEYS.get(round(d_pipe, 2))
    if segment is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} DN 档 {d_pipe!r} 越比阻表覆盖面（录入 DN300~DN800；"
            "扩档待数据包增补键——起草表追认点 4）"
        )
    return _factor(p, f"factor.wushui_tisheng.pipe.resistance.{segment}")


def _pipe(ctx: UnitContext, p: dict[str, float], q_pump: float) -> dict[str, float]:
    """TS-F4~F8：压力管水力（DN 0.1 m 档 ceil+比阻法沿程+局部）与总损。"""
    q_pump_si = q_pump / p["sec_per_hour"]
    d_pipe_raw = _apply(ctx, "TS-F4", {"q_pump_si": q_pump_si, "v_pipe": p["v_pipe"]})
    d_pipe = _ceil_step(d_pipe_raw, p["dia_disc_step"])
    a_pipe = _a_pipe_of(p, d_pipe)
    h_friction = _apply(
        ctx, "TS-F6", {"a_pipe": a_pipe, "l_pipe": p["l_pipe"], "q_pump_si": q_pump_si}
    )
    v_pipe_act = _apply(ctx, "TS-F5", {"q_pump_si": q_pump_si, "d_pipe": d_pipe})
    h_local = _apply(
        ctx,
        "TS-F7",
        {
            "zeta_total": _factor(p, _ZETA),
            "v_pipe_act": v_pipe_act,
            "g_gravity": p["g_gravity"],
        },
    )
    return {
        "q_pump_si": q_pump_si,
        "d_pipe_raw": d_pipe_raw,
        "d_pipe": d_pipe,
        "v_pipe_act": v_pipe_act,
        "h_friction": h_friction,
        "h_local": h_local,
        "h_loss": _apply(ctx, "TS-F8", {"h_friction": h_friction, "h_local": h_local}),
    }


def _head(ctx: UnitContext, p: dict[str, float], h_loss: float) -> dict[str, float]:
    """TS-F9：泵扬程三分量（静扬程+管路损失+自由水头——追认点 14 承接）。"""
    return {
        "h_pump": _apply(
            ctx,
            "TS-F9",
            {
                "h_static": p["h_static"],
                "h_loss": h_loss,
                "h_free": _factor(p, _FREE_HEAD),
            },
        )
    }


def _well(ctx: UnitContext, p: dict[str, float], q_pump_si: float) -> dict[str, float]:
    """TS-F10~F14：集水井调节容积/启停频率校核/井体几何与概算混凝土量。"""
    v_well = _apply(ctx, "TS-F10", {"q_pump_si": q_pump_si, "t_well": p["t_well"]})
    a_well = _apply(ctx, "TS-F11", {"v_well": v_well, "h_well": p["h_well"]})
    h_super = _factor(p, "factor.wushui_tisheng.superheight")
    h_well_total = _apply(ctx, "TS-F13", {"h_super": h_super, "h_well": p["h_well"]})
    return {
        "v_well": v_well,
        "a_well": a_well,
        "n_start": _apply(ctx, "TS-F12", {"q_pump_si": q_pump_si, "v_well": v_well}),
        "h_well_total": h_well_total,
        "v_concrete": _apply(
            ctx,
            "TS-F14",
            {
                "a_well": a_well,
                "h_well_total": h_well_total,
                "wall_coef": _factor(p, "factor.wushui_tisheng.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], prefix: str) -> tuple[float, float]:
    """带类系数取值（factor.wushui_tisheng.<键>.min/max 双键）。"""
    return (
        _factor(p, f"factor.wushui_tisheng.{prefix}.min"),
        _factor(p, f"factor.wushui_tisheng.{prefix}.max"),
    )


def _warnings(
    p: dict[str, float], pumps: dict[str, float], pipe: dict[str, float], well: dict[str, float]
) -> tuple[Warning, ...]:
    """校核带检查：实际流速带/单泵流量带/启停上限/调节时间带。"""
    found: list[Warning] = []
    vel = _band(p, "pipe.velocity_band")
    if not vel[0] <= pipe["v_pipe_act"] <= vel[1]:
        found.append(
            _warn(
                f"{_HB}；factor.wushui_tisheng.pipe.velocity_band.*",
                f"实际流速 = {pipe['v_pipe_act']:.4f} m/s 越出建议带 [{vel[0]}, {vel[1]}]"
                "——调节方向：v_pipe（名义流速）或泵台数（n_pump_duty 改变单泵流量）",
                "v_pipe",
            )
        )
    qflow = _band(p, "pump.q_flow_band")
    if not qflow[0] <= pumps["q_pump"] <= qflow[1]:
        found.append(
            _warn(
                f"{_HB}；factor.wushui_tisheng.pump.q_flow_band.*",
                f"单泵流量 = {pumps['q_pump']:.2f} m3/h 越出建议带 [{qflow[0]}, {qflow[1]}]"
                "——调节方向：factor.wushui_tisheng.pump.q_per_unit（概算锚/选泵型号面）",
                "n_standby",
            )
        )
    limit = _factor(p, "factor.wushui_tisheng.pump.start_band.max")
    if well["n_start"] > limit:
        found.append(
            _warn(
                f"{_HB}；factor.wushui_tisheng.pump.start_band.max",
                f"最大启动次数 = {well['n_start']:.4f} 次/h 超上限 {limit}"
                "（水位启停频繁损泵）——调节方向：t_well（↑集水井调节容积↑）",
                "t_well",
            )
        )
    tband = _band(p, "well.t_band")
    if not tband[0] <= p["t_well"] <= tband[1]:
        found.append(
            _warn(
                f"{_GB}；{_HB}；factor.wushui_tisheng.well.t_band.*",
                f"集水井调节时间 = {p['t_well']:.2f} min 越出建议带 [{tband[0]}, {tband[1]}]"
                "——调节方向：t_well（带内取值）",
                "t_well",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _WushuiTisheng()


@final
class _WushuiTisheng:
    """污水提升泵房 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """TS-F1~F14 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        pumps = _pumps(ctx, p, flow)
        pipe = _pipe(ctx, p, pumps["q_pump"])
        head = _head(ctx, p, pipe["h_loss"])
        well = _well(ctx, p, pipe["q_pump_si"])
        dims = {**pumps, **pipe, **head, **well}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            # 零去除键透传：removal.wushui_tisheng.*.mod_default 全 0.0
            # （提升单元无处理）——出水质=入水质逐键原样（不经 apply，
            # 简报 D2 裁决；提升指标=扬程 h_pump 经 dims 承载，水量不衰减）
            outqualities={out_ref: WaterQuality(dict(quality.concentrations))},
            dims=dims,
            warnings=_warnings(p, pumps, pipe, well),
            formula_ids=FORMULA_IDS,
        )
