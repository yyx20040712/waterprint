"""共享受限表达式求值器：公式 DSL 与工况映射 DSL 的唯一解析/求值内核。

输入:  DSL 表达式字符串（registry 公式、units_lib manifest 工况映射声明）
       + 宿主声明的允许名集合 + 求值期数值绑定
输出:  parse_checked → 白名单校验并归一后的 ast.Expression；
       eval_checked → float | bool；一切可预期非法 → ExprSyntaxError
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T0.5 冻结；正式镜像测试由人类流程补，见简报 T0.5）
#
# 【公开接口】
#   class ExprSyntaxError(Exception)
#       领域异常：语法非法/节点或运算符越白名单/函数越白名单/引用未声明/
#       常量类型越界/求值期名字未绑定——可预期错误一律走此异常，禁止静默。
#   ALLOWED_FUNCS: frozenset[str]
#       白名单函数 {min, max, abs, sqrt, log10}（仅位置参数）。
#   parse_checked(expr: str, allowed_names: frozenset[str]) -> ast.Expression
#       解析 + 静态校验（节点/运算符/函数/引用名/常量类型/参数数目）。
#       返回的树只含白名单节点：点式引用（Attribute 链，如 pool.all_pools）
#       在整链命中 allowed_names 后就地归一为扁平 Name——决策 1 的节点
#       清单对输出树成立（点式展平调和方案经总控裁决批准，T0.5）；
#       属性访问到活对象在构造上不可能（求值只查 bindings 字典，
#       永不 getattr）。
#   eval_checked(parsed: ast.Expression,
#                bindings: Mapping[str, float | bool]) -> float | bool
#       纯结构求值：Name（含归一后的点式名）→ bindings 同名键；数值/布尔
#       常量允许内联，出处由宿主规格约束（公式=FormulaSpec.norm_ref；
#       工况映射=声明式清单）。
#
# 【行为规格】
#   R1 节点白名单：Expression/BinOp/UnaryOp/Name/Constant/Compare/BoolOp/
#      IfExp/Call（Call 的 func 必须是白名单函数名，禁关键字参数）；
#      其余节点（Subscript/Lambda/JoinedStr/Starred 等）一律拒绝。
#   R2 运算符子集：BinOp 限 + - * / **；UnaryOp 限 +x -x not；
#      Compare 限 == != < > <= >=；BoolOp 限 and/or。
#   R3 引用规则：Name 与点式引用（整链扁平名）必须命中 allowed_names；
#      白名单函数名只在调用位隐式可用，作裸值引用同样须先声明。
#   R4 常量：仅 int/float/bool；str/bytes/None/complex 一律拒绝。
#   R5 错误与边界：语法错误 → ExprSyntaxError（异常链保留原 SyntaxError）；
#      求值期缺绑定 → ExprSyntaxError；数值域错误（除零/溢出/math 定义域）
#      按 Python 原生异常上抛、由宿主决定包装——本求值器只守语法与名字
#      边界，不吞数值语义。
#   R6 安全边界：零 eval/exec/compile/getattr；求值不可逃逸出 bindings。
#
# 【禁止】import 内部其他模块（L0 零内部依赖，仅标准库 ast/math/operator）。
#
# 【测试要求】负例：__import__('os')、a.b（点式引用未声明）、未声明 Name、
#   白名单外函数（如 pow）各抛 ExprSyntaxError；正例：算术式（含 ** 与
#   白名单函数）、条件式（IfExp+Compare+点式上下文字段）对照手算值。
#
# 【参照】简报 T0.5 决策 1/2/3；registry/formulas.py【表达式 DSL】；
#   contracts/manifest.py【工况映射 DSL】；ADR-007
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable, Mapping, Sequence
from typing import cast


class ExprSyntaxError(Exception):
    """受限表达式非法：语法/白名单/引用名/绑定 任一失败。"""


ALLOWED_FUNCS: frozenset[str] = frozenset({"min", "max", "abs", "sqrt", "log10"})

# Attribute 仅在解析期作为点式引用出现，_flatten 归一后输出树不含它。
_NODES: frozenset[type[ast.AST]] = frozenset(
    {
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Constant,
        ast.Compare, ast.BoolOp, ast.IfExp, ast.Call, ast.Attribute,
    }
)
_BIN_OPS: frozenset[type[ast.AST]] = frozenset(
    {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow}
)
_UNARY_OPS: frozenset[type[ast.AST]] = frozenset({ast.UAdd, ast.USub, ast.Not})
_CMP_OPS: frozenset[type[ast.AST]] = frozenset(
    {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE}
)
_BOOL_OPS: frozenset[type[ast.AST]] = frozenset({ast.And, ast.Or})
_OPS_BY_NODE: Mapping[type[ast.AST], frozenset[type[ast.AST]]] = {
    ast.BinOp: _BIN_OPS,
    ast.UnaryOp: _UNARY_OPS,
    ast.Compare: _CMP_OPS,
    ast.BoolOp: _BOOL_OPS,
}
_FIXED_ARITY: Mapping[str, int] = {"abs": 1, "sqrt": 1, "log10": 1}
_MIN_ARITY: Mapping[str, int] = {"min": 1, "max": 1}
_BIN_IMPL: Mapping[type[ast.operator], Callable[..., object]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNARY_IMPL: Mapping[type[ast.unaryop], Callable[..., object]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}
_CMP_IMPL: Mapping[type[ast.cmpop], Callable[..., object]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}
_FUNC_IMPL: Mapping[str, Callable[..., object]] = {
    "min": min,
    "max": max,
    "abs": abs,
    "sqrt": math.sqrt,
    "log10": math.log10,
}


def parse_checked(expr: str, allowed_names: frozenset[str]) -> ast.Expression:
    """解析并静态校验受限表达式；返回只含白名单节点的归一化表达式树。"""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ExprSyntaxError(f"表达式语法非法：{expr!r}（{exc.msg}）") from exc
    _check_nodes(tree)
    tree.body = cast(ast.expr, _flatten(tree.body, allowed_names))
    return tree


def eval_checked(
    parsed: ast.Expression, bindings: Mapping[str, float | bool]
) -> float | bool:
    """对 parse_checked 产物做纯结构求值；缺绑定/越白名单 → ExprSyntaxError。"""
    return _eval(parsed.body, bindings)


def _check_nodes(tree: ast.AST) -> None:
    """结构白名单：节点类型/运算符/常量类型/函数调用与参数数目。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            _check_constant(node)
        elif isinstance(node, ast.Call):
            _check_call(node)
        elif isinstance(node, ast.BinOp | ast.UnaryOp | ast.Compare | ast.BoolOp):
            _check_operator(node)
        elif isinstance(
            node, ast.Load | ast.operator | ast.unaryop | ast.cmpop | ast.boolop
        ):
            continue  # 运算符/上下文节点：合法性由 _check_operator 按父节点校验
        elif type(node) not in _NODES:
            raise ExprSyntaxError(f"节点越白名单：{type(node).__name__}")


