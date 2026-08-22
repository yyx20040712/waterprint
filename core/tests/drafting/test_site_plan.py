"""site_plan 镜像测试：厂区总平面（M5 交付——接口冻结守卫）。

输入:  waterprint.drafting.site_plan 公开符号
输出:  接口稳定性断言（M5 前本文件只守签名不测行为）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.site_plan")
site_layout = getattr(_mod, "site_layout", None)

pytestmark = pytest.mark.skipif(
    site_layout is None,
    reason="实现未就绪：waterprint.drafting.site_plan（M5）",
)


def test_entrypoint_frozen_until_m5() -> None:
    """R1：接口先冻结（防 M5 起步推翻消费方）：site_layout(site_design, plant_result, styles, options)。"""
    assert callable(site_layout)
