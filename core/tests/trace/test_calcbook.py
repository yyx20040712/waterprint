"""calcbook 镜像测试：计算书渲染（占位符零残留/模板禁公式/确定性接线）。

输入:  waterprint.trace.calcbook 公开符号
输出:  渲染契约断言（§11 R12——模板只展示，计算在 Python）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.trace.calcbook")
render_calcbook = getattr(_mod, "render_calcbook", None)

pytestmark = pytest.mark.skipif(
    render_calcbook is None,
    reason="实现未就绪：waterprint.trace.calcbook（M1）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：render_calcbook(trace, result, template, out)。"""
    assert callable(render_calcbook)


def test_no_marker_residue_wiring() -> None:
    """R1 接线断言：渲染产物中模板标记零残留。"""
    raise AssertionError(
        "M1 接线断言：最小模板渲染后无 {{field_id}} 残留——不得删除"
    )


def test_formula_template_rejected_wiring() -> None:
    """R2 接线断言：含 Excel 公式的模板加载即失败。"""
    raise AssertionError(
        "M1 接线断言：构造含公式单元格模板断言拒绝——不得删除（R12）"
    )
