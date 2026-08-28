"""污泥脱水计算实现：唯一计算源（TU-F1~TU-F8 全经 registry.apply 求值）。

输入:  UnitContext（上游 SLUDGE 量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（SLUDGE 泥饼出流三量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】TU-F1~TU-F8（docs/norms/sludge_tuoshui.md 起草表；
#   manifest.py 登记）——机械脱水双机档（带式主线/离心副档）：
#   PAM 投加 + 泥饼含水率 75~80% + 固体回收率 DS 守恒链（泥饼/
#   滤液分流闭合 TU-F5~F8——旧式未计回收率系口径缺陷本批修正）。
# 【双机档键选】machine_type（grid [1,2]——表 equip_type 枚举的
#   float 化）选 TU-F3 的 q_machine 键：1=MACHINE_BELT→machine.
#   belt_capacity、2=MACHINE_CENTRIFUGE→machine.centrifuge_capacity
#   （manifest 模块常量——零数值字面量）。
# 【DSL 收口】脱水机台数整台向上取整（n_machine_duty=ceil(raw)≥1）
#   在本文件收口（DSL 无 ceil；表 TU-F3 口径"整台向上取整 ≥1"）。
# 【入流装配】恰一入边且为 SLUDGE（shusong 同款）；入流三量
#   ×SECS_PER_DAY 回工程口径，泥饼出流三量回契约口径。
# 【回流口（GOLDEN3 D2 产股，2026-08-28）】filtrate 滤液端口
#   （manifest ports recycle=True 声明沿用）——compute 无条件产
#   filtrate 股（Q1 已裁启用）：q_wet/ds=TU-F7/F8 工程口径值÷
#   SECS_PER_DAY 回契约口径；moisture=1−(ds_filtrate/q_filtrate)/1000
#   干基近似反解（固体密度按水——仅 SludgeFlow 域完整性字段非设计
#   参数，I2 追认证注记）；1000 不作字面量（R2 零字面量）——由
#   TU-F6 恒等式 q_cake=ds_cake/((1−p_cake)·1000) 反解密度基数
#   (1−p_cake)·q_cake/ds_cake ≡ 1/1000（代数同式零新增假设）。
#   dims 不变（q_filtrate/ds_filtrate 本就回显）。
# 【三量链回显】dims 加 q_in/ds_in/p_in/q_out/ds_out/p_out（出=泥饼：
#   q_out=q_cake、ds_out=ds_cake、p_out=p_cake 参数值）——进出六量
#   全回显。
# 【系数通道】factor.tuoshui.* 8 键经 ctx.params 投影面取值（裸
#   短名投影）；缺键=领域异常。elevation_loss 键归高程链子系统，
#   本文件不消费（车间设备单元不建 wall_thickness_coef——bashi
#   先例口径）。
# 【输出面（D2）】outflows=泥饼+滤液两口 SLUDGE 三量（out=q_cake/
#   ds_cake/p_cake；filtrate=TU-F7/F8÷SECS_PER_DAY+干基近似
#   moisture）；dims=表结果 9 项+回显 6 项；outqualities=两出流口
#   恒键、值为空 WaterQuality 单元（SLUDGE 通道无水质指标——R5 单位元
#   语义，GR-04）；warnings=两带校核（PAM 带/泥饼
#   含水率带；param_key 归因+调节方向）；formula_ids=TU-F1~F8 全量。
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
from waterprint.units_lib.sludge.tuoshui.manifest import (
    FORMULA_IDS,
    MACHINE_BELT,
    MACHINE_CENTRIFUGE,
    SECS_PER_DAY,
    manifest,
)

_UNIT_ID = "sludge_tuoshui"
_GB = "GB 50014-2021 §8（污泥章——机械脱水泥饼含水率/PAM 投加，条号待核对）"
_HB5 = "给水排水设计手册（第 5 册 城镇排水）污泥脱水章（常用带）"
_BELT_CAPACITY = "factor.tuoshui.machine.belt_capacity"
_CENTRIFUGE_CAPACITY = "factor.tuoshui.machine.centrifuge_capacity"
_ETA_CAPTURE = "factor.tuoshui.eta_capture"
_DOSE_BAND = (
    "factor.tuoshui.dose_pam_band.min",
    "factor.tuoshui.dose_pam_band.max",
)
_CAKE_BAND = (
    "factor.tuoshui.cake_moisture_band.min",
    "factor.tuoshui.cake_moisture_band.max",
)
_PARAMS_POSITIVE = ("machine_type", "dose_pam", "n_standby")


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
    """参数域守卫：机档/药耗/备用台非正拒；机档非枚举值拒；p_cake 开域 (0,1)。"""
    machine = params.get("machine_type")
    if machine not in (MACHINE_BELT, MACHINE_CENTRIFUGE):
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'machine_type' 须命中双机档枚举"
            f" [{MACHINE_BELT}, {MACHINE_CENTRIFUGE}]（1 带式/2 离心）："
            f"得到 {machine!r}"
        )
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    p_cake = params.get("p_cake")
    if p_cake is None or not 0 < p_cake < 1:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'p_cake' 必须在开区间 (0,1)"
            f"（小数含水率——闭边界 1 使泥饼换算除零）：得到 {p_cake!r}"
        )


def _inflow(ctx: UnitContext) -> SludgeFlow:
    """入流装配：恰一入边且为 SLUDGE（多入/缺入/水线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], SludgeFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 SLUDGE 入边：得到 {len(refs)} 条"
            "（脱水机单入单出语义——滤液口为出流非入流）"
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


