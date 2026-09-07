"""调节池计算实现：唯一计算源（TJ-F1~F13 全经 registry.apply_batch
求值——批 13-C 同源向量路径：公式链以 ndarray 流动，标量=N=1 退化）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收；批 13-C
#   向量化重写：公式链经 _apply_batch 批量正门[AGENTS §13.6 同源向量
#   路径唯一——标量=N=1 退化；守卫层/warnings/ceil=N=1 边界件；N>1=
#   批 D 引擎正门]）
#
# 【公式组】TJ-F1~F13（docs/norms/tiaojiechi.md 起草表；manifest.py 登记）。
# 【DSL 收口】ceil 与构造步长离散在本文件收口（DSL 无 ceil）：池宽 B/
#   池长 L=ceil(b_raw·l_raw, side_disc_step 0.5 m 档)；溢流管 DN=ceil(
#   d_overflow_raw, length_disc_step 0.1 m 档)——**双步长参数并存**（两处
#   _ceil_vec 各携各步长零混淆，均 N=1 边界件）；π 经符号 pi 绑定
#   math.pi（_vec 装箱）。零数值字面量。
# 【流量口径】调节容积/搅拌/出水泵按平均日 flow.q_avg_daily（×86400/
#   ×3600 换算已内联公式串）；溢流/超越管按最高时 flow.q_design——四表
#   口径逐字（出水泵按平均时均匀输出，调节池均化功能的下游口径）。
# 【系数通道】factor.tiaojiechi.*/removal.tiaojiechi.* 经 ctx.params
#   投影面取值（app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D2）】outflows=入流透传；dims=四表水力结果全量 snake 键；
#   outqualities=零去除键透传（removal.tiaojiechi.*.mod_default 全 0.0
#   ——物理均化无去除，透传分支不经 apply、formula_ids 不含去除式，
#   与 M1a 三单元一律乘 (1−r) 的形态差异记档）；warnings=校核带越界
#   （实际停留时间带/有效水深带/长宽比带+实际调节容积≥需容积校核；
#   param_key 归因+调节方向）；formula_ids=实际求值公式号全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from typing import final

import numpy

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
    _apply_batch,
    _factor,
    _inflow,
    _make_ceil_step,
    _vec,
)
from waterprint.units_lib.municipal.tiaojiechi.manifest import FORMULA_IDS, manifest

type _Array = numpy.ndarray  # 向量链注记别名（批 13-C——公式链中间量形态）

_UNIT_ID = "municipal_tiaojiechi"
_HB = "给水排水设计手册（第 5 册 城镇排水）调节池/泵站章"
_HRT_BAND = (
    "factor.tiaojiechi.hrt_band.min",
    "factor.tiaojiechi.hrt_band.max",
)
_DEPTH_BAND = (
    "factor.tiaojiechi.depth_band.min",
    "factor.tiaojiechi.depth_band.max",
)
_RATIO_BAND = (
    "factor.tiaojiechi.ratio_lb_band.min",
    "factor.tiaojiechi.ratio_lb_band.max",
)
_STIR_DENSITY = "factor.tiaojiechi.stir.power_density"
_OVERFLOW_VELOCITY = "factor.tiaojiechi.overflow_velocity"
_PARAMS_POSITIVE = (
    "n",
    "t_reg",
    "h2",
    "ratio_lb",
    "n_pump_duty",
    "side_disc_step",
    "length_disc_step",
)
_FACTORS_POSITIVE = (_STIR_DENSITY, _OVERFLOW_VELOCITY)


_ceil_step = _make_ceil_step(_UNIT_ID, "取整步长", spaced=False)


def _ceil_vec(raw: _Array, step: float) -> _Array:
    """ceil 离散 N=1 边界件：取标→步长取整→回箱（批 13-C 数组链形态）。"""
    return _vec(_ceil_step(float(raw[0]), step))


def _validate(params: dict[str, float]) -> None:
    """参数域守卫：池数/时间/水深/长宽比/泵台数/步长与搅拌·溢流系数非正一律拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}")
    for key in _FACTORS_POSITIVE:
        if _factor(params, key, _UNIT_ID) <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 系数键 {key!r} 必须 > 0（搅拌功率密度/溢流管流速物理域）"
            )


