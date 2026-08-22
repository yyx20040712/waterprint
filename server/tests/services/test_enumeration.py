"""enumeration 服务镜像测试：单单元守护、分页白名单、arrow 重载。

输入:  waterprint_server.services.enumeration 公开符号
输出:  服务契约断言（ADR-005 的服务侧强制）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.enumeration")
submit_enumeration = getattr(_mod, "submit_enumeration", None)
fetch_solutions = getattr(_mod, "fetch_solutions", None)

pytestmark = [
    pytest.mark.skipif(
        None in (submit_enumeration, fetch_solutions),
        reason="实现未就绪：waterprint_server.services.enumeration（服务层 M2）",
    ),
]


def test_multi_unit_request_rejected_wiring() -> None:
    """R1 接线断言：多 unit_id 请求 422（防语义滑坡成全厂枚举）。"""
    raise AssertionError(
        "M2 接线断言：携带两个 unit_id 的枚举请求被拒绝——不得删除（ADR-005）"
    )


def test_infeasible_enumeration_is_done_not_failed_wiring() -> None:
    """R4 接线断言：无解枚举任务终态 done + feasible_count=0（非 failed）。"""
    raise AssertionError(
        "M2 接线断言：全 False 约束的枚举任务状态 done 且诊断端点可用——不得删除"
    )
