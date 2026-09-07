"""公式数组求值核：公式算术子集的 ndarray 语义求值+域拒逐行重放机制。

输入:  formulas 缓存解析树（登记期静态校验后的 ast.Expression）+
       绑定数组（等长一维 float64）+ 逐行标量重放核（contracts.eval_checked）
输出:  BatchOutcome（values 数组[域拒行 NaN]+issues 行级问题清单[异常实例/
       非有限值/None]）——消息构造与 NaN 政策归 formulas 正门（本核异常中性）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批 13-A：ADR-011 D1/D3 落地——task-13A-batch-plan §三/§四）
#
# 【公开接口】
#   class BatchOutcome(frozen)：values: ndarray（长度 N；域拒行=NaN）、
#       issues: tuple[Exception | float | None, ...]（逐行：重放抛出的
#       原生异常实例 / 重放产出的非有限值 / None=良行）
#   class KernelUnsupportedError(Exception)：求值核到达公式语法子集外
#       节点（登记期防线后运行时不可达——防御性，formulas 包装上抛）
#   evaluate_batch(tree: ast.Expression, arrays: Mapping[str, ndarray])
#       -> BatchOutcome
#   n1_scalars(arrays) / validate_arrays(bindings, expected)
#       批量绑定校验双件（N=1 快路径取标量+全量校验归一——消息经
#       BatchBindingError 中性承载，formulas 正门前缀 formula_id 翻译）
#
# 【行为规格】
#   R1 数组语义（GR-37 强制载体）：errstate(divide/over/invalid="raise")
#      局部承接——三态浮点错即中断整批；under 与 Python 标量语义同
#      （静默——非域拒面）。
#   R2 isfinite 二道网：整批算后全元素有限性校验（errstate 覆盖不到的
#      非有限产出面——网破即降级重放）。
#   R3 域拒逐行重放（task-13-design §三.2）：R1/R2 触发时以
#      contracts.eval_checked（Python 标量语义——registry 既有内核，
#      同一缓存树）逐行重放定位域拒行——良行取重放值（批 13-A 探针
#      实证 Python 标量与 numpy 数组语义位级恒等：414 公式×1235 求值
#      零位差），域拒行置 NaN+issues 记原生异常或非有限值。仅错误路径
#      付出逐行成本（正常批零开销）。
#   R4 节点子集：公式语法子集（登记期已拒 Compare/BoolOp/IfExp——
#      formulas._parse_rhs）= Expression/Constant[数值]/Name/BinOp
#      {+,-,*,/,**}/UnaryOp{+,-}/Call{min,max,abs,sqrt,log10}；子集外
#      节点=KernelUnsupportedError（防御性——正常语料不可达）。
#   R5 值恒等基础：numpy 元素运算（IEEE float64 确定性运算）与 Python
#      标量运算位级恒等——含 **2 快路径（square）与 **0.5（sqrt）经
#      值域 {1e-150..1e150} 全谱探针实证+CI Linux 机器证（批 13-A）；
#      ±0 持平的 min/max 取值差为语料域外边角（参数域守卫>0）。log10
#      例外：numpy SIMD 实现与 libm math.log10 平台相依末位 ulp 差
#      （CI 实证）——非位保证运算，全语料零使用；批/标量恒等以 approx
#      锚（test_formulas_kernel.py 平台注记——批 A CI 失守修锚笔）。
#
# 【禁区】import 面=numpy+contracts.expr（L1→L0 向下合法——numpy 先例
#   dimensions.py）；禁 import formulas（同层环——消息构造归正门，
#   本核异常中性）；本文件零数值字面量（魔法数字门禁区）。
#
# 【测试要求】tests/registry/test_formulas_kernel.py（N=1 锁定/N>1 批
#   正确性/域拒混合批/GR-37 强制/节点子集防御）。
#
# 【参照】ADR-011；task-13-design §三；task-13A-batch-plan §三/§四
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import final

import numpy

from waterprint.contracts.expr import eval_checked

_BIN_OPS: Mapping[
    type[ast.operator], Callable[[numpy.ndarray, numpy.ndarray], numpy.ndarray]
] = {
    ast.Add: numpy.add,
    ast.Sub: numpy.subtract,
    ast.Mult: numpy.multiply,
    ast.Div: numpy.true_divide,
    ast.Pow: numpy.power,
}


class KernelUnsupportedError(Exception):
    """求值核到达公式算术子集外节点（防御性——登记期防线后不可达）。"""


@dataclass(frozen=True)
@final
class BatchOutcome:
    """批量求值结果：值数组（域拒行 NaN）+ 逐行问题清单（异常中性）。"""

    values: numpy.ndarray
    issues: tuple[Exception | float | None, ...]


def _walk(node: ast.AST, arrays: Mapping[str, numpy.ndarray]) -> numpy.ndarray:
    """数组语义树求值（公式算术子集——R4）。"""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise KernelUnsupportedError(f"常量类型越界：{node.value!r}")
        return numpy.asarray(node.value, dtype=numpy.float64)
    if isinstance(node, ast.Name):
        return arrays[node.id]
    if isinstance(node, ast.BinOp):
        impl = _BIN_OPS.get(type(node.op))
        if impl is None:
            raise KernelUnsupportedError(f"运算符越子集：{ast.unparse(node)}")
        return impl(_walk(node.left, arrays), _walk(node.right, arrays))
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return numpy.negative(_walk(node.operand, arrays))
        if isinstance(node.op, ast.UAdd):
            return _walk(node.operand, arrays)
        raise KernelUnsupportedError(f"一元运算符越子集：{ast.unparse(node)}")
    if isinstance(node, ast.Call):
        return _call(node, arrays)
    raise KernelUnsupportedError(f"节点越子集：{type(node).__name__}")


def _call(node: ast.Call, arrays: Mapping[str, numpy.ndarray]) -> numpy.ndarray:
    """白名单函数的元素级实现（min/max 多参链接归约）。"""
    func = node.func
    if not isinstance(func, ast.Name):
        raise KernelUnsupportedError(f"调用位非白名单函数名：{ast.unparse(node)}")
    args = [_walk(arg, arrays) for arg in node.args]
    name = func.id
    if name == "min":
        outcome = args[0]
        for arg in args[1:]:
            outcome = numpy.minimum(outcome, arg)
        return outcome
    if name == "max":
        outcome = args[0]
        for arg in args[1:]:
            outcome = numpy.maximum(outcome, arg)
        return outcome
    if name == "abs" and len(args) == 1:
        return numpy.abs(args[0])
    if name == "sqrt" and len(args) == 1:
        return numpy.sqrt(args[0])
    if name == "log10" and len(args) == 1:
        return numpy.log10(args[0])
    raise KernelUnsupportedError(f"函数越子集：{ast.unparse(node)}")


def _replay_rows(
    tree: ast.Expression, arrays: Mapping[str, numpy.ndarray], count: int
) -> BatchOutcome:
    """域拒逐行重放（R3）：eval_checked 逐行定位+良行取值+域拒行 NaN。"""
    values = numpy.full(count, numpy.nan)
    issues: list[Exception | float | None] = []
    for row in range(count):
        scalar_bindings = {
            symbol: float(column[row]) for symbol, column in arrays.items()
        }
        try:
            outcome = eval_checked(tree, scalar_bindings)
            number = float(outcome)
        except (ArithmeticError, ValueError) as exc:
            issues.append(exc)
            continue
        if not isfinite(number):
            issues.append(number)
            continue
        values[row] = number
        issues.append(None)
    return BatchOutcome(values=values, issues=tuple(issues))


class BatchBindingError(Exception):
    """批量绑定校验拒绝（消息已格式化——formulas 正门翻译为领域异常）。"""


def n1_scalars(arrays: Mapping[str, numpy.ndarray]) -> dict[str, float] | None:
    """N=1 快路径取标量：全列恰 1 元素数值一维时抽标量（含有限校验）；
    前置不满足返回 None 交 validate_arrays 全量校验拒绝。

    动因（批 13-A 基准实测）：逐行枚举（N=1 退化）经数组校验/装箱
    开销 5s 预算失守——快路径=标量私核直连（数组开销归零，万级复归
    预算内）。非 float64 数值 dtype 两路统一 float64 语义（本路径
    float() 取标量/全量路径 ascontiguousarray——A 二审置信注记闭合）。"""
    scalars: dict[str, float] = {}
    for symbol, column in arrays.items():
        if (
            not isinstance(column, numpy.ndarray)
            or column.ndim != 1
            or column.size != 1
            or column.dtype.kind not in "iuf"
        ):
            return None
        value = float(column[0])
        if not isfinite(value):
            raise BatchBindingError(
                f"符号 {symbol!r} 的批量绑定含非有限值（GR-02 输入即拒）"
            )
        scalars[symbol] = value
    return scalars


def validate_arrays(
    bindings: Mapping[str, numpy.ndarray], expected: frozenset[str]
) -> dict[str, numpy.ndarray]:
    """数组绑定校验+归一：数值一维/等长/全有限（GR-02 输入即拒）。

    formula_id 由调用方前缀进消息（翻译层拼接——消息文本单源在本核）。"""
    if not expected:
        # 零符号公式不得经 apply_batch 正门（仅核内防御面支持 0 维广播
        # ——test_kernel_zero_dim_broadcast_defensive 白盒口径）。
        raise BatchBindingError("零符号无批量语义（N 不可推断）")
    columns: dict[str, numpy.ndarray] = {}
    count: int | None = None
    for symbol, value in bindings.items():
        if not isinstance(value, numpy.ndarray):
            raise BatchBindingError(
                f"符号 {symbol!r} 的批量绑定值必须为一维ndarray：得到 {type(value).__name__}"
            )
        if value.dtype.kind not in "iuf":
            raise BatchBindingError(f"符号 {symbol!r} 批量绑定 dtype 非数值：{value.dtype!r}")
        column = numpy.ascontiguousarray(value, dtype=numpy.float64)
        if column.ndim != 1 or column.size == 0:
            raise BatchBindingError(f"符号 {symbol!r} 批量绑定须非空一维：shape={value.shape!r}")
        if not bool(numpy.isfinite(column).all()):
            raise BatchBindingError(f"符号 {symbol!r} 的批量绑定含非有限值（GR-02 输入即拒）")
        if count is None:
            count = column.size
        elif column.size != count:
            raise BatchBindingError(f"批量长度不一致：{symbol!r}={column.size}≠{count}")
        columns[symbol] = column
    return columns


def evaluate_batch(
    tree: ast.Expression, arrays: Mapping[str, numpy.ndarray]
) -> BatchOutcome:
    """批量求值正门：errstate 三态承接→isfinite 二道网→正常批零重放。"""
    count = len(next(iter(arrays.values())))
    try:
        with numpy.errstate(divide="raise", over="raise", invalid="raise"):
            walked = numpy.asarray(_walk(tree.body, arrays), dtype=numpy.float64)
    except FloatingPointError:
        return _replay_rows(tree, arrays, count)
    # 零符号公式（裸常量右式）产出 0 维——广播至批长（语料外防御面）。
    values = numpy.full(count, float(walked)) if walked.ndim == 0 else walked
    if bool(numpy.isfinite(values).all()):
        return BatchOutcome(
            values=values, issues=tuple(None for _ in range(count))
        )
    return _replay_rows(tree, arrays, count)
