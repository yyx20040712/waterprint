"""app 镜像测试：用例编排（装配失败清单/双跑 diff=0/三元组传播——golden 承载）。

输入:  waterprint.app 公开符号
输出:  编排契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.app")
run_full_calc = getattr(_mod, "run_full_calc", None)
assemble = getattr(_mod, "assemble", None)

pytestmark = pytest.mark.skipif(
    None in (run_full_calc, assemble),
    reason="实现未就绪：waterprint.app（M1 三单元切片）",
)


def test_entrypoints_frozen() -> None:
    """入口冻结：assemble(project, env) / run_full_calc(project, conditions, env)。"""
    assert callable(assemble)
    assert callable(run_full_calc)


def test_double_run_byte_identical_wiring() -> None:
    """R3 接线断言：同 (project, conditions, env) 双跑序列化字节相同。

    与 golden 端到端互补：golden 给数值对照，本断言给可复算性。
    """
    raise AssertionError(
        "M1 接线断言：三单元切片双跑 diff=0——不得删除（§3 保证 6）"
    )
