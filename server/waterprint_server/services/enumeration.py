"""枚举服务用例：单单元枚举任务的编排与结果分页（ADR-005 语义守护）。

输入:  项目 id + unit_id + 网格/约束覆盖 + 排序分页参数
输出:  任务句柄 / 分页方案集 / 诊断报告
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_enumeration.py）
#
# 【公开接口】
#   submit_enumeration(project_id, unit_id, options) -> TaskHandle
#   fetch_solutions(task_id, page, size, sort) -> SolutionPage
#   fetch_diagnosis(task_id) -> DiagnosisReport（无解时）
#
# 【行为规格】
#   R1 语义守护：枚举对象永远是单单元（ADR-005）——请求携带多个
#      unit_id = 422 拒绝（服务层显式拒绝，防语义滑坡成全厂枚举）。
#   R2 分页默认 200/页（§12.2）；排序参数白名单（字段 ID 或
#      margin_min/cost），tie_break 固定（solution.ranking R1）。
#   R3 结果存储：万级行落 arrow 文件（任务产物目录，按 task_id +
#      三元组命名）；页请求按需重载（§16 A6——不整包回传）；core
#      侧枚举管线调用一律经 waterprint.app 对应用例
#      （run_enumeration，SENS-B 2026-08-23 UF-33，不直连 solution
#      子系统）。
#   R4 无解交付：pass_matrix 全 False → diagnosis 端点可用
#      （最小冲突集 + 建议）；任务状态 done + feasible_count=0
#      是合法终态（不是 failed）。
#
# 【实现注记（SERVER 2026-08-26）】
#   - 诊断交付面：端点集 v1 冻结 18 件不含独立 /diagnosis 端点
#     （routers/calc 规格 A1 锁定）——诊断负载随任务状态结果载荷
#     交付（fetch_diagnosis 服务面不变，供路由组装）。
#   - tie_break 固定：分页排序=stable sort（kind="stable"）保持
#     枚举序为次序键（solution.ranking R1 同源语义）。
#   - NaN→None：行记录 NaN 统一转 null（JSON 面 NaN 非法——§18）。
#
# 【测试要求】多单元拒绝、分页/排序白名单、arrow 重载、
#   无解合法终态。
#
# 【参照】重写计划 §12.2/§12.4/§16 A6；ADR-005
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（app_enumeration 同款）

from waterprint_server.jobs.manager import TaskHandle, TaskRequest, TaskStatus
from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import design_digest, read_project


class MultiUnitEnumerationError(ValueError):
    """多 unit_id 枚举请求（ADR-005 语义守护）——422 面。"""


class InvalidPageParameterError(ValueError):
    """分页/排序参数非法（页码/白名单外排序键）——422 面。"""


class TaskNotCompleteError(RuntimeError):
    """任务未完成（或非枚举任务）即取结果——409 面。"""


class DiagnosisNotAvailableError(RuntimeError):
    """无可解诊断（任务可行或未完成）——404 面。"""


@dataclass(frozen=True)
class SolutionPage:
    """分页方案集（§12.2 默认 200/页；rows=行记录列表）。"""

    task_id: str
    page: int
    size: int
    total: int
    sort: str
    columns: tuple[str, ...]
    rows: tuple[Mapping[str, Any], ...]


async def submit_enumeration(
    ctx: ServiceContext,
    project_id: str,
    unit_ids: Sequence[str],
    options: Mapping[str, Any] | None = None,
) -> TaskHandle:
    """提交单单元枚举（R1：多 unit_id 显式拒；幂等键含选项规范形）。"""
    if len(unit_ids) != 1:
        raise MultiUnitEnumerationError(
            f"枚举对象永远是单单元（ADR-005）：携带 {len(unit_ids)} 个 "
            f"unit_id={list(unit_ids)!r} 拒绝——防语义滑坡成全厂枚举"
        )
    unit_id = unit_ids[0]
    project = read_project(ctx, project_id)
    digest = design_digest(project.design)
    chosen = dict(options or {})
    key = (
        f"enumerate:{project_id}:{digest}:{unit_id}:"
        f"{sorted((str(k), str(v)) for k, v in chosen.items())}"
    )
    return await ctx.manager.submit(
        TaskRequest(
            kind="enumerate",
            priority=ctx.settings.task_queue_priorities["enumerate"],
            payload={
                "kind": "enumerate",
                "project_id": project_id,
                "project_path": str(ctx.projects_dir / f"{project_id}.wp.json"),
                "unit_id": unit_id,
                "conditions": list(project.design.checked_units),
                "options": chosen,
                "data_dir": str(ctx.settings.data_dir),
                "artifacts_dir": str(ctx.artifacts_dir),
            },
        ),
        idempotency_key=key,
    )


def _require_done_enumeration(ctx: ServiceContext, task_id: str) -> TaskStatus:
    """结果可取前提：done 且结果含行文件句柄（§16 A6 路径句柄）。"""
    status = ctx.manager.status(task_id)
    if status.kind != "enumerate" or status.state != "done" or status.result is None:
        raise TaskNotCompleteError(
            f"任务 {task_id!r} 状态 {status.state}（kind={status.kind}）——"
            "枚举结果只在 done 终态可取（§16 A6 分页重载前提）"
        )
    return status


def fetch_solutions(
    ctx: ServiceContext,
    task_id: str,
    page: int = 1,
    size: int | None = None,
    sort: str = "margin_min",
) -> SolutionPage:
    """分页方案集（R2：默认 200/页经 Settings；排序白名单；按需重载 arrow）。"""
    if page < 1 or (size is not None and size < 1):
        raise InvalidPageParameterError(
            f"分页参数非法：page={page!r}, size={size!r}（均须 >= 1——1 基页码）"
        )
    status = _require_done_enumeration(ctx, task_id)
    assert status.result is not None  # _require_done_enumeration 收窄（mypy）
    columns = tuple(status.result.get("columns", ()))
    # AUDIT2 C-3：白名单=列集 ∪ {margin_min}。原 ∪{cost} 使 sort=cost 过白名单
    # 后在 sort_values 处 KeyError→500（探针实录 2026-08-30）——cost 是导出侧
    # 概念，方案行集无此列；超集成员收口为 margin_min（枚举默认序键）。
    allowed = {*columns, "margin_min"}
    if sort not in allowed:
        raise InvalidPageParameterError(
            f"排序键 {sort!r} 不在白名单（合法面 {sorted(allowed)}——"
            "字段 ID 或 margin_min，R2）"
        )
    page_size = size if size is not None else ctx.settings.page_size_default
    frame = pd.read_feather(str(status.result["rows_file"]))
    ordered = frame.sort_values(sort, ascending=False, kind="stable")  # tie_break=枚举序
    start = (page - 1) * page_size
    window = ordered.iloc[start : start + page_size]
    records = [
        {key: (None if pd.isna(value) else value) for key, value in record.items()}
        for record in window.to_dict(orient="records")
    ]
    return SolutionPage(
        task_id=task_id,
        page=page,
        size=page_size,
        total=len(frame),
        sort=sort,
        columns=columns,
        rows=tuple(records),
    )


def fetch_diagnosis(ctx: ServiceContext, task_id: str) -> Mapping[str, Any]:
    """无解诊断（R4：最小冲突集+建议；可行任务无诊断=404 面）。"""
    status = _require_done_enumeration(ctx, task_id)
    assert status.result is not None  # _require_done_enumeration 收窄（mypy）
    diagnosis = status.result.get("diagnosis")
    if not isinstance(diagnosis, Mapping):
        raise DiagnosisNotAvailableError(
            f"任务 {task_id!r} 无诊断（可行解任务或诊断未产出——"
            "诊断只随无解枚举（feasible_count=0 合法终态 R4）交付）"
        )
    return diagnosis
