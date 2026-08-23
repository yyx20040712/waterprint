"""expr 镜像测试：受限表达式求值器（公式 DSL 与工况映射 DSL 的共用引擎）。

输入:  waterprint.contracts.expr 公开符号
       （ExprSyntaxError/parse_checked/eval_checked/ALLOWED_FUNCS）
输出:  白名单解析/归一化/求值/拒绝路径断言（实现合入后必须全绿；
       实现停靠于 t0.5-dsl-spec-wip 分支待合并，合并即激活本测试）
"""

from __future__ import annotations

import ast
import importlib

import pytest

try:
    _mod = importlib.import_module("waterprint.contracts.expr")
except ModuleNotFoundError:
    _mod = None
ExprSyntaxError = getattr(_mod, "ExprSyntaxError", None)
parse_checked = getattr(_mod, "parse_checked", None)
eval_checked = getattr(_mod, "eval_checked", None)
ALLOWED_FUNCS = getattr(_mod, "ALLOWED_FUNCS", None)

pytestmark = pytest.mark.skipif(
    None in (ExprSyntaxError, parse_checked, eval_checked, ALLOWED_FUNCS),
    reason="实现未就绪：waterprint.contracts.expr 公开符号缺失（t0.5 分支待合并）",
)


def test_allowed_funcs_exactly_five() -> None:
    """函数白名单恰五项（规格冻结值，增减 = 规格变更走显式修订）。"""
    expected = frozenset({"min", "max", "abs", "sqrt", "log10"})
    assert expected == ALLOWED_FUNCS


def test_arithmetic_positive_path() -> None:
    """正例：算术式（含 ** 与白名单函数）解析求值正确。"""
    parsed = parse_checked("a ** 2 + max(a, b)", frozenset({"a", "b"}))
    assert eval_checked(parsed, {"a": 3.0, "b": 4.0}) == pytest.approx(13.0)


def test_conditional_positive_path() -> None:
    """正例：条件式（IfExp+Compare+BoolOp，工况映射 DSL 子集）求值正确。"""
    parsed = parse_checked(
        "n if pool.all_pools and n >= 1 else n - 1",
        frozenset({"n", "pool.all_pools"}),
    )
    assert eval_checked(parsed, {"n": 4.0, "pool.all_pools": True}) == 4.0
    assert eval_checked(parsed, {"n": 4.0, "pool.all_pools": False}) == 3.0


def test_dotted_reference_flattened_to_whitelisted_name() -> None:
    """点式引用整链展平为扁平名；归一后树不含 Attribute；未声明点式名拒绝。"""
    parsed = parse_checked("pool.all_pools", frozenset({"pool.all_pools"}))
    assert not any(isinstance(node, ast.Attribute) for node in ast.walk(parsed))
    with pytest.raises(ExprSyntaxError):
        parse_checked("pool.other", frozenset({"pool.all_pools"}))


def test_reject_dangerous_and_undeclared() -> None:
    """负例：import 调用/未声明名/白名单外函数/未声明点式链一律拒绝。"""
    with pytest.raises(ExprSyntaxError):
        parse_checked("__import__('os')", frozenset({"os"}))
    with pytest.raises(ExprSyntaxError):
        parse_checked("a + 1", frozenset({"b"}))
    with pytest.raises(ExprSyntaxError):
        parse_checked("pow(a, 2)", frozenset({"a"}))
    with pytest.raises(ExprSyntaxError):
        parse_checked("a.b.c", frozenset({"a", "b", "c", "a.b"}))


def test_eval_missing_binding_raises() -> None:
    """求值期缺绑定 = ExprSyntaxError（禁止静默 None/0）。"""
    parsed = parse_checked("a + 1", frozenset({"a"}))
    with pytest.raises(ExprSyntaxError):
        eval_checked(parsed, {})
