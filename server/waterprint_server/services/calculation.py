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
import math
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
from waterprint_server.services.units import list_units

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
    """任务状态（stale=提示性标记 R1；failed 附结构化 error_code R1-2/AU-2）。

    error_code=DOMAIN_ERROR_CODES 按 error_type 名回填（main 注入表——
    worker 侧领域异常如 LoopDivergence 类不可直连导入[D7 forbidden]，经
    名义表接线 D3"LoopDivergence→422 附诊断"冻结行；无映射=None）。
    """
    status = ctx.manager.status(task_id)
    error_code = ctx.domain_error_codes.get(status.error_type or "") or None
    patched = dataclasses.replace(status, error_code=error_code)
    snapshot = ctx.manager.snapshot(task_id)
    if snapshot is None or not patched.project_id:
        return patched
    try:
        current = design_digest(read_project(ctx, patched.project_id).design)
    except ProjectNotFoundError:
        return patched
    return dataclasses.replace(patched, stale=patched.stale or snapshot != current)


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
    old = read_project(ctx, project_id)
    if unit_id not in old.design.nodes:
        raise InvalidSolutionRefError(
            f"方案目标单元 {unit_id!r} 不在项目 design.nodes（不可应用）"
        )
    _validate_apply_params(old, unit_id, params)
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


def _validate_apply_params(
    project: Any, unit_id: str, params: Mapping[str, Any]
) -> None:
    """AUDIT2 C-4：apply 参数域服务端守护（提交面 422 先于异步失败）。

    探针实录（2026-08-30）：字符串值/未知键 200 入档→此后该项目所有
    calc failed（InvalidAssemblyError 未命中 grid 档位）且回滚不覆盖
    异步重算失败——与 ADR-005「值全 number」不符。守护三面：
    值=有限数值（bool/str/NaN 拒）；键=单元目录已知参数（META1 目录
    真源——kind 通道：节点覆写含 kind 用 kind，否则 unit_id）；grid
    声明时值须命中档位（与 core 装配期同口径前置）。range 面不在
    本守护（core 语义未锚——policy 后续批裁量）。
    """
    node = project.design.nodes[unit_id]
    catalog_key = node.get("kind") if isinstance(node.get("kind"), str) else unit_id
    entry = next(
        (u for u in list_units().units if u.unit_id == catalog_key), None
    )
    if entry is None:
        raise InvalidSolutionRefError(
            f"方案目标单元 {unit_id!r} 无单元目录声明（kind={catalog_key!r}"
            "——META1 目录外不可应用）"
        )
    specs = {p.field_id: p for p in entry.params}
    for key, value in params.items():
        if not isinstance(key, str) or not key:
            raise InvalidSolutionRefError(
                f"方案参数 {key!r} 非法（字段 ID: str）"
            )
        spec = specs.get(key)
        if spec is None:
            raise InvalidSolutionRefError(
                f"方案参数 {key!r} 不在单元 {unit_id!r} 目录参数面"
                f"（合法 {sorted(specs)}——ADR-005 grid 字段投影语义）"
            )
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise InvalidSolutionRefError(
                f"方案参数 {key!r}={value!r} 非法（数值: int/float 有限值"
                "——bool/字符串/NaN 拒，ADR-005「值全 number」服务端口径）"
            )
        if spec.grid is not None and float(value) not in {float(g) for g in spec.grid}:
            raise InvalidSolutionRefError(
                f"方案参数 {key!r} 值 {value!r} 未命中 grid 档位"
                f" {list(spec.grid)}（枚举维——§12.4，与 core 装配期同口径前置）"
            )
