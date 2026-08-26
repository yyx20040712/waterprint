"""水头损失公式（沿程/局部/堰/孔口）：全部经公式注册表求值（挂条文溯源）。

输入:  几何参数（管长/管径/当量长度/堰宽…）+ 流量（当前工况）
输出:  水头损失值（m），每次求值产生计算迹记录
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/elevation/test_losses.py）
#
# 【公开接口】
#   friction_loss(geometry, flow) -> float      沿程损失（m）
#   local_loss(fittings, flow) -> float         局部损失（m，当量长度/系数法）
#   weir_loss(weir_geometry, flow) -> float     堰流损失（m）
#   orifice_loss(orifice_geometry, flow) -> float  孔口损失（m）
#   head_losses(...) -> Losses                  组合入口（逐项列明，可审计）
#
# 【行为规格】
#   R1 每个公式只经 registry.formulas.apply 求值（formula_id 挂规范条文，
#      如给排水手册/GB 50014 相关条文——具体条文号在实现期由领域专家
#      核定后登记，登记项无 norm_ref 不准入库）。
#   R2 粗糙系数/局部阻力系数等经验值一律来自 assumptions/coefficients，
#      本文件零魔法数（§3 保证 7）。
#   R3 非负不变量：一切损失 >= 0（性质测试）；负值 = 公式误用即失败。
#   R4 单调性（性质测试）：沿程损失随流量单调不减、随管径单调不增。
#   R5 工况关联：流量取当前工况档（design/avg 结果不同——按 condition_key
#      索引，§14.1）。
#
# 【测试要求】零魔法数静态断言（源码扫描数值字面量白名单）、
#   非负/单调性质、各公式 apply 产生迹记录。
#
# 【参照】重写计划 §13.3 职责表/§14.2 跌水与提升行
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final

from waterprint.contracts.trace_api import TraceSink
from waterprint.registry.assumptions import assumption
from waterprint.registry.formulas import FormulaSpec, apply, norm_ref_of, register

__all__ = [
    "InvalidLossError",
    "LossItem",
    "Losses",
    "friction_loss",
    "head_losses",
    "local_loss",
    "orifice_loss",
    "weir_loss",
]

_HB = "《给水排水设计手册（第 5 册 城镇排水）》管道/堰/孔口水力计算（起草，待追认）"

# EL-F1~F4：达西/当量长度（系数法）/堰流/孔口四族（D2 双源口径——GB 50014
# 相关条文号由领域专家核定后随数据批升版；经验系数一律符号绑定经
# assumptions 取值[R2 零魔法数]，结构常数（4/2/2÷3 指数）内联公式串）。
_FORMULAS: Final[tuple[FormulaSpec, ...]] = (
    FormulaSpec(
        "EL-F1",
        "h_f = lambda_friction * (length / diameter) "
        "* (4 * flow / (pi * diameter ** 2)) ** 2 / (2 * g)",
        {
            "lambda_friction": (
                "DIMENSIONLESS", "沿程阻力系数 λ（elevation.losses.friction_lambda）"
            ),
            "length": ("LENGTH", "管长 m"),
            "diameter": ("LENGTH", "管径 m"),
            "flow": ("FLOW", "流量 m3/s（当前工况档）"),
            "pi": ("DIMENSIONLESS", "圆周率（math.pi 绑定）"),
            "g": ("DIMENSIONLESS", "重力加速度 m/s2（elevation.losses.gravity）"),
        },
        "LENGTH",
        _HB,
    ),
    FormulaSpec(
        "EL-F2",
        "h_z = zeta * (4 * flow / (pi * diameter ** 2)) ** 2 / (2 * g)",
        {
            "zeta": ("DIMENSIONLESS", "局部阻力系数 ζ（当量 fittings 逐件求和前单件）"),
            "diameter": ("LENGTH", "管径 m"),
            "flow": ("FLOW", "流量 m3/s"),
            "pi": ("DIMENSIONLESS", "圆周率"),
            "g": ("DIMENSIONLESS", "重力加速度 m/s2"),
        },
        "LENGTH",
        _HB,
    ),
    FormulaSpec(
        "EL-F3",
        "h_w = (flow / (weir_coefficient * weir_width)) ** (2 / 3)",
        {
            "flow": ("FLOW", "堰流量 m3/s"),
            "weir_coefficient": (
                "DIMENSIONLESS", "矩形薄壁堰系数（elevation.losses.weir_coefficient）"
            ),
            "weir_width": ("LENGTH", "堰宽 m"),
        },
        "LENGTH",
        _HB,
    ),
    FormulaSpec(
        "EL-F4",
        "h_o = (flow / (orifice_coefficient * pi * diameter ** 2 / 4)) ** 2 / (2 * g)",
        {
            "flow": ("FLOW", "孔口流量 m3/s"),
            "orifice_coefficient": (
                "DIMENSIONLESS", "孔口流量系数 μ（elevation.losses.orifice_coefficient）"
            ),
            "diameter": ("LENGTH", "孔口直径 m"),
            "pi": ("DIMENSIONLESS", "圆周率"),
            "g": ("DIMENSIONLESS", "重力加速度 m/s2"),
        },
        "LENGTH",
        _HB,
    ),
)
for _spec in _FORMULAS:
    register(_spec)


class InvalidLossError(Exception):
    """水头损失求值非法（几何缺键/未知损失类/非有限值）——领域异常（GR-11 族）。"""


@dataclass(frozen=True)
@final
class LossItem:
    """单项损失（可审计六字段）：标签+类别+值+公式溯源+绑定快照+工况。"""

    label: str
    kind: str
    value: float
    formula_id: str
    norm_ref: str
    inputs: Mapping[str, float]
    condition_key: str


@dataclass(frozen=True)
@final
class Losses:
    """组合损失（不可变）：逐项列明 + 总和（R3 非负不变量载体）。"""

    items: tuple[LossItem, ...]
    total: float

    def by_label(self, label: str) -> float:
        """按归属标签取合计（build_profile 站间扣损失取数口）。"""
        return sum(
            item.value for item in self.items if item.label == label
        )


def _view(assumptions: Mapping[str, float] | None) -> Mapping[str, float]:
    """假设视图归一（None=默认清单；R2 经验值唯一通道）。"""
    return {} if assumptions is None else assumptions


def _pair(geometry: Mapping[str, object], key: str) -> float:
    """几何键取值（缺键/非有限 = 领域异常——禁静默默认）。"""
    raw = geometry.get(key)
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise InvalidLossError(
            f"损失几何缺键或非数值：{key!r}（得到 {raw!r}）"
        )
    value = float(raw)
    if not math.isfinite(value) or value <= 0.0:
        raise InvalidLossError(
            f"损失几何 {key!r} 须为正有限值：得到 {value!r}（GR-02/GR-04）"
        )
    return value


def friction_loss(
    geometry: Mapping[str, float],
    flow: float,
    ctx: tuple[str, str] = ("", ""),
    sink: TraceSink | None = None,
    assumptions: Mapping[str, float] | None = None,
) -> float:
    """沿程损失（m）：EL-F1 达西公式，λ 经 assumptions（R1/R2）。"""
    view = _view(assumptions)
    return apply(
        "EL-F1",
        {
            "lambda_friction": assumption("elevation.losses.friction_lambda", view),
            "length": _pair(geometry, "length"),
            "diameter": _pair(geometry, "diameter"),
            "flow": float(flow),
            "pi": math.pi,
            "g": assumption("elevation.losses.gravity", view),
        },
        ctx,
        sink,
    )


def local_loss(
    fittings: Sequence[Mapping[str, float]],
    flow: float,
    ctx: tuple[str, str] = ("", ""),
    sink: TraceSink | None = None,
    assumptions: Mapping[str, float] | None = None,
) -> float:
    """局部损失（m）：EL-F2 系数法逐件求和（当量长度口径系数法承载）。"""
    view = _view(assumptions)
    total = 0.0
    for fitting in fittings:
        total += apply(
            "EL-F2",
            {
                "zeta": _pair(fitting, "zeta"),
                "diameter": _pair(fitting, "diameter"),
                "flow": float(flow),
                "pi": math.pi,
                "g": assumption("elevation.losses.gravity", view),
            },
            ctx,
            sink,
        )
    return total


def weir_loss(
    weir_geometry: Mapping[str, float],
    flow: float,
    ctx: tuple[str, str] = ("", ""),
    sink: TraceSink | None = None,
    assumptions: Mapping[str, float] | None = None,
) -> float:
    """堰流损失（m）：EL-F3 矩形薄壁堰（m 系数经 assumptions）。"""
    return apply(
        "EL-F3",
        {
            "flow": float(flow),
            "weir_coefficient": assumption(
                "elevation.losses.weir_coefficient", _view(assumptions)
            ),
            "weir_width": _pair(weir_geometry, "weir_width"),
        },
        ctx,
        sink,
    )


def orifice_loss(
    orifice_geometry: Mapping[str, float],
    flow: float,
    ctx: tuple[str, str] = ("", ""),
    sink: TraceSink | None = None,
    assumptions: Mapping[str, float] | None = None,
) -> float:
    """孔口损失（m）：EL-F4（μ 系数经 assumptions）。"""
    view = _view(assumptions)
    return apply(
        "EL-F4",
        {
            "flow": float(flow),
            "orifice_coefficient": assumption(
                "elevation.losses.orifice_coefficient", view
            ),
            "diameter": _pair(orifice_geometry, "diameter"),
            "pi": math.pi,
            "g": assumption("elevation.losses.gravity", view),
        },
        ctx,
        sink,
    )


def _segment_bindings(
    label: str, spec: Mapping[str, object], flow: float,
    view: Mapping[str, float],
) -> tuple[str, dict[str, float]]:
    """段声明 → (formula_id, apply 绑定)（经验系数经 assumptions 符号绑定）。"""
    kind = spec.get("kind")
    gravity = assumption("elevation.losses.gravity", view)
    if kind == "friction":
        return "EL-F1", {
            "lambda_friction": assumption(
                "elevation.losses.friction_lambda", view
            ),
            "length": _pair(spec, "length"),
            "diameter": _pair(spec, "diameter"),
            "flow": float(flow),
            "pi": math.pi,
            "g": gravity,
        }
    if kind == "weir":
        return "EL-F3", {
            "flow": float(flow),
            "weir_coefficient": assumption(
                "elevation.losses.weir_coefficient", view
            ),
            "weir_width": _pair(spec, "weir_width"),
        }
    if kind == "orifice":
        return "EL-F4", {
            "flow": float(flow),
            "orifice_coefficient": assumption(
                "elevation.losses.orifice_coefficient", view
            ),
            "diameter": _pair(spec, "diameter"),
            "pi": math.pi,
            "g": gravity,
        }
    if kind == "local":
        fittings = spec.get("fittings")
        if not isinstance(fittings, Sequence) or not fittings:
            raise InvalidLossError(
                f"local 段 {label!r} 缺 fittings 序列（系数法逐件求和前提）"
            )
        zeta_total = sum(_pair(item, "zeta") for item in fittings)
        diameters = {_pair(item, "diameter") for item in fittings}
        if len(diameters) != 1:
            raise InvalidLossError(
                f"local 段 {label!r} fittings 管径不一致：{sorted(diameters)}"
                "（系数法求和要求同径——分管径请分段声明）"
            )
        return "EL-F2", {
            "zeta": zeta_total,
            "diameter": diameters.pop(),
            "flow": float(flow),
            "pi": math.pi,
            "g": gravity,
        }
    raise InvalidLossError(
        f"未知损失类别：{kind!r}（合法 friction/local/weir/orifice——"
        f"段 {label!r}，GR-09）"
    )


def head_losses(
    segments: Sequence[tuple[str, Mapping[str, object], float]],
    ctx: tuple[str, str] = ("", ""),
    sink: TraceSink | None = None,
    assumptions: Mapping[str, float] | None = None,
) -> Losses:
    """组合入口（逐项列明可审计）：每段 (label, spec, flow)，spec.kind 选族。

    每段经 registry.apply 求值（R1/R3 唯一求值路径），绑定快照随 LossItem
    入迹（inputs）——profile/drafting/cost 消费方零二次推导。
    """
    items: list[LossItem] = []
    for label, spec, flow in segments:
        formula_id, bindings = _segment_bindings(
            label, spec, flow, _view(assumptions)
        )
        value = apply(formula_id, bindings, ctx, sink)
        items.append(
            LossItem(
                label=label,
                kind=str(spec["kind"]),
                value=value,
                formula_id=formula_id,
                norm_ref=norm_ref_of(formula_id),
                inputs=bindings,
                condition_key=ctx[1],
            )
        )
    return Losses(items=tuple(items), total=sum(item.value for item in items))
