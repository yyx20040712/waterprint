"""pools 镜像测试：池体图元（尺寸同源/水面高程/n_active 排布接线）。

输入:  waterprint.geometry.pools 公开符号
输出:  池体图元契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.geometry.pools")
pool_primitives = getattr(_mod, "pool_primitives", None)

pytestmark = pytest.mark.skipif(
    pool_primitives is None,
    reason="实现未就绪：waterprint.geometry.pools（M2）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：pool_primitives(unit_result, assumptions)。"""
    assert callable(pool_primitives)


def test_no_recomputation_wiring() -> None:
    """R1 接线断言：图元尺寸 == 结果字段值（几何层零业务公式）。"""
    raise AssertionError(
        "M2 接线断言：构造池长宽深结果，断言盒体 dims 逐项相等——不得删除"
    )
