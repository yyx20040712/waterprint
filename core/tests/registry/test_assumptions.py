"""assumptions 镜像测试：设计假设清单唯一真源（默认值显性化——病灶根治点）。

输入:  waterprint.registry.assumptions 公开符号
输出:  优先级/出处门槛/覆盖语义断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.registry.assumptions")
Assumption = getattr(_mod, "Assumption", None)
assumption = getattr(_mod, "assumption", None)
DEFAULT_ASSUMPTIONS = getattr(_mod, "DEFAULT_ASSUMPTIONS", None)

pytestmark = pytest.mark.skipif(
    None in (Assumption, assumption, DEFAULT_ASSUMPTIONS),
    reason="实现未就绪：waterprint.registry.assumptions（M1）",
)


def test_default_assumptions_all_have_source() -> None:
    """R2：每条默认假设必须带出处（无出处不准入库）。"""
    for item in DEFAULT_ASSUMPTIONS:
        assert item.source, f"假设 {item.key} 缺出处"
        assert item.note, f"假设 {item.key} 缺影响说明"


def test_override_takes_precedence_over_default() -> None:
    """R1：项目覆盖值优先于默认值。"""
    target = DEFAULT_ASSUMPTIONS[0]
    value = assumption(target.key, {target.key: target.default + 1.0})
    assert value == pytest.approx(target.default + 1.0)


def test_unknown_key_raises() -> None:
    """未知键取值抛领域异常（禁止静默默认——魔法数借道）。"""
    with pytest.raises(Exception, match=".+"):
        assumption("no_such_assumption", {})


def test_register_without_source_rejected() -> None:
    """R2（登记侧）：无出处条目拒绝注册。"""
    with pytest.raises(Exception, match=".+"):
        Assumption(key="test_no_source", default=1.0, dim="LENGTH", source="", note="")
