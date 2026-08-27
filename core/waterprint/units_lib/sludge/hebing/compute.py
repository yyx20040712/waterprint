"""污泥合并计算实现：唯一计算源（HB-F1~HB-F13 全经 registry.apply 求值）。

输入:  UnitContext（图源参数三股排泥 + 衡算参数 + 系数投影 + 迹收集器）
输出:  UnitResult（SLUDGE 出流三量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】HB-F1~HB-F13（docs/norms/sludge_hebing.md 起草表；
#   manifest.py 登记）——三股汇流（mix P4 干基质量恒等镜像）+
#   经验产率法主线/机理互校（ADR-008 ④）+ 汇流-产率法闭合校核。
# 【图源形态】无入边（上游水线单元无 SLUDGE 排泥口，三股排泥经
#   manifest 参数注入——表"衔接参数"节口径；mine_water_input 图源
#   先例同型）；compute 不读 ctx.inflows。
# 【单位换算】表公式全按工程口径 m³/d、kg/d（dims 期望值=表逐字）；
#   出流 SludgeFlow 契约口径 m3/s、kg/s——SECS_PER_DAY（manifest
#   数值白名单区常量）换算；moisture 无量纲直通。
# 【系数通道】factor.hebing.* 12 键经 ctx.params 投影面取值
#   （app._unit_params 剥 sludge_ 前缀裸短名投影）；缺键=领域异常。
#   elevation_loss 键归高程链子系统（后续批），本文件不消费；
#   yield.y_band/yield_syn_band/k_decay_band 三带键为数据包自校面，
#   本文件不消费（constraints.py 注记同源）。
# 【输出面（D2）】outflows=出流一口 SludgeFlow 三量（q_total/ds_total/
#   p_merged 换算）；dims=表结果 13 项全量 snake 键（出流三量链
#   q_total/ds_total/p_merged 即表键，无额外回显键）；outqualities=出流口恒键、值为空
#   WaterQuality 单元（SLUDGE 通道无水质指标——R5 单位元语义，GR-04）
#   warnings=互校偏差超上限（dev_pct >
#   factor.hebing.dev_band.max——ADR-008 ④ 校核侧语义，出警告不阻断；
#   param_key=yield_syn 调节方向归因）；formula_ids=HB-F1~F13 全量。
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
from waterprint.units_lib.sludge.hebing.manifest import (
    FORMULA_IDS,
    SECS_PER_DAY,
    manifest,
)

_UNIT_ID = "sludge_hebing"
_ADR = "ADR-008 ④（经验产率法主线+机理互校已拍板——偏差>20% 提示核对 SS/BOD 比）"
_DEV_MAX = "factor.hebing.dev_band.max"
_YIELD = "factor.hebing.yield.y"
_YIELD_SYN = "factor.hebing.yield_syn"
_K_DECAY20 = "factor.hebing.k_decay20"
_THETA_KD = "factor.hebing.theta_kd"
_PARAMS_POSITIVE = (
    "ds_primary",
    "ds_bio",
    "ds_chem",
    "q_avg_daily",
    "v_bio",
    "x_vss",
)
_MOISTURE_KEYS = ("p_primary", "p_bio", "p_chem")


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：ds 三股/流量/容积/MLVSS 非正拒；含水率开域 (0,1) 外拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    for key in _MOISTURE_KEYS:
        value = params.get(key)
        if value is None or not 0 < value < 1:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须在开区间 (0,1)"
                f"（小数含水率——闭边界 0/1 使干基反解除零）：得到 {value!r}"
            )
    s0, se = params.get("s0_bod"), params.get("se_bod")
    if s0 is None or se is None or s0 <= se:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数须 s0_bod > se_bod（BOD 去除量非正则"
            f"产率法主线失义——HB-F8）：得到 s0_bod={s0!r}, se_bod={se!r}"
        )


def _apply(ctx: UnitContext, formula_id: str, bindings: dict[str, float]) -> float:
    """apply 薄封装：统一携带 (unit_id, condition_key) 与 trace sink。"""
    return formulas.apply(
        formula_id,
        bindings,
        (ctx.unit_id, ConditionSet.key(ctx.condition)),
        sink=ctx.trace,
    )


def _stocks(ctx: UnitContext, p: dict[str, float]) -> dict[str, float]:
    """HB-F1~F3：三股排泥湿泥量（含水率换算——上游表衔接实值）。"""
    return {
        "q_primary": _apply(
            ctx, "HB-F1", {"ds_primary": p["ds_primary"], "p_primary": p["p_primary"]}
        ),
        "q_bio": _apply(
            ctx, "HB-F2", {"ds_bio": p["ds_bio"], "p_bio": p["p_bio"]}
        ),
        "q_chem": _apply(
            ctx, "HB-F3", {"ds_chem": p["ds_chem"], "p_chem": p["p_chem"]}
        ),
    }


def _merge(
    ctx: UnitContext, p: dict[str, float], stocks: dict[str, float]
) -> dict[str, float]:
    """HB-F4~F7：汇流 DS/湿量/干基水量/合并含水率（mix P4 镜像）。"""
    ds_total = _apply(
        ctx,
        "HB-F4",
        {
            "ds_primary": p["ds_primary"],
            "ds_bio": p["ds_bio"],
            "ds_chem": p["ds_chem"],
        },
    )
    q_total = _apply(ctx, "HB-F5", stocks)
    w_water = _apply(
        ctx,
        "HB-F6",
        {
            "ds_primary": p["ds_primary"],
            "p_primary": p["p_primary"],
            "ds_bio": p["ds_bio"],
            "p_bio": p["p_bio"],
            "ds_chem": p["ds_chem"],
            "p_chem": p["p_chem"],
        },
    )
    return {
        "ds_total": ds_total,
        "q_total": q_total,
        "w_water": w_water,
        "p_merged": _apply(
            ctx, "HB-F7", {"w_water": w_water, "ds_total": ds_total}
        ),
    }


def _yield_chain(ctx: UnitContext, p: dict[str, float]) -> dict[str, float]:
    """HB-F8~F11：经验产率主线 + 机理互校 + 偏差（ADR-008 ④）。"""
    common = {"q_avg_daily": p["q_avg_daily"], "s0_bod": p["s0_bod"], "se_bod": p["se_bod"]}
    s_y = _apply(
        ctx, "HB-F8", {**common, "y_yield": _factor(p, _YIELD)}
    )
    k_dt = _apply(
        ctx,
        "HB-F9",
        {
            "k_d20": _factor(p, _K_DECAY20),
            "theta_kd": _factor(p, _THETA_KD),
            "t_design": p["t_design"],
        },
    )
    dx_bio = _apply(
        ctx,
        "HB-F10",
        {
            "y_syn": _factor(p, _YIELD_SYN),
            **common,
            "k_dt": k_dt,
            "v_bio": p["v_bio"],
            "x_vss": p["x_vss"],
        },
    )
    return {
        "s_y": s_y,
        "k_dt": k_dt,
        "dx_bio": dx_bio,
        "dev_pct": _apply(ctx, "HB-F11", {"s_y": s_y, "dx_bio": dx_bio}),
    }


def _closure(
    ctx: UnitContext, p: dict[str, float], merged: dict[str, float], s_y: float
) -> dict[str, float]:
    """HB-F12~F13：产率法口径全厂干泥量 + 汇流-产率法闭合差。"""
    ds_check = _apply(
        ctx,
        "HB-F12",
        {"ds_primary": p["ds_primary"], "s_y": s_y, "ds_chem": p["ds_chem"]},
    )
    return {
        "ds_check": ds_check,
        "dev_close": _apply(
            ctx,
            "HB-F13",
            {"ds_total": merged["ds_total"], "ds_check": ds_check},
        ),
    }


def _warnings(dev_pct: float, dev_max: float) -> tuple[Warning, ...]:
    """互校偏差超上限警告（ADR-008 ④：>20% 提示核对 SS/BOD 比，不阻断）。"""
    if dev_pct <= dev_max:
        return ()
    return (
        Warning(
            severity=Severity.WARN,
            source=f"{_ADR}；{_DEV_MAX}",
            message=(
                f"经验产率/机理互校偏差 dev_pct = {dev_pct:.4f}% 超上限"
                f" {dev_max}%——提示核对原水 SS/BOD 比（惰性组分使经验产率"
                "与机理 VSS 产率分叉；调节方向：yield_syn/k_decay20 系数档"
                "或上游产率参数复核）"
            ),
            param_key="yield_syn",
        ),
    )


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _SludgeHebing()


@final
class _SludgeHebing:
    """污泥合并 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """HB-F1~F13 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        stocks = _stocks(ctx, p)
        merged = _merge(ctx, p, stocks)
        yields = _yield_chain(ctx, p)
        closure = _closure(ctx, p, merged, yields["s_y"])
        dims = {**stocks, **merged, **yields, **closure}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={
                out_ref: SludgeFlow(
                    q_wet=dims["q_total"] / SECS_PER_DAY,
                    ds=dims["ds_total"] / SECS_PER_DAY,
                    moisture=dims["p_merged"],
                )
            },
            # 出流水质面=空 WaterQuality 单位元（R5/GR-04——SLUDGE 通道
            # 无水质指标，但出流面两 Mapping 口恒有键：executor 入流
            # 装配取上游 qualities 池键的纯污泥图前提，builtin 三节点
            # 同款形态）
            outqualities={out_ref: WaterQuality({})},
            dims=dims,
            warnings=_warnings(dims["dev_pct"], _factor(p, _DEV_MAX)),
            formula_ids=FORMULA_IDS,
        )
