"""dxf_writer 镜像测试：ezdxf 唯一接触点（R2018/UTF-8/确定性/路径安全）。

输入:  waterprint.drafting.dxf_writer 公开符号
输出:  落盘契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.dxf_writer")
write_dxf = getattr(_mod, "write_dxf", None)

pytestmark = pytest.mark.skipif(
    write_dxf is None,
    reason="实现未就绪：waterprint.drafting.dxf_writer（M2）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：write_dxf(entities, styles, out, meta)。"""
    assert callable(write_dxf)


def test_path_traversal_rejected_wiring() -> None:
    """R4 接线断言：输出路径含 ../ 或绝对路径分量 → 领域异常（安全门）。"""
    raise AssertionError(
        "M2 接线断言：构造越界 out 路径断言拒绝——不得删除（§18 路径安全）"
    )


def test_byte_determinism_wiring() -> None:
    """R3 接线断言：同实体组双跑落盘字节级相同（时钟进 meta 不进文件头）。"""
    raise AssertionError(
        "M2 接线断言：最小实体组双跑字节相同——不得删除（快照回归前提）"
    )
