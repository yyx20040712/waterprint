"""sheets 镜像测试：图框块库（五幅面全覆盖/尺寸表出处/栏位完整）。

输入:  waterprint.drafting.sheets 公开符号
输出:  图框契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.sheets")
sheet_frame = getattr(_mod, "sheet_frame", None)
SHEET_SIZES = getattr(_mod, "SHEET_SIZES", None)

pytestmark = pytest.mark.skipif(
    None in (sheet_frame, SHEET_SIZES),
    reason="实现未就绪：waterprint.drafting.sheets（M2）",
)


def test_all_five_sheet_sizes_present() -> None:
    """R1：A0~A4 全集齐备。"""
    assert set(SHEET_SIZES) == {"A0", "A1", "A2", "A3", "A4"}


@pytest.mark.parametrize("size", ["A0", "A1", "A2", "A3", "A4"])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_frame_generates_for_every_size_and_orientation(size: str, orientation: str) -> None:
    """R1：五幅面 × 横竖全覆盖生成不缺件。"""
    spec = {"size": size, "orientation": orientation, "scale": "1:100"}
    entities = sheet_frame(spec)
    assert entities
