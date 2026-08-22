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
# 【测试要求】工厂可重复构建（无全局状态）、生命周期启停、
#   异常映射表完整性、（实现后）契约自检失败路径。
#
# 【参照】重写计划 §12.2/§13.4/§15/§16 A5/§18
# ══════════════════════════════════════════════════════════════════
