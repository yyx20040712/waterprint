"""公式求值件：apply/apply_batch 唯一正门（b2-s2 拆自 formulas.py）。

输入:  formula_id + bindings（标量 float / 批量 ndarray）+ ctx 二元组
       （unit_id, condition_key）+ 可选 TraceSink
输出:  求值结果（标量 float / shape (N,) ndarray）+ sink 记
       TraceNodeSpec 五字段快照（bindings 副本——T3A-01）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（拆自 formulas.py 规格头——完整原文见 git 历史）：
#   R3 apply 是唯一求值路径：绕过 apply 直接抄公式代码=评审拒绝
#   （否则计算迹断链，§16 A1"注册表与实现漂移"防线）。
#   R6 apply 拒绝路径（D8）：未知 id 拒；bindings 键集 == symbols
#   键集（缺/多键拒，消息含 formula_id+键名）；绑定值非有限拒
#   （GR-02 输入即拒）；绑定值巨 int（float() 溢出）收编为领域异常
#   （ARCH1 D1a）；原生数值异常 from exc 包装上抛；结果非有限拒
#   （GR-02 运算产生转领域异常）。
#   apply=标量 N=1 退化（ADR-011 D1/批 13-A）：eval_checked 求值缓存
#   解析树（禁 eval/exec/lambda）；apply_batch=批量正门（批 13-A
#   ——GR-37 载体）：N==1=标量私核快路径（apply 同一实现——UF-36
#   机器锚）；N>1=formulas_kernel 数组语义（errstate 三态+isfinite
#   二道网）+域拒行 NaN；N>1 携 sink=拒。形状合约（批 13-D
#   A2-03/G1-03）：N=1 → shape (1,)；N>1 → shape (N,)。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

import numpy

from waterprint.contracts.expr import eval_checked
from waterprint.contracts.trace_api import TraceNodeSpec, TraceSink
from waterprint.registry import formulas_kernel
from waterprint.registry.formulas.spec import InvalidFormulaError
from waterprint.registry.formulas.store import _REGISTRY, _Entry


def _lookup(formula_id: str) -> _Entry:
    """登记项查取：未知 id=领域异常（apply/apply_batch 共用拒绝面）。"""
    entry = _REGISTRY.get(formula_id)
    if entry is None:
        raise InvalidFormulaError(
            f"未登记公式：{formula_id!r}（apply 只消费 register 登记项）"
        )
    return entry


def _check_keys(formula_id: str, bindings: Mapping[str, object], expected: frozenset[str]) -> None:
    """绑定键集==symbols 键集校验（双正门共用——消息恒等）。"""
    given = frozenset(bindings)
    if given != expected:
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 求值绑定键集与 symbols 键集不一致："
            f"缺 {sorted(expected - given)}，多 {sorted(given - expected)}"
            f"（应恰为 {sorted(expected)}）"
        )


def _canonical_native(exc: ArithmeticError | ValueError) -> str:
    """原生异常消息跨版本归一（GOV4 维护小批·3.14 入矩阵配套）。

    Python 3.14 起 ZeroDivisionError 统一为 'division by zero'（3.12/3.13
    float 路径为 'float division by zero'）——本求值器绑定值恒 float，
    除零必经 float 路径，锚文本以 float 形为准（R1 锚②锁定测试的逐字
    锚面=领域诊断消息版本稳定性契约）。
    """
    if isinstance(exc, ZeroDivisionError) and str(exc) == "division by zero":
        return "float division by zero"
    return str(exc)


def _apply_scalar(
    entry: _Entry,
    values: dict[str, float],
    ctx: tuple[str, str],
    sink: TraceSink | None,
    trace_bindings: Mapping[str, float] | None = None,
) -> float:
    """标量求值私核（N=1 退化与 apply 同一实现——R1 锚②异常构造点）。"""
    try:
        outcome = eval_checked(entry.tree, values)
    except (ArithmeticError, ValueError) as exc:
        raise InvalidFormulaError(
            f"公式 {entry.spec.formula_id!r} 求值数值域错误"
            f"（除零/溢出/定义域，expr R5 原生异常包装）：{_canonical_native(exc)}"
        ) from exc
    if isinstance(outcome, bool) or not isinstance(outcome, int | float):
        raise InvalidFormulaError(
            f"公式 {entry.spec.formula_id!r} 求值结果非数值：{outcome!r}"
            "（公式=纯数值；布尔面属工况映射 DSL）"
        )
    result = float(outcome)
    if not isfinite(result):
        raise InvalidFormulaError(
            f"公式 {entry.spec.formula_id!r} 求值结果非有限：{result!r}"
            "（GR-02 运算产生即转领域异常）"
        )
    if sink is not None:
        sink.record(
            TraceNodeSpec(
                formula_id=entry.spec.formula_id,
                unit_id=ctx[0],
                condition_key=ctx[1],
                bindings=dict(trace_bindings if trace_bindings is not None else values),
                result=result,
            )
        )
    return result


def apply(
    formula_id: str,
    bindings: Mapping[str, float],
    ctx: tuple[str, str],
    sink: TraceSink | None = None,
) -> float:
    """唯一求值正门（R3/R6；标量=N=1 退化——批 13-A）：校验→标量私核。"""
    entry = _lookup(formula_id)
    _check_keys(formula_id, bindings, frozenset(entry.spec.symbols))
    values: dict[str, float] = {}
    for symbol, value in bindings.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidFormulaError(
                f"公式 {formula_id!r} 符号 {symbol!r} 的绑定值必须为数值："
                f"得到 {value!r}"
            )
        try:
            number = float(value)
        except OverflowError as exc:
            raise InvalidFormulaError(
                f"公式 {formula_id!r} 符号 {symbol!r} 的绑定值超出浮点域："
                f"原值类型 {type(value).__name__}"
                "（GR-02 输入即拒；ARCH1 D1a——原生异常收编）"
            ) from exc
        if not isfinite(number):
            raise InvalidFormulaError(
                f"公式 {formula_id!r} 符号 {symbol!r} 的绑定值非有限："
                f"{number!r}（GR-02 输入即拒）"
            )
        values[symbol] = number
    return _apply_scalar(entry, values, ctx, sink, trace_bindings=bindings)


def apply_batch(
    formula_id: str,
    bindings: Mapping[str, numpy.ndarray],
    ctx: tuple[str, str],
    sink: TraceSink | None = None,
) -> numpy.ndarray:
    """批量正门（批 13-A 同源向量路径）：N=1=标量私核；N>1=数组核+域拒 NaN
    （域拒行仅以 NaN 表达、行级原因不对外——kernel issues 诊断在正门
    收敛；下游行级标注交 enumerate nan_flag 既有列，R5 口径零变）。

    形状合约（批 13-D A2-03/G1-03 兑现——接口文档+出口显式断言）：
    bindings=等长一维数值 ndarray（非等长/零长/二维/非数值 dtype/非有限
    绑定=InvalidFormulaError——kernel validate_arrays 承载）；N=1 →
    返回 shape (1,)（快路径标量私核单点装箱）；N>1 → 返回 shape (N,)
    （域拒行 NaN）——两出口断言见函数体。
    """
    entry = _lookup(formula_id)
    _check_keys(formula_id, bindings, frozenset(entry.spec.symbols))
    try:
        scalars = formulas_kernel.n1_scalars(bindings)
        if scalars is not None:
            singleton = numpy.asarray([_apply_scalar(entry, scalars, ctx, sink)])
            assert singleton.shape == (1,)  # G1-03：N=1 返回形状合约（防御性）
            return singleton
        arrays = formulas_kernel.validate_arrays(bindings, frozenset(entry.spec.symbols))
    except formulas_kernel.BatchBindingError as exc:
        raise InvalidFormulaError(f"公式 {formula_id!r} {exc}") from exc
    count = len(next(iter(arrays.values())))
    if sink is not None:
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 批量求值（N={count}）禁携迹收集器：万级落迹会爆炸"
        )
    try:
        outcome = formulas_kernel.evaluate_batch(entry.tree, arrays)
    except formulas_kernel.KernelUnsupportedError as exc:
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 求值核不可达节点：{exc}"
            "（公式算术子集外——登记期防线后防御性拒绝）"
        ) from exc
    values = numpy.asarray(outcome.values, dtype=numpy.float64)
    assert values.shape == (count,)  # A2-03：N>1 出口形状合约（防御性）
    # 域拒行 NaN（§三.2）：核内重放已置 NaN；N>1 不抛——上浮交 nan_flag（R5 零变）。
    return values
