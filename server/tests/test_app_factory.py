"""应用工厂镜像测试：生命周期、异常映射、契约自检。

输入:  waterprint_server.main 公开符号
输出:  工厂契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.main")
create_app = getattr(_mod, "create_app", None)

pytestmark = [
    pytest.mark.skipif(
        create_app is None,
        reason="实现未就绪：waterprint_server.main.create_app（服务层 M2）",
    ),
]


def test_factory_repeats_without_global_state_wiring() -> None:
    """R1 接线断言：create_app 两次构建互不污染（可测试工厂）。"""
    raise AssertionError(
        "M2 接线断言：连续两次 create_app，路由数/异常映射一致且独立——不得删除"
    )


def test_domain_exception_mapping_complete_wiring() -> None:
    """R2 接线断言：领域异常映射表覆盖核心异常（400/404/422）。"""
    raise AssertionError(
        "M2 接线断言：InvalidUnitConfig→400、NotFound→404、LoopDivergence→422"
        "（附诊断体）——不得删除"
    )
