"""联合枚举服务用例：静态预检护栏 + 异步任务提交（ADR-025 新正门）。

输入:  项目 id + unit_ids + 网格/约束覆盖选项
输出:  TaskHandle（kind=joint_enumerate——同 worker 制式）/422 预检拒绝
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 定稿件 W5/W7/N1/N3——2026-09-20；镜像测试
#   server/tests/services/test_joint_enumeration.py）
#
# 【公开接口】
#   submit_joint_enumeration(ctx, project_id, unit_ids, options)
#       -> TaskHandle（异步 job 同 enumerate worker 制式）
#   class JointEnumerationTooLargeError(ValueError)：静态预检超限
#       （rows>max_total_rows 或 N>max_units）——422 面（W7 事前拒绝
#       优于事后截断；公式 g·(k^N−1)/(k−1)·W_s，k=1→g·N[N1]；W_s=
#       validation_conditions=1[all_outer] 时全工况数，否则 1[W5]）
#   class InvalidJointUnitsError(ValueError)：unit_ids 空/重复/未知
#       ——422 面（请求形态校验；重复与未知在 core 侧另有二道闸）
#
# 【行为规格】
#   R1 静态预检（W7 主闸）：请求时验算 rows=g·(k^N−1)/(k−1)·W_s
#      ≤max_total_rows——g=逐单元网格行数（请求覆盖 values/range 计数，
#      缺省=manifest grid 档）、k=beam_width、N=len(unit_ids)；护栏值
#      经 core.DEFAULT_ASSUMPTIONS 合成视图 ∪ design.assumption_overrides
#      （项目假设管道——core 消费同源）。超限 422（不进任务队列）。
#   R2 旧拒绝点不松：单单元枚举语义面 services/enumeration.py 一字
#      不动（MultiUnitEnumerationError 仍在）；本面=多单元正门。
#   R3 任务载荷：kind=joint_enumerate、unit_ids、conditions（=
#      design.checked_units——build_condition_set 正门）、options
#      （grids/constraints 二键）、data_dir/artifacts_dir（worker 面）。
#   R4 N 硬域（N3）：max_units 名义护栏（默认 6，覆盖可调）；硬上限 8
#      由 rows 公式天然守域（不另立常数）。
#
# 【测试要求】预检 422 双面（rows/N）、请求覆盖网格计数、无效 unit_ids、
#   任务句柄 kind。
#
# 【参照】.workflow/b4-3/design-final.md §一 W5/W7/N1/N3；ADR-025 决策 1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from waterprint import app as core

from waterprint_server.jobs.manager import TaskHandle, TaskRequest
from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import design_digest, read_project

_KEY_MAX_UNITS = "solution.joint.max_units"
_KEY_BEAM = "solution.joint.beam_width"
_KEY_MAX_ROWS = "solution.joint.max_total_rows"
_KEY_VALIDATION = "solution.joint.validation_conditions"
_ALL_OUTER = 1.0


class JointEnumerationTooLargeError(ValueError):
    """静态预检超限（rows>max_total_rows / N>max_units）——422 面。"""


class InvalidJointUnitsError(ValueError):
    """unit_ids 空/重复/未知——422 面（请求形态校验）。"""


def _assumption_view(project: Any) -> dict[str, float]:
    """合成视图：DEFAULT_ASSUMPTIONS ∪ design 覆盖（core 消费同源）。"""
    view = {entry.key: entry.default for entry in core.DEFAULT_ASSUMPTIONS}
    view.update(project.design.assumption_overrides)
    return view


def _validate_units(
    unit_ids: Sequence[str], catalog: Mapping[str, tuple[Any, Any]]
) -> None:
    """R2 请求形态校验：非空/无重复/全在单元目录。"""
    if not unit_ids:
        raise InvalidJointUnitsError(
            "联合枚举 unit_ids 须至少一个目标单元（空集=请求形态缺陷）"
        )
    seen: set[str] = set()
    for unit_id in unit_ids:
        if unit_id in seen:
            raise InvalidJointUnitsError(f"unit_ids 重复：{unit_id!r}")
        seen.add(unit_id)
        if unit_id not in catalog:
            raise InvalidJointUnitsError(
                f"目标单元 {unit_id!r} 不在单元目录（合法面 {sorted(catalog)}）"
            )


def _grid_size(specs: Sequence[Mapping[str, Any]]) -> int:
    """单单元网格行数（core.build_grid 计数——spec→Grid 单源复用）。"""
    return core.build_grid(list(specs), overrides={}, guard_base=False).total


def _grid_specs_of(
    unit_id: str, catalog: Mapping[str, tuple[Any, Any]], options: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    """网格声明：请求覆盖优先，缺省=manifest grid 档（R3 零代码注入同源）。"""
    override = (options.get("grids") or {}).get(unit_id)
    specs = list(override) if override else [
        {"field_id": spec.field_id, "values": list(spec.grid)}
        for spec in catalog[unit_id][0].params if spec.grid is not None
    ]
    if not specs:
        raise InvalidJointUnitsError(
            f"单元 {unit_id!r} 无网格声明（manifest grid 档缺席且无请求覆盖）"
        )
    return specs


def _precheck(
    unit_ids: Sequence[str], grid_sizes: Sequence[int], view: Mapping[str, float],
    conditions_count: int,
) -> None:
    """R1 静态预检：N≤max_units 且 rows=g·(k^N−1)/(k−1)·W_s≤max_rows。"""
    if len(unit_ids) > view[_KEY_MAX_UNITS]:
        raise JointEnumerationTooLargeError(
            f"目标单元数 {len(unit_ids)} 超 max_units={view[_KEY_MAX_UNITS]:g}"
            f"（{_KEY_MAX_UNITS}——N3 硬域由 rows 公式天然守域）"
        )
    multiplier = conditions_count if view[_KEY_VALIDATION] >= _ALL_OUTER else 1
    rows = core.estimate_rows(grid_sizes, view[_KEY_BEAM], multiplier)
    if rows > view[_KEY_MAX_ROWS]:
        raise JointEnumerationTooLargeError(
            f"分级枚举行估计 {rows:g} 超预算 max_total_rows={view[_KEY_MAX_ROWS]:g}"
            f"（g={max(grid_sizes)}, k={view[_KEY_BEAM]:g}, N={len(unit_ids)}, "
            f"W_s={multiplier}——W7 静态预检；建议缩小网格/降低 beam_width/减少单元）"
        )


async def submit_joint_enumeration(
    ctx: ServiceContext,
    project_id: str,
    unit_ids: Sequence[str],
    options: Mapping[str, Any] | None = None,
) -> TaskHandle:
    """联合枚举提交正门：静态预检（422 主闸）→异步 job（同 worker 制式）。"""
    project = read_project(ctx, project_id)
    chosen = dict(options or {})
    catalog = core.discover_units()
    _validate_units(unit_ids, catalog)
    grid_sizes = [
        _grid_size(_grid_specs_of(unit_id, catalog, chosen)) for unit_id in unit_ids
    ]
    checked = list(project.design.checked_units)
    _precheck(
        unit_ids, grid_sizes, _assumption_view(project), len(checked) + 2
    )
    digest = design_digest(project.design)
    key = (
        f"joint-enumerate:{project_id}:{digest}:{list(unit_ids)}:"
        f"{sorted((str(k), str(v)) for k, v in chosen.items())}"
    )
    return await ctx.manager.submit(
        TaskRequest(
            kind="joint_enumerate",
            priority=ctx.settings.task_queue_priorities["joint_enumerate"],
            payload={
                "kind": "joint_enumerate",
                "project_id": project_id,
                "project_path": str(ctx.projects_dir / f"{project_id}.wp.json"),
                "unit_ids": list(unit_ids),
                "conditions": checked,
                "options": chosen,
                "data_dir": str(ctx.settings.data_dir),
                "artifacts_dir": str(ctx.artifacts_dir),
            },
        ),
        idempotency_key=key,
    )
