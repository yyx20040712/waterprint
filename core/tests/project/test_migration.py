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
_io = importlib.import_module("waterprint.project.io")
InvalidProjectError = getattr(_io, "InvalidProjectError", None)

pytestmark = pytest.mark.skipif(
    None in (migrate, SUPPORTED_VERSIONS),
    reason="实现未就绪：waterprint.project.migration（M1）",
)


def test_supported_versions_form_a_chain_from_current() -> None:
    """R1：版本序列非空且含当前版（链式结构前提）。"""
    assert SUPPORTED_VERSIONS
    assert SUPPORTED_VERSIONS[-1] == "2.0"


def test_future_version_rejected_wiring() -> None:
    """R3 接线断言：format_version > 当前 → 拒绝（不降级打开）。"""
    with pytest.raises(InvalidProjectError, match="999.0"):
        migrate({"format_version": "999.0", "design": {}, "view": {},
                 "metadata": {"content_hash": "0" * 64,
                              "engine_version": "0.1.0",
                              "data_version": "coefficients@0.1.0"}})


def test_unmappable_field_rejected_wiring() -> None:
    """R2 接线断言：语义不明字段 → 领域异常指明路径（禁止猜测性默认）。"""
    # v1 产品首发无历史迁移链：含未知旧字段的样本以"未知历史版本"拒
    # 语义落（T7a D8 裁决——0.9 不在合法序列，无从映射）。
    with pytest.raises(InvalidProjectError, match="未知历史版本"):
        migrate({"format_version": "0.9", "legacy_field": "旧字段样本"})