def _check_constant(node: ast.Constant) -> None:
    if not isinstance(node.value, bool | int | float):
        raise ExprSyntaxError(f"常量类型越界：{node.value!r}（仅数值/布尔）")


def _check_call(node: ast.Call) -> None:
    func = node.func
    if not isinstance(func, ast.Name) or func.id not in ALLOWED_FUNCS:
        raise ExprSyntaxError(f"白名单外函数调用：{ast.unparse(node)}")
    if node.keywords:
        raise ExprSyntaxError(f"函数调用禁用关键字参数：{ast.unparse(node)}")
    fixed = _FIXED_ARITY.get(func.id)
    if fixed is not None and len(node.args) != fixed:
        raise ExprSyntaxError(f"函数 {func.id} 参数数目应为 {fixed}：{ast.unparse(node)}")
    least = _MIN_ARITY.get(func.id)
    if least is not None and len(node.args) < least:
        raise ExprSyntaxError(f"函数 {func.id} 至少需 {least} 个参数：{ast.unparse(node)}")


def _check_operator(
    node: ast.BinOp | ast.UnaryOp | ast.Compare | ast.BoolOp,
) -> None:
    if isinstance(node, ast.Compare):
        ops: list[ast.AST] = list(node.ops)
    else:
        ops = [node.op]
    allowed = _OPS_BY_NODE.get(type(node))
    if allowed is None or any(type(op) not in allowed for op in ops):
        raise ExprSyntaxError(f"运算符越白名单：{ast.unparse(node)}")


