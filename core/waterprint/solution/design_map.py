"""可行域引导（design_map）：轴声明→稠密求值面→可行段/掩码结构化产物。

输入:  轴声明（1~2 个 {field_id, range?, step?}）+ 网格求值行（enumerate
       同源——R1 单实现双用）+ 双源可行掩码（非 NaN AND 约束通过）
输出:  DesignMap（轴元数据/统计/1D 可行段|2D 掩码/约束覆盖/诊断块——确定性 JSON 面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FD 批 PD1~PD5 终裁 2026-09-09 会话 n+28；镜像测试
#   tests/solution/test_design_map.py）
#
# 【公开接口】
#   derive_step(span: tuple[float, float]) -> float
#       缺省步长单源：(max-min)/10（PD8——与 webapp features/params/lib
#       deriveStep 同式同注释，跨语言黄金值用例互锁：同一 range→同一
#       step/点数期望，防 Python/JS 派生漂移）
#   axis_point_budget(span, step) -> int
#       解析期点数预算（P1-5：与 grid._ranged_values 生成同式——
#       numpy.arange(low, high+stride/2, stride) 长度镜像，闭区间含
#       首末点口径；先于 build_grid 拦截，杜绝「先生成后拒绝」）
#   resolve_axes(params, axes) -> tuple[ResolvedAxis, ...]
#       轴声明归一：长度 1~2/field_id 存在且属该单元/重复拒/range 缺省
#       =manifest range（缺席拒——无扫描基准）/覆盖 min<max 且 ⊆manifest
#       （闭区间，越界 fail-closed）/step>0 有限（P0-1 core 防御面）/
#       step 缺省=derive_step
#   ensure_budget(resolved, overrides) -> None
#       总点数=各轴预算之积超 solution.design_map.max_points（registry
#       伴生件注册，default=2500 待专家追认）→ DesignMapTooLarge（消息
#       形态照抄 GridTooLarge 泛化口径）；max_points 覆盖值 <1 拒
#       （0/负覆盖值域守卫——挂账硬化裁量本批兑现）
#   axis_mappings(resolved) -> list[Mapping]
#       build_grid 喂入形（{field_id, range{min,max}, step}——Mapping
#       起止步长既有路径，不建第二采样器，PD1）
#   build_design_map(unit_id, grid, feasible, resolved, coverage) -> DesignMap
#       产物装配：轴值=网格列真值（unique 升序）；1D=segments（可行段
#       合并——极大连续可行点列 [{start,end}] 值域对）；2D=mask（声明
#       序 row-major 0/1——grid 字典序域经转置归位）；stats；
#       diagnosis 逐轴块（投影口径——2D 任一补全可行即入投影）
#   class DesignMap(不可变)：unit_id/axes/stats/axis_values/segments
#       （1D）|mask（2D）/constraint_coverage/diagnosis + payload()
#       （确定性 JSON——双跑 sort_keys 字节同，常驻断言）
#   class ResolvedAxis(不可变)：field_id/dim/label_zh/min/max/step
#   widest_segment(values, mask) -> {start,end,centroid} | None
#       最宽可行段纯函数（公开——diagnose._grid_statistics 幅度统计
#       同源消费，禁 B4 双胞胎）
#   class DesignMapTooLarge(Exception)：护栏超限（4xx 映射——server 面）
#   class InvalidDesignMapError(Exception)：轴声明非法（GR-11 族，422 面
#       的 core 防御侧）
#   feasible_mask(frame, pass_matrix) -> ndarray[bool]
#       PD2 双源可行掩码：行非 NaN（计算域有效）∧ 约束通过——空约束
#       集=全真（GR-14）下 NaN 域拒仍构成不可行面（「全绿」≠「无
#       信息」，P0-2 终裁核心；app 正门装配消费）
#
# 【行为规格】
#   R1 单实现双用：稠密求值走 enumerate_solutions 同管线（app 装配），
#      本文件零求值逻辑——可行掩码由调用方按双源口径（行非 NaN AND
#      约束通过，PD2）传入；「无第二判据」由对拍测试证明。
#   R2 确定性：同输入同产物（payload() sort_keys 字节同——浮点取自
#      网格生成值，无中间重算）。
#   R3 降级不拒：无适用约束单元=constraint_coverage="degraded"（绿区
#      =计算有效域，诚实呈现）；"full"=约束集非空。
#   R4 不编造：无可行段=diagnosis 逐轴 magnitude/widest_segment/
#      recommended_value 均 None，只报 feasible_ratio（含 0）。
#
# 【测试要求】轴声明四类拒/预算拦截先于网格/产物形态全字段+双跑字节同/
#   段合并与 2D 转置/诊断块 None 面（PD5 四类契约）。
#
# 【参照】briefs/task-FD-plan.md PD1~PD5；reports/explore-FD-freeze.md
#   结论2/3/4
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any, Final, final

import numpy
import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（enumerate 同款记档）

from waterprint.contracts.manifest import ParamSpec
from waterprint.registry.assumptions import assumption
from waterprint.solution.constraints import Constraint
from waterprint.solution.grid import Grid

_MAX_POINTS_KEY: Final[str] = "solution.design_map.max_points"
_MAX_AXES: Final[int] = 2  # FD 契约：1D 行内区间条/2D 模态热力图（ruff PLR2004 同源）


class DesignMapTooLarge(Exception):  # noqa: N818  # 名冻结自 FD 终裁 PD4
    """可行域扫描总点数超护栏（各轴 points 之积 > max_points）——领域异常。"""


class InvalidDesignMapError(Exception):
    """轴声明非法（长度/未知字段/range 越界/step 非正）——GR-11 族。"""


@dataclass(frozen=True)
@final
class ResolvedAxis:
    """归一后的轴声明（不可变）：扫描区间 + 有效步长 + 声明面元数据。"""

    field_id: str
    dim: str
    label_zh: str | None
    minimum: float
    maximum: float
    step: float


@dataclass(frozen=True)
@final
class DesignMap:
    """可行域产物（不可变）：确定性 JSON 面（payload()）。"""

    unit_id: str
    axes: tuple[Mapping[str, Any], ...]
    stats: Mapping[str, float]
    axis_values: tuple[tuple[float, ...], ...]
    segments: tuple[Mapping[str, float], ...] | None  # 1D 专用（2D=None）
    mask: tuple[tuple[int, ...], ...] | None  # 2D 专用（声明序 row-major；1D=None）
    constraint_coverage: str  # "full" | "degraded"
    diagnosis: Mapping[str, Any]

    def payload(self) -> dict[str, Any]:
        """确定性 JSON 投影（双跑 sort_keys 字节同——R2 常驻断言面）。"""
        return {
            "unit_id": self.unit_id,
            "axes": [dict(axis) for axis in self.axes],
            "stats": dict(self.stats),
            "axis_values": [list(values) for values in self.axis_values],
            "segments": (
                None
                if self.segments is None
                else [dict(segment) for segment in self.segments]
            ),
            "mask": None if self.mask is None else [list(row) for row in self.mask],
            "constraint_coverage": self.constraint_coverage,
            "diagnosis": dict(self.diagnosis),
        }


def _number(value: object, where: str) -> float:
    """数值守卫（GR-02，grid._number 同口径）：bool 拒/非数值拒/非有限拒。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidDesignMapError(f"{where} 必须为数值（int|float，bool 拒）：得到 {value!r}")
    number = float(value)
    if not isfinite(number):
        raise InvalidDesignMapError(f"{where} 非有限：{number!r}（GR-02 输入即拒）")
    return number


