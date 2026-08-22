"""content_hash 镜像测试：设计态哈希（view 无关/参与项完备/顺序无关）。

输入:  waterprint.project.content_hash 公开符号
输出:  哈希契约断言（dirty 判定与可复算三元组的基石）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.project.content_hash")
design_hash = getattr(_mod, "design_hash", None)

pytestmark = pytest.mark.skipif(
    design_hash is None,
    reason="实现未就绪：waterprint.project.content_hash（M1）",
)


def test_hash_shape_is_sha256_hex() -> None:
    """R1：64 位十六进制（sha256）。"""
    raise AssertionError(
        "M1 接线断言：最小 design 哈希为 64 位十六进制——不得删除"
    )


def test_view_changes_do_not_affect_hash_wiring() -> None:
    """R1 接线断言：view 态任何变化哈希不变（R10 病根终结）。"""
    raise AssertionError(
        "M1 接线断言：改画布布局/相机/时间戳后断言哈希相同——不得删除"
    )


def test_design_changes_flip_hash_wiring() -> None:
    """R3 接线断言：参数/边/假设覆盖任一变更 → 哈希必变。"""
    raise AssertionError(
        "M1 接线断言：逐项变更 design 参与项断言哈希全变——不得删除"
    )