def _dotted_path(node: ast.AST) -> str | None:
    """Name/Attribute 链 → 点式扁平名；根非 Name（如 f(x).attr）返回 None。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_path(node.value)
        if base is not None:
            return f"{base}.{node.attr}"
    return None


def _flatten(node: ast.AST, allowed_names: frozenset[str]) -> ast.AST:
    """校验引用名并把点式引用归一为扁平 Name（返回可能替换后的节点）。"""
    if isinstance(node, ast.Attribute | ast.Name):
        ref = _dotted_path(node)
        if ref is not None and ref in allowed_names:
            return ast.copy_location(ast.Name(id=ref, ctx=ast.Load()), node)
        raise ExprSyntaxError(f"引用未声明：{ast.unparse(node)}")
    if isinstance(node, ast.Call):
        node.args = cast(
            "list[ast.expr]",
            [_flatten(arg, allowed_names) for arg in node.args],
        )
        return node
    for field, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            setattr(node, field, _flatten(value, allowed_names))
        elif isinstance(value, list):
            setattr(
                node,
                field,
                [
                    _flatten(item, allowed_names) if isinstance(item, ast.AST) else item
                    for item in value
                ],
            )
    return node


def _eval(node: ast.expr, bindings: Mapping[str, float | bool]) -> float | bool:
    if isinstance(node, ast.Constant):
        return _constant(node)
    if isinstance(node, ast.Name):
        return _binding(node.id, bindings)
    if isinstance(node, ast.BinOp | ast.UnaryOp):
        return _apply_operator(node, bindings)
    if isinstance(node, ast.BoolOp | ast.IfExp):
        return _eval_logical(node, bindings)
    if isinstance(node, ast.Compare):
        return _eval_compare(node, bindings)
    if isinstance(node, ast.Call):
        return _eval_call(node, bindings)
    raise ExprSyntaxError(f"节点越白名单：{type(node).__name__}")


def _constant(node: ast.Constant) -> float | bool:
    value = node.value
    if isinstance(value, bool | int | float):
        return value
    raise ExprSyntaxError(f"常量类型越界：{value!r}")


def _binding(name: str, bindings: Mapping[str, float | bool]) -> float | bool:
    if name in bindings:
        return bindings[name]
    raise ExprSyntaxError(f"未绑定名字：{name}")


def _apply_operator(
    node: ast.BinOp | ast.UnaryOp, bindings: Mapping[str, float | bool]
) -> float | bool:
    if isinstance(node, ast.BinOp):
        lhs = _eval(node.left, bindings)
        rhs = _eval(node.right, bindings)
        impl = _BIN_IMPL.get(type(node.op))
        if impl is not None:
            return cast(float | bool, impl(lhs, rhs))
    else:
        operand = _eval(node.operand, bindings)
        impl = _UNARY_IMPL.get(type(node.op))
        if impl is not None:
            return cast(float | bool, impl(operand))
    raise ExprSyntaxError(f"运算符越白名单：{ast.unparse(node)}")


def _eval_logical(
    node: ast.BoolOp | ast.IfExp, bindings: Mapping[str, float | bool]
) -> float | bool:
    if isinstance(node, ast.BoolOp):
        return _eval_boolop(node, bindings)
    if _eval(node.test, bindings):
        return _eval(node.body, bindings)
    return _eval(node.orelse, bindings)


def _eval_boolop(node: ast.BoolOp, bindings: Mapping[str, float | bool]) -> float | bool:
    is_and = isinstance(node.op, ast.And)
    result: float | bool = _eval(node.values[0], bindings)
    for value in node.values[1:]:
        if is_and and not result:
            return result
        if not is_and and result:
            return result
        result = _eval(value, bindings)
    return result


def _eval_compare(node: ast.Compare, bindings: Mapping[str, float | bool]) -> bool:
    left: float | bool = _eval(node.left, bindings)
    for op, comparator in zip(node.ops, node.comparators, strict=True):
        impl = _CMP_IMPL.get(type(op))
        if impl is None:
            raise ExprSyntaxError(f"比较符越白名单：{type(op).__name__}")
        right = _eval(comparator, bindings)
        if not cast(bool, impl(left, right)):
            return False
        left = right
    return True


def _eval_call(node: ast.Call, bindings: Mapping[str, float | bool]) -> float | bool:
    func = node.func
    if not isinstance(func, ast.Name) or func.id not in _FUNC_IMPL:
        raise ExprSyntaxError(f"白名单外函数调用：{ast.unparse(node)}")
    args = [_eval(arg, bindings) for arg in node.args]
    return _call_function(func.id, args)


def _call_function(name: str, args: Sequence[float | bool]) -> float | bool:
    if not args:
        raise ExprSyntaxError(f"函数 {name} 缺少实参")
    if name == "min":
        return min(args)
    if name == "max":
        return max(args)
    if name == "abs":
        return abs(cast(float, args[0]))
    value = cast(float, args[0])
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log10":
        return math.log10(value)
    raise ExprSyntaxError(f"白名单外函数调用：{name}")
