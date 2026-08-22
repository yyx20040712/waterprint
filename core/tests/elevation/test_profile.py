"""profile 镜像测试：沿程推算（纵断连续性、工况索引、超高来源、越界警告）。

输入:  waterprint.elevation.profile 公开符号
输出:  纵断语义断言（详细数值 golden 归 M2 市政案例）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.elevation.profile")
build_profile = getattr(_mod, "build_profile", None)

pytestmark = pytest.mark.skipif(
    build_profile is None,
    reason="实现未就绪：waterprint.elevation.profile（M2）",
)


def test_build_profile_is_the_single_entry() -> None:
    """入口冻结：build_profile(plant_result, losses, inlet_config, assumptions, condition_key)。"""
    assert callable(build_profile)


def test_water_level_continuity_contract_is_specified() -> None:
    """R1 连续性断言接线位：下游水面 <= 上游水面 − 损失。

    需要三单元图结果（M2 市政 golden）后接线；实现者不得删除。
    """
    raise AssertionError(
        "M2 接线断言：构造线性三单元纵断，断言每相邻站 "
        "water_level[i+1] <= water_level[i] - losses[i]——不得删除"
    )
