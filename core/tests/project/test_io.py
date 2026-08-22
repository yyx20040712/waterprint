"""io 镜像测试：项目文件确定性序列化（双跑字节相同/往返无损/防弹加载）。

输入:  waterprint.project.io 公开符号 + 最小项目数据
输出:  序列化契约断言（ADR-004 核心）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.project.io")
save_project = getattr(_mod, "save_project", None)
load_project = getattr(_mod, "load_project", None)
dumps = getattr(_mod, "dumps", None)
loads = getattr(_mod, "loads", None)

pytestmark = pytest.mark.skipif(
    None in (save_project, load_project, dumps, loads),
    reason="实现未就绪：waterprint.project.io（M1）",
)


def test_double_save_is_byte_identical_wiring() -> None:
    """R1 接线断言：同对象两次 dumps 字节级相同（键排序/定点浮点/无时钟）。"""
    raise AssertionError(
        "M1 接线断言：构造最小项目（含浮点参数），dumps 两次比较字节——不得删除"
    )


def test_roundtrip_lossless_wiring() -> None:
    """R2 接线断言：save→load→save 字节相同。"""
    raise AssertionError(
        "M1 接线断言：tmp_path 落盘往返字节一致——不得删除"
    )


def test_malformed_input_rejected_wiring() -> None:
    """R3 接线断言：未知字段/超深 JSON 拒绝且错误消息含字段路径。"""
    raise AssertionError(
        "M1 接线断言：构造未知字段 JSON 断言拒绝与路径消息——不得删除（§18）"
    )
