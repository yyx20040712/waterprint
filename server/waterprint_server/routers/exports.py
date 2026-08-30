"""导出端点：计算书/图纸/概算/审计报告的文件流输出。

输入:  导出选项（kind + condition_key + 单元选择）
输出:  文件流（Content-Disposition 附带安全文件名）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_exports.py）
#
# 【端点集（v1 冻结）】
#   POST /api/exports/calcbook          Excel 计算书（trace.calcbook）
#   POST /api/exports/audit             HTML 审计报告（trace.audit）
#   POST /api/exports/dxf               图纸包（单单元/全厂；M2 起）
#   POST /api/exports/estimate          概算表（M3 起）
#   GET  /api/exports                   已生成产物列表（含三元组摘要）
#
# 【行为规格】
#   R1 消费最近完成结果集（绑定三元组）；若 stale，响应 409 附
#      "输入版本"信息，用户显式选择"导出旧结果"（?force=1）或先重算
#      （§17.1 导出行——禁止静默导出旧结果冒充新结果）。
#   R2 导出走任务队列（批量出图 30 张类请求，优先级低于交互计算
#      §17.1 优先级：交互计算 > 枚举 > 批量导出）。
#   R3 输出路径：Settings.exports_dir 内命名（项目 id + kind +
#      condition + 时间基三元组摘要——确定性命名，禁当前时钟进文件名）；
#      文件名白名单字符集（Content-Disposition 转义）。
#   R4 大文件流式响应（StreamingResponse/FileResponse）；DXF/Excel
#      均为产物文件读取流，不在内存拼装超大包。
#
# 【实现注记（SERVER 2026-08-26）】
#   - audit/dxf/estimate 端点透传 core ArtifactKindNotReady→501
#     （诚实未就绪——audit 归 M4/dxf 归 M2 出图批/estimate 归 M3，
#     core export_artifact 同款语义）；模板缺位（UF-16）同 501 面。
#   - 批量（options.items>1）转 export_batch 任务：本端点返回句柄
#     JSON（task_id 非 None）而非文件流；单产物即时生成返回文件流。
#   - 响应模型=服务层冻结 dataclass（ExportMeta——禁协议层重复声明）。
#
# 【测试要求】stale 409 与 force 语义、文件名安全、流式完整性、
#   队列优先级。
#
# 【参照】重写计划 §17.1/§18 路径安全
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from waterprint_server.services import ServiceContext
from waterprint_server.services import exports as service
from waterprint_server.services.exports import ExportMeta

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


class ExportRequest(BaseModel):
    """导出请求（condition_key 缺省=all；options.items 多项=批量转任务）。"""

    project_id: str
    condition_key: str = ""
    options: dict[str, Any] | None = None


async def _export(
    body: ExportRequest, request: Request, kind: str, force: bool
) -> Response:
    """四端点同构薄封装（业务全部在 service；R1/R2/R3 随行）。"""
    handle = await service.create_export(
        _ctx(request),
        body.project_id,
        kind,
        body.condition_key,
        body.options,
        force=force,
    )
    if handle.task_id is not None:  # 批量转任务（R2 低优先级队列）→ 句柄 JSON
        return Response(
            content=json.dumps(asdict(handle), ensure_ascii=False),
            media_type="application/json",
        )
    return FileResponse(handle.path, filename=Path(handle.path).name)  # R4 文件流


@router.post("/calcbook")
async def export_calcbook(
    body: ExportRequest, request: Request, force: bool = False
) -> Response:
    """Excel 计算书（stale 409/force 旧三元组标注在 service→异常映射）。"""
    return await _export(body, request, "calcbook", force)


@router.post("/audit")
async def export_audit(
    body: ExportRequest, request: Request, force: bool = False
) -> Response:
    """HTML 审计报告（M4 归属——ArtifactKindNotReady→501 透传）。"""
    return await _export(body, request, "audit", force)


@router.post("/dxf")
async def export_dxf(body: ExportRequest, request: Request, force: bool = False) -> Response:
    """图纸包（M2 出图批——ArtifactKindNotReady→501 透传）。"""
    return await _export(body, request, "dxf", force)


@router.post("/estimate")
async def export_estimate(
    body: ExportRequest, request: Request, force: bool = False
) -> Response:
    """概算表（M3 归属——ArtifactKindNotReady→501 透传）。"""
    return await _export(body, request, "estimate", force)


# ENG4 D3（I-5）注记（源码注释面——路由 docstring 即 OpenAPI description
# 源，注记入 docstring 会致契约漂移）：project_id 缺省=空串→service 侧
# 过滤一切恒 []（无「列出全部」语义——前端无消费面，语义裁决挂 UX 批）。
@router.get("", response_model=list[ExportMeta])
async def list_exports(request: Request, project_id: str = "") -> list[ExportMeta]:
    """已生成产物列表（?project_id= 过滤；含三元组摘要与 stale 标注）。"""
    return list(service.list_exports(_ctx(request), project_id))
