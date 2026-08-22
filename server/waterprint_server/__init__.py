"""WaterPrint 服务层包根：HTTP 编排，业务在 core（本包零计算）。

输入:  HTTP 请求（经 routers）/ 任务参数（经 jobs）
输出:  ASGI 应用（main 正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【分层规则（§13.4）】
#   routers → services → jobs；service 只调 core L4（app.py）；
#   router 禁业务逻辑（≤150 行）；service 禁 import fastapi；
#   job 只做序列化与调用 core。
# 【契约自检】启动时 OpenAPI 与 core pydantic 模型一致性检查
#   （契约漂移前置到启动期，§15 工程细节 5）。
# ══════════════════════════════════════════════════════════════════
