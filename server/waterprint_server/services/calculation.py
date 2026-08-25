"""计算服务用例：全流程计算/方案应用的任务化编排（幂等与快照绑定）。

输入:  项目 id + 工况选择 / 方案应用请求
输出:  任务句柄 / 应用后新 design_hash 与重算触发
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_calculation.py）
#
# 【公开接口】
#   submit_calculation(project_id, conditions) -> TaskHandle
#       幂等键 (design_hash, conditions)——重复提交返回既有句柄
#   apply_solution(project_id, solution_ref) -> ApplyOutcome
#       原子：写 design → 新 hash → 失效相关缓存 → 触发重算任务；
#       全部成功才提交（失败回滚，§17.1 方案应用行）
#   bind_snapshot(task) -> design_hash
#       任务启动时绑定输入快照
#
# 【行为规格】
#   R1 计算执行进 jobs（进程池）；本层负责任务注册、幂等查重、
#      快照绑定与 stale 判定（完成时对比当前 hash，§17.1）。stale
#      语义统一（SENS-B 2026-08-23 UF-37）：守门一律消费时实时比对
#      （口径见 services/exports.py R1），本层"完成时对比"降级为 UI
#      提示性标记（不作守门依据）；幂等查重与 stale 标记须在同一
#      事件循环临界区内完成（单进程 asyncio 契约）。
#   R2 方案应用的事务边界在本层：core 侧提供写入与 hash 计算，
#      服务层组织"校验→写入→失效→触发"序列与回滚（半写 = 数据
#      不一致，测试构造中途失败断言回滚）。
#   R3 优先级：交互计算 > 枚举 > 批量导出（§17.1 队列治理——
#      防 30 张图饿死交互）。
#   R4 结果落地：PlantResult 序列化进 exports/projects 数据区，
#      绑定三元组；大结果（枚举）走 arrow 文件 + 分页重载（§16 A6）。
#
# 【实现注记（SERVER 2026-08-26）】
#   - 缓存失效（R2 序列第三步）：M2 无 incremental 缓存层（UF-08
#     注记"缓存属 incremental 优化层"）——no-op 占位；apply_solution
#     事务=校验→原子写→（缓存失效 no-op）→触发重算；回滚=恢复原
#     项目对象重存（core 确定性序列化保证字节还原无损）。
#   - apply_solution 为 async（触发重算=await submit_calculation，
#     同一事件循环临界区）；回滚捕获面=提交路径现实异常族
#     （OSError/RuntimeError/ValueError/KeyError），测试以注毒触发器
#     断言字节回滚。
#
# 【测试要求】幂等、stale 判定、应用回滚、优先级排序。
#
# 【参照】重写计划 §17.1/§16 A6/§15 工程细节 3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from waterprint import app as core

from waterprint_server.jobs.manager import TaskHandle, TaskRequest, TaskStatus

# TaskStatus 再导出（routers 响应模型面——routers→jobs 非声明边，分层 §13.4）
__all__ = ["ApplyOutcome", "TaskStatus"]
from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import (
    ProjectNotFoundError,
    design_digest,
    read_project,
    save_project,
)

# 回滚捕获面：重算触发的现实异常族（grep 门禁禁过宽 except——领域面枚举）。
_TRIGGER_FAILURES = (OSError, RuntimeError, ValueError, KeyError)


class InvalidSolutionRefError(ValueError):
    """方案应用请求非法（unit_id 缺失/参数形态）——422 面。"""


@dataclass(frozen=True)
class ApplyOutcome:
    """方案应用结果（§17.1：原子写+新 hash+触发重算）。"""

    project_id: str
    new_hash: str
    design_changed: bool
    recalc_task_id: str


def bind_snapshot(ctx: ServiceContext, task_id: str, project_id: str) -> str:
    """快照绑定（公开接口第三件）：任务启动即绑定输入 design 哈希。"""
    digest = design_digest(read_project(ctx, project_id).design)
    ctx.manager.bind_snapshot(task_id, digest)
    return digest


async def submit_calculation(
    ctx: ServiceContext, project_id: str, conditions: Sequence[str]
) -> TaskHandle:
    """提交全流程计算（幂等键=(design_hash, conditions)，R1）。"""
    project = read_project(ctx, project_id)
    digest = design_digest(project.design)
    key = f"calc:{project_id}:{digest}:{'|'.join(sorted(conditions))}"
    handle = await ctx.manager.submit(
        TaskRequest(
            kind="calc",
            priority=ctx.settings.task_queue_priorities["calc"],
            payload={
                "kind": "calc",
                "project_id": project_id,
                "project_path": str(ctx.projects_dir / f"{project_id}.wp.json"),
                "conditions": list(conditions),
                "data_dir": str(ctx.settings.data_dir),
                "artifacts_dir": str(ctx.artifacts_dir),
            },
        ),
        idempotency_key=key,
    )
    ctx.manager.bind_snapshot(handle.task_id, digest)
    return handle


def task_status(ctx: ServiceContext, task_id: str) -> TaskStatus:
    """任务状态（stale=提示性标记：快照 vs 当前 design，UF-37 口径 R1）。"""
    status = ctx.manager.status(task_id)
    snapshot = ctx.manager.snapshot(task_id)
    if snapshot is None or not status.project_id:
        return status
    try:
        current = design_digest(read_project(ctx, status.project_id).design)
    except ProjectNotFoundError:
        return status
    return dataclasses.replace(status, stale=status.stale or snapshot != current)


def cancel_task(ctx: ServiceContext, task_id: str) -> bool:
    """取消透传（R3 calc：已完成结果不受取消影响——终态返回 False）。"""
    return ctx.manager.cancel(task_id)


async def apply_solution(
    ctx: ServiceContext, project_id: str, solution_ref: Mapping[str, Any]
) -> ApplyOutcome:
    """方案应用（R2 事务：校验→原子写→缓存失效[no-op]→触发重算+回滚）。"""
    unit_id = solution_ref.get("unit_id")
    params = solution_ref.get("params")
    if not isinstance(unit_id, str) or not unit_id or not isinstance(params, Mapping):
        raise InvalidSolutionRefError(
            f"solution_ref 须含 unit_id: str 与 params: 映射：得到 {solution_ref!r}"
        )
    for key, value in params.items():
        if (
            not isinstance(key, str)
            or not key
            or isinstance(value, bool)
            or not isinstance(value, (int, float, str))
        ):
            raise InvalidSolutionRefError(
                f"方案参数 {key!r}={value!r} 非法（字段 ID: str + 数值/字符串值）"
            )
    old = read_project(ctx, project_id)
    if unit_id not in old.design.nodes:
        raise InvalidSolutionRefError(
            f"方案目标单元 {unit_id!r} 不在项目 design.nodes（不可应用）"
        )
    merged: dict[str, Any] = dict(old.design.nodes[unit_id])
    merged.update(dict(params))
    updated = old.model_copy(
        update={
            "design": old.design.model_copy(
                update={"nodes": {**old.design.nodes, unit_id: merged}}
            )
        }
    )
    outcome = save_project(ctx, project_id, updated)
    try:
        handle = await submit_calculation(ctx, project_id, tuple(old.design.checked_units))
    except _TRIGGER_FAILURES as exc:
        core.save_project(old, ctx.projects_dir / f"{project_id}.wp.json")  # 回滚：字节还原
        raise RuntimeError(
            f"方案应用第二步（触发重算）失败已回滚——项目文件还原为应用前态：{exc}"
        ) from exc
    return ApplyOutcome(
        project_id=project_id,
        new_hash=outcome.content_hash,
        design_changed=outcome.design_changed,
        recalc_task_id=handle.task_id,
    )
