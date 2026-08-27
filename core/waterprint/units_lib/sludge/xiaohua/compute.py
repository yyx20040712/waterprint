"""污泥消化计算实现：唯一计算源（XH-F1~XH-F11 全经 registry.apply 求值）。

输入:  UnitContext（上游 SLUDGE 量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（SLUDGE 出流三量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】XH-F1~XH-F11（docs/norms/sludge_xiaohua.md 起草表；
#   manifest.py 登记）——中温厌氧消化主线（35 ℃）：进泥挥发分/
#   消化时间容积式/挥发分降解/产气量/VS 容积负荷校核 + 消化减量
#   DS 守恒链（XH-F7~F9：降解 VS 以沼气离开系统→出泥三量链联立）
#   + 圆柱池径立方根式/概算。
# 【温度承载（UF-09）】参数 t_digest_temp（默认 35——manifest range
#   33~37 中温档）承载消化温度；v1 温度不进 DSL 公式（恒 35 档），
#   factor.xiaohua.temp 键登记不消费——高温 55 档归追认/设备批
#   （表公式表头注记口径）。
# 【DSL 收口】池径 0.5 m 档 ceil 在本文件收口（SIDE_DISC_STEP=
#   manifest 常量；DSL 无 ceil）。零数值字面量。
# 【入流装配】恰一入边且为 SLUDGE（shusong 同款）；入流三量
#   ×SECS_PER_DAY 回工程口径，出流三量（XH-F7~F9 联立）回契约口径。
# 【三量链回显】dims 加 q_in/ds_in/p_in（q_out/ds_out/p_out 即表键）
#   ——进出六量全回显。
# 【系数通道】factor.xiaohua.* 13 键经 ctx.params 投影面取值（裸
#   短名投影）；缺键=领域异常。temp/elevation_loss 两键本批不消费
#   （UF-09 注记/高程链子系统——表"其他数据键"口径）。
# 【输出面（D2）】outflows=出流一口 SLUDGE 三量；dims=表结果 12 项
#   （含池径取整前审计面 d_raw+取整后 d）+回显 3 项；outqualities=出流口恒键、值为空
#   WaterQuality 单元（SLUDGE 通道无水质指标——R5 单位元语义，GR-04）；
#   warnings=四带校核（消化时间带/VS 降解率带/产气率带/VS 容积负荷
#   带——结果校核；param_key 归因+调节方向）；formula_ids=XH-F1~F11
#   全量。
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
from waterprint.units_lib.sludge.xiaohua.manifest import (
    FORMULA_IDS,
    SECS_PER_DAY,
    SIDE_DISC_STEP,
    manifest,
)

_UNIT_ID = "sludge_xiaohua"
_GB = "GB 50014-2021 §8（污泥章——消化时间/挥发分降解率/产气率，条号待核对）"
_HB5 = "给水排水设计手册（第 5 册 城镇排水）污泥消化章（中温消化常用带）"
_TIME_BAND = (
    "factor.xiaohua.time_band.min",
    "factor.xiaohua.time_band.max",
)
_ETA_VS_BAND = (
    "factor.xiaohua.eta_vs_band.min",
    "factor.xiaohua.eta_vs_band.max",
)
_BIOGAS_BAND = (
    "factor.xiaohua.biogas_rate_band.min",
    "factor.xiaohua.biogas_rate_band.max",
)
_VS_LOAD_BAND = (
    "factor.xiaohua.vs_load_band.min",
    "factor.xiaohua.vs_load_band.max",
)
_F_VS = "factor.xiaohua.f_vs"
_RATIO_DH = "factor.xiaohua.ratio_dh"
_WALL = "factor.xiaohua.wall_thickness_coef"
_PARAMS_POSITIVE = ("t_digest", "n", "t_digest_temp", "eta_vs", "r_biogas")


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
    """参数域守卫：时间/池数/温度/降解率/产气率非正一律拒；降解率上限<1。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    eta = params.get("eta_vs")
    if eta is not None and eta >= 1:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'eta_vs' 必须 < 1（挥发分降解率小数——"
            f">=1 使消化减量超进泥 DS 量）：得到 {eta!r}"
        )