def derive_step(span: tuple[float, float]) -> float:
    """缺省步长单源（PD8）：(max-min)/10——11 档指引粒度；与 webapp
    deriveStep 同式（黄金值用例互锁，注释双向引用）。"""
    return (span[1] - span[0]) / 10


def axis_point_budget(span: tuple[float, float], step: float) -> int:
    """解析期点数预算（P1-5）：grid._ranged_values 生成式同源 arange 长度
    （闭区间含首末点口径）。R 轮注记：_ranged_values 另有 I-1 钳制面
    （非整除上界裁 v≤high）——预算恒 ≥ 实际点数（安全方向上界，护栏
    无旁路；「逐字镜像」仅指 arange 展开同式）。"""
    return len(numpy.arange(span[0], span[1] + step / 2, step))


@dataclass(frozen=True)
@final
class DesignMapOptions:
    """可行域引导选项（不可变）：轴声明+固定参数映射+约束集（app 正门消费）。"""

    axes: tuple[Mapping[str, object], ...]
    fixed_params: Mapping[str, float]
    constraints: tuple[Constraint, ...] = ()

    def __post_init__(self) -> None:
        """axes/constraints 序列归一 tuple（裸 str 拒——EnumerationOptions 同款防线）。"""
        if isinstance(self.axes, str) or isinstance(self.constraints, str):
            raise InvalidDesignMapError(
                "DesignMapOptions.axes/constraints 必须为序列，不接受裸 str"
                f"（逐字符拆解为伪键）：得到 {self.axes!r} / {self.constraints!r}"
            )
        object.__setattr__(self, "axes", tuple(self.axes))
        object.__setattr__(self, "constraints", tuple(self.constraints))


