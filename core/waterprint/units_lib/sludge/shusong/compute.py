"""污泥输送计算实现：唯一计算源（ST-F1~ST-F9 全经 registry.apply 求值）。

输入:  UnitContext（上游 SLUDGE 量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（SLUDGE 出流三量穿流 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】ST-F1~ST-F9（docs/norms/sludge_shusong.md 起草表；
#   manifest.py 登记）——压力流管径/流速（GB §8）+ 重力自流最小
#   坡度/流速（曼宁满流）两式主线 + DS/含水率穿流守恒显式。
# 【DSL 收口】管径 0.025 m 档（DN25 细管档）ceil 在本文件收口
#   （DSL 无 ceil；PIPE_DISC_STEP=manifest 常量，零数值字面量）。
#   求值序 F5（i_req）→F7（i_slope）→F6（v_grav）——表内 F6/F7 依赖
#   倒挂，每条 apply 独立无碍，formula_ids 按表号全量。
# 【入流装配】恰一入边且为 SLUDGE（多入/缺入/水线=领域异常——
#   ningjiao WATER 同款镜像）；入流三量 ×SECS_PER_DAY 回工程口径
#   （表公式 m³/d、kg/d）。
# 【单位换算】出流穿流三量回契约口径（q_wet/ds ÷SECS_PER_DAY，
#   moisture 直通）；dims 全按工程口径（表期望值=断言源）。
# 【三量链回显】dims 加 q_in/ds_in/p_in（进端）与 q_out（出端湿量
#   穿流；ds_out/p_out 即表键）——进出泥量-含水率-DS 六量全回显。
# 【系数通道】factor.shusong.* 6 键经 ctx.params 投影面取值（裸短名
#   投影）；缺键=领域异常。elevation_loss 键归高程链子系统，本文件
#   不消费。
# 【输出面（D2）】outflows=出流一口 SLUDGE 三量穿流；dims=表结果
#   10 项+回显 4 项；outqualities=出流口恒键、值为空
#   WaterQuality 单元（SLUDGE 通道无水质指标——R5 单位元语义，GR-04）；warnings=压力流速带越界（归因
#   v_press——名义流速改档）+ 重力流速低于最小值（归因 d_grav——
#   放大重力段管径）；formula_ids=ST-F1~F9 全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import final

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
from waterprint.units_lib._constants import SECS_PER_DAY
from waterprint.units_lib._unit_compute import _apply, _factor, _inflow_sludge, _make_ceil_step
from waterprint.units_lib.sludge.shusong.manifest import (
    FORMULA_IDS,
    PIPE_DISC_STEP,
    manifest,
)

_UNIT_ID = "sludge_shusong"
_GB = "GB 50014-2021 §8（污泥章——污泥管道压力流速，条号待核对）"
_HB5 = "给水排水设计手册（第 5 册 城镇排水）污泥管道章（重力输泥常用带）"
_V_BAND = (
    "factor.shusong.velocity_band.min",
    "factor.shusong.velocity_band.max",
)
_GRAVITY_V_MIN = "factor.shusong.gravity_v_min"
_N_MANNING = "factor.shusong.n_manning"
_SLOPE_MIN = "factor.shusong.slope_min"
_PARAMS_POSITIVE = ("v_press", "d_grav")


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：名义流速/重力段管径非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )


_ceil_step = _make_ceil_step(_UNIT_ID, "取整步长", spaced=False)


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _SludgeShusong()


@final
class _SludgeShusong:
    """污泥输送 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """ST-F1~F9 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        inflow = _inflow_sludge(ctx, "输泥管单入单出语义")
        # 入流三量回工程口径（表公式 m³/d、kg/d——单位换算归实装面）
        q_wet = inflow.q_wet * SECS_PER_DAY
        ds_in = inflow.ds * SECS_PER_DAY
        p_in = inflow.moisture
        q_h = _apply(ctx, "ST-F1", {"q_wet": q_wet})
        q_si = _apply(ctx, "ST-F2", {"q_h": q_h})
        d_raw = _apply(
            ctx, "ST-F3", {"q_si": q_si, "pi": math.pi, "v_press": p["v_press"]}
        )
        d_pipe = _ceil_step(d_raw, PIPE_DISC_STEP)
        v_act = _apply(
            ctx, "ST-F4", {"q_si": q_si, "pi": math.pi, "d_pipe": d_pipe}
        )
        n_manning = _factor(p, _N_MANNING, _UNIT_ID)
        i_req = _apply(
            ctx,
            "ST-F5",
            {
                "v_grav_min": _factor(p, _GRAVITY_V_MIN, _UNIT_ID),
                "n_manning": n_manning,
                "d_grav": p["d_grav"],
            },
        )
        i_slope = _apply(
            ctx,
            "ST-F7",
            {"i_req": i_req, "slope_min": _factor(p, _SLOPE_MIN, _UNIT_ID)},
        )
        v_grav = _apply(
            ctx,
            "ST-F6",
            {"n_manning": n_manning, "d_grav": p["d_grav"], "i_slope": i_slope},
        )
        ds_out = _apply(ctx, "ST-F8", {"ds_in": ds_in})
        p_out = _apply(ctx, "ST-F9", {"p_in": p_in})
        dims = {
            "q_in": q_wet,
            "ds_in": ds_in,
            "p_in": p_in,
            "q_h": q_h,
            "q_si": q_si,
            "d_raw": d_raw,
            "d_pipe": d_pipe,
            "v_act": v_act,
            "i_req": i_req,
            "i_slope": i_slope,
            "v_grav": v_grav,
            "ds_out": ds_out,
            "p_out": p_out,
            "q_out": q_wet,
        }
        warnings: list[Warning] = []
        band = (
            _factor(p, _V_BAND[0], _UNIT_ID),
            _factor(p, _V_BAND[1], _UNIT_ID),
        )
        if not band[0] <= v_act <= band[1]:
            warnings.append(
                _warn(
                    f"{_GB}；{_V_BAND[0]}~{_V_BAND[1]}",
                    f"压力段实际流速 v_act = {v_act:.4f} m/s 越出建议带"
                    f" [{band[0]}, {band[1]}]（取整后实流速）——调节方向："
                    "v_press（名义流速改档使取整管径落带）",
                    "v_press",
                )
            )
        v_min = _factor(p, _GRAVITY_V_MIN, _UNIT_ID)
        if v_grav < v_min:
            warnings.append(
                _warn(
                    f"{_HB5}；{_GRAVITY_V_MIN}",
                    f"重力段流速 v_grav = {v_grav:.4f} m/s 低于最小流速"
                    f" {v_min}（整定坡度下校核）——调节方向：d_grav"
                    "（放大重力段管径提高满流流速）",
                    "d_grav",
                )
            )
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
            warnings=tuple(warnings),
            formula_ids=FORMULA_IDS,
        )
