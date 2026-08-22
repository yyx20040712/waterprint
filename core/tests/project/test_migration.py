"""migration 镜像测试：版本迁移链（链式到达/未来版拒绝/不可迁移拒绝）。

输入:  waterprint.project.migration 公开符号
输出:  迁移链契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.project.migration")
migrate = getattr(_mod, "migrate", None)
SUPPORTED_VERSIONS = getattr(_mod, "SUPPORTED_VERSIONS", None)

pytestmark = pytest.mark.skipif(
    None in (migrate, SUPPORTED_VERSIONS),
    reason="实现未就绪：waterprint.project.migration（M1）",
)


def test_supported_versions_form_a_chain_from_current() -> None:
    """R1：版本序列非空且含当前版（链式结构前提）。"""
    assert SUPPORTED_VERSIONS
    assert SUPPORTED_VERSIONS[-1] == "1.0"


def test_future_version_rejected_wiring() -> None:
    """R3 接线断言：format_version > 当前 → 拒绝（不降级打开）。"""
    raise AssertionError(
        "M1 接线断言：构造 'format_version': '999.0' 断言拒绝——不得删除"
    )


def test_unmappable_field_rejected_wiring() -> None:
    """R2 接线断言：语义不明字段 → 领域异常指明路径（禁止猜测性默认）。"""
    raise AssertionError(
        "M1 接线断言：构造含未知旧字段的样本断言拒绝——不得删除"
    )
