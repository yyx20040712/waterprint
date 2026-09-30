"""R2 统一异常映射域伴生件（main.py 500 行恰墙拆件——批6g 结构债）。

输入:  core/server 领域异常类基（可导入面）+worker 侧名义表键
输出:  _EXCEPTION_STATUS 类基映射表+DOMAIN_ERROR_CODES 名义表+
       _register_exception_handlers 注册器（main 单点消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批6g 2026-09-26 拆件：main.py 500 行恰满零余量——wave6
#   §批6g 授权「中间件/挂载段拆 main_lib.py 先例（门禁脚本同款）」；
#   ADR-024 拆件配方的单元包外模块裁定面=master plan 预裁拆法）。
#   语义自 main._EXCEPTION_STATUS/DOMAIN_ERROR_CODES/
#   _register_exception_handlers 逐字迁入（B3 R1 整域逐字搬运先例，
#   行为等价烤验=server openapi dump 双跑 diff=0+全量绿）。
#
# 【公开接口】（同节点伴生件——main 单点消费+DOMAIN_ERROR_CODES
#   经 main 再导出=test_app_factory 消费面零改动）
#   _EXCEPTION_STATUS：类基映射表（core/server 领域异常→HTTP 码，
#       集中一处禁散落——R2 唯一翻译处的数据面）
#   DOMAIN_ERROR_CODES：worker 侧领域异常名义映射（LoopDivergence→422
#       附诊断是 R2 冻结行；消费面=services.calculation.task_status
#       经 ServiceContext 注入——fastapi/status 数值面归 main_lib 后
#       services 禁 import fastapi 口径不变）
#   _register_exception_handlers(app)：映射表逐条注册（冻结错误体
#       {detail, error_type}+429 Retry-After 建议性头）
#
# 【层序注记】main_lib 不入 import-linter layers 契约（unconstrained
#   ——auth/sse_limits/ai_config_store 先例同款）；main→main_lib 为
#   同节点文件粒度拆件边（structure-graph §1c 天然豁免 (f) 规则，
#   services.exports→exports_registry 先例同构）。
#
# 【测试要求】经 test_app_factory 镜像测试覆盖（映射表完整性/错误体
#   形态——本件拆件非独立规格面）。
#
# 【参照】AGENTS §2 预算墙；.workflow/backend-calc-complete/
#   wave6-master-plan.md §批6g
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from typing import Final

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from waterprint import app as core
from waterprint import flows
from waterprint.contracts.manifest import InvalidUnitConfig

from waterprint_server.auth import AuthError
from waterprint_server.jobs import worker
from waterprint_server.jobs.manager import UnknownTaskError
from waterprint_server.services.ai_connection import UvNotFoundError
from waterprint_server.services.calculation import InvalidSolutionRefError
from waterprint_server.services.compare import CompareSourceNotFoundError
from waterprint_server.services.cost import (
    CostSourceNotFoundError,
    InvalidCostRequestError,
)
from waterprint_server.services.design_map import DesignMapSourceNotFoundError
from waterprint_server.services.elevation import (
    ElevationSourceNotFoundError,
    InvalidElevationRequestError,
)
from waterprint_server.services.enumeration import (
    DiagnosisNotAvailableError,
    InvalidPageParameterError,
    MultiUnitEnumerationError,
    TaskKindMismatchError,
    TaskNotCompleteError,
)
from waterprint_server.services.exports import (
    ExportFileNotFoundError,
    ExportSourceNotFoundError,
    ExportTemplateMissingError,
    InvalidExportRequestError,
    StaleExportError,
)

# B4-3（2026-09-20）：联合枚举服务面异常（422 族——静态预检/请求形态）。
from waterprint_server.services.joint_enumeration import (
    InvalidJointUnitsError,
    JointEnumerationTooLargeError,
)
from waterprint_server.services.project_lifecycle import ProjectBusyError
from waterprint_server.services.projects import (
    ImportNotReadyError,
    InvalidProjectPayloadError,
    PayloadTooLargeError,
    ProjectLockedError,
    ProjectNotFoundError,
)
from waterprint_server.services.scene import (
    InvalidSceneRequestError,
    SceneSourceNotFoundError,
)
from waterprint_server.services.sensitivity import SensitivitySourceNotFoundError
from waterprint_server.services.site import InvalidSpacingRequestError
from waterprint_server.services.trust import TrustSourceNotFoundError
from waterprint_server.sse_limits import RateLimitedError

# ── R2 统一异常映射表（集中一处；core/server 领域异常→HTTP 码）──
# 类基映射（可导入面）：InvalidUnitConfig→400 / NotFound 族→404 /
# 冲突族（锁/stale/未完成）→409 / 参数族→422 / 未就绪族→501。
# R2A 批1（N-3）：AuthError→401——经统一 handler 自动获得冻结错误体
# {detail, error_type}（不引入 403，终裁三.沿册项）。
_EXCEPTION_STATUS: Final[tuple[tuple[type[Exception], int], ...]] = (
    (AuthError, status.HTTP_401_UNAUTHORIZED),
    # B6 D5（SSE 治理）：RateLimitedError→429（统一错误体 {detail,
    # error_type}+Retry-After 建议性头——异常携带值；不声明 responses=
    # openapi 零字节破面）。
    (RateLimitedError, status.HTTP_429_TOO_MANY_REQUESTS),
    (InvalidUnitConfig, status.HTTP_400_BAD_REQUEST),
    # AI2（2026-09-13）：uv 不在 PATH=一键接入前置依赖缺（用户环境面）→400。
    (UvNotFoundError, status.HTTP_400_BAD_REQUEST),
    (core.InvalidAssemblyError, status.HTTP_400_BAD_REQUEST),
    (core.InvalidProjectError, status.HTTP_400_BAD_REQUEST),
    (ProjectNotFoundError, status.HTTP_404_NOT_FOUND),
    (UnknownTaskError, status.HTTP_404_NOT_FOUND),
    (DiagnosisNotAvailableError, status.HTTP_404_NOT_FOUND),
    (ExportSourceNotFoundError, status.HTTP_404_NOT_FOUND),
    # EXPD D2：下载产物不在册（产物缺/边车缺——注册口径双闸）→404。
    (ExportFileNotFoundError, status.HTTP_404_NOT_FOUND),
    (SceneSourceNotFoundError, status.HTTP_404_NOT_FOUND),
    (ElevationSourceNotFoundError, status.HTTP_404_NOT_FOUND),
    (CostSourceNotFoundError, status.HTTP_404_NOT_FOUND),
    (TrustSourceNotFoundError, status.HTTP_404_NOT_FOUND),  # P2 次批 ADR-012 D8
    (CompareSourceNotFoundError, status.HTTP_404_NOT_FOUND),  # P2 第三批 ADR-018 D5
    (SensitivitySourceNotFoundError, status.HTTP_404_NOT_FOUND),  # 批6e wave6 授权
    (ProjectLockedError, status.HTTP_409_CONFLICT),
    # P2 生命周期批（2026-09-12）：删除守卫③在途任务→409（C3）。
    (ProjectBusyError, status.HTTP_409_CONFLICT),
    (StaleExportError, status.HTTP_409_CONFLICT),
    (TaskNotCompleteError, status.HTTP_409_CONFLICT),
    (TaskKindMismatchError, status.HTTP_409_CONFLICT),  # API-1：kind≠enumerate
    (MultiUnitEnumerationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    # B4-3：联合枚举静态预检（rows/N 超限）与请求形态（空/重复/未知
    # unit_ids）→422（W7 事前拒绝面）。
    (JointEnumerationTooLargeError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidJointUnitsError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    # B4-3：core 侧联合枚举输入非法（worker 运行面二道闸）→400
    # （InvalidAssemblyError 同族）。
    (core.InvalidJointEnumerationError, status.HTTP_400_BAD_REQUEST),
    (InvalidPageParameterError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSolutionRefError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidExportRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    # H2（exp-hygiene-20260930）：flows 校验/审计异常族→422（GR-11 参数族
    # ——结果数据/意图面不可渲染，用户输入域非服务端 500；单产物 audit 渲染
    # 期 flows.InvalidFlowError/InvalidAuditError/InvalidAuditPathError 三件
    # 未映射=rare 500 缺陷收口；server 面 trace forbidden，经 flows 再导出取用）。
    (flows.InvalidFlowError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (flows.InvalidAuditError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (flows.InvalidAuditPathError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSceneRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSpacingRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),  # L4b 工况面
    (InvalidElevationRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidCostRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidProjectPayloadError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    # ENG7：脏 site 几何（coord_grid 非有限/非正——用户输入非法同族，
    # GR-11 族；core 再导出面经 app 正门，main→app 边在册零图谱改动）。
    (core.InvalidSitePlanError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    # FD 批（PD6 2026-09-09）：轴声明非法（长度 pydantic 面/字段不存在/
    # min≥max/⊆manifest 越界/step 非正——core 防御面）→422；护栏超限
    # （DesignMapTooLarge=4xx 呈裁落 400——InvalidUnitConfig 同族）；
    # 目标单元不在项目=404（services 面前置拒）。
    (core.InvalidDesignMapError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (core.DesignMapTooLarge, status.HTTP_400_BAD_REQUEST),
    (DesignMapSourceNotFoundError, status.HTTP_404_NOT_FOUND),
    # ENG2 D3：非弃用名（HTTP_413_CONTENT_TOO_LARGE==413，值同简报所书
    # REQUEST_ENTITY_TOO_LARGE 旧别名——用旧名会常驻 StarletteDeprecationWarning）。
    (PayloadTooLargeError, status.HTTP_413_CONTENT_TOO_LARGE),
    (worker.InvalidTaskPayloadError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (ValidationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (ValueError, status.HTTP_422_UNPROCESSABLE_CONTENT),  # 兜底：路径分量/DSL 值面
    (core.ArtifactKindNotReady, status.HTTP_501_NOT_IMPLEMENTED),
    (ImportNotReadyError, status.HTTP_501_NOT_IMPLEMENTED),
    (ExportTemplateMissingError, status.HTTP_501_NOT_IMPLEMENTED),
)
# 名义映射（worker 侧领域异常诊断面——类不可直连导入时按名映射，
# LoopDivergence→422 附诊断是 R2 冻结行）。R1-2（AU-2 接线 2026-08-26）：
# 消费面=services.calculation.task_status（经 ServiceContext.domain_error_codes
# 注入——fastapi/status 数值面归本件独占，services 禁 import fastapi），
# failed 任务按 error_type 名回填结构化 error_code 字段。
DOMAIN_ERROR_CODES: Final[dict[str, int]] = {
    "LoopDivergence": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "InvalidUnitConfig": status.HTTP_400_BAD_REQUEST,
    "InvalidExecutionError": status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _register_exception_handlers(app: FastAPI) -> None:
    """R2 唯一翻译处：映射表逐条注册（禁散落 add_exception_handler）。"""

    def _make_handler(code: int) -> Callable[[Request, Exception], JSONResponse]:
        def handler(_request: Request, exc: Exception) -> JSONResponse:
            structlog.get_logger(__name__).warning(
                "domain_exception_mapped", error=str(exc), status_code=code
            )
            response = JSONResponse(
                status_code=code,
                content={"detail": str(exc), "error_type": type(exc).__name__},
            )
            # B6 D5：429 附 Retry-After 建议性头（异常属性携带——统一错误体
            # 形态不变；浏览器 EventSource 遵从度不一，建议性语义不依赖）。
            if isinstance(exc, RateLimitedError):
                response.headers["Retry-After"] = str(exc.retry_after)
            return response

        return handler

    for exception_type, code in _EXCEPTION_STATUS:
        app.add_exception_handler(exception_type, _make_handler(code))
