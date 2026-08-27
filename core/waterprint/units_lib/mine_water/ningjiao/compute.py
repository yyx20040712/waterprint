"""混凝反应池计算实现：唯一计算源（KN-F1~F15 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KN-F1~F15（docs/norms/mine_water_ningjiao.md 起草表；
#   manifest.py 登记）。KN-F6/F7/F9 为下标泛式单条 DSL——各四次
#   apply 绑不同区值（p1~p4/a1~a4/l1~l4），formula_ids 每号一次。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池宽
#   B=ceil(b_raw, side_disc_step 0.5 m 档)；各区池长 l_i 构造值不
#   取整（表 KN-F9 口径——狭长分格）。零数值字面量。
# 【流量口径】各区容积/功率/几何按最高时 flow.q_design（KN-F1~F9，
#   ×3600 已内联公式串）；药剂耗量按平均日 flow.q_avg_daily
#   （KN-F11~F13，×86400 已内联）——表流量口径逐字。
# 【导出量合成】p_total（全厂装机=Σp_i×n）在 compute 以符号算术
#   合成（零字面量、无新工程常数——表 KN-F6 变量列"Σ×n=全厂装机"
#   口径，模板 chuchenchi q1 单输出导出量先例）。
# 【系数通道】factor.mine_ningjiao.*/removal.mine_ningjiao.* 经
#   ctx.params 投影面取值（app._unit_params 线感知投影，mine_ 限定
#   键空间）；缺键=领域异常。elevation_loss 键归高程链子系统（后续
#   批），本文件不消费；t_total ≤12 校核表内无 data 包键——不造
#   无依据键，仅表内注记（待追认）。
# 【输出面（D2）】outflows=入流透传；dims=表结果全量 snake 键（四区
#   容积/功率/面积/池长+GT+三药剂+总高+混凝土）；outqualities=入质
#   ×(1−removal.mod_default) 双指标（零去除键 0.0 穿流——药耗面不
#   改水质面，絮体分离在下游 cifenli/gaomidu）；warnings=校核带
#   越界（GT 带/四区停留四带/水深带/长宽比带；param_key 归因+调节
#   方向）；formula_ids=实际求值公式号全量。
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
from waterprint.units_lib.mine_water.ningjiao.manifest import FORMULA_IDS, manifest

_UNIT_ID = "mine_water_ningjiao"
_HB = "给水排水设计手册（第 3 册 城镇给水）混合/絮凝 G 值法与 GT 校核常用带"
_GT_BAND = ("factor.mine_ningjiao.gt_band.min", "factor.mine_ningjiao.gt_band.max")
_T_MIX_BAND = (
    "factor.mine_ningjiao.t_mix_band.min",
    "factor.mine_ningjiao.t_mix_band.max",
)
_T_SEED_BAND = (
    "factor.mine_ningjiao.t_seed_band.min",
    "factor.mine_ningjiao.t_seed_band.max",
)
_T_FLOC_BAND = (
    "factor.mine_ningjiao.t_floc_band.min",
    "factor.mine_ningjiao.t_floc_band.max",
)
_T_RIPEN_BAND = (
    "factor.mine_ningjiao.t_ripen_band.min",
    "factor.mine_ningjiao.t_ripen_band.max",
)
_DEPTH_BAND = (
    "factor.mine_ningjiao.depth_band.min",
    "factor.mine_ningjiao.depth_band.max",
)
_RATIO_BAND = (
    "factor.mine_ningjiao.cell_ratio_lb_band.min",
    "factor.mine_ningjiao.cell_ratio_lb_band.max",
)
_G_MIX = "factor.mine_ningjiao.g_mix"
_G_SEED = "factor.mine_ningjiao.g_seed"
_G_FLOC = "factor.mine_ningjiao.g_floc"
_G_RIPEN = "factor.mine_ningjiao.g_ripen"
_PARAMS_POSITIVE = (
    "n",
    "t_mix",
    "t_seed",
    "t_floc",
    "t_ripen",
    "h2",
    "ratio_lb",
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
    """构造步长向上取整（KN-F8 的 0.5 m 离散；步长>0 守卫）。"""
    if step <= 0:
        raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {step!r}")
    return math.ceil(value / step) * step


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/四区停留/水深/长宽比/步长非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（反应池单入单出语义）"
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


def _zones(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """KN-F1~F5：四分区容积（最高时口径）与总停留校核。"""
    volumes = {
        "v1": _apply(
            ctx, "KN-F1", {"q_design": flow.q_design, "t_mix": p["t_mix"], "n": p["n"]}
        ),
        "v2": _apply(
            ctx, "KN-F2", {"q_design": flow.q_design, "t_seed": p["t_seed"], "n": p["n"]}
        ),
        "v3": _apply(
            ctx, "KN-F3", {"q_design": flow.q_design, "t_floc": p["t_floc"], "n": p["n"]}
        ),
        "v4": _apply(
            ctx,
            "KN-F4",
            {"q_design": flow.q_design, "t_ripen": p["t_ripen"], "n": p["n"]},
        ),
    }
    return {
        **volumes,
        "t_total": _apply(
            ctx,
            "KN-F5",
            {
                **volumes,
                "q_design": flow.q_design,
                "n": p["n"],
            },
        ),
    }


def _power(ctx: UnitContext, p: dict[str, float], zones: dict[str, float]) -> dict[str, float]:
    """KN-F6 泛式四次求值：四区搅拌功率（kW 单区）+全厂装机合成。"""
    powers = {
        "p1": _apply(ctx, "KN-F6", {"g_i": _factor(p, _G_MIX), "v_i": zones["v1"]}),
        "p2": _apply(ctx, "KN-F6", {"g_i": _factor(p, _G_SEED), "v_i": zones["v2"]}),
        "p3": _apply(ctx, "KN-F6", {"g_i": _factor(p, _G_FLOC), "v_i": zones["v3"]}),
        "p4": _apply(ctx, "KN-F6", {"g_i": _factor(p, _G_RIPEN), "v_i": zones["v4"]}),
    }
    return {
        **powers,
        # DSL 单输出导出量（表 KN-F6 变量列"Σ×n=全厂装机"，零字面量）
        "p_total": sum(powers.values()) * p["n"],
    }


def _layout(ctx: UnitContext, p: dict[str, float], zones: dict[str, float]) -> dict[str, float]:
    """KN-F7~F9：四区面积（泛式四次）/池宽（0.5 m 档）/各区池长。"""
    areas = {
        "a1": _apply(ctx, "KN-F7", {"v_i": zones["v1"], "h2": p["h2"]}),
        "a2": _apply(ctx, "KN-F7", {"v_i": zones["v2"], "h2": p["h2"]}),
        "a3": _apply(ctx, "KN-F7", {"v_i": zones["v3"], "h2": p["h2"]}),
        "a4": _apply(ctx, "KN-F7", {"v_i": zones["v4"], "h2": p["h2"]}),
    }
    b_raw = _apply(ctx, "KN-F8", {"a_max": areas["a3"], "ratio_lb": p["ratio_lb"]})
    b = _ceil_step(b_raw, p["side_disc_step"])
    lengths = {
        f"l{index}": _apply(ctx, "KN-F9", {"a_i": area, "b": b})
        for index, area in enumerate(areas.values(), start=1)
    }
    return {**areas, "b_raw": b_raw, "b": b, **lengths}


def _gt(ctx: UnitContext, p: dict[str, float]) -> float:
    """KN-F10：四分区总 GT 校核（ΣG_i·t_i 总量口径）。"""
    return _apply(
        ctx,
        "KN-F10",
        {
            "g_mix": _factor(p, _G_MIX),
            "t_mix": p["t_mix"],
            "g_seed": _factor(p, _G_SEED),
            "t_seed": p["t_seed"],
            "g_floc": _factor(p, _G_FLOC),
            "t_floc": p["t_floc"],
            "g_ripen": _factor(p, _G_RIPEN),
            "t_ripen": p["t_ripen"],
        },
    )


def _dose(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, float]:
    """KN-F11~F13：PAC/PAM/磁种日耗量（平均日口径）。"""
    dose_pac = _factor(p, "factor.mine_ningjiao.dose.pac")
    dose_pam = _factor(p, "factor.mine_ningjiao.dose.pam")
    dose_seed = _factor(p, "factor.mine_ningjiao.seed.dose")
    return {
        "m_pac": _apply(
            ctx, "KN-F11", {"q_avg_daily": flow.q_avg_daily, "dose_pac": dose_pac}
        ),
        "m_pam": _apply(
            ctx, "KN-F12", {"q_avg_daily": flow.q_avg_daily, "dose_pam": dose_pam}
        ),
        "m_seed": _apply(
            ctx, "KN-F13", {"q_avg_daily": flow.q_avg_daily, "dose_seed": dose_seed}
        ),
    }


def _depth(
    ctx: UnitContext, p: dict[str, float], zones: dict[str, float]
) -> dict[str, float]:
    """KN-F14~F15：池总高与概算混凝土量。"""
    h_total = _apply(
        ctx,
        "KN-F14",
        {"h_super": _factor(p, "factor.mine_ningjiao.superheight"), "h2": p["h2"]},
    )
    return {
        "h_total": h_total,
        "v_concrete": _apply(
            ctx,
            "KN-F15",
            {
                "v1": zones["v1"],
                "v2": zones["v2"],
                "v3": zones["v3"],
                "v4": zones["v4"],
                "h2": p["h2"],
                "h_total": h_total,
                "n": p["n"],
                "wall_coef": _factor(p, "factor.mine_ningjiao.wall_thickness_coef"),
            },
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0]), _factor(p, keys[1])


def _retention_warning(
    p: dict[str, float],
    param_key: str,
    band_keys: tuple[str, str],
    value: float,
    zone: str,
) -> Warning | None:
    """单区停留时间带检查（四区同型，参数键归因）。"""
    band = _band(p, band_keys)
    if not band[0] <= value <= band[1]:
        return _warn(
            f"{_HB}；{band_keys[0]}~{band_keys[1]}",
            f"{zone}停留时间 = {value:.4f} min 越出建议带"
            f" [{band[0]}, {band[1]}]——调节方向：{param_key}（梯度递减链上该区带内取值）",
            param_key,
        )
    return None


def _warnings(
    p: dict[str, float],
    gt_total: float,
) -> tuple[Warning, ...]:
    """校核带检查：GT 总量带/四区停留四带/有效水深带/分区长宽比带。"""
    found: list[Warning] = []
    gt = _band(p, _GT_BAND)
    if not gt[0] <= gt_total <= gt[1]:
        found.append(
            _warn(
                f"{_HB}；{_GT_BAND[0]}~{_GT_BAND[1]}",
                f"四分区总 GT = {gt_total:.1f} 越出建议带"
                f" [{gt[0]}, {gt[1]}]——调节方向：t_mix/t_seed/t_floc/t_ripen"
                "（↑延长停留）或 G 值键档（追认后修订批）",
                "t_mix",
            )
        )
    zones = (
        ("t_mix", _T_MIX_BAND, p["t_mix"], "混合区"),
        ("t_seed", _T_SEED_BAND, p["t_seed"], "磁种混合区"),
        ("t_floc", _T_FLOC_BAND, p["t_floc"], "絮凝区"),
        ("t_ripen", _T_RIPEN_BAND, p["t_ripen"], "熟化区"),
    )
    for param_key, band_keys, value, zone in zones:
        warning = _retention_warning(p, param_key, band_keys, value, zone)
        if warning is not None:
            found.append(warning)
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= p["h2"] <= dep[1]:
        found.append(
            _warn(
                f"{_HB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"有效水深 h2 = {p['h2']:.4f} m 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：h2（反应池水深常用带内取值）",
                "h2",
            )
        )
    ratio = _band(p, _RATIO_BAND)
    if not ratio[0] <= p["ratio_lb"] <= ratio[1]:
        found.append(
            _warn(
                f"{_HB}；{_RATIO_BAND[0]}~{_RATIO_BAND[1]}",
                f"最大分区长宽比 = {p['ratio_lb']:.4f} 越出建议带"
                f" [{ratio[0]}, {ratio[1]}]——调节方向：ratio_lb（分区布置常用带内取值）",
                "ratio_lb",
            )
        )
    return tuple(found)


def _out_quality(p: dict[str, float], inflow: WaterQuality) -> WaterQuality:
    """出水质：双指标 ×(1−removal.mod_default)（零去除键 0.0 穿流），其余透传。"""
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
    return _MineNingjiao()


@final
class _MineNingjiao:
    """混凝反应池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KN-F1~F15 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx)
        zones = _zones(ctx, p, flow)
        power = _power(ctx, p, zones)
        layout = _layout(ctx, p, zones)
        gt_total = _gt(ctx, p)
        dose = _dose(ctx, p, flow)
        depth = _depth(ctx, p, zones)
        dims = {**zones, **power, **layout, "gt_total": gt_total, **dose, **depth}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            outqualities={out_ref: _out_quality(p, quality)},
            dims=dims,
            warnings=_warnings(p, gt_total),
            formula_ids=FORMULA_IDS,
        )
