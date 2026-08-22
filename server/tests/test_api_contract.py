"""API 契约测试：路由存在性/方法/响应骨架（OpenAPI 单一事实源的测试侧守卫）。

输入:  create_app 产出的 OpenAPI schema（实现后）
输出:  契约结构断言（端点集与 §13.4 四路由器规格一致）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；休眠测试——app 实现后激活）
#
# 覆盖用例（实现后必须全部转绿，skip 数归零）：
#   A1 OpenAPI 生成成功且端点集 == 四路由器规格的并集
#      （projects 5 + calc 6 + exports 5 + events 2）；
#   A2 每端点有请求/响应 schema（无 Any 泄漏）；
#   A3 错误响应模型统一（领域异常映射表齐全）；
#   A4 /api/projects/{id} 越界 id（../、绝对路径）→ 4xx 非 500。
#
# 休眠机制：与 core 测试同款 getattr 守卫（waterprint_server.main
#   的 create_app 缺失即 skip 并注明原因）。
# ══════════════════════════════════════════════════════════════════

import importlib

import pytest

_main = importlib.import_module("waterprint_server.main")
_CREATE_APP = getattr(_main, "create_app", None)

pytestmark = pytest.mark.skipif(
    _CREATE_APP is None,
    reason="实现未就绪：waterprint_server.main.create_app（服务层 M2 起实现）",
)


def test_openapi_endpoint_set(client) -> None:
    """A1：端点集与路由器规格一致（防止端点漂移无测试感知）。"""
    raise AssertionError("实现后替换为真实断言（红-绿：先写失败断言再实现）")


def test_openapi_schema_no_any_leak(client) -> None:
    """A2：请求/响应 schema 完整，无 Any 类型字段。"""
    raise AssertionError("实现后替换为真实断言")


def test_error_model_complete(client) -> None:
    """A3：领域异常 → HTTP 映射表完整。"""
    raise AssertionError("实现后替换为真实断言")


def test_project_id_path_traversal_rejected(client) -> None:
    """A4：路径穿越 id 拒绝（安全门）。"""
    raise AssertionError("实现后替换为真实断言")