def _machine_key(machine_type: float) -> str:
    """双机档键选：1 带式→belt_capacity；2 离心→centrifuge_capacity。"""
    if machine_type == MACHINE_BELT:
        return _BELT_CAPACITY
    return _CENTRIFUGE_CAPACITY


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _SludgeTuoshui()


@final
class _SludgeTuoshui:
    """污泥脱水 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """TU-F1~F8 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        inflow = _inflow(ctx)
        q_wet = inflow.q_wet * SECS_PER_DAY
        ds_in = inflow.ds * SECS_PER_DAY
        p_in = inflow.moisture
        w_pam = _apply(ctx, "TU-F1", {"ds_in": ds_in, "dose_pam": p["dose_pam"]})
        q_in_h = _apply(ctx, "TU-F2", {"q_wet": q_wet})
        n_machine_raw = _apply(
            ctx,
            "TU-F3",
            {"q_in_h": q_in_h, "q_machine": _factor(p, _machine_key(p["machine_type"]))},
        )
        # 台数整台向上取整（表 TU-F3 口径 ≥1——DSL 无 ceil，本文件收口）
        n_machine_duty = float(math.ceil(n_machine_raw))
        n_machine_total = _apply(
            ctx,
            "TU-F4",
            {"n_machine_duty": n_machine_duty, "n_standby": p["n_standby"]},
        )
        ds_cake = _apply(
            ctx, "TU-F5", {"ds_in": ds_in, "eta_capture": _factor(p, _ETA_CAPTURE)}
        )
        q_cake = _apply(ctx, "TU-F6", {"ds_cake": ds_cake, "p_cake": p["p_cake"]})
        q_filtrate = _apply(ctx, "TU-F7", {"q_wet": q_wet, "q_cake": q_cake})
        ds_filtrate = _apply(ctx, "TU-F8", {"ds_in": ds_in, "ds_cake": ds_cake})
        dims = {
            "q_in": q_wet,
            "ds_in": ds_in,
            "p_in": p_in,
            "w_pam": w_pam,
            "q_in_h": q_in_h,
            "n_machine_raw": n_machine_raw,
            "n_machine_duty": n_machine_duty,
            "n_machine_total": n_machine_total,
            "ds_cake": ds_cake,
            "q_cake": q_cake,
            "q_filtrate": q_filtrate,
            "ds_filtrate": ds_filtrate,
            "q_out": q_cake,
            "ds_out": ds_cake,
            "p_out": p["p_cake"],
        }
        warnings: list[Warning] = []
        dose_band = _band(p, _DOSE_BAND)
        if not dose_band[0] <= p["dose_pam"] <= dose_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_HB5}；{_DOSE_BAND[0]}~{_DOSE_BAND[1]}",
                    message=(
                        f"PAM 投加量 dose_pam = {p['dose_pam']:.4f} g/kgDS 越出"
                        f"建议带 [{dose_band[0]}, {dose_band[1]}]——调节方向："
                        "dose_pam（阳离子 PAM 带内取值，带式取 4/离心档取 3）"
                    ),
                    param_key="dose_pam",
                )
            )
        cake_band = _band(p, _CAKE_BAND)
        if not cake_band[0] <= p["p_cake"] <= cake_band[1]:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source=f"{_GB}；{_CAKE_BAND[0]}~{_CAKE_BAND[1]}",
                    message=(
                        f"泥饼含水率 p_cake = {p['p_cake']:.4f} 越出建议带"
                        f" [{cake_band[0]}, {cake_band[1]}]——调节方向："
                        "p_cake（机械脱水常用带 75~80%，过深脱水非机械档）"
                    ),
                    param_key="p_cake",
                )
            )
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        filtrate_ref = PortRef(unit_id=ctx.unit_id, port_id="filtrate")
        return UnitResult(
            outflows={
                out_ref: SludgeFlow(
                    q_wet=q_cake / SECS_PER_DAY,
                    ds=ds_cake / SECS_PER_DAY,
                    moisture=p["p_cake"],
                ),
                # GOLDEN3 D2：filtrate 滤液无条件产股（Q1 已裁启用）——
                # q_wet/ds=TU-F7/F8 回契约口径；moisture 干基近似反解
                # 1−(ds_filtrate/q_filtrate)/1000（密度基数经 TU-F6
                # 恒等式反解 ≡(1−p_cake)·q_cake/ds_cake，R2 零字面量
                # ——规格头注记）
                filtrate_ref: SludgeFlow(
                    q_wet=q_filtrate / SECS_PER_DAY,
                    ds=ds_filtrate / SECS_PER_DAY,
                    moisture=1
                    - (ds_filtrate / q_filtrate)
                    * (1 - p["p_cake"])
                    * q_cake
                    / ds_cake,
                ),
            },
            # 出流水质面=空 WaterQuality 单元（R5/GR-04——SLUDGE 通道
            # 无水质指标，但出流面两 Mapping 口恒有键：executor 入流
            # 装配取上游 qualities 池键的纯污泥图前提，builtin 三节点
            # 同款形态；filtrate 口同款两口恒键）
            outqualities={
                out_ref: WaterQuality({}),
                filtrate_ref: WaterQuality({}),
            },
            dims=dims,
            warnings=tuple(warnings),
            formula_ids=FORMULA_IDS,
        )