def _resolve_range(
    axis: Mapping[str, object], spec: ParamSpec, where: str
) -> tuple[float, float]:
    """轴区间解析：覆盖 ?? manifest（min<max 且 ⊆manifest——fail-closed，PD1）。"""
    declared = axis.get("range", None)
    if declared is None:
        if spec.range is None:
            raise InvalidDesignMapError(
                f"{where} 无 range 声明可扫描（manifest range 缺席——FD 轴须为"
                "连续区间参数；覆盖亦无处 ⊆ 基准，fail-closed 拒）"
            )
        return spec.range
    if not isinstance(declared, Mapping):
        raise InvalidDesignMapError(
            f"{where} 的 range 覆盖须为对象（min/max）：{type(declared).__name__}"
        )
    unknown = sorted(set(declared) - {"min", "max"})
    if unknown or "min" not in declared or "max" not in declared:
        raise InvalidDesignMapError(
            f"{where} 的 range 覆盖须恰含 min/max：得到 {sorted(declared)}"
        )
    low = _number(declared["min"], f"{where} 的 range.min")
    high = _number(declared["max"], f"{where} 的 range.max")
    if low >= high:
        raise InvalidDesignMapError(
            f"{where} 的 range 覆盖须 min<max（得到 min={low!r}, max={high!r}）"
        )
    # R-2（G1-03，R 轮 2026-09-10）：manifest 无 range 基准时显式覆盖一律拒
    # ——无基准即无处 ⊆ 校验（fail-closed；原 if spec.range is not None
    # 守卫使无基准参数直通，与函数注释/PD1 矛盾——D 一审+二审双确认）
    if spec.range is None:
        raise InvalidDesignMapError(
            f"{where} 无 manifest range 基准（fail-closed 拒——FD 轴须为"
            "连续区间参数，覆盖无处 ⊆ 校验）"
        )
    base_low, base_high = spec.range
    if low < base_low or high > base_high:
        raise InvalidDesignMapError(
            f"{where} 的 range 覆盖越界：[{low:g}, {high:g}] 须 ⊆ manifest"
            f" [{base_low:g}, {base_high:g}]（fail-closed 拒——PD1）"
        )
    return low, high


def _resolve_step(axis: Mapping[str, object], span: tuple[float, float], where: str) -> float:
    """步长解析：覆盖（>0 有限——P0-1 core 防御）?? derive_step 派生缺省。"""
    raw_step = axis.get("step", None)
    if raw_step is None:
        return derive_step(span)
    step = _number(raw_step, f"{where} 的 step")
    if step <= 0:
        raise InvalidDesignMapError(
            f"{where} 的 step 须 > 0 且有限（得到 {step!r}"
            "——P0-1：除零/空序列防线，server 422+core 防御双面）"
        )
    return step


