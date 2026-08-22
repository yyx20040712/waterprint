"""projects 服务镜像测试：保存语义（design_changed）、导入完整性。

输入:  waterprint_server.services.projects 公开符号
输出:  服务契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.projects")
save_project = getattr(_mod, "save_project", None)
import_legacy = getattr(_mod, "import_legacy", None)

pytestmark = [
    pytest.mark.skipif(
        None in (save_project, import_legacy),
        reason="实现未就绪：waterprint_server.services.projects（服务层 M2/M4）",
    ),
]


def test_view_only_save_reports_no_design_change_wiring() -> None:
    """R2 接线断言：仅改 view 态的保存 design_changed=False（§17.1）。"""
    raise AssertionError(
        "M2 接线断言：改画布布局后保存，SaveOutcome.design_changed 为 False——不得删除"
    )


def test_legacy_import_lists_unmapped_fields_wiring() -> None:
    """R3 接线断言：旧格式导入的未映射字段清单完整返回（禁止静默丢弃）。"""
    raise AssertionError(
        "M4 接线断言：含未知字段的旧项目导入，ImportReport.unmapped 非空——不得删除"
    )
