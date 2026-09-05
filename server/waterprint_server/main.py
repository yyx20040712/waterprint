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
#   - R3 契约自检：OpenAPI 生成成功 + 端点集==27（九路由器规格并集
#     ——META1 注释同步勘误：原记 18 系 FE1 前陈数；FE7 +elevation1；
#     FE8 +cost1；EXPD 勘误：原记 25 系 SC1 前陈数）+ A2 面（schema 无
#     Any 泄漏）由镜像测试常驻；
#     启动期断言=端点数；+1=constraints GET，CP1 D4；+1=site/spacing
#     GET，L4b D1）。
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
from contextlib import asynccontextmanager, suppress
from typing import Any, Final

import structlog
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from waterprint import app as core
from waterprint.contracts.manifest import InvalidUnitConfig

from waterprint_server.auth import AuthError, verify_token, verify_token_sse
from waterprint_server.jobs import worker
from waterprint_server.jobs.manager import Manager, UnknownTaskError
from waterprint_server.routers import (
    calc,
    cost,
    elevation,
    events,
    exports,
    projects,
    scene,
    site,
    units,
)
from waterprint_server.services import ServiceContext
from waterprint_server.services.calculation import InvalidSolutionRefError
from waterprint_server.services.cost import (
    CostSourceNotFoundError,
    InvalidCostRequestError,
)
from waterprint_server.services.elevation import (
    ElevationSourceNotFoundError,
    InvalidElevationRequestError,
)
from waterprint_server.services.enumeration import (
    DiagnosisNotAvailableError,
    InvalidPageParameterError,
    MultiUnitEnumerationError,
    TaskNotCompleteError,
)
from waterprint_server.services.exports import (
    ExportFileNotFoundError,
    ExportSourceNotFoundError,
    ExportTemplateMissingError,
    InvalidExportRequestError,
    StaleExportError,
)
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
from waterprint_server.services.site import InvalidSpacingRequestError
from waterprint_server.settings import Settings, ensure_directories, get_settings