def resolve_axes(
    params: Sequence[ParamSpec], axes: Sequence[Mapping[str, object]]
) -> tuple[ResolvedAxis, ...]:
    """轴声明归一正门：声明序保持（产物 axes/mask 序=用户声明序）。"""
    if not 1 <= len(axes) <= _MAX_AXES:
        raise InvalidDesignMapError(
            f"axes 长度须为 1~{_MAX_AXES}（1D 行内区间条/2D 模态热力图——FD 契约）："
            f"得到 {len(axes)}"
        )
    spec_by_field = {spec.field_id: spec for spec in params}
    resolved: list[ResolvedAxis] = []
    seen: set[str] = set()
    for position, axis in enumerate(axes):
        raw_id = axis.get("field_id")
        if not isinstance(raw_id, str) or not raw_id:
            raise InvalidDesignMapError(
                f"轴声明[{position}] 缺非空字符串 field_id：得到 {raw_id!r}"
            )
        if raw_id in seen:
            raise InvalidDesignMapError(f"轴字段重复：{raw_id!r}（双轴须异字段）")
        seen.add(raw_id)
        spec = spec_by_field.get(raw_id)
        if spec is None:
            raise InvalidDesignMapError(
                f"轴字段 {raw_id!r} 不在该单元参数声明面（合法 {sorted(spec_by_field)}）"
            )
        where = f"轴字段 {raw_id!r}"
        low, high = _resolve_range(axis, spec, where)
        step = _resolve_step(axis, (low, high), where)
        resolved.append(
            ResolvedAxis(
                field_id=raw_id,
                dim=str(spec.dim),
                label_zh=spec.label_zh,
                minimum=low,
                maximum=high,
                step=step,
            )
        )
    return tuple(resolved)


def ensure_budget(
    resolved: Sequence[ResolvedAxis], overrides: Mapping[str, float]
) -> None:
    """护栏（PD4）：解析期拦截——预算总点数超 max_points 即拒（先于 build_grid）。"""
    max_points = assumption(_MAX_POINTS_KEY, overrides)
    if max_points < 1:
        raise InvalidDesignMapError(
            f"{_MAX_POINTS_KEY} 覆盖值须 >= 1：得到 {max_points!r}"
            "（0/负值=全扫描拒绝的静默陷阱——域守卫，挂账硬化本批兑现）"
        )
    points = [axis_point_budget((axis.minimum, axis.maximum), axis.step) for axis in resolved]
    total = 1
    for count in points:
        total *= count
    if total > max_points:
        raise DesignMapTooLarge(
            f"可行域扫描总点数 {total} 超护栏 max_points = {max_points:g}"
            f"（{_MAX_POINTS_KEY}，各轴点数 {points}——建议缩小某轴步长/范围"
            "或经假设覆盖调整上限）"
        )


def axis_mappings(resolved: Sequence[ResolvedAxis]) -> list[dict[str, object]]:
    """build_grid 喂入形（Mapping 起止步长既有路径——PD1 不建第二采样器）。"""
    return [
        {
            "field_id": axis.field_id,
            "range": {"min": axis.minimum, "max": axis.maximum},
            "step": axis.step,
        }
        for axis in resolved
    ]


def feasible_mask(
    frame: pandas.DataFrame, pass_matrix: pandas.DataFrame
) -> numpy.ndarray:
    """PD2 双源可行掩码：行非 NaN（计算域有效）∧ 约束通过。

    空约束集=pass_matrix 零列全真（apply_constraints GR-14 空集语义）
    ——NaN 域拒行（负数开方/除零域等）仍构成不可行面：「全绿」≠
    「无信息」（P0-2 终裁；与 degraded 标注互补——降级单元的绿区=
    计算有效域）。
    """
    constraint_ok = pass_matrix.all(axis=1).to_numpy(dtype=bool)
    domain_ok = ~frame["nan_flag"].to_numpy(dtype=bool)
    return numpy.asarray(constraint_ok & domain_ok, dtype=bool)


def _segments_of(values: Sequence[float], mask: numpy.ndarray) -> list[dict[str, float]]:
    """可行段合并（PD3 1D）：极大连续可行点列 → [{start,end}] 值域对。"""
    segments: list[dict[str, float]] = []
    start: int | None = None
    for index, feasible in enumerate(mask):
        if feasible and start is None:
            start = index
        elif not feasible and start is not None:
            segments.append(
                {"start": float(values[start]), "end": float(values[index - 1])}
            )
            start = None
    if start is not None:
        segments.append({"start": float(values[start]), "end": float(values[len(values) - 1])})
    return segments