def _inflow(ctx: UnitContext) -> SludgeFlow:
    """入流装配：恰一入边且为 SLUDGE（多入/缺入/水线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], SludgeFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 SLUDGE 入边：得到 {len(refs)} 条"
            "（消化池单入单出语义）"
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
    return _SludgeXiaohua()


@final
class _SludgeXiaohua:
    """污泥消化 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """XH-F1~F11 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        inflow = _inflow(ctx)
        q_wet = inflow.q_wet * SECS_PER_DAY
        ds_in = inflow.ds * SECS_PER_DAY
        p_in = inflow.moisture
        w_vs = _apply(ctx, "XH-F1", {"ds_in": ds_in, "f_vs": _factor(p, _F_VS)})
        v_total = _apply(ctx, "XH-F2", {"q_wet": q_wet, "t_digest": p["t_digest"]})
        v_single = _apply(ctx, "XH-F3", {"v_total": v_total, "n": p["n"]})
        w_vs_deg = _apply(ctx, "XH-F4", {"w_vs": w_vs, "eta_vs": p["eta_vs"]})
        v_biogas = _apply(ctx, "XH-F5", {"w_vs_deg": w_vs_deg, "r_biogas": p["r_biogas"]})
        l_vs = _apply(ctx, "XH-F6", {"w_vs": w_vs, "v_total": v_total})
        ds_out = _apply(ctx, "XH-F7", {"ds_in": ds_in, "w_vs_deg": w_vs_deg})
        q_out = _apply(ctx, "XH-F8", {"q_wet": q_wet, "w_vs_deg": w_vs_deg})
        p_out = _apply(ctx, "XH-F9", {"ds_out": ds_out, "q_out": q_out})
        d_raw = _apply(
            ctx,
            "XH-F10",
            {"v_single": v_single, "pi": math.pi, "r_dh": _factor(p, _RATIO_DH)},
        )
        if SIDE_DISC_STEP <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 的取整步长必须 > 0：得到 {SIDE_DISC_STEP!r}"
            )
        # 池径 0.5 m 档向上取整（表 XH-F10 口径——DSL 无 ceil，本文件收口）
        d = math.ceil(d_raw / SIDE_DISC_STEP) * SIDE_DISC_STEP
        v_concrete = _apply(
            ctx, "XH-F11", {"v_total": v_total, "wall_coef": _factor(p, _WALL)}
        )
        dims = {
            "q_in": q_wet,
            "ds_in": ds_in,
            "p_in": p_in,
            "w_vs": w_vs,
            "v_total": v_total,
            "v_single": v_single,
            "w_vs_deg": w_vs_deg,
            "v_biogas": v_biogas,
            "l_vs": l_vs,
            "ds_out": ds_out,
            "q_out": q_out,
            "p_out": p_out,
            "d_raw": d_raw,
            "d": d,
            "v_concrete": v_concrete,
        }
        warnings: list[Warning] = []
        time_band = _band(p, _TIME_BAND)
        if not time_band[0] <= p["t_digest"] <= time_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_GB}；{_TIME_BAND[0]}~{_TIME_BAND[1]}",
                    message=(
                        f"消化时间 t_digest = {p['t_digest']:.4f} d 越出建议带"
                        f" [{time_band[0]}, {time_band[1]}]——调节方向："
                        "t_digest（中温消化带内取值）"
                    ),
                    param_key="t_digest",
                )
            )
        eta_band = _band(p, _ETA_VS_BAND)
        if not eta_band[0] <= p["eta_vs"] <= eta_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_GB}；{_ETA_VS_BAND[0]}~{_ETA_VS_BAND[1]}",
                    message=(
                        f"VS 降解率 eta_vs = {p['eta_vs']:.4f} 越出建议带"
                        f" [{eta_band[0]}, {eta_band[1]}]——调节方向：eta_vs（带内取值）"
                    ),
                    param_key="eta_vs",
                )
            )
        biogas_band = _band(p, _BIOGAS_BAND)
        if not biogas_band[0] <= p["r_biogas"] <= biogas_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_GB}；{_BIOGAS_BAND[0]}~{_BIOGAS_BAND[1]}",
                    message=(
                        f"产气率 r_biogas = {p['r_biogas']:.4f} m³/kgVS 越出建议带"
                        f" [{biogas_band[0]}, {biogas_band[1]}]——调节方向："
                        "r_biogas（中温产气带内取值）"
                    ),
                    param_key="r_biogas",
                )
            )
        load_band = _band(p, _VS_LOAD_BAND)
        if not load_band[0] <= l_vs <= load_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_HB5}；{_VS_LOAD_BAND[0]}~{_VS_LOAD_BAND[1]}",
                    message=(
                        f"VS 容积负荷 l_vs = {l_vs:.4f} kgVS/(m³·d) 越出建议带"
                        f" [{load_band[0]}, {load_band[1]}]——调节方向："
                        "t_digest（延长消化时间摊薄负荷）"
                    ),
                    param_key="t_digest",
                )
            )
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={
                out_ref: SludgeFlow(
                    q_wet=q_out / SECS_PER_DAY, ds=ds_out / SECS_PER_DAY,
                    moisture=p_out,
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
