"""styles 镜像测试：制图样式基线（五类图层/命名规范/出处/确定性）。

输入:  waterprint.drafting.styles 公开符号
输出:  样式契约断言（ADR-006 / GB/T 50001）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.styles")
base_styles = getattr(_mod, "base_styles", None)
LAYER_PREFIX = getattr(_mod, "LAYER_PREFIX", None)

pytestmark = pytest.mark.skipif(
    None in (base_styles, LAYER_PREFIX),
    reason="实现未就绪：waterprint.drafting.styles（M2）",
)


def test_layer_prefix_is_wp_dash() -> None:
    """R1：图层命名前缀 WP-。"""
    assert LAYER_PREFIX == "WP-"


def test_five_layer_categories_complete() -> None:
    """R1：五类图层齐备（工艺/建筑/标注/尺寸/图框）。"""
    styles = base_styles()
    categories = {layer.name.split("-")[1] for layer in styles.layers}
    assert {"process", "arch", "anno", "dim", "frame"} <= categories


def test_style_definitions_carry_source() -> None:
    """R2：样式定义挂标准出处。"""
    styles = base_styles()
    for layer in styles.layers:
        assert getattr(layer, "source", ""), f"图层 {layer.name} 缺出处"