def widest_segment(values: Sequence[float], mask: numpy.ndarray) -> dict[str, float] | None:
    """最宽可行段（PD9，公开=diagnose 幅度统计消费）：{start,end,centroid}
    ——无可行段 None（不编造）。"""
    best: dict[str, float] | None = None
    for segment in _segments_of(values, mask):
        if best is None or segment["end"] - segment["start"] > best["end"] - best["start"]:
            best = segment
    if best is None:
        return None
    return {**best, "centroid": (best["start"] + best["end"]) / 2}


def _diagnosis_axes(
    resolved: Sequence[ResolvedAxis], projections: Sequence[numpy.ndarray],
    axis_values: Sequence[Sequence[float]],
) -> list[dict[str, Any]]:
    """诊断块逐轴面（PD9）：magnitude=最宽段半宽（1D）/各轴最宽段投影（2D）。"""
    entries: list[dict[str, Any]] = []
    for axis, projection, values in zip(resolved, projections, axis_values, strict=True):
        widest = widest_segment(values, projection)
        entries.append(
            {
                "field_id": axis.field_id,
                "magnitude": None if widest is None else (widest["end"] - widest["start"]) / 2,
                "widest_segment": widest,
                "recommended_value": None if widest is None else widest["centroid"],
            }
        )
    return entries


def build_design_map(
    unit_id: str,
    grid: Grid,
    feasible: numpy.ndarray,
    resolved: Sequence[ResolvedAxis],
    coverage: str,
) -> DesignMap:
    """产物装配正门：网格真值列→轴值；双源掩码→段/掩码/统计/诊断（R2/R3/R4）。"""
    if len(feasible) != grid.total:
        raise InvalidDesignMapError(
            f"可行掩码长度 {len(feasible)} ≠ 网格总点数 {grid.total}"
            "（装配前置条件违反——双源掩码须逐网格行，PD2）"
        )
    declared_fields = [axis.field_id for axis in resolved]
    axis_values = tuple(
        tuple(float(value) for value in numpy.unique(grid.array[field_id]))
        for field_id in declared_fields
    )
    mask_flat = numpy.asarray(feasible, dtype=bool)
    core_grid = mask_flat.reshape(grid.shape)
    projections: tuple[numpy.ndarray, ...]
    if len(declared_fields) == 1:
        segments: tuple[dict[str, float], ...] | None = tuple(
            _segments_of(axis_values[0], mask_flat)
        )
        mask_rows: tuple[tuple[int, ...], ...] | None = None
        projections = (mask_flat,)
    else:
        # grid 字段序=字典序（build_grid R2）；声明序不一致时转置归位
        oriented = core_grid if grid.fields == tuple(declared_fields) else core_grid.T
        mask_rows = tuple(tuple(int(cell) for cell in row) for row in oriented)
        segments = None
        projections = (oriented.any(axis=1), oriented.any(axis=0))
    count = int(mask_flat.sum())
    total = int(grid.total)
    feasible_ratio = count / total
    stats: dict[str, float] = {
        "total": total,
        "feasible": count,
        "infeasible": total - count,
        "feasible_ratio": feasible_ratio,
    }
    axes_meta = tuple(
        {
            "field_id": axis.field_id,
            "dim": axis.dim,
            "label_zh": axis.label_zh,
            "range": {"min": axis.minimum, "max": axis.maximum},
            "step": axis.step,
            "points": len(values),
        }
        for axis, values in zip(resolved, axis_values, strict=True)
    )
    return DesignMap(
        unit_id=unit_id,
        axes=axes_meta,
        stats=stats,
        axis_values=axis_values,
        segments=segments,
        mask=mask_rows,
        constraint_coverage=coverage,
        diagnosis={
            "feasible_ratio": feasible_ratio,
            "axes": _diagnosis_axes(resolved, projections, axis_values),
        },
    )
