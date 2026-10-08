"""单单元结果明细端点：GET /api/calc/projects/{pid}/units/{uid}/results。

输入:  路径参 project_id/unit_id + 查询参 condition_key（缺省 design）
输出:  UnitDetailResponse（行模型=out_dims 服务端联表+stale/design_hash 回显）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B2 结果与方案批 2026-10-09 任务书 §二.①；镜像测试
#   server/tests/routers/test_unit_detail.py）
#
# 【端点集】
#   GET /api/calc/projects/{project_id}/units/{unit_id}/results
#       ?condition_key=design（缺省）——单单元结果明细切片（端点集
#       44→45——B2 任务书 §二.①授权破面）
#
# 【行为规格】
#   R1 薄协议转换（routers 禁业务）：取数/联表/新鲜度全在
#      services.unit_detail（compare/trust 同制）；本件=路由声明+
#      responses 404 契约（PL-03 契约枚举制式——openapi 与行为一致）。
#   R2 路由归属申报（任务书 §二.① 落档义务）：路径前缀 /api/calc
#      （任务书建议路径原样），路由文件=**新件 unit_detail.py** 而非
#      calc.py——calc 镜像测试 test_calc.py 端点集恰十二件冻结断言系
#      人类锁定面（test-lock.manifest.json 在册），改挂 calc.router
#      必改锁定测试=越人类锁定红线；独立路由件=solution.py（联合枚举）
#      先例同构。
#   R3 stale=§12 快照绑定语义（输入变更标 stale 显式回显禁静默覆盖
#      ——calc.py 头注 §17.1 惯例；服务面 result_is_stale 四端点同口径）。
#
# 【测试要求】test_unit_detail.py 五用例（200 形状/行模型对账/工况参
#   与 404/404 三面文案区分/stale 流转）。
#
# 【参照】B2 任务书 §二.①；routers/solution.py（独立路由件先例）；
#   services/unit_detail.py（用例母本）；agent tools/results.py（形源）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any, Final

from fastapi import APIRouter, Query, Request, status

from waterprint_server.errors import ErrorResponse
from waterprint_server.services import ServiceContext
from waterprint_server.services.unit_detail import (
    UnitDetailResponse,
    build_unit_detail,
)

router = APIRouter(prefix="/api/calc", tags=["calc"])

# PL-03 契约枚举（B2 结果与方案批 2026-10-09）：unit_detail 端点实际 404
# （未知项目/无结果集/工况或单元不在快照——行为面 test_unit_detail.py
# 404 家族）——responses 声明使 openapi 与行为一致（trust/compare/
# sensitivity/validation 同制）。
_UNIT_DETAIL_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "项目不存在/无结果集（先重算）或工况·单元不在结果快照",
    },
}


def _ctx(request: Request) -> ServiceContext:
    """装配束取用（app.state.ctx——main 工厂注入；calc.py 同款私有件）。"""
    return request.app.state.ctx  # type: ignore[no-any-return]


@router.get(
    "/projects/{project_id}/units/{unit_id}/results",
    response_model=UnitDetailResponse,
    responses=_UNIT_DETAIL_RESPONSES,
)
async def get_unit_results(
    project_id: str,
    unit_id: str,
    request: Request,
    condition_key: str | None = Query(default=None),
) -> UnitDetailResponse:
    """单单元结果明细切片（B2 §二.①——最近完成结果集纯投影：行=out_dims
    声明面服务端联表〔FE 零副本〕+端口流量水质段+warnings/formula_ids
    数据面+stale/design_hash 回显〔快照绑定 §17.1——输入变更标 stale
    显式回显禁静默覆盖〕；condition_key 缺省=design）。"""
    return build_unit_detail(_ctx(request), project_id, unit_id, condition_key)
