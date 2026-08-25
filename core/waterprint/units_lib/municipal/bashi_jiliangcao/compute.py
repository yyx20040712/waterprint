"""巴歇尔计量槽计算实现：唯一计算源（BL-F1~F9 全经 registry.apply 求值）。

输入:  UnitContext（上游量 + 参数 + 工况 + 假设 + 迹收集器）
输出:  UnitResult（输出端口量 + dims 全量 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【公式组】BL-F1~F9（docs/norms/bashi_jiliangcao.md 起草表；manifest.py
#   登记）——B7 七档全档流量式主线：实测水头流量读数（F1）、设计/平均
#   水头反解与选档校核（F2/F3）、标准型构造尺寸（F4~F7）、淹没度自由流
#   判别（F8）、槽身水头损失（F9）。
# 【选档机制】喉宽 b_throat=grid 档位参数（B7 七档）；compute 按
#   round(b,2) 命中档名（flume.<档名>.* 键段），非档位值=InvalidUnitConfig
#   （档位面归 grid 层——Ruling ④同精神：compute 只保 b>0+命中）。
#   换算常量 ×1000 内联于公式（manifest 白名单区），本文件零换算字面量。
# 【流量口径（三表逐字冻结）】槽型选档与设计水头按最高时 flow.q_design
#   （峰值可计量）；平均时水头按 flow.q_avg_daily 校核。
# 【系数通道】factor.bashi_jiliangcao.*/removal.bashi_jiliangcao.* 经
#   ctx.params 投影面取值（app._unit_params，M1a 现状对齐）；缺键=领域异常。
# 【输出面（D2）】outflows=入流透传；dims=三表量测/构造结果全量 snake 键
#   （q_meas 按平均时水头读数=往返闭环校载体）；outqualities=零去除键
#   透传（removal.bashi_jiliangcao.*.mod_default 全 0.0——计量单元无
#   处理，透传分支不经 apply、formula_ids 不含去除式，与 ziwai 零去除
#   形态同款记档）；warnings=选档水头适用带（ha_design 越档 hmin/hmax）+
#   淹没度自由流判别（σ>scrit）两条；formula_ids=实际求值公式号全量。
# 【编写规则】同 _template/compute.py：R1 公式经注册表；R2 零字面量；
#   R3 工况只经参数；R4 纯函数；R5 禁 import 其他单元与 L3；R6 ≤400 行。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

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
from waterprint.units_lib.municipal.bashi_jiliangcao.manifest import (
    FORMULA_IDS,
    GRADES,
    THROAT_GRID,
    manifest,
)

_UNIT_ID = "municipal_bashi_jiliangcao"
_HB = "给水排水设计手册（第 5 册 城镇排水）量水堰槽章"
# 档位值→档名映射（B7 七档；round(b,2) 命中——档位面 manifest 声明，
# THROAT_GRID 真源区取值，本文件零档位字面量）。
_GRADE_BY_THROAT: dict[float, str] = dict(zip(THROAT_GRID, GRADES, strict=True))
_KEY_C = "factor.bashi_jiliangcao.flume.{grade}.c"
_KEY_N = "factor.bashi_jiliangcao.flume.{grade}.n"
_KEY_HMIN = "factor.bashi_jiliangcao.flume.{grade}.hmin"
_KEY_HMAX = "factor.bashi_jiliangcao.flume.{grade}.hmax"
_KEY_SCRIT = "factor.bashi_jiliangcao.flume.{grade}.scrit"


def _factor(params: dict[str, float], key: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


def _grade_of(params: dict[str, float]) -> tuple[str, dict[str, float]]:
    """选档：b_throat>0 守卫 + round(b,2) 档位命中 → (档名, 档系数面)。"""
    b_throat = params.get("b_throat")
    if b_throat is None or b_throat <= 0:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 参数 'b_throat' 必须 > 0：得到 {b_throat!r}"
        )
    grade = _GRADE_BY_THROAT.get(round(b_throat, 2))
    if grade is None:
        raise InvalidUnitConfig(
            f"单元 {_UNIT_ID!r} 喉宽 {b_throat!r} 非 B7 七档标准档位"
            f"（合法 {sorted(_GRADE_BY_THROAT)}——档位面经 manifest grid 声明，"
            "起草表追认点 1）"
        )
    return grade, {
        "c_coef": _factor(params, _KEY_C.format(grade=grade)),
        "n_exp": _factor(params, _KEY_N.format(grade=grade)),
        "hmin": _factor(params, _KEY_HMIN.format(grade=grade)),
        "hmax": _factor(params, _KEY_HMAX.format(grade=grade)),
        "scrit": _factor(params, _KEY_SCRIT.format(grade=grade)),
    }


def _inflow(ctx: UnitContext) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条"
            "（计量槽单入单出语义）"
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


def _heads(
    ctx: UnitContext, flow: WaterFlow, coef: dict[str, float]
) -> dict[str, float]:
    """BL-F1~F3：设计/平均水头反解与平均时流量读数（往返闭环）。"""
    binds = {"c_coef": coef["c_coef"], "n_exp": coef["n_exp"]}
    ha_design = _apply(ctx, "BL-F2", {"q_design": flow.q_design, **binds})
    ha_avg = _apply(ctx, "BL-F3", {"q_avg_daily": flow.q_avg_daily, **binds})
    return {
        "ha_design": ha_design,
        "ha_avg": ha_avg,
        "q_meas": _apply(ctx, "BL-F1", {"ha": ha_avg, **binds}),
    }


def _geometry(ctx: UnitContext, p: dict[str, float], b_throat: float) -> dict[str, float]:
    """BL-F4~F7：标准型构造尺寸（收缩/喉道/扩散段）与槽总长。"""
    l1 = _apply(ctx, "BL-F5", {"b_throat": b_throat})
    l_throat = _factor(p, "factor.bashi_jiliangcao.geometry.l_throat")
    l_diffuse = _factor(p, "factor.bashi_jiliangcao.geometry.l_diffuse")
    return {
        "b1": _apply(ctx, "BL-F4", {"b_throat": b_throat}),
        "l1": l1,
        "b2": _apply(ctx, "BL-F6", {"b_throat": b_throat}),
        "l_total": _apply(
            ctx, "BL-F7", {"l1": l1, "l_throat": l_throat, "l_diffuse": l_diffuse}
        ),
        "l_throat": l_throat,
        "l_diffuse": l_diffuse,
        # 构造面常量（标准型：喉道底跌落 N/槽身边距 K——dims 承载供出图）
        "n_depress": _factor(p, "factor.bashi_jiliangcao.geometry.n_depress"),
        "k_margin": _factor(p, "factor.bashi_jiliangcao.geometry.k_margin"),
    }


def _check(ctx: UnitContext, p: dict[str, float], ha_design: float) -> dict[str, float]:
    """BL-F8/F9：淹没度自由流判别与槽身水头损失（估算口径）。"""
    hb = _factor(p, "factor.bashi_jiliangcao.hb_design")
    ratio = _factor(p, "factor.bashi_jiliangcao.loss_ratio")
    return {
        "sigma": _apply(ctx, "BL-F8", {"hb_design": hb, "ha_design": ha_design}),
        "h_loss": _apply(ctx, "BL-F9", {"loss_ratio": ratio, "ha_design": ha_design}),
    }


def _warn(source: str, message: str, param_key: str) -> Warning:
    """单条校核带越界警告（severity=WARN，GR 口径三必带）。"""
    return Warning(severity=Severity.WARN, source=source, message=message, param_key=param_key)


def _warnings(
    p: dict[str, float],
    grade: str,
    coef: dict[str, float],
    heads: dict[str, float],
    check: dict[str, float],
) -> tuple[Warning, ...]:
    """校核带检查：选档水头适用带（ha_design 越档）+ 淹没度自由流判别。"""
    found: list[Warning] = []
    if not coef["hmin"] <= heads["ha_design"] <= coef["hmax"]:
        found.append(
            _warn(
                f"{_HB}；factor.bashi_jiliangcao.flume.{grade}.hmin/hmax",
                f"设计水头 ha_design = {heads['ha_design']:.4f} m 越出本档适用带"
                f" [{coef['hmin']}, {coef['hmax']}]——调节方向：b_throat"
                "（换档：小档加深水头/大档减浅水头，B7 七档 grid）",
                "b_throat",
            )
        )
    if check["sigma"] > coef["scrit"]:
        found.append(
            _warn(
                f"{_HB}；factor.bashi_jiliangcao.flume.{grade}.scrit",
                f"淹没度 sigma = {check['sigma']:.4f} 超临界淹没度"
                f" {coef['scrit']}（淹没流，Q=C·h^n 自由流式失效）——调节方向："
                "hb_design（降低下游水深设计假定）或 b_throat（大档加深 ha）",
                "b_throat",
            )
        )
    return tuple(found)


def make_unit() -> Unit:
    """单元工厂（包 __init__ 白名单导出；executor 经 app 装配消费）。"""
    return _Bashi()


@final
class _Bashi:
    """巴歇尔计量槽 Unit 协议实现：manifest 声明 + compute 纯函数。"""

    manifest = manifest

    def compute(self, ctx: UnitContext) -> UnitResult:
        """BL-F1~F9 主算路径（纯函数：同 ctx 必同 UnitResult）。"""
        p = dict(ctx.params)
        grade, coef = _grade_of(p)
        in_ref, flow = _inflow(ctx)
        quality = ctx.inqualities.get(in_ref, WaterQuality({}))
        heads = _heads(ctx, flow, coef)
        geometry = _geometry(ctx, p, p["b_throat"])
        check = _check(ctx, p, heads["ha_design"])
        dims = {**heads, **geometry, **check}
        out_ref = PortRef(unit_id=ctx.unit_id, port_id="out")
        return UnitResult(
            outflows={out_ref: WaterFlow(q_avg_daily=flow.q_avg_daily, kz=flow.kz)},
            # 零去除键透传：removal.bashi_jiliangcao.*.mod_default 全 0.0
            # （计量单元无处理）——出水质=入水质逐键原样（不经 apply，
            # 简报 D2 裁决；计量指标=流量经 dims 的 q_meas/ha_design 承载）
            outqualities={out_ref: WaterQuality(dict(quality.concentrations))},
            dims=dims,
            warnings=_warnings(p, grade, coef, heads, check),
            formula_ids=FORMULA_IDS,
        )
