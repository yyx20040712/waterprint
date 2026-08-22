"""section_view 镜像测试：单体剖面图（三线齐备/标高同源/剖切联动接线）。

输入:  waterprint.drafting.section_view 公开符号
输出:  剖面图契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.section_view")
unit_section = getattr(_mod, "unit_section", None)

pytestmark = pytest.mark.skipif(
    unit_section is None,
    reason="实现未就绪：waterprint.drafting.section_view（M2）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：unit_section(unit_result, profile_station, styles, condition_key, options)。"""
    assert callable(unit_section)


def test_three_lines_wiring() -> None:
    """R2 接线断言：水面/池底/地面三线实体存在且值 == Profile（M2 后接线）。"""
    raise AssertionError(
        "M2 接线断言：剖面图三线实体存在且标高取自 ElevationProfile——不得删除"
    )
