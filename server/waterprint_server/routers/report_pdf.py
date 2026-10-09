"""Typst PDF 计算书导出端点：POST /api/exports/report_pdf。

输入:  导出请求体 {project_id, condition_key, options} + ?force 查询参
输出:  PDF 文件流（Content-Disposition 附安全文件名）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 计算说明批 2026-10-09 任务书 §二.⑥；镜像测试
#   server/tests/routers/test_report_pdf.py）
#
# 【端点集】
#   POST /api/exports/report_pdf（body 沿既有惯例 {project_id,
#       condition_key, options}+?force=1——端点集 46→47，B6 任务书
#       §一.5/§二.⑥ 授权破面）
#
# 【行为规格】
#   R1 薄协议转换（routers 禁业务）：守门/装配/编译/边车全在
#      services.report_pdf；本件=路由声明+文件流（calcbook 四端点
#      同款 R4 文件流先例——单产物即时生成无批量任务面）。
#   R2 路由归属申报（B6 落档义务）：路径前缀沿 /api/exports 域而
#      路由件=**新件 report_pdf.py**——test_exports.py 镜像测试
#      exports 路由器恰七件冻结断言系人类锁定面（test-lock
#      manifest 在册），扩挂 exports.router 必改锁定测试=越人类
#      锁定红线；独立路由件=unit_detail.py（B2）先例同构。
#   R3 stale 守门 409/force 旧三元组标注在 service（§17.1 同族）；
#      typst 部署依赖缺/编译失败=500 族显式消息（main_lib 映射）。
#
# 【测试要求】test_report_pdf.py 六用例（端点集恰一件/200 真编译+
#   面板+下载/stale 409/force 标注/404 两面/unit_id 422）。
#
# 【参照】B6 任务书 §二.⑥；routers/exports.py（导出端点先例）；
#   services/report_pdf.py（编排母本）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import FileResponse

from waterprint_server.errors import ErrorResponse
from waterprint_server.routers.exports import ExportRequest, _ctx
from waterprint_server.services.report_pdf import create_report_pdf_export

router = APIRouter(prefix="/api/exports", tags=["exports"])

# PL-03 契约枚举（R1 回炉 N5-k2——routers/report.py _REPORT_RESPONSES
# 同形）：本端点实际 4xx/5xx 面（404 源不可得/409 stale 守门/422
# unit_id 拒与非 design 工况/500 typst 编译族——行为面 test_report_pdf
# .py 各用例），responses 声明使 openapi 与行为一致。
_REPORT_PDF_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "项目不存在/无结果集（先重算）或缺 design_hash",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "结果集过期（?force=1 可携旧三元组标注导出）",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "unit_id 不适用（全厂整厂产物）或非 design 工况"
        "（报告锚定=design 单工况；非 design 报告=后续批）",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "typst 编译失败/超时或部署依赖缺"
        "（WATERPRINT_TYPST_PATH——docs/deployment.md「导出格式」节）",
    },
}


@router.post("/report_pdf", responses=_REPORT_PDF_RESPONSES)
async def export_report_pdf(
    body: ExportRequest, request: Request, force: bool = False
) -> Response:
    """Typst PDF 计算书（B6 §二.⑥——AST→Typst 源→typst CLI 编译；全厂
    整厂产物 unit_id 422 拒；stale 409/?force=1 旧三元组标注同族；部署
    依赖=服务主机 typst CLI 必在〔docs/deployment.md「导出格式」节〕）。"""
    handle = create_report_pdf_export(
        _ctx(request),
        body.project_id,
        body.condition_key,
        body.options,
        force=force,
    )
    return FileResponse(handle.path, filename=Path(handle.path).name)  # R4 文件流
