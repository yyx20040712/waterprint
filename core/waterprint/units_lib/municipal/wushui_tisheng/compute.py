"""污水提升泵房计算实现：唯一计算源（TS-F1~F14 全经 registry.apply_batch
求值——批 13-C 同源向量路径：公式链以 ndarray 流动，标量=N=1 退化）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收；批 13-C
#   向量化重写：公式链经 _apply_batch 批量正门[AGENTS §13.6 同源向量
#   路径唯一——标量=N=1 退化；守卫层/warnings/ceil/DN 档表=N=1 边界件；
#   N>1=批 D 引擎正门]）
#
# 【批 MINOR(2026-09-08)重复清理】_ceil_vec def 拷贝下沉 _unit_compute._make_ceil_vec
#   （模块级绑定，调用点形态零变；两参空 extra 形态）；type _Array 收口 Array。
# 【公式组】TS-F1~F14（docs/norms/wushui_tisheng.md 起草表；manifest.py
#   登记）——集水井调节容积法+泵扬程三分量主线：选泵（F1~F3，整台
#   ceil 收口）、压力管水力（F4~F6，DN 0.1 m 档 ceil+比阻档表键命中）、
#   局部损失与管路总损（F7~F8）、泵扬程三分量（F9，M2b1 追认点 14
#   承接）、集水井与启停校核（F10~F12）、井体几何与概算（F13~F14）。
# 【DSL 收口】ceil 离散在本文件收口（DSL 无 ceil）：工作泵台数
#   n_pump_duty=ceil(n_pump_raw) 整台；出水管径 d_pipe=ceil(d_pipe_raw,
#   dia_disc_step 0.1 m 档=DN 档)——两处均 N=1 边界件（取标→取整→
#   回箱）。DN 档命中比阻表键（dn300~dn800）＝标量参数面（档值取标
#   查表——数组化形态零变），越表=领域异常（档表覆盖面显式声明）。
#   q_design_h/q_pump_si 经 sec_per_hour 参数符号合成（AO-F13 同款，
#   零换算字面量——ndarray 符号算术，IEEE 元素运算位恒等）。
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
from waterprint.units_lib._unit_compute import (
    Array as _Array,
)
from waterprint.units_lib._unit_compute import (
    _apply_batch,
    _factor,
    _inflow,
    _make_ceil_step,
    _make_ceil_vec,
    _vec,
)
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


_ceil_step = _make_ceil_step(_UNIT_ID, "取整步长", spaced=False)

_ceil_vec = _make_ceil_vec(_ceil_step)  # ceil 离散 N=1 边界件（批 MINOR 下沉单源）


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：静扬程/流速/管长/备用台数/井几何/步长/换算非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _pumps(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, _Array]:
    """TS-F1~F3：选泵（整台 ceil 收口）与泵组配置（2 用 1 备档）。"""
    q_design_h = _vec(flow.q_design) * _vec(p["sec_per_hour"])  # DSL 单输出导出量
    n_pump_raw = _apply_batch(
        ctx,
        "TS-F1",
        {"q_design_h": q_design_h, "q_per_pump": _vec(_factor(p, _Q_PER_PUMP, _UNIT_ID))},
    )
    n_pump_duty = _vec(float(math.ceil(n_pump_raw[0])))  # 整台 ceil＝N=1 边界件
    return {
        "q_design_h": q_design_h,
        "n_pump_raw": n_pump_raw,
        "n_pump_duty": n_pump_duty,
        "q_pump": _apply_batch(
            ctx, "TS-F2", {"q_design_h": q_design_h, "n_pump_duty": n_pump_duty}
        ),
        "n_pump_total": _apply_batch(
            ctx, "TS-F3", {"n_pump_duty": n_pump_duty, "n_standby": _vec(p["n_standby"])}
        ),
    }


def _a_pipe_of(p: dict[str, float], d_pipe: float) -> float:
    """比阻档表命中：d_pipe 档值 → dnXXX 键取值（越表=领域异常）——
    标量参数面（档值查表，数组化形态零变）。"""
    segment = _DN_KEYS.get(round(d_pipe, 2))
    if segment is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} DN 档 {d_pipe!r} 越比阻表覆盖面（录入 DN300~DN800；"
            "扩档待数据包增补键——起草表追认点 4）"
        )
    return _factor(p, f"factor.wushui_tisheng.pipe.resistance.{segment}", _UNIT_ID)


def _pipe(ctx: UnitContext, p: dict[str, float], q_pump: _Array) -> dict[str, _Array]:
    """TS-F4~F8：压力管水力（DN 0.1 m 档 ceil+比阻法沿程+局部）与总损。"""
    q_pump_si = q_pump / _vec(p["sec_per_hour"])  # DSL 单输出导出量
    d_pipe_raw = _apply_batch(ctx, "TS-F4", {"q_pump_si": q_pump_si, "v_pipe": _vec(p["v_pipe"])})
    d_pipe = _ceil_vec(d_pipe_raw, p["dia_disc_step"])
    a_pipe = _vec(_a_pipe_of(p, float(d_pipe[0])))  # DN 档表命中＝N=1 取标查表
    h_friction = _apply_batch(
        ctx, "TS-F6", {"a_pipe": a_pipe, "l_pipe": _vec(p["l_pipe"]), "q_pump_si": q_pump_si}
    )
    v_pipe_act = _apply_batch(ctx, "TS-F5", {"q_pump_si": q_pump_si, "d_pipe": d_pipe})
    h_local = _apply_batch(
        ctx,
        "TS-F7",
        {
            "zeta_total": _vec(_factor(p, _ZETA, _UNIT_ID)),
            "v_pipe_act": v_pipe_act,
            "g_gravity": _vec(p["g_gravity"]),
        },
    )
    return {
        "q_pump_si": q_pump_si,
        "d_pipe_raw": d_pipe_raw,
        "d_pipe": d_pipe,
        "v_pipe_act": v_pipe_act,
        "h_friction": h_friction,
        "h_local": h_local,
        "h_loss": _apply_batch(ctx, "TS-F8", {"h_friction": h_friction, "h_local": h_local}),
    }


def _head(ctx: UnitContext, p: dict[str, float], h_loss: _Array) -> dict[str, _Array]:
    """TS-F9：泵扬程三分量（静扬程+管路损失+自由水头——追认点 14 承接）。"""
    return {
        "h_pump": _apply_batch(
            ctx,
            "TS-F9",
            {
                "h_static": _vec(p["h_static"]),
                "h_loss": h_loss,
                "h_free": _vec(_factor(p, _FREE_HEAD, _UNIT_ID)),
            },
        )
    }


def _well(ctx: UnitContext, p: dict[str, float], q_pump_si: _Array) -> dict[str, _Array]:
    """TS-F10~F14：集水井调节容积/启停频率校核/井体几何与概算混凝土量。"""
    v_well = _apply_batch(ctx, "TS-F10", {"q_pump_si": q_pump_si, "t_well": _vec(p["t_well"])})
    a_well = _apply_batch(ctx, "TS-F11", {"v_well": v_well, "h_well": _vec(p["h_well"])})
    h_super = _factor(p, "factor.wushui_tisheng.superheight", _UNIT_ID)
    h_well_total = _apply_batch(
        ctx, "TS-F13", {"h_super": _vec(h_super), "h_well": _vec(p["h_well"])}
    )
    return {
        "v_well": v_well,
        "a_well": a_well,
        "n_start": _apply_batch(ctx, "TS-F12", {"q_pump_si": q_pump_si, "v_well": v_well}),
        "h_well_total": h_well_total,
        "v_concrete": _apply_batch(
            ctx,
            "TS-F14",
            {
                "a_well": a_well,
                "h_well_total": h_well_total,
                "wall_coef": _vec(
                    _factor(p, "factor.wushui_tisheng.wall_thickness_coef", _UNIT_ID)
                ),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], prefix: str) -> tuple[float, float]:
    """带类系数取值（factor.wushui_tisheng.<键>.min/max 双键）。"""
    return (
        _factor(p, f"factor.wushui_tisheng.{prefix}.min", _UNIT_ID),
        _factor(p, f"factor.wushui_tisheng.{prefix}.max", _UNIT_ID),
    )


def _warnings(
    p: dict[str, float], pumps: dict[str, _Array], pipe: dict[str, _Array], well: dict[str, _Array]
) -> tuple[Warning, ...]:
    """校核带检查：实际流速带/单泵流量带/启停上限/调节时间带。"""
    found: list[Warning] = []
    v_pipe_act = float(pipe["v_pipe_act"][0])
    q_pump = float(pumps["q_pump"][0])
    n_start = float(well["n_start"][0])
    vel = _band(p, "pipe.velocity_band")
    if not vel[0] <= v_pipe_act <= vel[1]:
        found.append(
            _warn(
                f"{_HB}；factor.wushui_tisheng.pipe.velocity_band.*",
                f"实际流速 = {v_pipe_act:.4f} m/s 越出建议带 [{vel[0]}, {vel[1]}]"
                "——调节方向：v_pipe（名义流速）或泵台数（n_pump_duty 改变单泵流量）",
                "v_pipe",
            )
        )
    qflow = _band(p, "pump.q_flow_band")
    if not qflow[0] <= q_pump <= qflow[1]:
        found.append(
            _warn(
                f"{_HB}；factor.wushui_tisheng.pump.q_flow_band.*",
                f"单泵流量 = {q_pump:.2f} m3/h 越出建议带 [{qflow[0]}, {qflow[1]}]"
                "——调节方向：factor.wushui_tisheng.pump.q_per_unit（概算锚/选泵型号面）",
                # 归因唯一真实杠杆=概算锚系数键（n_standby 只进 TS-F3 与 q_pump
                # 零耦合——M2c R1-b 修正 2026-08-26；系数键入 param_key 为新
                # 形态但语义正确，Warning.source 系数键引已有先例）
                "factor.wushui_tisheng.pump.q_per_unit",
            )
        )
    limit = _factor(p, "factor.wushui_tisheng.pump.start_band.max", _UNIT_ID)
    if n_start > limit:
        found.append(
            _warn(
                f"{_HB}；factor.wushui_tisheng.pump.start_band.max",
                f"最大启动次数 = {n_start:.4f} 次/h 超上限 {limit}"
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
        in_ref, flow = _inflow(ctx, "泵房单入单出语义")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        pumps = _pumps(ctx, p, flow)
        pipe = _pipe(ctx, p, pumps["q_pump"])
        head = _head(ctx, p, pipe["h_loss"])
        well = _well(ctx, p, pipe["q_pump_si"])
        arrays = {**pumps, **pipe, **head, **well}
        dims = {key: float(value[0]) for key, value in arrays.items()}
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