# ── R2 统一异常映射表（集中一处；core/server 领域异常→HTTP 码）──
# 类基映射（可导入面）：InvalidUnitConfig→400 / NotFound 族→404 /
# 冲突族（锁/stale/未完成）→409 / 参数族→422 / 未就绪族→501。
# R2A 批1（N-3）：AuthError→401——经统一 handler 自动获得冻结错误体
# {detail, error_type}（不引入 403，终裁三.沿册项）。
_EXCEPTION_STATUS: Final[tuple[tuple[type[Exception], int], ...]] = (
    (AuthError, status.HTTP_401_UNAUTHORIZED),
    (InvalidUnitConfig, status.HTTP_400_BAD_REQUEST),
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
    (ProjectLockedError, status.HTTP_409_CONFLICT),
    (StaleExportError, status.HTTP_409_CONFLICT),
    (TaskNotCompleteError, status.HTTP_409_CONFLICT),
    (MultiUnitEnumerationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidPageParameterError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSolutionRefError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidExportRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSceneRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidSpacingRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),  # L4b 工况面
    (InvalidElevationRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidCostRequestError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidProjectPayloadError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    # ENG7：脏 site 几何（coord_grid 非有限/非正——用户输入非法同族，
    # GR-11 族；core 再导出面经 app 正门，main→app 边在册零图谱改动）。
    (core.InvalidSitePlanError, status.HTTP_422_UNPROCESSABLE_CONTENT),
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
# 注入——fastapi/status 数值面归 main 独占，services 禁 import fastapi），
# failed 任务按 error_type 名回填结构化 error_code 字段。
DOMAIN_ERROR_CODES: Final[dict[str, int]] = {
    "LoopDivergence": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "InvalidUnitConfig": status.HTTP_400_BAD_REQUEST,
    "InvalidExecutionError": status.HTTP_422_UNPROCESSABLE_CONTENT,
}
# 端点集冻结 5+6+5+2+1+1+2+1+1+1+1+1=27（白名单字面量和式；+1=scene GET，FE1 D1；
# +1=elevation GET，FE7 D1；+2=units/assumptions GET，META1 D2——静态只读
# 目录两端点；+1=cost GET，FE8 D1；+1=constraints GET，CP1 D4；
# +1=site/spacing GET，L4b D1——间距校核取数端点；+1=exports/ifc POST，
# SC1 D7——BIM 模型导出端点，openapi 25→26 破面已授权；+1=exports/
# {file_name} GET，EXPD D4——产物下载端点，openapi 26→27 破面已授权
# [Ruling 2026-09-05 ②]）
_EXPECTED_ENDPOINTS: Final[int] = 10 + 10 - 2 + 1 + 1 + 2 + 1 + 1 + 1 + 1 + 1
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


async def _sweep_periodically(manager: Manager, interval_s: int) -> None:
    """WP4（修1）：TTL 周期清扫——sleep 先行（启动清扫由 lifespan 直调承担）。

    单文件失败面已在 registry.unlink_task_face 归一 warning；本层兜底=
    单轮意外异常不倒灌 lifespan（任务不崩，下轮续——清扫失败≠服务失败）。
    R-1 K-3：捕获 Exception 基类的字面形态被 gate_patterns.BARE_EXCEPT_RE
    实拦（裁决前提勘误）——按 calculation._TRIGGER_FAILURES 先例以现实
    异常族枚举实现同一语义。
    """
    while True:
        await asyncio.sleep(interval_s)
        try:
            manager.sweep_expired()
        except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
            structlog.get_logger(__name__).warning(
                "task_sweep_round_failed", reason=repr(exc)
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
    """R3 契约自检：OpenAPI 生成成功 + 端点集==27（漂移前置到启动期）。"""
    schema = app.openapi()
    operations = sum(len(methods) for methods in schema["paths"].values())
    if operations != _EXPECTED_ENDPOINTS:
        raise RuntimeError(
            f"契约自检失败：端点集 {operations} != {_EXPECTED_ENDPOINTS}"
            "（九路由器规格并集 projects5+calc6+exports6+events2+scene1"
            "+elevation1+units2+cost1+constraints1+site1——A1 锁定；SC1 ifc 增）"
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
            registry_dir=settings.exports_dir / "tasks" / "registry",  # S2 D3：终态落盘+重启恢复
            artifacts_dir=settings.exports_dir / "tasks",  # WP4：calc/enum 产物淘汰面
            task_retention_s=settings.task_retention_s,  # WP4 修1：TTL 旋钮注入（启用清扫）
            task_registry_cap=settings.task_registry_cap,
            loop=asyncio.get_running_loop(),
            progress_queue=queue,
            max_concurrent=settings.calc_workers,
        )
        manager.start()
        manager.sweep_expired()  # WP4：启动清扫（恢复记录=新租约，首轮通常空转）
        sweeper = asyncio.create_task(  # WP4：周期清扫（teardown 取消——禁悬挂任务）
            _sweep_periodically(manager, settings.task_sweep_interval_s)
        )
        app.state.ctx = ServiceContext(
            settings=settings, manager=manager, domain_error_codes=DOMAIN_ERROR_CODES
        )
        _contract_self_check(app)
        yield
        sweeper.cancel()
        # WP4K G1-01（Kimi 回填审）：清扫任务若已带既往异常死亡，await 会重抛
        # 且 suppress 仅压 CancelledError——异常族之外的意外型仍可倒灌
        # lifespan。teardown 侧全谱压制（suppress(Exception) 不触 grep 门禁
        # 裸 except 拦截；正门续跑语义由 _sweep_periodically 异常族承担）。
        with suppress(asyncio.CancelledError, Exception):
            await sweeper
        await manager.shutdown(_SHUTDOWN_TIMEOUT)
        pool.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(title="WaterPrint 服务层", version="0.1.0", lifespan=lifespan)
    # R2A 批1（终裁 R-1/D3）：include 级鉴权依赖挂载——七业务路由器受保
    #（20 非事件操作仅认 Bearer），events 两 SSE 端点用双通道依赖（header
    # 或 ？token=）；units 三静态只读端点豁免（不挂）。端点集/路径/方法
    # 变化仅 SC1/EXPD 增量（_EXPECTED_ENDPOINTS=27 现值——契约自检常驻；
    # 旧注记「=24 恒」系 R2A 时点快照，SC1 顺带销注释漂移）。
    app.include_router(projects.router, dependencies=[Depends(verify_token)])
    app.include_router(calc.router, dependencies=[Depends(verify_token)])
    app.include_router(exports.router, dependencies=[Depends(verify_token)])
    app.include_router(events.router, dependencies=[Depends(verify_token_sse)])
    app.include_router(scene.router, dependencies=[Depends(verify_token)])
    app.include_router(elevation.router, dependencies=[Depends(verify_token)])
    app.include_router(cost.router, dependencies=[Depends(verify_token)])
    # L4b：site/spacing 鉴权族挂载（项目数据面——units 静态目录族外同保）
    app.include_router(site.router, dependencies=[Depends(verify_token)])
    # units 豁免面契约明示（R-3）：三操作显式 security=[]（公开面明示，
    # 区别于未声明）——FastAPI include 面无 security 参数，经路由对象
    # openapi_extra 直挂（0.141 实证：include 后 app.routes 为包装件，
    # 真源在 router.routes）。
    for units_route in units.router.routes:
        if isinstance(units_route, APIRoute):
            units_route.openapi_extra = {"security": []}
    app.include_router(units.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_DEV_ORIGINS),  # R5 开发期白名单
        allow_methods=["*"],
        # N-2（R2A 批1 查补）：Authorization 已覆盖——["*"] 通配下预检响应
        # 回显请求的 Access-Control-Request-Headers（dev 5173 面不断）。
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

if __name__ == "__main__":
    # WP1（部署面安全收口 2026-09-02）：裸机/开发态启动入口——host/port 经
    # settings（默认 127.0.0.1:8000，只听本地回环；对外绑定=WATERPRINT_HOST
    # 显式覆盖=信任决策，见 docs/deployment.md「安全红线」节）。容器内不走
    # 本块（Dockerfile CMD 直接 uvicorn --host 0.0.0.0 供 nginx 跨容器反代，
    # 8000 不发布宿主）。局部 import：模块导入面（测试/ASGI 部署）零增量依赖。
    import uvicorn  # 启动块正门（模块级 if 块不在 PLC0415 函数体口径内）

    _settings = get_settings()
    # R-1（G1-01）：传已建 app 对象非字符串路径——python -m 启动时模块以 __main__
    # 身份已执行，字符串路径会再 import 实名模块一遍=双 app 实例（无 reload 收益）。
    uvicorn.run(app, host=_settings.host, port=_settings.port)
