"""计算说明书报告端点：GET /api/calc/projects/{pid}/report。

输入:  路径参 project_id + 查询参 condition_key（缺省 design）
输出:  ReportResponse（markdown+章节两级索引+stale/design_hash 回显）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 计算说明批 2026-10-09 任务书 §二.④；镜像测试
#   server/tests/routers/test_report.py）
#
# 【端点集】
#   GET /api/calc/projects/{project_id}/report?condition_key=design
#       （缺省）——计算说明书报告（端点集 45→46——B6 任务书 §一.3
#       授权破面）
#
# 【行为规格】
#   R1 薄协议转换（routers 禁业务）：装配/verify/新鲜度全在
#      services.report（unit_detail 同制）；本件=路由声明+responses
#      404 契约（PL-03 契约枚举制式——openapi 与行为一致）。
#   R2 路由归属申报（任务书 §二.④ 落档义务）：路径前缀 /api/calc，
#      路由文件=**新件 report.py** 而非 calc.py——calc 镜像测试
#      test_calc.py 端点集恰十二件冻结断言系人类锁定面
#      （test-lock.manifest.json 在册），改挂 calc.router 必改锁定
#      测试=越人类锁定红线；独立路由件=unit_detail.py（B2）先例同构。
#   R3 stale=§12 快照绑定语义（输入变更标 stale 显式回显禁静默覆盖
#      ——calc.py 头注 §17.1 惯例；md/PDF 两产物同一装配真源）。
#
# 【测试要求】test_report.py 五用例（200 形状+数学块/工况参与 404/
#   404 两面文案区分/stale 流转/路由件端点集恰一件）。
#
# 【参照】B6 任务书 §二.④；routers/unit_detail.py（独立路由件先例）；
#   services/report.py（用例母本）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any, Final

from fastapi import APIRouter, Query, Request, status

from waterprint_server.errors import ErrorResponse
from waterprint_server.services import ServiceContext
from waterprint_server.services.report import ReportResponse, build_report

router = APIRouter(prefix="/api/calc", tags=["calc"])

# PL-03 契约枚举（B6 计算说明批 2026-10-09）：report 端点实际 404
# （未知项目/无结果集/工况不在结果集——行为面 test_report.py 404 家族）
# ——responses 声明使 openapi 与行为一致（unit_detail 同制）。
_REPORT_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "项目不存在/无结果集（先重算）或工况不在结果集",
    },
}


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入；unit_detail 同款私有件）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get(
    "/projects/{project_id}/report",
    response_model=ReportResponse,
    responses=_REPORT_RESPONSES,
)
async def get_project_report(
    project_id: str,
    request: Request,
    condition_key: str | None = Query(default=None),
) -> ReportResponse:
    """计算说明书报告（B6 §二.④——markdown〔$$ 数学块+公式溯源附录〕
    +sections 两级索引〔章 level=1/unit_calc 单元小节 level=2——前端
    导航数据源〕+stale/design_hash 显式回显〔快照绑定 §17.1——输入
    变更标 stale 禁静默覆盖〕；verify_report 全绿才返；condition_key
    缺省=design）。"""
    return build_report(_ctx(request), project_id, condition_key)
