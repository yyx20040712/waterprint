"""应用工厂与生命周期：进程池创建/销毁、路由装配、契约自检。

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
#   - R3 契约自检：OpenAPI 生成成功 + 端点集==28（FD 起 calc6→7，九路由器并集
#     ——META1 注释同步勘误：原记 18 系 FE1 前陈数；FE7 +elevation1；
#     FE8 +cost1；EXPD 勘误：原记 25 系 SC1 前陈数）+ A2 面（schema 无
#     Any 泄漏）由镜像测试常驻；
#     启动期断言=端点数；+1=constraints GET，CP1 D4；+1=site/spacing
#     GET，L4b D1）。
#   - executor 注入口：create_app(settings, executor=None)——测试注入
#     ThreadPoolExecutor（跳过 spawn；探针另以真进程池实录）。
#
# 【批6g 拆分注记】（2026-09-26，wave6 §批6g——main.py 500 行恰满零
#   余量，批2b 欠账③+R4 欠账①兑现）：R2 统一异常映射域
#   （_EXCEPTION_STATUS 类基表+DOMAIN_ERROR_CODES 名义表+
#   _register_exception_handlers 注册器及其异常导入面）整体迁
#   main_lib.py 伴生件（门禁脚本 *_lib.py 先例+services.exports→
#   exports_registry 同节点拆件注记同构——B3 R1 整域逐字搬运，行为
#   等价烤验=openapi dump 双跑 diff=0）；DOMAIN_ERROR_CODES 经本文件
#   再导出=test_app_factory 消费面零改动。生命周期/路由挂载/契约自检
#   留守（装配根语句数=挂载面声明式展开）。
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
import os
import uuid
from collections.abc import AsyncIterator, Callable
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import asynccontextmanager, suppress
from typing import Any, Final

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from waterprint_server.auth import verify_token, verify_token_sse
from waterprint_server.jobs import worker
from waterprint_server.jobs.manager import Manager

# 批6g 拆件（wave6 §批6g）：R2 统一异常映射域伴生件（main_lib——
# 类基表+名义表+注册器）；DOMAIN_ERROR_CODES 再导出=test_app_factory
# 消费面零改动（app_assembly/app_enumeration_gates 再导出先例同构）。
from waterprint_server.main_lib import DOMAIN_ERROR_CODES, _register_exception_handlers
from waterprint_server.routers import (
    ai_chat,
    ai_config,
    ai_connection,
    calc,
    cost,
    debug,
    elevation,
    events,
    exports,
    projects,
    scene,
    site,
    solution,
    unit_detail,
    units,
)
from waterprint_server.services import ServiceContext
from waterprint_server.settings import (
    Settings,
    ensure_directories,
    get_settings,
    validate_data_packages,
)
from waterprint_server.sse_limits import SseLimiter

# 端点集冻结 5+7+5+2+1+1+2+1+1+1+1+1+3=31（白名单字面量和式[calc 6→7=FD design-map，
# A2-N-01 勘正]；+1=scene GET，FE1 D1；
# +1=elevation GET，FE7 D1；+2=units/assumptions GET，META1 D2——静态只读
# 目录两端点；+1=cost GET，FE8 D1；+1=constraints GET，CP1 D4；
# +1=site/spacing GET，L4b D1——间距校核取数端点；+1=exports/ifc POST，
# SC1 D7——BIM 模型导出端点，openapi 25→26 破面已授权；+1=exports/
# {file_name} GET，EXPD D4——产物下载端点，openapi 26→27 破面已授权
# [Ruling 2026-09-05 ②]；+1=calc/design-map POST，FD PD6——可行域引导
# 同步求值端点，openapi 27→28 破面已授权[Ruling 2026-09-09 序列批复①
# +常设指令]；+1+1+1=projects/{id}/copy POST+rename POST+{id} DELETE，
# P2 项目生命周期治理批——openapi 28→31 破面[常设指令推荐序沿册：
# op-chain-fix-plan §五+briefs/task-p2-lifecycle-plan.md]）
# +1=P2 次批 trust（GET /api/calc/trust/{project_id}——ADR-012 D8，2026-09-12）
# +1=P2 第三批 compare（GET /api/calc/compare/{project_id}——ADR-018 D5，
# 2026-09-12：多工况对比矩阵，32→33 破面[常设指令推荐序沿册]）
# +1+1=AI2（GET /api/ai/connection + POST /api/ai/connection/setup——MCP
# 一键接入面，2026-09-13：33→35 破面[AI2 任务书预裁决授权]）
# +1=B4-1（GET /api/debug/ops-chain/{project_id}——操作链集中 debug 观测面，
# 《裁决书》方案五①，2026-09-19：35→36 破面[裁决书批次编排批 4 授权]）
_EXPECTED_ENDPOINTS: Final[int] = (
    10
    + 10
    - 2
    + 1
    + 1
    + 2
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1
    + 1  # B4-3：POST /api/solution/joint-enumerate（联合枚举正门，36→37 破面
         # =ADR-025 决策 1——.workflow/b4-3/design-final.md 授权）
    + 2
    + 1  # B4-4b 子批 2：/api/ai/sessions 三端点（清单/历史/发言，37→40 破面
         # =.workflow/b4-4b/design-final.md §四授权）
    + 2 + 1  # F1 /api/ai/config 40→42〔brief-F1 §二授权〕；批6e sensitivity 42→43〔wave6 授权〕
    + 1  # 2A1：GET /api/calc/validation/{project_id}（校验观测+聚合消费面，43→44
         # 〔2a1-20261005 任务书 §3 D3/D4 预期 39 路径 44 操作授权〕）
    + 1  # B2 结果与方案批：GET /api/calc/projects/{project_id}/units/{unit_id}/
         # results（单单元明细切片——行模型=out_dims 服务端联表，44→45 破面
         # 〔b2-20261009 任务书 §二.①授权〕）
)
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
            structlog.get_logger(__name__).warning("task_sweep_round_failed", reason=repr(exc))


def _contract_self_check(app: FastAPI) -> None:
    """R3 契约自检：OpenAPI 生成成功 + 端点集==28（FD 起 calc6→7；漂移前置到启动期）。"""
    schema = app.openapi()
    operations = sum(len(methods) for methods in schema["paths"].values())
    if operations != _EXPECTED_ENDPOINTS:
        raise RuntimeError(
            f"契约自检失败：端点集 {operations} != {_EXPECTED_ENDPOINTS}"
            "（九路由器规格并集 projects5+calc7+exports6+events2+scene1"
            "+elevation1+units2+cost1+constraints1+site1——A1 锁定；SC1 ifc 增）"
        )


def create_app(  # noqa: PLR0915  # 装配根语句数=路由挂载面声明式展开（B4-4b 子批 2 +ai_chat 后 40→41，结构非逻辑面）
    settings: Settings, executor: Executor | None = None
) -> FastAPI:
    """应用工厂（可测试可重复构建——装配束挂 app.state 无全局可变态）。"""
    _configure_logging(settings)
    # B4-4b 门一 W1-k2 处置：AI 三键 env 单通道归一化（settings 含 .env 文件源
    # 时进程 env 缺位——worker 子进程桥只读 env；setdefault 不覆写既有值）。
    for _key, _value in (
        ("WATERPRINT_AI_BASE_URL", settings.ai_base_url),
        ("WATERPRINT_AI_API_KEY", settings.ai_api_key),
        ("WATERPRINT_AI_MODEL", settings.ai_model),
        ("WATERPRINT_AI_LLM_TIMEOUT_S", str(settings.ai_llm_timeout_s)),
    ):
        if _value:
            os.environ.setdefault(_key, _value)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        ensure_directories(settings)
        queue: mp.Queue[Any] = mp.Queue()
        pool = (
            executor
            if executor is not None
            else ProcessPoolExecutor(
                max_workers=settings.calc_workers,
                initializer=worker._init_progress_queue,  # noqa: SLF001  # 池 initializer 正门（R3 进度通路）
                initargs=(queue,),
            )
        )
        manager = Manager(
            pool,
            cancel_dir=settings.exports_dir / "tasks" / "cancel",
            registry_dir=settings.exports_dir / "tasks" / "registry",  # S2 D3：终态落盘+重启恢复
            artifacts_dir=settings.exports_dir / "tasks",  # WP4：calc/enum 产物淘汰面
            task_retention_s=settings.task_retention_s,  # WP4 修1：TTL 旋钮注入（启用清扫）
            task_registry_cap=settings.task_registry_cap,
            sse_heartbeat_seconds=settings.sse_heartbeat_seconds,  # B6 D6：SSE 心跳旋钮
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
            settings=settings,
            manager=manager,
            domain_error_codes=DOMAIN_ERROR_CODES,
            sse_limiter=SseLimiter.from_settings(settings),  # B6：四维限流器装配
        )
        _contract_self_check(app)
        yield
        sweeper.cancel()
        # WP4K G1-01：清扫任务若已带既往异常死亡，await 会重抛
        # 且 suppress 仅压 CancelledError——异常族之外的意外型仍可倒灌
        # lifespan。teardown 侧全谱压制（suppress(Exception) 不触 grep 门禁
        # 裸 except 拦截；正门续跑语义由 _sweep_periodically 异常族承担）。
        with suppress(asyncio.CancelledError, Exception):
            await sweeper
        await manager.shutdown(_SHUTDOWN_TIMEOUT)
        pool.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(title="WaterPrint 服务层", version="0.1.0", lifespan=lifespan)
    # R2A 批1（终裁 R-1/D3）：include 级鉴权依赖挂载——七业务路由器受保
    # （20 非事件操作仅认 Bearer），events 两 SSE 端点用双通道依赖（header
    # 或 ？token=）；units 三静态只读端点豁免（不挂）。端点集/路径/方法
    # 变化仅 SC1/EXPD 增量（_EXPECTED_ENDPOINTS=27 现值——契约自检常驻；
    # 旧注记「=24 恒」系 R2A 时点快照，SC1 顺带销注释漂移）。
    # B6 D3 必改1（依赖序）：events 挂载序=[sse_connect_gate,
    # verify_token_sse]——FastAPI include 级 dependencies 列表序执行
    # （0.141 实证），建连闸（速率令牌+全局阈探测）先于认证：401 风暴的
    # 建连消耗被 429 前置压制；闸零路径参=openapi 零波面。
    app.include_router(projects.router, dependencies=[Depends(verify_token)])
    app.include_router(calc.router, dependencies=[Depends(verify_token)])
    # B2 结果与方案批（2026-10-09）：单单元明细切片（GET /api/calc/
    # projects/{pid}/units/{uid}/results——路径前缀沿 calc 域，路由件独立
    # 挂载：calc 镜像测试端点集冻结断言=人类锁定面，扩挂 calc.router 必
    # 改锁定测试；Bearer 沿册同保）。
    app.include_router(unit_detail.router, dependencies=[Depends(verify_token)])
    # B4-3：联合枚举正门（/api/solution/joint-enumerate——Bearer 沿册同保）。
    app.include_router(solution.router, dependencies=[Depends(verify_token)])
    app.include_router(exports.router, dependencies=[Depends(verify_token)])
    app.include_router(
        events.router,
        dependencies=[Depends(events.sse_connect_gate), Depends(verify_token_sse)],
    )
    app.include_router(scene.router, dependencies=[Depends(verify_token)])
    app.include_router(elevation.router, dependencies=[Depends(verify_token)])
    app.include_router(cost.router, dependencies=[Depends(verify_token)])
    # L4b：site/spacing 鉴权族挂载（项目数据面——units 静态目录族外同保）
    app.include_router(site.router, dependencies=[Depends(verify_token)])

    # B4-1：操作链观测面（GET /api/debug/ops-chain——35→36，《裁决书》方案五①）
    app.include_router(debug.router, dependencies=[Depends(verify_token)])
    # AI2（2026-09-13）：AI 接入面挂载（状态检查+一键接入——Bearer 沿册同保）
    app.include_router(ai_connection.router, dependencies=[Depends(verify_token)])
    # B4-4b 子批 2（2026-09-24）：对话 pane 中继面挂载（会话清单/历史/发言
    # ——37→40 破面=.workflow/b4-4b/design-final.md §四授权）。
    app.include_router(ai_chat.router, dependencies=[Depends(verify_token)])
    # F1（healthcheck-20260925 2026-09-25）：LLM 配置面挂载（GET/PUT
    # /api/ai/config——40→42 破面=brief-F1-ai-config.md §二授权；Bearer 同保）。
    app.include_router(ai_config.router, dependencies=[Depends(verify_token)])
    # units 豁免面契约明示（R-3）：三操作显式 security=[]（公开面明示，
    # 区别于未声明）——FastAPI include 面无 security 参数，经路由对象
    # openapi_extra 直挂（0.141 实证：include 后 app.routes 为包装件，
    # 真源在 router.routes）。
    for units_route in (route for route in units.router.routes if isinstance(route, APIRoute)):
        units_route.openapi_extra = {"security": []}
    app.include_router(units.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_DEV_ORIGINS),  # R5 开发期白名单
        allow_methods=["*"],
        # N-2（R2A 批1）：Authorization 已覆盖——["*"] 通配回显预检 Headers（dev 5173 不断）。
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _edge_headers(request: Request, call_next: Callable[..., Any]) -> Any:
        """R5 请求 ID（响应头回写+structlog 绑定）；C-2：/api/ GET/HEAD 读面 no-store。"""
        identifier = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=identifier)
        response = await call_next(request)
        response.headers["X-Request-ID"] = identifier
        # C-2：GET/HEAD+/api/ 禁缓存（收编单点；HEAD 防御纵深——APIRoute 实测 405）。
        if request.method in ("GET", "HEAD") and request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
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
    # E2E-1（e2e-audit 2026-09-24 P0-A）：启动 fail-fast——四数据包 manifest
    # 在场校验先于 uvicorn（缺包=可执行文案拒绝启动，非 500 晚拒在用户脸上）。
    validate_data_packages(_settings)
    # R-1（G1-01）：传已建 app 对象非字符串路径——python -m 启动时模块以 __main__
    # 身份已执行，字符串路径会再 import 实名模块一遍=双 app 实例（无 reload 收益）。
    uvicorn.run(app, host=_settings.host, port=_settings.port)
