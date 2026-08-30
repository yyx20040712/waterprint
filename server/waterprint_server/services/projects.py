"""项目服务用例：创建/读取/保存/列表/校验/迁移导入（core project 层的编排壳）。

输入:  项目 id / ProjectFile 数据（routers 透传）
输出:  项目元数据 / ProjectFile / 校验报告（core 产出包装）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_projects.py）
#
# 【公开接口】
#   create_project(payload) / list_projects() / read_project(id) /
#   save_project(id, project) -> SaveOutcome（新 hash + design_changed）
#   validate_project(id) -> ValidationReport
#   import_legacy(payload) -> ImportReport（M4，best-effort 映射清单）
#
# 【行为规格】
#   R1 文件操作只经 core.project.io（确定性序列化/原子保存/锁探测
#      在 core 实现）；core 侧调用一律经 waterprint.app 对应用例
#      （load_project/save_project 薄封装，SENS-B 2026-08-23 UF-33）；
#      本层加目录白名单与 id 校验（§18）。
#   R2 save 返回 design_changed 布尔（hash 对比）——routers 据此响应
#      dirty 语义（§17.1 项目保存行：保存只写 view 态不触发计算）。
#   R3 导入旧格式：core.project.migration + best-effort 字段映射，
#      未映射字段清单必须完整返回（禁止静默丢弃）。——M4 归属：
#      import_legacy 显式未就绪语义（ImportNotReadyError→501，简报
#      SERVER D3 裁决：不假装功能）。
#   R4 禁 pickle（§18）；项目列表元数据来自文件读取（无独立索引库）。
#
# 【实现注记（SERVER 2026-08-26）】
#   - design_digest：project.content_hash.design_hash 的 B4 双胞胎
#     （sha256(io.dumps_design 等价确定性序列化)——server 禁直连
#     waterprint.project，D7 forbidden；镜像测试与 core 真源逐字节
#     对照断言锁死不漂移）。app 面 design_hash 用例收口=追认点
#     （undefined-features-register 登记）。
#   - 上传面深度闸：_check_depth 迭代计数（Settings.max_json_depth，
#     与 core io._MAX_DEPTH 同源口径）——pydantic 前置防栈炸弹。
#   - 锁冲突（R4 router 规格 409）：save 前置探测 {id}.wp.lock
#      （ENG4 D4/I-7 勘误 2026-08-30：path.with_suffix(".lock") 于
#      {id}.wp.json 上=替换最后后缀，非 .wp.json.lock 叠加；io 锁语义
#      同款），冲突=ProjectLockedError 带锁路径（持有者信息）。
#
# 【测试要求】往返保存 design_changed 语义、导入未映射清单、
#   id 白名单、锁冲突透传。
#
# 【参照】重写计划 §13.4/§17.1/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Any, Final

from waterprint import app as core
from waterprint.contracts.project_schema import (
    DesignState,
    Metadata,
    ProjectFile,
    parse_project,
)

from waterprint_server.services import ServiceContext
from waterprint_server.settings import ENGINE_VERSION, safe_child

_PROJECT_SUFFIX: Final[str] = ".wp.json"
_ROUND_DIGITS: Final[int] = 10  # 与 core io._ROUND_DIGITS 同源（B4 双胞胎）
_DESIGN_FORMAT_VERSION: Final[str] = "1.0"  # 与 core io._FORMAT_VERSION 同源
_JSON_KWARGS: Final[dict[str, Any]] = {
    "sort_keys": True,
    "ensure_ascii": False,
    "separators": (",", ":"),
}


class ProjectNotFoundError(KeyError):
    """项目不存在——领域异常（404 面）。"""


class ProjectLockedError(RuntimeError):
    """项目文件被锁定（§17.3 v1 单用户最低成本方案）——409 面。"""

    def __init__(self, lock_path: Path) -> None:
        super().__init__(
            f"项目文件被锁定：{lock_path} 存在——另一会话可能正在编辑"
            "（§17.3 并发打开防护；持有者信息=锁文件路径）"
        )
        self.lock_path = lock_path


class ImportNotReadyError(RuntimeError):
    """旧系统导入未就绪（M4 归属）——诚实 501，禁假装功能。"""


class InvalidProjectPayloadError(ValueError):
    """上传项目 payload 非法（深度炸弹/形态）——422 面。"""


class PayloadTooLargeError(ValueError):
    """上传面字节体积闸（Content-Length 超 max_upload_mb）——413 面。"""


@dataclass(frozen=True)
class SaveOutcome:
    """保存结果（R2：新 hash + design_changed；view 变更不触发计算语义）。"""

    content_hash: str
    design_changed: bool
    project_id: str


@dataclass(frozen=True)
class ProjectSummary:
    """列表元数据（R4：来自文件读取，无独立索引库）。"""

    project_id: str
    format_version: str
    content_hash: str
    engine_version: str
    data_version: str
    view_timestamp: str


@dataclass(frozen=True)
class ValidationReport:
    """零计算快速校验报告（R3：装载面错误清单）。"""

    valid: bool
    errors: tuple[str, ...]


# ── design_digest：content_hash.design_hash 的 B4 双胞胎 ──────────


def _normalize(value: Any, path: str, depth: int) -> Any:
    """确定性归一（io._normalize 同款纪律：str 键/round(x,10)/有限性）。"""
    if depth >= 10**2:  # 与 core io._MAX_DEPTH 同源（B4 双胞胎注记）
        raise InvalidProjectPayloadError(f"项目数据嵌套过深：{path}（>100 层）")
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise InvalidProjectPayloadError(f"项目数据含非有限值：{path} 处（GR-02）")
        return round(value, _ROUND_DIGITS)
    if isinstance(value, Mapping):
        return {
            str(key): _normalize(item, f"{path}.{key}", depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, Sequence):
        return [_normalize(item, f"{path}[{index}]", depth + 1) for index, item in enumerate(value)]
    raise InvalidProjectPayloadError(f"项目数据含不可序列化类型 {type(value).__name__}：{path}")


def design_digest(design: DesignState) -> str:
    """design 态内容哈希（core project.content_hash.design_hash 双胞胎）。

    = sha256({"format_version": 头, "design": 归一树} 的确定性 JSON+尾换行)；
    镜像测试与 core 真源逐字节对照（防双胞胎漂移）。
    """
    tree = {
        "format_version": _DESIGN_FORMAT_VERSION,
        "design": _normalize(design.model_dump(mode="json"), "design", 0),
    }
    return sha256((json.dumps(tree, **_JSON_KWARGS) + "\n").encode("utf-8")).hexdigest()


def result_is_stale(latest: Mapping[str, Any], project: ProjectFile) -> bool:
    """结果集相对当前项目 design 是否过期（AUDIT2 C-1——三读端点共用）。

    口径：latest.design_hash（任务完成时锚定的 design 摘要）≠ 当前
    design_digest → True（改 design/假设覆盖不重算即过期——契约
    result_schema R4「结果过期消费方必须显式提示，禁止静默使用」的
    服务面实现）；latest 缺 design_hash 键=无法证新鲜 → True
    （fail-visible，兼防 D5 族 KeyError 裸 500）。exports 守门
    （StaleExportError 409）与 TaskStatus.stale 同源比对。
    """
    return bool(latest.get("design_hash") != design_digest(project.design))


def _with_hash(project: ProjectFile, digest: str) -> ProjectFile:
    """metadata.content_hash 回填（保存前一致化——可复算三元组 R3）。"""
    return project.model_copy(
        update={"metadata": project.metadata.model_copy(update={"content_hash": digest})}
    )


def _check_depth(value: Any, limit: int) -> None:
    """上传面深度闸（迭代计数防栈炸弹；与 core io 深度闸同族，§18）。"""
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth >= limit:
            raise InvalidProjectPayloadError(
                f"项目 JSON 嵌套深度超过上限 {limit}（§18 上传面——防栈耗尽炸弹）"
            )
        if isinstance(current, Mapping):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, Sequence) and not isinstance(current, str | bytes):
            stack.extend((item, depth + 1) for item in current)


def _project_path(ctx: ServiceContext, project_id: str) -> Path:
    """基点内拼接（R1：safe_child 分量校验拒 ../ 与绝对路径）。"""
    return safe_child(ctx.projects_dir, project_id).with_name(project_id + _PROJECT_SUFFIX)


def create_project(ctx: ServiceContext, payload: Mapping[str, Any]) -> SaveOutcome:
    """创建（空项目或导入 JSON 深度闸装载）→ 落盘（经 app.save_project）。"""
    _check_depth(payload, ctx.settings.max_json_depth)
    raw = payload.get("project")
    if raw is None:
        project = ProjectFile(
            format_version=_DESIGN_FORMAT_VERSION,
            design=DesignState(),
            metadata=Metadata(
                format_version=_DESIGN_FORMAT_VERSION,
                content_hash="",
                engine_version=ENGINE_VERSION,
                data_version="",
            ),
        )
    else:
        _check_depth(raw, ctx.settings.max_json_depth)
        try:
            project = parse_project(raw)
        except ValueError as exc:  # pydantic ValidationError 族（ValueError 基）→422
            raise InvalidProjectPayloadError(f"导入项目校验失败：{exc}") from exc
    project_id = uuid.uuid4().hex
    digest = design_digest(project.design)
    core.save_project(_with_hash(project, digest), _project_path(ctx, project_id))
    return SaveOutcome(content_hash=digest, design_changed=True, project_id=project_id)


def list_projects(ctx: ServiceContext) -> tuple[ProjectSummary, ...]:
    """项目列表（R4：文件读取——名称=文件 id、哈希/时间元数据）。"""
    summaries: list[ProjectSummary] = []
    for path in sorted(ctx.projects_dir.glob(f"*{_PROJECT_SUFFIX}")):
        try:
            project = core.load_project(path)
        except core.InvalidProjectError:
            continue  # 损坏文件不阻塞列表（装载错误走 read/validate 端点）
        summaries.append(
            ProjectSummary(
                project_id=path.stem,
                format_version=project.format_version,
                content_hash=project.metadata.content_hash,
                engine_version=project.metadata.engine_version,
                data_version=project.metadata.data_version,
                view_timestamp=project.view.timestamp,
            )
        )
    return tuple(summaries)


def read_project(ctx: ServiceContext, project_id: str) -> ProjectFile:
    """读取完整 ProjectFile（经 app.load_project：M-3 版本门+SERVER D2 双闸）。"""
    path = _project_path(ctx, project_id)
    if not path.is_file():
        raise ProjectNotFoundError(f"项目 {project_id!r} 不存在（基点内无 {path.name}）")
    return core.load_project(path)


def save_project(ctx: ServiceContext, project_id: str, project: ProjectFile) -> SaveOutcome:
    """保存（原子写经 app.save_project；锁前置探测 409；stale 标记）。

    R2：design_changed=design 态对比（view-only 保存=False——保存只写
    view 态不触发计算）；编辑 design 后对在途任务置 stale 提示标记
    （UF-37：守门在消费侧实时比对，本标记仅 UI 提示）。
    """
    path = _project_path(ctx, project_id)
    if not path.is_file():
        raise ProjectNotFoundError(f"项目 {project_id!r} 不存在（基点内无 {path.name}）")
    lock = path.with_suffix(".lock")
    if lock.exists():
        raise ProjectLockedError(lock)
    old = core.load_project(path)
    digest = design_digest(project.design)
    core.save_project(_with_hash(project, digest), path)
    if old.design != project.design:
        for task_id in ctx.manager.task_ids_for_project(project_id):
            record = ctx.manager.status(task_id)
            if not record.stale and record.state not in {"done", "cancelled", "failed"}:
                ctx.manager.mark_stale(task_id)
    return SaveOutcome(
        content_hash=digest,
        design_changed=old.design != project.design,
        project_id=project_id,
    )


def validate_project(ctx: ServiceContext, project_id: str) -> ValidationReport:
    """零计算快速校验（R3：装载面=严格 schema+版本门+双闸）。"""
    try:
        read_project(ctx, project_id)
    except core.InvalidProjectError as exc:
        return ValidationReport(valid=False, errors=(str(exc),))
    return ValidationReport(valid=True, errors=())


def import_legacy(ctx: ServiceContext, payload: Mapping[str, Any]) -> None:
    """旧系统导入（M4 归属）——显式未就绪，不假装功能（诚实 501）。"""
    raise ImportNotReadyError(
        "旧系统导入未就绪（归属 M4——core.project.migration 迁移链与 "
        "best-effort 字段映射清单在该批落地；禁静默空 ImportReport）"
    )
