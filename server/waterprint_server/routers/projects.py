"""项目 CRUD 端点：创建/读取/保存/列表/校验（薄，只做协议转换）。

输入:  pydantic 请求（项目数据/列表查询）
输出:  pydantic 响应（项目元数据/校验报告）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_projects.py）
#
# 【端点集（v1 冻结+P2 生命周期扩面 2026-09-12）】
#   POST   /api/projects                    创建（空项目或导入 JSON）
#   GET    /api/projects                    列表（名称/哈希/时间元数据）
#   GET    /api/projects/{id}               读取（完整 ProjectFile）
#   PUT    /api/projects/{id}               保存（design+view，返回新
#                                          content_hash 与 dirty 状态）
#   POST   /api/projects/{id}/validate      校验（零计算快速反馈）
#   POST   /api/projects/{id}/copy          复制（P2——新 id 落盘，design
#                                          不动同 digest）
#   POST   /api/projects/{id}/rename        重命名（P2——view.name 轻通道
#                                          design_changed=False）
#   DELETE /api/projects/{id}               删除（P2——404/锁/在途三守卫
#                                          后 unlink）
#
# 【行为规格】
#   R1 路径安全：{id} 白名单字符集校验（拒绝 ../ 与绝对路径），
#      文件操作全部限制在 Settings.projects_dir 内。
#   R2 上传防弹（§18）：JSON 大小/深度上限（Settings）；
#      校验失败 422 带字段路径错误清单（core parse_project 透传）。
#   R3 保存语义：返回新 content_hash；design 变更与 view 变更在
#      响应中区分（view-only 保存不触发 dirty 重算语义 §17.1）。
#   R4 并发防护：同项目写锁探测（{id}.wp.lock——ENG4 D4/I-7 勘误：
#      with_suffix 替换 {id}.wp.json 末后缀；冲突 409 带持有者信息，
#      §17.3 v1 单用户最低成本方案）。
#   R5 禁 pickle：项目 IO 永远 JSON（§18 IPC 行）。
#
# 【测试要求】CRUD 往返、越界 id 拒绝、大小/深度炸弹 422、
#   写锁 409、校验端点错误清单。
#
# 【参照】重写计划 §13.4/§17.3/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any, Final

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from waterprint.contracts.project_schema import parse_project

from waterprint_server.errors import ErrorResponse
from waterprint_server.services import ServiceContext
from waterprint_server.services import project_lifecycle as lifecycle
from waterprint_server.services import projects as service
from waterprint_server.services.projects import PayloadTooLargeError

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入，无全局可变态）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


def _reject_oversized_body(request: Request) -> None:
    """上传面体积闸依赖（§18）：Content-Length 超 max_upload_mb 即拒（413）。

    幂积十进制口径同 core io._MAX_BYTES 先例（10**2*10**2*10**2=MB）。
    头缺席=放行：chunked 无定长 v1 不拦——客户端全为定长 JSON，结构
    炸弹由深度闸 _check_depth 常驻守。依赖层接线而非中间件：避开
    Starlette 用户中间件在 ExceptionMiddleware 之外的处理器次序陷阱。
    """
    raw = request.headers.get("content-length")
    if raw is None:
        return
    settings = _ctx(request).settings
    limit = settings.max_upload_mb * 10**2 * 10**2 * 10**2
    size = int(raw)
    if size > limit:
        raise PayloadTooLargeError(
            f"请求体超过上传上限：Content-Length {size} 字节 > "
            f"max_upload_mb={settings.max_upload_mb}（上限 {limit} 字节，§18 上传面）"
        )


class CreateProjectRequest(BaseModel):
    """创建请求：空创建（project 缺省）或导入 JSON（§18 深度闸在服务面）。

    P0-1：name=项目显示名（可选；空白新建直带名称省一次回写 PUT；
    导入时非空则覆盖导入文件自带名）。
    """

    project: dict[str, Any] | None = None
    name: str | None = None


class SaveOutcomeResponse(BaseModel):
    """R3 保存语义：新 content_hash + design/view 区分。"""

    project_id: str
    content_hash: str
    design_changed: bool


class ProjectSummaryResponse(BaseModel):
    """列表条目（name=显示名；空串=未命名回退 id；哈希/时间元数据）。"""

    project_id: str
    format_version: str
    content_hash: str
    engine_version: str
    data_version: str
    view_timestamp: str
    name: str = ""


class ValidationResponse(BaseModel):
    """校验报告（零计算；错误清单带字段路径）。"""

    valid: bool
    errors: list[str]


class RenameProjectRequest(BaseModel):
    """重命名请求（P2）：新显示名（strip/1~100 校验在服务面）。"""

    name: str


class DeleteOutcomeResponse(BaseModel):
    """删除确认（P2）：project_id 回显。"""

    project_id: str


@router.post(
    "", response_model=SaveOutcomeResponse, dependencies=[Depends(_reject_oversized_body)]
)
async def create_project(body: CreateProjectRequest, request: Request) -> SaveOutcomeResponse:
    """创建（空项目或导入）——薄转换：调 service → 响应包装。"""
    outcome = service.create_project(
        _ctx(request), {"project": body.project, "name": body.name}
    )
    return SaveOutcomeResponse(
        project_id=outcome.project_id,
        content_hash=outcome.content_hash,
        design_changed=outcome.design_changed,
    )


@router.get("", response_model=list[ProjectSummaryResponse])
async def list_projects(request: Request) -> list[ProjectSummaryResponse]:
    """列表（元数据来自文件读取，无独立索引库）。"""
    return [
        ProjectSummaryResponse(
            project_id=item.project_id,
            format_version=item.format_version,
            content_hash=item.content_hash,
            engine_version=item.engine_version,
            data_version=item.data_version,
            view_timestamp=item.view_timestamp,
            name=item.name,
        )
        for item in service.list_projects(_ctx(request))
    ]


@router.get("/{project_id}")
async def read_project(project_id: str, request: Request) -> dict[str, Any]:
    """读取完整 ProjectFile（JSON 化；M-3 版本门+D2 双闸在 service/core）。"""
    return service.read_project(_ctx(request), project_id).model_dump(mode="json")


@router.put(
    "/{project_id}",
    response_model=SaveOutcomeResponse,
    dependencies=[Depends(_reject_oversized_body)],
)
async def save_project(
    project_id: str, body: dict[str, Any], request: Request
) -> SaveOutcomeResponse:
    """保存（R3：新 hash+design_changed 区分；R4 锁 409 在 service→异常映射）。"""
    outcome = service.save_project(
        _ctx(request), project_id, parse_project(body)  # 422 带：ValidationError 映射
    )
    return SaveOutcomeResponse(
        project_id=outcome.project_id,
        content_hash=outcome.content_hash,
        design_changed=outcome.design_changed,
    )


@router.post("/{project_id}/validate", response_model=ValidationResponse)
async def validate_project(
    project_id: str, request: Request, body: dict[str, Any] | None = None
) -> ValidationResponse:
    """校验（零计算快速反馈——装载面+结构面；body 可选=待存草稿 P0-3 呈裁④甲）。"""
    if body is None:
        report = service.validate_project(_ctx(request), project_id)
    else:
        report = service.validate_payload(body)
    return ValidationResponse(valid=report.valid, errors=list(report.errors))


# PL-03 契约枚举（GOV5）：lifecycle 三端点实际 404/409（_EXCEPTION_STATUS
# 映射）——responses 声明使 openapi 与行为一致（行为面测试见
# services/test_project_lifecycle.py 404/409 家族）。
_LIFECYCLE_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "项目不存在"},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": "写锁冲突或在途任务"},
}


@router.post(
    "/{project_id}/copy",
    response_model=SaveOutcomeResponse,
    responses=_LIFECYCLE_RESPONSES,
)
async def copy_project(project_id: str, request: Request) -> SaveOutcomeResponse:
    """复制（P2 生命周期）——薄转换：新 id+副本名在服务面，design 零动。"""
    outcome = lifecycle.copy_project(_ctx(request), project_id)
    return SaveOutcomeResponse(
        project_id=outcome.project_id,
        content_hash=outcome.content_hash,
        design_changed=outcome.design_changed,
    )


@router.post(
    "/{project_id}/rename",
    response_model=SaveOutcomeResponse,
    dependencies=[Depends(_reject_oversized_body)],  # PL-N-03 R2：name 自由文本面同制防线
    responses=_LIFECYCLE_RESPONSES,
)
async def rename_project(
    project_id: str, body: RenameProjectRequest, request: Request
) -> SaveOutcomeResponse:
    """重命名（P2 生命周期）——view.name 轻通道（design_changed=False）。"""
    outcome = lifecycle.rename_project(_ctx(request), project_id, body.name)
    return SaveOutcomeResponse(
        project_id=outcome.project_id,
        content_hash=outcome.content_hash,
        design_changed=outcome.design_changed,
    )


@router.delete(
    "/{project_id}",
    response_model=DeleteOutcomeResponse,
    responses=_LIFECYCLE_RESPONSES,
)
async def delete_project(project_id: str, request: Request) -> DeleteOutcomeResponse:
    """删除（P2 生命周期）——404/锁/在途三守卫后 unlink（不可逆）。"""
    outcome = lifecycle.delete_project(_ctx(request), project_id)
    return DeleteOutcomeResponse(project_id=outcome.project_id)
