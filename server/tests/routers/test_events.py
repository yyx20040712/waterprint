"""events 路由镜像测试：SSE 端点（响应头、断连清理、背压）。

输入:  waterprint_server.routers.events 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.routers.events")
router = getattr(_mod, "router", None)

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.events（服务层 M2）",
    ),
]


def test_router_exposes_two_streams_wiring() -> None:
    """端点集 == 规格两件（tasks/{id} 与 projects/{id}）。"""
    raise AssertionError(
        "M2 接线断言：两个 SSE 端点存在且响应头含 X-Accel-Buffering: no"
        "（§11 R5 反代缓冲对策）——不得删除"
    )


def test_client_disconnect_releases_subscription_wiring() -> None:
    """R1 接线断言：断连后订阅释放（无句柄泄漏）。"""
    raise AssertionError(
        "M2 接线断言：断开 SSE 连接后 Manager 无残留订阅——不得删除"
    )
