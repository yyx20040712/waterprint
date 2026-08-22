"""projects 路由镜像测试：CRUD 端点（薄层、路径安全、写锁）。

输入:  waterprint_server.routers.projects 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.routers.projects")
router = getattr(_mod, "router", None)

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.projects（服务层 M2）",
    ),
]


def test_router_exposes_five_endpoints_wiring() -> None:
    """端点集 == 规格五件（POST/GET/GET/PUT/POST validate）。"""
    raise AssertionError(
        "M2 接线断言：OpenAPI 中本路由端点路径与规格一致——不得删除（防端点漂移）"
    )


def test_project_id_traversal_rejected_wiring() -> None:
    """R1 接线断言：{id} 含 ../ 或绝对路径 → 4xx 非 500（§18）。"""
    raise AssertionError(
        "M2 接线断言：client.put('/api/projects/..%2Fevil', ...) 返回 4xx——不得删除"
    )
