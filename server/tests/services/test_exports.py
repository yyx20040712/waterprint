"""exports 服务镜像测试：stale 守门、确定性命名、批量转任务。

输入:  waterprint_server.services.exports 公开符号
输出:  服务契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.exports")
create_export = getattr(_mod, "create_export", None)
list_exports = getattr(_mod, "list_exports", None)

pytestmark = [
    pytest.mark.skipif(
        None in (create_export, list_exports),
        reason="实现未就绪：waterprint_server.services.exports（服务层 M2/M3）",
    ),
]


def test_export_filename_is_deterministic_wiring() -> None:
    """R4 接线断言：同输入两次导出产物同名（无时钟进文件名，幂等覆盖）。"""
    raise AssertionError(
        "M2/M3 接线断言：同三元组两次 create_export 产物路径相同——不得删除"
    )


def test_forced_export_of_stale_result_is_labeled_wiring() -> None:
    """R1 接线断言：force 导出旧结果的产物名/元数据显式标注旧三元组。"""
    raise AssertionError(
        "M2/M3 接线断言：force 导出的元数据含输入三元组且与当前不同——不得删除"
    )
