"""profile_drawing 镜像测试：高程纵断图（四线/比例分设/工况标注接线）。

输入:  waterprint.drafting.profile_drawing 公开符号
输出:  纵断图契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.profile_drawing")
profile_sheet = getattr(_mod, "profile_sheet", None)

pytestmark = pytest.mark.skipif(
    profile_sheet is None,
    reason="实现未就绪：waterprint.drafting.profile_drawing（M5）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：profile_sheet(profile, styles, options)（横纵比例分设）。"""
    assert callable(profile_sheet)


def test_four_lines_wiring() -> None:
    """R1 接线断言：地面/水面/池底/管底四线实体存在且值 == Profile（M5 后接线）。"""
    raise AssertionError(
        "M5 接线断言：纵断图四线实体存在且标高取自 ElevationProfile——不得删除"
    )
