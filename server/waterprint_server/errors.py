"""统一错误体的类型化声明（PL-03 契约枚举——GOV5 治理余账批）。

输入:  无（纯 pydantic 模型件——main._make_handler 运行时构造同形态体）
输出:  ErrorResponse（{detail, error_type}——openapi responses 声明面）

规格说明（PL-03 两笔挂账收口：n+41 lifecycle 404/409 枚举+n+42 trust
  404 增量）：
  - 运行时行为零变化——本件只服务 openapi 契约声明（端点 responses=
    {404/409: {"model": ErrorResponse}} 使文档与 _EXCEPTION_STATUS
    映射的实际行为一致）；响应体构造仍在 main._make_handler 唯一翻译
  处（禁散落）；
  - 声明面范围=PL-03 点名的 lifecycle 三端点（rename/copy/delete
    404+409）+trust 端点（404——行为面已测 n+42）；其余端点的 404
  统一枚举挂账（行为测试面未全覆盖，不宜只加声明）；
  - orval 消费面：includeHttpResponseReturnType=false（GOV5-1）下
    错误模型仅入 components.schemas，GET 返回类型不变。
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """统一错误体（{detail, error_type}——R2 起冻结形态）。"""

    detail: str
    error_type: str
