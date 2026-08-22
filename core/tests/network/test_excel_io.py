"""excel_io 镜像测试：管网 Excel 读写（模板往返/错误带行号/上限防弹接线）。

输入:  waterprint.network.excel_io 公开符号
输出:  读写契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.network.excel_io")
read_network_excel = getattr(_mod, "read_network_excel", None)
write_result_sheet = getattr(_mod, "write_result_sheet", None)

pytestmark = pytest.mark.skipif(
    None in (read_network_excel, write_result_sheet),
    reason="实现未就绪：waterprint.network.excel_io（M3）",
)


def test_entrypoints_frozen() -> None:
    """入口冻结：read_network_excel(path) / write_result_sheet(path, design)。"""
    assert callable(read_network_excel)
    assert callable(write_result_sheet)


def test_template_roundtrip_wiring() -> None:
    """R1 接线断言：读→写→重读一致（模板列位映射不漂移）。"""
    raise AssertionError(
        "M3 接线断言：构造最小管网模板文件往返一致——不得删除"
    )
