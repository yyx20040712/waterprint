"""项目 CRUD 端点：创建/读取/保存/列表/校验（薄，只做协议转换）。

输入:  pydantic 请求（项目数据/列表查询）
输出:  pydantic 响应（项目元数据/校验报告）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_projects.py）
#
# 【端点集（v1 冻结）】
#   POST   /api/projects                    创建（空项目或导入 JSON）
#   GET    /api/projects                    列表（名称/哈希/时间元数据）
#   GET    /api/projects/{id}               读取（完整 ProjectFile）
#   PUT    /api/projects/{id}               保存（design+view，返回新
#                                          content_hash 与 dirty 状态）
#   POST   /api/projects/{id}/validate      校验（零计算快速反馈）
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

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from waterprint.contracts.project_schema import parse_project

from waterprint_server.services import ServiceContext
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
    """创建请求：空创建（project 缺省）或导入 JSON（§18 深度闸在服务面）。"""

    project: dict[str, Any] | None = None


class SaveOutcomeResponse(BaseModel):
    """R3 保存语义：新 content_hash + design/view 区分。"""

    project_id: str
    content_hash: str
    design_changed: bool


class ProjectSummaryResponse(BaseModel):
    """列表条目（名称=文件 id；哈希/时间元数据）。"""

    project_id: str
    format_version: str
    content_hash: str
    engine_version: str
    data_version: str
    view_timestamp: str


class ValidationResponse(BaseModel):
    """校验报告（零计算；错误清单带字段路径）。"""

    valid: bool
    errors: list[str]


@router.post(
    "", response_model=SaveOutcomeResponse, dependencies=[Depends(_reject_oversized_body)]
)
async def create_project(body: CreateProjectRequest, request: Request) -> SaveOutcomeResponse:
    """创建（空项目或导入）——薄转换：调 service → 响应包装。"""
    outcome = service.create_project(_ctx(request), {"project": body.project})
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
async def validate_project(project_id: str, request: Request) -> ValidationResponse:
    """校验（零计算快速反馈——装载面错误清单）。"""
    report = service.validate_project(_ctx(request), project_id)
    return ValidationResponse(valid=report.valid, errors=list(report.errors))
