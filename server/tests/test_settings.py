"""settings 镜像测试：环境配置（路径基点字段、fail-fast 校验）。

输入:  waterprint_server.settings 公开符号
输出:  配置契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.settings")
Settings = getattr(_mod, "Settings", None)
get_settings = getattr(_mod, "get_settings", None)

pytestmark = [
    pytest.mark.skipif(
        None in (Settings, get_settings),
        reason="实现未就绪：waterprint_server.settings（服务层 M2）",
    ),
]


def test_settings_exposes_path_and_limit_fields() -> None:
    """路径基点 + 上限字段齐备（§18 安全面与 §17.2 缓存上限的配置载体）。"""
    names = set(getattr(Settings, "model_fields", {}))
    assert {
        "projects_dir", "exports_dir", "data_dir", "calc_workers",
        "max_upload_mb", "max_excel_rows",
    } <= names


def test_zero_workers_rejected_wiring() -> None:
    """R2 接线断言：calc_workers < 1 启动即失败（fail fast 不静默默认）。"""
    raise AssertionError(
        "M2 接线断言：Settings(calc_workers=0, ...) 构造抛 ValidationError——不得删除"
    )
