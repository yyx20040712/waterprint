"""pumps 镜像测试：提升判定（跌水警告、自流空计划、扬程不等式、工况标注）。

输入:  waterprint.elevation.pumps 公开符号
输出:  判定语义断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.elevation.pumps")
evaluate_pumping = getattr(_mod, "evaluate_pumping", None)

pytestmark = pytest.mark.skipif(
    evaluate_pumping is None,
    reason="实现未就绪：waterprint.elevation.pumps（M2）",
)


def test_evaluate_pumping_is_the_single_entry() -> None:
    """入口冻结：evaluate_pumping(profile, assumptions) -> PumpingPlan。"""
    assert callable(evaluate_pumping)


def test_gravity_flow_yields_empty_stations_and_no_warnings() -> None:
    """R4：全程自流 = 空站位列表是合法结果（非异常）。

    需要可构造的 ElevationProfile（M2）后接线；实现者不得删除。
    """
    raise AssertionError(
        "M2 接线断言：构造自流纵断，断言 stations 为空且 drop_warnings 为空"
        "——不得删除"
    )
