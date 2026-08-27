"""V型滤池计算实现：唯一计算源（KV-F1~F11 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KV-F1~KV-F11（docs/norms/mine_water_vxinglvchi.md 起草表；
#   manifest.py 登记）——均质滤料低滤速精滤主线+气水反冲三阶段。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：单格
#   宽 B=ceil(b_raw, side_disc_step 0.1 m 档)/单格长 L=ceil(l_raw,
#   同档)。零数值字面量。
# 【t_bw 合成】三阶段反冲停滤历时=t_air+t_sim+t_water（三 factor 键
#   求和，零字面量——ningjiao p_total 单输出导出量先例），dims 审计
#   面 t_bw=12 min 与表主算例输入同值；KV-F2/KV-F8 两处消费。
# 【流量口径】过滤面积/反冲耗水率按平均日 flow.q_avg_daily×k_self
#   （日处理量口径——滤池 24 h 连续过滤，异于沉淀类最高时口径，
#   KV-F1 ×86400 已内联公式串）——表流量口径逐字。
# 【参数域】格数 n 须 ≥2（KV-F5 强制滤速 n/(n−1) 一格冲洗语义——
#   n=1 除零守卫在参数域拒绝层拦截）。
# 【系数通道】factor.mine_vxinglvchi.*/removal.mine_vxinglvchi.* 经
#   ctx.params 投影面取值（app._unit_params 线感知投影，mine_ 限定
#   键空间）；缺键=领域异常。elevation_loss 键归高程链子系统（后续
#   批，语义含滤层过滤水头），本文件不消费；wash.air 气冲强度键
#   不入水量公式（气量非水量——表 KV-F8 口径），仅登记在册。
# 【输出面（D2）】outflows=入流透传；dims=表结果全量 snake 键（日
#   处理量/停滤历时/有效时长/总与单格过滤面积/强制滤速/单格尺寸
#   （含取整前审计面）/反冲水量/耗水率/总高/混凝土）；outqualities=
#   入质×(1−removal.mod_default) 双指标（SS 6.8→1.36/COD 56→51.8
#   ——衔接下游 ziwai 表，COD 51.8 为全厂终水）；warnings=校核带
#   越界（滤速带/强制滤速上限/滤层厚带/砂上水深带/周期带/反冲耗水
#   率上限；param_key 归因+调节方向）；formula_ids=实际求值公式号
#   全量。
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
from waterprint.units_lib.mine_water.vxinglvchi.manifest import FORMULA_IDS, manifest

_UNIT_ID = "mine_water_vxinglvchi"
_GB = "GB/T 41019-2021（过滤段滤速/强制滤速，条号待核对）"
_HB = "给水排水设计手册（第 3 册 城镇给水）V 型滤池滤料/气水反冲/反冲耗水常用带"
_V_FILTER_BAND = (
    "factor.mine_vxinglvchi.v_filter_band.min",
    "factor.mine_vxinglvchi.v_filter_band.max",
)
_V_FORCED_MAX = "factor.mine_vxinglvchi.v_forced.max"
_MEDIA_BAND = (
    "factor.mine_vxinglvchi.media.depth_band.min",
    "factor.mine_vxinglvchi.media.depth_band.max",
)
_WATER_BAND = (
    "factor.mine_vxinglvchi.water_above_band.min",
    "factor.mine_vxinglvchi.water_above_band.max",
)
_CYCLE_BAND = (
    "factor.mine_vxinglvchi.cycle_band.min",
    "factor.mine_vxinglvchi.cycle_band.max",
)
_RATIO_MAX = "factor.mine_vxinglvchi.wash.ratio_max"
_PARAMS_POSITIVE = (
    "v_filter",
    "t_filter",
    "h_media",
    "h_water",
    "h_plate",
    "h_under",
    "side_disc_step",
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
    """构造步长向上取整（KV-F6/F7 的 0.1 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：格数≥2（强制滤速除零守卫）/滤速/周期/层厚非正一律拒。"""
    cells = params.get("n")
    if cells is None or cells <= 1:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'n' 必须 ≥ 2（一格冲洗时余格承载——"
            f"KV-F5 强制滤速 n/(n−1) 除零守卫）：得到 {cells!r}"
        )
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
            "（滤池单入单出语义）"
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


def _t_bw(p: dict[str, float]) -> float:
    """三阶段反冲停滤历时合成（t_air+t_sim+t_water，零字面量审计面）。"""
    return (
        _factor(p, "factor.mine_vxinglvchi.wash.t_air")
        + _factor(p, "factor.mine_vxinglvchi.wash.t_sim")
        + _factor(p, "factor.mine_vxinglvchi.wash.t_water")
    )


def _filter_face(
    ctx: UnitContext, p: dict[str, float], flow: WaterFlow, t_bw: float
) -> dict[str, float]:
    """KV-F1~F4：日处理量/有效过滤时长/总与单格过滤面积。"""
    q_d = _apply(
        ctx,
        "KV-F1",
        {
            "q_avg_daily": flow.q_avg_daily,
            "k_self": _factor(p, "factor.mine_vxinglvchi.selfuse_coef"),
        },
    )
    t_w = _apply(ctx, "KV-F2", {"t_bw": t_bw, "t_filter": p["t_filter"]})
    f_total = _apply(
        ctx, "KV-F3", {"q_d": q_d, "v_filter": p["v_filter"], "t_w": t_w}
    )
    return {
        "q_d": q_d,
        "t_w": t_w,
        "f_total": f_total,
        "f_single": _apply(ctx, "KV-F4", {"f_total": f_total, "n": p["n"]}),
    }


def _cell_layout(ctx: UnitContext, p: dict[str, float], f_single: float) -> dict[str, float]:
    """KV-F6~F7：单格宽/长（0.1 m 档，含取整前审计面）。"""
    b_raw = _apply(
        ctx,
        "KV-F6",
        {"f_single": f_single, "ratio_lb": _factor(p, "factor.mine_vxinglvchi.cell_ratio_lb")},
    )
    width = _ceil_step(b_raw, p["side_disc_step"])
    l_raw = _apply(ctx, "KV-F7", {"f_single": f_single, "b": width})
    return {
        "b_raw": b_raw,
        "b": width,
        "l_raw": l_raw,
        "l": _ceil_step(l_raw, p["side_disc_step"]),
    }


def _wash(
    ctx: UnitContext, p: dict[str, float], q_d: float, t_bw: float
) -> dict[str, float]:
    """KV-F5/KV-F8~F9：强制滤速校核+反冲水量与耗水率（三阶段族）。"""
    v_force_act = _apply(
        ctx, "KV-F5", {"n": p["n"], "v_filter": p["v_filter"]}
    )
    w_wash = _apply(
        ctx,
        "KV-F8",
        {
            "q_w_sim": _factor(p, "factor.mine_vxinglvchi.wash.water_sim"),
            "t_sim": _factor(p, "factor.mine_vxinglvchi.wash.t_sim"),
            "q_w": _factor(p, "factor.mine_vxinglvchi.wash.water"),
            "t_water": _factor(p, "factor.mine_vxinglvchi.wash.t_water"),
            "q_sweep": _factor(p, "factor.mine_vxinglvchi.wash.sweep"),
            "t_bw": t_bw,
        },
    )
    return {
        "v_force_act": v_force_act,
        "w_wash": w_wash,
        "eta_wash": _apply(
            ctx,
            "KV-F9",
            {"w_wash": w_wash, "t_filter": p["t_filter"], "q_d": q_d, "n": p["n"]},
        ),
    }


def _depth(
    ctx: UnitContext, p: dict[str, float], cell: dict[str, float]
) -> dict[str, float]:
    """KV-F10~F11：滤池总高与概算混凝土量。"""
    h_total = _apply(
        ctx,
        "KV-F10",
        {
            "h_super": _factor(p, "factor.mine_vxinglvchi.superheight"),
            "h_water": p["h_water"],
            "h_media": p["h_media"],
            "h_plate": p["h_plate"],
            "h_under": p["h_under"],
        },
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "KV-F11",
            {
                "l": cell["l"],
                "b": cell["b"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.mine_vxinglvchi.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _band_warning(
    value: float,
    band_keys: tuple[str, str],
    param_key: str,
    advice: str,
    p: dict[str, float],
) -> Warning | None:
    """通用带检查（min≤v≤max，参数键归因+调节方向）。"""
    band = _band(p, band_keys)
    if not band[0] <= value <= band[1]:
        return _warn(
            f"{_HB}；{band_keys[0]}~{band_keys[1]}",
            f"参数 {param_key} = {value:.4f} 越出建议带"
            f" [{band[0]}, {band[1]}]——调节方向：{advice}",
            param_key,
        )
    return None


def _warnings(
    p: dict[str, float], v_force_act: float, eta_wash: float
) -> tuple[Warning, ...]:
    """校核带检查：滤速带/强制滤速上限/滤层厚带/砂上水深带/周期带/耗水率上限。"""
    found: list[Warning] = []
    checks: tuple[tuple[float, tuple[str, str], str, str], ...] = (
        (p["v_filter"], _V_FILTER_BAND, "v_filter", "v_filter（低滤速精滤档带内取值）"),
        (p["h_media"], _MEDIA_BAND, "h_media", "h_media（均质滤料带内取值）"),
        (p["h_water"], _WATER_BAND, "h_water", "h_water（恒水位过滤带内取值）"),
        (p["t_filter"], _CYCLE_BAND, "t_filter", "t_filter（周期带内取值）"),
    )
    for value, band_keys, param_key, advice in checks:
        warning = _band_warning(value, band_keys, param_key, advice, p)
        if warning is not None:
            found.append(warning)
    if v_force_act > _factor(p, _V_FORCED_MAX):
        found.append(
            _warn(
                f"{_GB}；{_V_FORCED_MAX}",
                f"强制滤速 = {v_force_act:.4f} m/h 越上限"
                f" {_factor(p, _V_FORCED_MAX)}（一格冲洗时余格承载）"
                "——调节方向：v_filter（降滤速）或 n（增格数）",
                "v_filter",
            )
        )
    if eta_wash > _factor(p, _RATIO_MAX):
        found.append(
            _warn(
                f"{_HB}；{_RATIO_MAX}",
                f"反冲耗水率 = {eta_wash:.6f} 越上限"
                f" {_factor(p, _RATIO_MAX)}（单格日冲一次口径）"
                "——调节方向：t_filter（延长周期降频）",
                "t_filter",
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
    return _MineVxinglvchi()


@final
class _MineVxinglvchi:
    """V 型滤池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KV-F1~F11 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        t_bw = _t_bw(p)
        face = _filter_face(ctx, p, flow, t_bw)
        cell = _cell_layout(ctx, p, face["f_single"])
        wash = _wash(ctx, p, face["q_d"], t_bw)
        dims = {
            "t_bw": t_bw,
            **face,
            **cell,
            **wash,
            **_depth(ctx, p, cell),
        }
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, wash["v_force_act"], wash["eta_wash"]),
            formula_ids=FORMULA_IDS,
        )
