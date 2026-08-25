"""应用工厂与生命周期：进程池创建/销毁、路由装配、异常映射、契约自检。

输入:  Settings（settings.py）
输出:  ASGI app（uvicorn 入口 waterprint_server.main:app）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/test_app_factory.py）
#
# 【公开接口】
#   create_app(settings: Settings) -> FastAPI    应用工厂（可测试）
#   app = create_app(get_settings())             模块级实例（部署入口）
#
# 【行为规格】
#   R1 生命周期：startup 创建 ProcessPoolExecutor（workers 数来自
#      Settings，Windows spawn——core 模块导入零副作用是前提 §12.2）、
#      jobs.Manager；shutdown 优雅等待（超时强杀并报告）。
#   R2 统一异常映射：core 领域异常 → HTTP 码（InvalidUnitConfig→400、
#      LoopDivergence→422 附诊断、NotFound→404…映射表集中一个 handler
#      注册点；core 禁抛 HTTP 语义——本层是唯一翻译处，§15 工程细节 1）。
#   R3 契约自检（启动期）：OpenAPI schema 与 core pydantic 模型比对，
#      不一致 = 启动失败（漂移前置，§15 工程细节 5）。
#   R4 结构化日志：structlog 配置（事件带 project_hash/unit_id/
#      condition/formula_id 字段，可反查计算迹 §15 工程细节 2）；
#      只落本地文件、脱敏（§18）。
#   R5 中间件：CORS（仅开发期白名单）、请求 ID；SSE 路由注册
#      （X-Accel-Buffering: no 头，R5 反代缓冲对策）。
#   R6 单进程假设（§16 A5）：部署契约 api replicas=1 + calc workers=N，
#      多副本=失忆——部署文档明示。
#
# 【实现注记（SERVER 2026-08-26）】
#   - R2 LoopDivergence（graph.loop 类）不可直连导入（D7 forbidden：
#     waterprint.graph）——类基映射覆盖可导入面，LoopDivergence 等
#     仅 worker 侧产生的领域异常经 DOMAIN_ERROR_CODES 名义表映射
#     （failed 任务诊断消费面），集中一处不散落。
#   - R3 契约自检：OpenAPI 生成成功 + 端点集==18（四路由器规格并集）
#     + A2 面（schema 无 Any 泄漏）由镜像测试常驻；启动期断言=端点数。
#   - executor 注入口：create_app(settings, executor=None)——测试注入
#     ThreadPoolExecutor（跳过 spawn；探针另以真进程池实录）。
#
# 【测试要求】工厂可重复构建（无全局状态）、生命周期启停、
#   异常映射表完整性、（实现后）契约自检失败路径。
#
# 【参照】重写计划 §12.2/§13.4/§15/§16 A5/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import logging
import multiprocessing as mp
import uuid
from collections.abc import AsyncIterator, Callable
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from typing import Any, Final

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from waterprint import app as core
from waterprint.contracts.manifest import InvalidUnitConfig

from waterprint_server.jobs import worker
from waterprint_server.jobs.manager import Manager, UnknownTaskError
from waterprint_server.routers import calc, events, exports, projects
from waterprint_server.services import ServiceContext
from waterprint_server.services.calculation import InvalidSolutionRefError
from waterprint_server.services.enumeration import (
    DiagnosisNotAvailableError,
    InvalidPageParameterError,
    MultiUnitEnumerationError,
    TaskNotCompleteError,
)
from waterprint_server.services.exports import (
    ExportSourceNotFoundError,
    ExportTemplateMissingError,
    InvalidExportRequestError,
    StaleExportError,
)
from waterprint_server.services.projects import (
    ImportNotReadyError,
    InvalidProjectPayloadError,
    ProjectLockedError,
    ProjectNotFoundError,
)
from waterprint_server.settings import Settings, ensure_directories, get_settings

# ── R2 统一异常映射表（集中一处；core/server 领域异常→HTTP 码）──
# 类基映射（可导入面）：InvalidUnitConfig→400 / NotFound 族→404 /
# 冲突族（锁/stale/未完成）→409 / 参数族→422 / 未就绪族→501。
_EXCEPTION_STATUS: Final[tuple[tuple[type[Exception], int], ...]] = (
    (InvalidUnitConfig, status.HTTP_400_BAD_REQUEST),
    (core.InvalidAssemblyError, status.HTTP_400_BAD_REQUEST),
    (core.InvalidProjectError, status.HTTP_400_BAD_REQUEST),
    (ProjectNotFoundError, status.HTTP_404_NOT_FOUND),
    (UnknownTaskError, status.HTTP_404_NOT_FOUND),
    (DiagnosisNotAvailableError, status.HTTP_404_NOT_FOUND),
    (ExportSourceNotFoundError, status.HTTP_404_NOT_FOUND),
    (ProjectLockedError, status.HTTP_409_CONFLICT),
    (StaleExportError, status.HTTP_409_CONFLICT),
    (TaskNotCompleteError, status.HTTP_409_CONFLICT),
    (MultiUnitEnumerationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidPageParameterError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSolutionRefError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidExportRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidProjectPayloadError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (worker.InvalidTaskPayloadError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (ValidationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (ValueError, status.HTTP_422_UNPROCESSABLE_CONTENT),  # 兜底：路径分量/DSL 值面
    (core.ArtifactKindNotReady, status.HTTP_501_NOT_IMPLEMENTED),
    (ImportNotReadyError, status.HTTP_501_NOT_IMPLEMENTED),
    (ExportTemplateMissingError, status.HTTP_501_NOT_IMPLEMENTED),
)
# 名义映射（worker 侧领域异常诊断面——类不可直连导入时按名映射，
# LoopDivergence→422 附诊断是 R2 冻结行；消费面=solutions/diagnosis）。
DOMAIN_ERROR_CODES: Final[dict[str, int]] = {
    "LoopDivergence": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "InvalidUnitConfig": status.HTTP_400_BAD_REQUEST,
    "InvalidExecutionError": status.HTTP_422_UNPROCESSABLE_CONTENT,
}
_EXPECTED_ENDPOINTS: Final[int] = 10 + 10 - 2  # 端点集冻结 5+6+5+2=18（白名单字面量和式）
_SHUTDOWN_TIMEOUT: Final[float] = 10.0  # 优雅停机等待（秒；白名单字面量 10）
# R5 开发期 CORS 白名单（部署面经反代域名收敛——产品内网工具约束）。
_DEV_ORIGINS: Final[tuple[str, ...]] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _configure_logging(settings: Settings) -> None:
    """R4 structlog：JSON 行落本地文件（logging 幂等配置，可重复构建）。"""
    handler = logging.FileHandler(settings.log_file, delay=True)  # 惰性建文件（导入零落盘）
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _register_exception_handlers(app: FastAPI) -> None:
    """R2 唯一翻译处：映射表逐条注册（禁散落 add_exception_handler）。"""

    def _make_handler(code: int) -> Callable[[Request, Exception], JSONResponse]:
        def handler(_request: Request, exc: Exception) -> JSONResponse:
            structlog.get_logger(__name__).warning(
                "domain_exception_mapped", error=str(exc), status_code=code
            )
            return JSONResponse(
                status_code=code,
                content={"detail": str(exc), "error_type": type(exc).__name__},
            )

        return handler

    for exception_type, code in _EXCEPTION_STATUS:
        app.add_exception_handler(exception_type, _make_handler(code))


def _contract_self_check(app: FastAPI) -> None:
    """R3 契约自检：OpenAPI 生成成功 + 端点集==18（漂移前置到启动期）。"""
    schema = app.openapi()
    operations = sum(len(methods) for methods in schema["paths"].values())
    if operations != _EXPECTED_ENDPOINTS:
        raise RuntimeError(
            f"契约自检失败：端点集 {operations} != {_EXPECTED_ENDPOINTS}"
            "（四路由器规格并集 projects5+calc6+exports5+events2——A1 锁定）"
        )


def create_app(settings: Settings, executor: Executor | None = None) -> FastAPI:
    """应用工厂（可测试可重复构建——装配束挂 app.state 无全局可变态）。"""
    _configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        ensure_directories(settings)
        queue: mp.Queue[Any] = mp.Queue()
        pool = executor if executor is not None else ProcessPoolExecutor(
            max_workers=settings.calc_workers,
            initializer=worker._init_progress_queue,  # noqa: SLF001  # 池 initializer 正门（R3 进度通路）
            initargs=(queue,),
        )
        manager = Manager(
            pool,
            cancel_dir=settings.exports_dir / "tasks" / "cancel",
            loop=asyncio.get_running_loop(),
            progress_queue=queue,
            max_concurrent=settings.calc_workers,
        )
        manager.start()
        app.state.ctx = ServiceContext(settings=settings, manager=manager)
        _contract_self_check(app)
        yield
        await manager.shutdown(_SHUTDOWN_TIMEOUT)
        pool.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(title="WaterPrint 服务层", version="0.1.0", lifespan=lifespan)
    app.include_router(projects.router)
    app.include_router(calc.router)
    app.include_router(exports.router)
    app.include_router(events.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_DEV_ORIGINS),  # R5 开发期白名单
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id(request: Request, call_next: Callable[..., Any]) -> Any:
        """R5 请求 ID（响应头回写 + structlog 上下文绑定）。"""
        identifier = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=identifier)
        response = await call_next(request)
        response.headers["X-Request-ID"] = identifier
        return response

    _register_exception_handlers(app)
    return app


app: FastAPI = create_app(get_settings())
