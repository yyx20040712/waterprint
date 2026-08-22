"""exports 路由镜像测试：导出端点（stale 守门、文件名安全）。

输入:  waterprint_server.routers.exports 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.routers.exports")
router = getattr(_mod, "router", None)

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.exports（服务层 M2/M3）",
    ),
]


def test_router_exposes_five_endpoints_wiring() -> None:
    """端点集 == 规格五件（calcbook/audit/dxf/estimate/列表）。"""
    raise AssertionError(
        "M2/M3 接线断言：端点路径与规格一致——不得删除"
    )


def test_stale_result_returns_409_with_context_wiring() -> None:
    """R1 接线断言：结果集三元组过期且未 force → 409 附输入版本信息。"""
    raise AssertionError(
        "M2/M3 接线断言：构造 stale 场景断言 409 与三元组摘要——不得删除"
    )
