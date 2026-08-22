"""plan_view 镜像测试：单体平面图（标注完备/工况标注/纯投影接线）。

输入:  waterprint.drafting.plan_view 公开符号
输出:  平面图契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.plan_view")
unit_plan = getattr(_mod, "unit_plan", None)

pytestmark = pytest.mark.skipif(
    unit_plan is None,
    reason="实现未就绪：waterprint.drafting.plan_view（M2）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：unit_plan(unit_result, manifest, styles, condition_key, options)。"""
    assert callable(unit_plan)


def test_annotation_completeness_wiring() -> None:
    """R3 接线断言：总尺寸/分格尺寸/标高符号标注实体存在（M2 首批单元后接线）。"""
    raise AssertionError(
        "M2 接线断言：已知矩形池平面含总尺寸/分格/标高标注实体——不得删除"
    )