def _basin(ctx: UnitContext, p: dict[str, float], flow: WaterFlow) -> dict[str, _Array]:
    """TJ-F1~F8：需调节容积/单池几何（B·L 0.5 m 档）/实际容积与停留时间。"""
    v_total = _apply_batch(
        ctx, "TJ-F1", {"q_avg_daily": _vec(flow.q_avg_daily), "t_reg": _vec(p["t_reg"])}
    )
    v1 = _apply_batch(ctx, "TJ-F2", {"v_total": v_total, "n": _vec(p["n"])})
    a1 = _apply_batch(ctx, "TJ-F3", {"v1": v1, "h2": _vec(p["h2"])})
    b_raw = _apply_batch(ctx, "TJ-F4", {"a1": a1, "ratio_lb": _vec(p["ratio_lb"])})
    b = _ceil_vec(b_raw, p["side_disc_step"])
    l_raw = _apply_batch(ctx, "TJ-F5", {"a1": a1, "B": b})
    length = _ceil_vec(l_raw, p["side_disc_step"])
    a_act = _apply_batch(ctx, "TJ-F6", {"B": b, "L": length})
    v_act_total = _apply_batch(
        ctx, "TJ-F7", {"a_act": a_act, "h2": _vec(p["h2"]), "n": _vec(p["n"])}
    )
    return {
        "v_total": v_total,
        "v1": v1,
        "a1": a1,
        "b_raw": b_raw,
        "b": b,
        "l_raw": l_raw,
        "l": length,
        "a_act": a_act,
        "v_act_total": v_act_total,
        "t_reg_act": _apply_batch(
            ctx, "TJ-F8", {"v_act_total": v_act_total, "q_avg_daily": _vec(flow.q_avg_daily)}
        ),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _band(p: dict[str, float], keys: tuple[str, str]) -> tuple[float, float]:
    """带类系数取值（min/max 双键）。"""
    return _factor(p, keys[0], _UNIT_ID), _factor(p, keys[1], _UNIT_ID)


def _warnings(p: dict[str, float], basin: dict[str, _Array]) -> tuple[Warning, ...]:
    """校核带检查：实际停留时间/有效水深/长宽比/调节容积充足性。"""
    found: list[Warning] = []
    t_reg_act = float(basin["t_reg_act"][0])
    v_act_total = float(basin["v_act_total"][0])
    v_total = float(basin["v_total"][0])
    hrt = _band(p, _HRT_BAND)
    if not hrt[0] <= t_reg_act <= hrt[1]:
        found.append(
            _warn(
                f"{_HB}；{_HRT_BAND[0]}~{_HRT_BAND[1]}",
                f"实际调节停留时间 = {t_reg_act:.4f} h 越出建议带"
                f" [{hrt[0]}, {hrt[1]}]——调节方向：t_reg（↑扩容）或 h2/n（↑加深加格）",
                "t_reg",
            )
        )
    dep = _band(p, _DEPTH_BAND)
    if not dep[0] <= p["h2"] <= dep[1]:
        found.append(
            _warn(
                f"{_HB}；{_DEPTH_BAND[0]}~{_DEPTH_BAND[1]}",
                f"有效水深 h2 = {p['h2']:.4f} m 越出建议带"
                f" [{dep[0]}, {dep[1]}]——调节方向：h2（工程常用带内取值）",
                "h2",
            )
        )
    ratio = _band(p, _RATIO_BAND)
    if not ratio[0] <= p["ratio_lb"] <= ratio[1]:
        found.append(
            _warn(
                f"{_HB}；{_RATIO_BAND[0]}~{_RATIO_BAND[1]}",
                f"池长宽比 L/B = {p['ratio_lb']:.4f} 越出建议带"
                f" [{ratio[0]}, {ratio[1]}]——调节方向：ratio_lb（矩形池工程常用）",
                "ratio_lb",
            )
        )
    if v_act_total < v_total:
        found.append(
            _warn(
                f"{_HB}；TJ-F7 调节容积校核（v_act_total ≥ v_total）",
                f"实际调节容积 = {v_act_total:.4f} m³ 低于需容积"
                f" {v_total:.4f} m³——调节方向：h2（↑加深）或 n（↑加格）",
                "h2",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _Tiaojiechi()


@final
class _Tiaojiechi:
    """调节池 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """TJ-F1~F13 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        in_ref, flow = _inflow(ctx, "调节池单入单出语义")
        basin = _basin(ctx, p, flow)
        p_stir = _apply_batch(
            ctx,
            "TJ-F9",
            {
                "v_act_total": basin["v_act_total"],
                "w_stir": _vec(_factor(p, _STIR_DENSITY, _UNIT_ID)),
            },
        )
        q_pump1 = _apply_batch(
            ctx,
            "TJ-F10",
            {"q_avg_daily": _vec(flow.q_avg_daily), "n_pump_duty": _vec(p["n_pump_duty"])},
        )
        d_overflow = _ceil_vec(
            _apply_batch(
                ctx,
                "TJ-F11",
                {
                    "q_design": _vec(flow.q_design),
                    "pi": _vec(math.pi),
                    "v_overflow": _vec(_factor(p, _OVERFLOW_VELOCITY, _UNIT_ID)),
                },
            ),
            p["length_disc_step"],
        )
        h_total = _apply_batch(
            ctx,
            "TJ-F12",
            {
                "h_super": _vec(_factor(p, "factor.tiaojiechi.superheight", _UNIT_ID)),
                "h2": _vec(p["h2"]),
            },
        )
        v_concrete = _apply_batch(
            ctx,
            "TJ-F13",
            {
                "a_act": basin["a_act"],
                "h_total": h_total,
                "n": _vec(p["n"]),
                "wall_coef": _vec(_factor(p, "factor.tiaojiechi.wall_thickness_coef", _UNIT_ID)),
            },
        )
        arrays = {
            **basin,
            "p_stir": p_stir,
            "q_pump1": q_pump1,
            "d_overflow": d_overflow,
            "h_total": h_total,
            "v_concrete": v_concrete,
        }
        dims = {key: float(value[0]) for key, value in arrays.items()}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            # 零去除键透传：removal.tiaojiechi.*.mod_default 全 0.0（物理
            # 均化无去除）——出水质=入水质逐键原样（不经 apply，简报 D2 裁决）
            outqualities={out_ref: WaterQuality(dict(quality.concentrations))},
            dims=dims,
            warnings=_warnings(p, basin),
            formula_ids=FORMULA_IDS,
        )
