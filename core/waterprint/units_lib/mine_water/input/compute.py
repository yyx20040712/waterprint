"""矿井水输入计算实现：唯一计算源（KI-F1~F7 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【公式组】KI-F1~F7（docs/norms/mine_water_input.md 起草表；
#   manifest.py 登记）。
# 【注入点语义】本单元=矿井水线链首（executor 源节点：零入边）——
#   ctx.inflows 非空一律拒（全厂流量口径与进水水质的唯一注入点，
#   表单元信息节）；出流水量经 KI-F1 求值后按 q_design/kz 反解
#   q_avg_daily 规范单位（m3/s，零字面量——86400 换算已在公式串）；
#   出流水质=参数面六指标注入（GB/T 19223-2015 含悬浮物类典型值；
#   零去除键——输入源单元无处理功能，不经 apply、formula_ids 不含
#   去除式，与市政 tiaojiechi 零去除透传形态记档同款）。
# 【系数通道】factor.mine_input.* 经 ctx.params 投影面取值
#   （app._unit_params 线感知投影，mine_ 限定键空间）；缺键=领域异常。
# 【输出面（D2）】outflows=注入水量；dims=表主算例七量全量 snake 键；
#   outqualities=参数注入六指标；warnings=超高校核带越界
#   （freeboard ≥ factor.mine_input.freeboard.min；param_key 归因+
#   调节方向）；formula_ids=实际求值公式号全量。
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
from waterprint.units_lib.mine_water.input.manifest import FORMULA_IDS, manifest

_UNIT_ID = "mine_water_input"
_FREEBOARD_MIN = "factor.mine_input.freeboard.min"
_H_LOSS = "factor.mine_input.elevation_loss"
_KZ_MIN = "kz"
_PARAMS_POSITIVE = (
    "q_avg_daily",
    "kz",
    "dn_inlet",
    "z_water_inlet",
    "z_ground",
    "h_pool",
    "ss_in",
    "cod_in",
    "bod5_in",
    "nh3n_in",
    "tn_in",
    "tp_in",
)
_QUALITY_PARAMS = ("ss_in", "cod_in", "bod5_in", "nh3n_in", "tn_in", "tp_in")
_QUALITY_INDICATORS = ("SS", "CODCR", "BOD5", "NH3N", "TN", "TP")


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
    """参数域守卫：流量/管径/标高/水深/浓度非正一律拒；kz≥1 厂界口径拒。"""
    for key in _PARAMS_POSITIVE:
        value = params.get(key)
        if value is None or value <= 0:
            raise InvalidUnitConfig(
                f"单元 {_UNIT_ID!r} 参数 {key!r} 必须 > 0：得到 {value!r}"
            )
    if params[_KZ_MIN] < 1:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'kz' 必须 >= 1（总变化系数厂界口径，"
            f"flow.py R2 同精神）：得到 {params[_KZ_MIN]!r}"
        )


def _no_inflow(ctx: UnitContext) -> None:
    """链首守卫：注入点不接收任何入边（表单元信息节"唯一注入点"语义）。"""
    if ctx.inflows:
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 为矿井水线入水定义注入点，不接收任何入边："
            f"得到 {len(ctx.inflows)} 条（流量与水质经参数面注入）"
        )


def _apply(ctx: UnitContext, formula_id: str, bindings: dict[str, float]) -> float:
    """apply 薄封装：统一携带 (unit_id, condition_key) 与 trace sink。"""
    return formulas.apply(
        formula_id,
        bindings,
        (ctx.unit_id, ConditionSet.key(ctx.condition)),
        sink=ctx.trace,
    )


def _flow_and_elevation(ctx: UnitContext, p: dict[str, float]) -> dict[str, float]:
    """KI-F1~F7：设计流量/平均时流量/进水管流速/高程链/超高。"""
    q_design = _apply(ctx, "KI-F1", {"q_avg_daily": p["q_avg_daily"], "kz": p["kz"]})
    q_avg_h = _apply(ctx, "KI-F2", {"q_avg_daily": p["q_avg_daily"]})
    v_inlet = _apply(
        ctx,
        "KI-F3",
        {"q_avg_daily": p["q_avg_daily"], "pi": math.pi, "dn_inlet": p["dn_inlet"]},
    )
    z_pipe_bottom = _apply(
        ctx, "KI-F4", {"z_water_inlet": p["z_water_inlet"], "dn_inlet": p["dn_inlet"]}
    )
    z_water = _apply(
        ctx,
        "KI-F5",
        {"z_water_inlet": p["z_water_inlet"], "h_loss": _factor(p, _H_LOSS)},
    )
    return {
        "q_design": q_design,
        "q_avg_h": q_avg_h,
        "v_inlet": v_inlet,
        "z_pipe_bottom": z_pipe_bottom,
        "z_water": z_water,
        "z_bottom": _apply(ctx, "KI-F6", {"z_water": z_water, "h_pool": p["h_pool"]}),
        "freeboard": _apply(ctx, "KI-F7", {"z_ground": p["z_ground"], "z_water": z_water}),
    }


def _warn(source: str, message: str, param_key: str | None) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _warnings(p: dict[str, float], dims: dict[str, float]) -> tuple[Warning, ...]:
    """校核带检查：地面高出进水水面下限（freeboard ≥ freeboard.min）。"""
    floor = _factor(p, _FREEBOARD_MIN)
    if dims["freeboard"] < floor:
        return (
            _warn(
                f"GB/T 41019-2021（厂区布置，条号待核对）；{_FREEBOARD_MIN}",
                f"地面高出进水水面 = {dims['freeboard']:.4f} m 低于下限"
                f" {floor}——调节方向：z_ground（↑抬高地面）或 h_loss（↓减小进水损失）",
                "z_ground",
            ),
        )
    return ()


def _out_quality(p: dict[str, float]) -> WaterQuality:
    """出水质：参数面六指标注入（进水水质面，零去除不经 apply）。"""
    return WaterQuality(
        {
            indicator: p[param]
            for indicator, param in zip(
                _QUALITY_INDICATORS, _QUALITY_PARAMS, strict=True
            )
        }
    )


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _MineInput()


@final
class _MineInput:
    """矿井水输入 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """KI-F1~F7 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        _validate(p)
        _no_inflow(ctx)
        dims = _flow_and_elevation(ctx, p)
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            # 注入水量：q_avg_daily 规范单位 m3/s=KI-F1 求值 q_design/kz
            # （86400 换算在公式串，compute 零字面量）
            outflows={
                out_ref: WaterFlow(q_avg_daily=dims["q_design"] / p["kz"], kz=p["kz"])
            },
            outqualities={out_ref: _out_quality(p)},
            dims=dims,
            warnings=_warnings(p, dims),
            formula_ids=FORMULA_IDS,
        )
