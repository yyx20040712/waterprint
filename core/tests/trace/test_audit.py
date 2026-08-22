"""audit 镜像测试：审计报告（结构完整/转义/自包含/确定性接线）。

输入:  waterprint.trace.audit 公开符号
输出:  报告契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.trace.audit")
render_audit_html = getattr(_mod, "render_audit_html", None)

pytestmark = pytest.mark.skipif(
    render_audit_html is None,
    reason="实现未就绪：waterprint.trace.audit（M4）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：render_audit_html(trace, result, out)。"""
    assert callable(render_audit_html)


def test_escapes_user_controlled_text_wiring() -> None:
    """R2 接线断言：恶意单元名（含 <script>）被转义。"""
    raise AssertionError(
        "M4 接线断言：含 <script> 的单元名渲染后不出现原始标签——不得删除（§18）"
    )
