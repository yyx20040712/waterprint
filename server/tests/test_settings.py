"""settings 镜像测试：环境配置（路径基点字段、fail-fast 校验）。

输入:  waterprint_server.settings 公开符号
输出:  配置契约断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from pydantic import ValidationError

_mod = importlib.import_module("waterprint_server.settings")
Settings = getattr(_mod, "Settings")
get_settings = getattr(_mod, "get_settings")
safe_child = getattr(_mod, "safe_child")
ensure_directories = getattr(_mod, "ensure_directories")

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
    assert get_settings() is get_settings()  # lru_cache 单例（测试可 cache_clear 覆盖）


def test_zero_workers_rejected_wiring() -> None:
    """R2 接线断言：calc_workers < 1 启动即失败（fail fast 不静默默认）。"""
    with pytest.raises(ValidationError):
        Settings(calc_workers=0)
    assert Settings(calc_workers=1).calc_workers == 1  # 合法下限过（1=白名单值）


def test_path_component_whitelist_rejects_traversal() -> None:
    """R1 消费方行为：safe_child 拒 ../、绝对路径、分隔符注入（§18 路径安全）。"""
    base = Path("base")
    assert safe_child(base, "proj_1").parent == base
    for evil in ("..", "../evil", "/abs", "a/b", "", "C:" + chr(92) + "x", "a b"):
        with pytest.raises(ValueError, match="路径分量非法"):
            safe_child(base, evil)
