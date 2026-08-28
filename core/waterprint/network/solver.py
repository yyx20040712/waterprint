"""管径枚举/并联/跌水井判定：管段序列的下游衔接设计。

输入:  管段模型序列（excel_io 读入：流量/长度/起终点地面标高…）
输出:  设计结果（各段管径/坡度/充满度/井底标高 + 跌水井与并联判定）

NET2 实装注记（2026-08-28，段二批）：
- 设计规则逐字照 docs/norms/network_manning.md"三段管线设计手算"
  节：①坡度=本段地面坡度（平行敷设）；②管底平接（下段起=上段末，
  衔接差>0 计跌差）；③管径枚举自小大到首个 NM-F5 三校核全过者入选。
- 约束全数据（R4）：DesignOptions 由调用方从 coefficients network.*
  21 键装配（cli/golden 同款），源码零字面量——充满度分档边界取自
  fill_ratio_steps 键序（键名后缀即 DN 边界，无硬编码分界值）。
- DesignOptions 扩 roughness 字段（规格头四字段外的最小必要扩展——
  糙率是水力实参非约束，manning 函数族签名口径；记档实现报告）。
- 并联判定（R3）：全部管径失败且充满度超限时，以最大管径双管各
  Q/2 水力等效拆分重试，通过则并联组标注（用户可否决）；仍失败→
  无解段显式失败+违反约束清单（R5 禁静默）。
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/network/test_solver.py）
#
# 【公开接口】
#   design_pipes(segments: Sequence[PipeSegment],
#                options: DesignOptions) -> NetworkDesign
#   class PipeSegment：segment_id、design_flow、length、
#       ground_start / ground_end（地面标高）、upstream_invert
#   class DesignOptions：available_diameters（可选管径序列——数据，
#      来自 coefficients/assumptions）、max_depth、min_velocity、
#      max_velocity（约束值全部带出处）
#   class NetworkDesign：各段 {diameter, slope, velocity, depth_ratio,
#       invert_start, invert_end}、drop_wells（跌水井位与跌差）、
#       parallel（并联管段组）、warnings
#
# 【行为规格】
#   R1 管径枚举：按可选管径序列自小到大试算，首个满足流速/充满度/
#      埋深约束的组合入选（枚举语义显式、确定性——同输入同设计）。
#   R2 衔接规则：下游管底 <= 上游管底（管底衔接）；覆土/埋深不足或
#      超深 → 跌水井判定（跌差进结果，警示标注）；坡度异常段
#      （过陡/倒坡）生成 Warning。
#   R3 并联判定：单管不满足（充满度超限）→ 并联双管方案（同沟敷设
#      水力等效拆分），并联组标注（用户可否决）。
#   R4 约束是数据：流速/埋深/覆土限值来自 options/coefficients，
#      零代码常量（§3 保证 7 精神延伸到管网域）。
#   R5 无解段（任何管径都不满足）→ 显式失败段 + 原因（最小冲突
#      语义：列出违反的约束），禁止静默选最接近的。
#
# 【测试要求】已知三段管线 golden 设计（docs/norms 手算对照）、
#   跌水井触发/不触发、并联触发、无解段原因完整、确定性。
#
# 【参照】重写计划 §13.3 管网行/§14.3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, final

from waterprint.contracts.quantity import DimKey, parse
from waterprint.network.manning import (
    full_flow_capacity,
    partial_flow,
    solve_depth,
)
from waterprint.registry.coefficients import (
    Coefficients,
    load_coefficients,
)
from waterprint.registry.formulas import apply

__all__ = [
    "DesignOptions",
    "DropWell",
    "FailedSegment",
    "NetworkDesign",
    "ParallelGroup",
    "PipeSegment",
    "SegmentDesign",
    "build_design_options",
    "design_pipes",
    "load_network_coefficients",
]


# NM-F5 裕度式求值上下文（manning 同款——formula_id 已入注册表可溯源）。
_CTX: Final[tuple[str, str]] = ("network", "solver")
# 约束名标识（R5 失败原因清单锚——与 NM-F5 裕度式 id 对应）
_FILL_CONSTRAINT: Final[str] = "max_fill_ratio"
_DEPTH_CONSTRAINT: Final[str] = "max_depth"
_VELOCITY_CONSTRAINT: Final[str] = "velocity_band"


@dataclass(frozen=True)
@final
class PipeSegment:
    """管段输入模型（模板 7 列投影；upstream_invert 留空=承接上段末管底）。"""

    segment_id: str
    design_flow: float  # q_design m³/s
    length: float  # m
    ground_start: float  # 起端地面标高 m
    ground_end: float  # 末端地面标高 m
    upstream_invert: float | None = None  # 起端管底标高 m（首段必填）


@dataclass(frozen=True)
@final
class DesignOptions:
    """设计约束与可选面（全数据装配——R4 源码零字面量）。"""

    available_diameters: tuple[float, ...]  # 可选管径 m（升序）
    min_velocity: float  # v_band_min m/s
    max_velocity: float  # v_band_max m/s
    max_depth: float  # 埋深上限 m
    fill_ratio_steps: tuple[tuple[float, float], ...]  # (DN 边界 m, 上限) 升序
    roughness: float  # 曼宁糙率 n（实参传入）


@dataclass(frozen=True)
@final
class SegmentDesign:
    """单段设计结果（手算表三段结果表列位）。"""

    segment_id: str
    diameter: float  # 管径 m
    slope: float  # 坡度 m/m（=地面坡度，平行敷设）
    velocity: float  # 非满流流速 m/s
    depth_ratio: float  # 充满度 h/D
    invert_start: float  # 起端管底标高 m
    invert_end: float  # 末端管底标高 m


@dataclass(frozen=True)
@final
class DropWell:
    """跌水井（衔接差>0 记跌差——手算表设计规则 2）。"""

    segment_id: str
    drop: float  # 跌差 m（本段起管底低于上段末管底的差值）


@dataclass(frozen=True)
@final
class ParallelGroup:
    """并联管段组（R3：单管充满度超限→同沟双管各半水力等效拆分）。"""

    segment_id: str
    diameter: float  # 单管管径 m
    per_pipe_flow: float  # 单管设计流量 m³/s（=q_design/2）
    depth_ratio: float  # 单管充满度
    velocity: float  # 单管流速 m/s


@dataclass(frozen=True)
@final
class FailedSegment:
    """无解段显式失败（R5：违反约束清单——禁静默选最接近）。"""

    segment_id: str
    reasons: tuple[str, ...]  # 逐管径违反约束清单（含约束名）


@dataclass(frozen=True)
@final
class NetworkDesign:
    """管网设计结果（规格头 NetworkDesign 结构 + failures 承载面）。"""

    results: tuple[SegmentDesign, ...]
    drop_wells: tuple[DropWell, ...]
    parallel: tuple[ParallelGroup, ...]
    warnings: tuple[str, ...]
    failures: tuple[FailedSegment, ...] = ()


def _fill_limit_for(diameter: float, steps: Sequence[tuple[float, float]]) -> float:
    """充满度上限分档：升序键序取首个 DN 边界≥管径的档（边界值全自键名）。"""
    for boundary, limit in steps:
        if diameter <= boundary:
            return limit
    return steps[-1][1]


def _segment_slope(segment: PipeSegment) -> float:
    """坡度=本段地面坡度（手算表设计规则 1：平行敷设，埋深沿程一致）。"""
    return (segment.ground_start - segment.ground_end) / segment.length


def _check_diameter(
    diameter: float,
    slope: float,
    options: DesignOptions,
    flow: float,
    invert_ground: tuple[float, float],
) -> tuple[bool, float, float, tuple[str, ...]]:
    """单管径试算三校核（NM-F5 裕度式经注册表求值，≥0 合格）。

    invert_ground=(管底标高, 地面标高)——埋深校核位对（PLR0913 收口打包）。
    返回 (是否入选, 充满度, 流速, 违反约束清单)；超满流（NM-F4 无根）
    计充满度超限类失败——埋深校核不依赖求根，仍执行（R5 清单完整）。
    """
    invert, ground = invert_ground
    violations: list[str] = []
    margin_depth = apply(
        "NM-F5-DEPTH",
        {"depth_max": options.max_depth, "ground": ground, "invert": invert},
        _CTX,
    )
    if margin_depth < 0.0:
        violations.append(
            f"DN(d={diameter:.3f}m): {_DEPTH_CONSTRAINT}——埋深 "
            f"{ground - invert:.2f} m 超上限 {options.max_depth:.1f} m"
        )
    capacity = full_flow_capacity(diameter, slope, options.roughness)
    if flow > capacity:
        violations.append(
            f"DN(d={diameter:.3f}m): {_FILL_CONSTRAINT}——Q={flow:.4f} 超满流"
            f"输水能力 {capacity:.4f} m3/s（承压，NM-F4 无根）"
        )
        return False, 0.0, 0.0, tuple(violations)
    depth = solve_depth(diameter, slope, options.roughness, flow)
    velocity = partial_flow(diameter, slope, options.roughness, depth).velocity
    margin_fill = apply(
        "NM-F5-FILL",
        {"fill_limit": _fill_limit_for(diameter, options.fill_ratio_steps), "h_d": depth},
        _CTX,
    )
    margin_velocity = apply(
        "NM-F5-V",
        {
            "v_part": velocity,
            "v_band_min": options.min_velocity,
            "v_band_max": options.max_velocity,
        },
        _CTX,
    )
    if margin_fill < 0.0:
        violations.append(
            f"DN(d={diameter:.3f}m): {_FILL_CONSTRAINT}——h/D={depth:.4f} 超该档最大设计充满度"
        )
    if margin_velocity < 0.0:
        violations.append(
            f"DN(d={diameter:.3f}m): {_VELOCITY_CONSTRAINT}——v={velocity:.4f} m/s "
            f"出设计流速带 [{options.min_velocity:.1f}, "
            f"{options.max_velocity:.1f}] m/s"
        )
    return not violations, depth, velocity, tuple(violations)


def _design_one_segment(
    segment: PipeSegment,
    options: DesignOptions,
    slope: float,
    invert_start: float,
    invert_end: float,
) -> tuple[SegmentDesign | None, ParallelGroup | None, FailedSegment | None, str]:
    """单段枚举设计：首个全过管径入选；否则并联尝试；否则显式失败。

    返回 (单管结果|None, 并联组|None, 失败段|None, 警示消息)——恰一态。
    """
    reasons: list[str] = []
    fill_blocked = False
    for diameter in options.available_diameters:
        passed, depth, velocity, why = _check_diameter(
            diameter,
            slope,
            options,
            segment.design_flow,
            (invert_start, segment.ground_start),
        )
        if passed:
            return (
                SegmentDesign(
                    segment_id=segment.segment_id,
                    diameter=diameter,
                    slope=slope,
                    velocity=velocity,
                    depth_ratio=depth,
                    invert_start=invert_start,
                    invert_end=invert_end,
                ),
                None,
                None,
                "",
            )
        reasons.extend(why)
        if any(_FILL_CONSTRAINT in line for line in why):
            fill_blocked = True
    if fill_blocked:
        largest = options.available_diameters[-1]
        half_flow = segment.design_flow / 2.0
        passed, depth, velocity, why = _check_diameter(
            largest,
            slope,
            options,
            half_flow,
            (invert_start, segment.ground_start),
        )
        if passed:
            warning = (
                f"{segment.segment_id}: 单管充满度超限——并联双管方案 "
                f"DN(d={largest:.3f}m) 各输半量（同沟敷设水力等效拆分，"
                "用户可否决，R3）"
            )
            return (
                None,
                ParallelGroup(
                    segment_id=segment.segment_id,
                    diameter=largest,
                    per_pipe_flow=half_flow,
                    depth_ratio=depth,
                    velocity=velocity,
                ),
                None,
                warning,
            )
        reasons.extend(why)
    return None, None, FailedSegment(segment.segment_id, tuple(reasons)), ""


def design_pipes(segments: Sequence[PipeSegment], options: DesignOptions) -> NetworkDesign:
    """管段序列设计正门：逐段管径枚举→三校核→衔接/跌水/并联/失败清单。"""
    results: list[SegmentDesign] = []
    drop_wells: list[DropWell] = []
    parallel: list[ParallelGroup] = []
    warnings: list[str] = []
    failures: list[FailedSegment] = []
    previous_invert: float | None = None
    for segment in segments:
        invert_start = (
            segment.upstream_invert if segment.upstream_invert is not None else previous_invert
        )
        if invert_start is None:
            failures.append(
                FailedSegment(
                    segment.segment_id,
                    ("upstream_invert——首段起端管底标高缺失（模板首段必填）",),
                )
            )
            continue
        slope = _segment_slope(segment)
        if slope <= 0.0:
            failures.append(
                FailedSegment(
                    segment.segment_id,
                    ("slope——地面倒坡/平坡（ground_start≤ground_end，曼宁域外）",),
                )
            )
            previous_invert = invert_start
            continue
        invert_end = invert_start - slope * segment.length
        if previous_invert is not None:
            drop = previous_invert - invert_start
            if drop > 0.0:
                drop_wells.append(DropWell(segment.segment_id, drop))
                warnings.append(
                    f"{segment.segment_id}: 管底衔接差 {drop:.3f} m > 0——跌水井"
                    "判定（跌差过大时校核消能，手册口径，R2）"
                )
            elif invert_start > previous_invert:
                warnings.append(f"{segment.segment_id}: 管底抬升（起管底高于上段末——顶托风险，R2）")
        result, group, failure, warning = _design_one_segment(
            segment, options, slope, invert_start, invert_end
        )
        if result is not None:
            results.append(result)
        if group is not None:
            parallel.append(group)
        if failure is not None:
            failures.append(failure)
        if warning:
            warnings.append(warning)
        previous_invert = invert_end
    return NetworkDesign(
        results=tuple(results),
        drop_wells=tuple(drop_wells),
        parallel=tuple(parallel),
        warnings=tuple(warnings),
        failures=tuple(failures),
    )


# ── 系数装配面（NET2 段二批：cli network 子命令与 golden 测试同口径；
#    结构图谱 network→registry 边承载——真库路径按 conftest 同款
#    core/waterprint/network → repo/data/coefficients 回溯）──


def load_network_coefficients() -> Coefficients:
    """装载真库系数包（repo data/coefficients——21 个 network.* 键宿主）。"""
    repo_root = Path(__file__).resolve().parents[2].parent
    return load_coefficients(repo_root / "data" / "coefficients")


def _millimeters(key_suffix: str) -> float:
    """键名后缀 DN 数值（mm）→ 米（单位换算契约——contracts.parse）。"""
    return parse(float(key_suffix), "mm", DimKey.LENGTH)


def build_design_options(coefficients: Coefficients, pipe_type: str) -> DesignOptions:
    """从 coefficients network.* 21 键装配 DesignOptions（R4 源码零字面量）。

    管径序列=network.dn.* 键值（mm 经单位换算契约转 m）；充满度分档=
    network.max_fill_ratio.dn* 键序（键名后缀即 DN 边界，无硬编码分界）；
    管材=network.roughness.<pipe_type>（模板 pipe_type 列/CLI --roughness
    同键名口径）。
    """
    diameters = tuple(
        sorted(
            parse(coefficients.get(key).value, "mm", DimKey.LENGTH)
            for key in coefficients.keys("network.dn.")
        )
    )
    steps = tuple(
        sorted(
            (_millimeters(key.rsplit("dn", 1)[1]), coefficients.get(key).value)
            for key in coefficients.keys("network.max_fill_ratio.")
        )
    )
    return DesignOptions(
        available_diameters=diameters,
        min_velocity=coefficients.get("network.velocity_band.min").value,
        max_velocity=coefficients.get("network.velocity_band.max").value,
        max_depth=coefficients.get("network.max_depth").value,
        fill_ratio_steps=steps,
        roughness=coefficients.get(f"network.roughness.{pipe_type}").value,
    )
