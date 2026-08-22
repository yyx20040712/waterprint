"""cli 镜像测试：命令行入口（退出码语义/new-unit 幂等保护/编码防线）。

输入:  waterprint.cli.main 公开符号
输出:  CLI 契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.cli")
main = getattr(_mod, "main", None)

pytestmark = pytest.mark.skipif(
    main is None,
    reason="实现未就绪：waterprint.cli（M1）",
)


def test_exit_code_semantics_wiring() -> None:
    """R1 接线断言：0 成功 / 2 用法错误 / 3 校验失败 / 4 计算失败。"""
    raise AssertionError(
        "M1 接线断言：无参调用断言退出码 2；坏项目文件断言 3——不得删除"
    )


def test_new_unit_refuses_existing_target_wiring() -> None:
    """R2 接线断言：目标单元包已存在 = 拒绝（防误覆盖）。"""
    raise AssertionError(
        "M1 接线断言：对 _template 再生成 'test_demo' 两次，第二次拒绝——不得删除"
    )
