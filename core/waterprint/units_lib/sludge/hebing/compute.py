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
# 【图源形态→双模（GOLDEN4a D2，2026-08-28）】三 IN 口（in_primary/
#   in_bio/in_chem）实体化后 compute 双模：三口全无边=参数注入模式
#   （现行三案例形态——行为逐字节不变）；三口全有边=入流直值模式
#   （三股 q_wet/ds 从 inflows 直取 ×SECS_PER_DAY 回工程口径、
#   p_x=inflow.moisture，HB-F4~F7/F8~F13 照跑——p_merged 恒等/产率链
#   不变；HB-F1~F3 不重算[入流即真值，避免双源冲突]，dims 的 q 三股
#   =入流直值回显）；部分有边=InvalidUnitConfig 显式拒（三股口须全连
#   或全不连——GR-14 族部分注入态非法）。入流模式 formula_ids=
#   FORMULA_IDS_FLOW（F4~F13——与 trace 一致的审计口径）。
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
    FORMULA_IDS_FLOW,
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


# 三股 IN 口 →（湿量 dims 键, 干基参数键, 含水率参数键）族（GOLDEN4a D1）
_STOCK_PORTS: tuple[tuple[str, str, str, str], ...] = (
    ("in_primary", "q_primary", "ds_primary", "p_primary"),
    ("in_bio", "q_bio", "ds_bio", "p_bio"),
    ("in_chem", "q_chem", "ds_chem", "p_chem"),
)
_STOCK_PORT_IDS = frozenset(entry[0] for entry in _STOCK_PORTS)


def _inflow_stocks(
    ctx: UnitContext,
) -> tuple[dict[str, float], dict[str, float]] | None:
    """三口入流装配（D2 双模）：全无边=None（参数注入模式）；全有边=
    （三股湿量 dims 回显, ds/p 参数覆写）二元组；部分有边/非泥股=拒。"""
    unexpected = [
        ref for ref in ctx.inflows if ref.port_id not in _STOCK_PORT_IDS
    ]
    present = {
        ref.port_id: flow
        for ref, flow in ctx.inflows.items()
        if ref.port_id in _STOCK_PORT_IDS
    }
    if not present and not unexpected:
        return None
    if len(present) != len(_STOCK_PORTS) or unexpected:
        connected = sorted(present)
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 三股口须全连或全不连——部分注入态非法"
            f"（GOLDEN4a D2/GR-14 族）：已连 {connected}"
            f"（+未声明口入流 {sorted(ref.port_id for ref in unexpected)}"
            "——三口=in_primary/in_bio/in_chem）"
        )
    stocks: dict[str, float] = {}
    overrides: dict[str, float] = {}
    for port_id, q_key, ds_key, p_key in _STOCK_PORTS:
        flow = present[port_id]
        if not isinstance(flow, SludgeFlow):
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流口 {port_id!r} 须 SLUDGE 股："
                f"得到 {type(flow).__name__}（三股口类型化前提）"
            )
        q_eng = flow.q_wet * SECS_PER_DAY
        ds_eng = flow.ds * SECS_PER_DAY
        if q_eng <= 0 or ds_eng <= 0:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流口 {port_id!r} 的 q_wet/ds 必须"
                f" > 0（工程口径）：得到 q={q_eng!r}, ds={ds_eng!r}"
            )
        if not 0 < flow.moisture < 1:
            raise InvalidUnitConfig(
                f"单元 {ctx.unit_id!r} 入流口 {port_id!r} 含水率必须在开"
                f"区间 (0,1)（干基反解除零）：得到 {flow.moisture!r}"
            )
        stocks[q_key] = q_eng
        overrides[ds_key] = ds_eng
        overrides[p_key] = flow.moisture
    return stocks, overrides


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
        """HB-F1~F13 主算路径（双模：三口无边=参数注入/全有边=入流直值）。"""
        p = dict(ctx.params)
        formula_ids: tuple[str, ...] = FORMULA_IDS
        inflow = _inflow_stocks(ctx)
        if inflow is None:
            _validate(p)
            stocks = _stocks(ctx, p)  # HB-F1~F3（参数注入模式——现行行为）
        else:
            # 入流直值模式：ds/p 六键=入流直值覆写（入流即真值），衡算面
            # 参数域守卫经覆写后的 p 统一执行；HB-F1~F3 不重算（D2）
            stocks, overrides = inflow
            p.update(overrides)
            _validate(p)
            formula_ids = FORMULA_IDS_FLOW
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
            formula_ids=formula_ids,
        )
