"""项目生命周期用例：复制/重命名/删除（projects 用例的治理姊妹面）。

输入:  项目 id / 新名称（routers 透传）+ ServiceContext
输出:  SaveOutcome（复制/重命名）/ DeleteOutcome（删除确认）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（briefs/task-p2-lifecycle-plan.md §一 L1——P2 启动批
# 2026-09-12；镜像测试 server/tests/services/test_project_lifecycle.py）
#
# 【公开接口】
#   copy_project(ctx, id) -> SaveOutcome（新 id；design 不动=同 digest）
#   rename_project(ctx, id, raw_name) -> SaveOutcome（view.name 轻通道）
#   delete_project(ctx, id) -> DeleteOutcome（三守卫过即 unlink）
#
# 【行为规格】
#   C1 复制：守卫②锁前置（新鲜 409/陈旧清除——core read_project_text
#      对锁存在恒拒，零锁读不可达故对齐 save 锁族语义）→读源→新 uuid
#      落盘经 core.save_project；副本名=源名非空时「{名} (副本)」重名
#      递增「(副本2/3…)」（占用集=list_projects 实读名称面；基名截断
#      至 PROJECT_NAME_MAX 内）；源无名→副本无名（空串语义沿 P0-1
#      ——FE 回退 id 显示）。
#   C2 重命名：名称经 normalize_name（>上限 422）+非空约束（重命名至
#      未命名=无意义拒 422）；守卫②锁前置同 C1（read 先行会以 core
#      InvalidProjectError 400 面拒锁——错族，故守卫前置于读）；写经
#      save_project 复用面（深度闸/design_changed=False/digest 复算
#      恒等——view 态不参与 content_hash，P0-1 通道语义）。在途任务
#      零触碰（design 未变不触发 stale 标记——save_project 既有语义）。
#   C3 删除三守卫：①不存在→ProjectNotFoundError 404；②锁新鲜→
#      ProjectLockedError 409（陈旧锁经 clear_stale_lock 清除放行）；
#      ③在途任务（queued/running）→ProjectBusyError 409 述因（终态
#      记录留内存不阻——任务史非项目资产）。过三守卫 unlink 项目文件；
#      锁件/任务记录不动（锁属编辑会话、记录属任务史——不静默级联
#      红线③）。
#   R1 文件操作全经 projects.project_path（safe_child 白名单——../与
#      绝对路径拒）；R2 禁 pickle；R3 副本名只动 view.name（metadata
#      哈希随 design 重算恒等——复制非内容变更）。
#
# 【测试要求】C1/C2/C3 各守卫与往返用例（brief §四）。
#
# 【参照】op-chain-fix-plan §五 P2/briefs/task-p2-lifecycle-plan.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from waterprint import app as core

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import (
    PROJECT_NAME_MAX,
    InvalidProjectPayloadError,
    ProjectNotFoundError,
    SaveOutcome,
    clear_stale_lock,
    design_digest,
    list_projects,
    normalize_name,
    project_path,
    read_project,
    save_project,
    with_hash,
)

# 副本名后缀族：「 (副本)」首发+「 (副本N)」递增（列表可读性制——批内裁量③）
_COPY_SUFFIX: str = " (副本)"


class ProjectBusyError(RuntimeError):
    """项目有在途任务（queued/running）——删除 409 面（C3 守卫③）。"""


@dataclass(frozen=True)
class DeleteOutcome:
    """删除确认（project_id 回显——幂等语义由 404 承担）。"""

    project_id: str


def _copy_name(ctx: ServiceContext, source_name: str) -> str:
    """副本名（C1）：源名非空→「{名} (副本)」重名递增；源无名→空串。

    递增制「(副本2/3…)」至首个空闲（占用集有限必终止）；**逐候选动态
    截断**基名保全长 ≤PROJECT_NAME_MAX（PL-N-01 R2 真修：预算按当前
    候选后缀实长计算——两位序数「(副本10)」后缀更长即再让一位基名，
    任意序数恒不越限）。
    """
    if not source_name:
        return ""
    taken = {item.name for item in list_projects(ctx)}
    index = 1
    while True:
        suffix = _COPY_SUFFIX if index == 1 else f"{_COPY_SUFFIX[:-1]}{index})"
        room = max(PROJECT_NAME_MAX - len(suffix), 1)
        candidate = f"{source_name[:room]}{suffix}"
        if candidate not in taken:
            return candidate
        index += 1


def _guarded_path(ctx: ServiceContext, project_id: str) -> Path:
    """守卫①②共用前置：存在性 404+锁（新鲜 409/陈旧清除）→ 返回项目路径。

    read_project 直读在锁存在时以 core InvalidProjectError（400 族）拒
    ——错族；故 C1/C2 一律先经本守卫（与 save/delete 锁族同语义）。
    """
    path = project_path(ctx, project_id)
    if not path.is_file():
        raise ProjectNotFoundError(f"项目 {project_id!r} 不存在（基点内无 {path.name}）")
    lock = path.with_suffix(".lock")
    if lock.exists():
        clear_stale_lock(lock, ctx.settings.lock_expiry_s)
    return path


def copy_project(ctx: ServiceContext, project_id: str) -> SaveOutcome:
    """复制（C1）：守卫前置→读源→新 id 落盘（design 不动；副本名占用面递增）。"""
    _guarded_path(ctx, project_id)
    source = read_project(ctx, project_id)
    name = _copy_name(ctx, source.view.name)
    copied = source.model_copy(
        update={"view": source.view.model_copy(update={"name": name})}
    )
    new_id = uuid.uuid4().hex
    digest = design_digest(copied.design)
    core.save_project(with_hash(copied, digest), project_path(ctx, new_id))
    return SaveOutcome(content_hash=digest, design_changed=True, project_id=new_id)


def rename_project(ctx: ServiceContext, project_id: str, raw_name: object) -> SaveOutcome:
    """重命名（C2）：守卫前置→view.name 改写经 save_project（深度闸同源）。

    名称校验（422）先于存在性（404）——与 FastAPI body 校验层序一致
    （pydantic 拒劣 body 在 handler 逻辑前，PL-N-06 R2 口径记档+测试锁）。
    """
    name = normalize_name(raw_name)
    if not name:
        raise InvalidProjectPayloadError(
            f"重命名名称不能为空（1~{PROJECT_NAME_MAX} 字符，去首尾空白后）"
        )
    _guarded_path(ctx, project_id)
    project = read_project(ctx, project_id)
    renamed = project.model_copy(
        update={"view": project.view.model_copy(update={"name": name})}
    )
    return save_project(ctx, project_id, renamed)


def delete_project(ctx: ServiceContext, project_id: str) -> DeleteOutcome:
    """删除（C3 三守卫）：404→锁 409→在途 409→unlink 项目文件。"""
    path = _guarded_path(ctx, project_id)
    busy = _busy_tasks(ctx, project_id)
    if busy:
        raise ProjectBusyError(
            f"项目有 {len(busy)} 个在途任务（{', '.join(busy)}）——"
            "请等待完成或取消后再删除（C3 守卫③）"
        )
    path.unlink()
    return DeleteOutcome(project_id=project_id)


def _busy_tasks(ctx: ServiceContext, project_id: str) -> tuple[str, ...]:
    """在途任务清点（C3 守卫③：queued/running；终态记录不阻）。"""
    busy: list[str] = []
    for task_id in ctx.manager.task_ids_for_project(project_id):
        if ctx.manager.status(task_id).state in {"queued", "running"}:
            busy.append(task_id)
    return tuple(busy)
