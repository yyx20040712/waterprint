"""formulas_kernel+apply_batch 批量语义镜像测试（批 13-A）。

输入:  registry 批量求值面（formulas.apply_batch + formulas_kernel.evaluate_batch
       探针公式 B13K-* 本件登记，进程内唯一前缀）
输出:  测试结果（N=1 恒等/N>1 逐行恒等/域拒 NaN/GR-37 强制/守卫拒绝面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批 13-A；AGENTS §13.6——同源向量路径唯一=本件机器锚承载）
#
# 【锚面】
#   R1 N=1 恒等（UF-36 防双轨实质口径）：apply_batch(N=1)[0] == apply
#      逐值精确（位级——探针覆盖 + - * / ** min/max/abs/sqrt 全算术面）。
#   R2 N>1 逐行恒等：批量结果与逐行 apply 位级相同（64 行网格）。
#   R3 域拒行 NaN（task-13-design §三.2）：混合批良行取值/域拒行 NaN
#      （除零行[重放异常]与静默溢出行[重放非有限值]两类定位机制）。
#   R4 GR-37 强制：errstate 三态（除零/溢出/无效）承接——错误路径降级
#      重放定位；N=1 域拒消息与标量 apply 恒等（同一异常构造点）。
#   R5 守卫面：批量绑定校验（非 ndarray/布尔 dtype/非一维/空/非有限/
#      长度不一致/零符号）+N>1 携 sink 拒+未知 id/键集不一致（与 apply
#      共用拒绝面）。
#   R6 防御面：求值核算术子集外节点=KernelUnsupportedError（白盒直驱
#      合成树——登记期防线后运行时不可达）。
#
# 【参照】task-13A-batch-plan §三/§四/§七；ADR-011
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
from typing import Any

import numpy
import pytest

from waterprint.contracts.quantity import DimKey
from waterprint.contracts.trace_api import TraceNodeSpec
from waterprint.registry.formulas import (
    FormulaSpec,
    InvalidFormulaError,
    apply,
    apply_batch,
    by_id,
    register,
)
from waterprint.registry.formulas_kernel import (
    KernelUnsupportedError,
)
from waterprint.registry.formulas_kernel import (
    evaluate_batch as kernel_evaluate_batch,
)

_NORM = "批13-A 批量语义镜像探针(仅测试面)"
_CTX = ("b13k_mirror", "design")


def _probe(formula_id: str, expression: str, symbols: dict[str, tuple[str, str]], out: str) -> None:
    register(
        FormulaSpec(
            formula_id=formula_id,
            expression=expression,
            symbols=symbols,  # type: ignore[arg-type]
            output_dim=DimKey(out),  # type: ignore[arg-type]
            norm_ref=_NORM,
        )
    )


_DIMS = {"a": "LENGTH", "b": "LENGTH", "c": "DIMENSIONLESS"}
_probe("B13K-ADD", "OUT = a + b - c", {"a": ("LENGTH", "x"), "b": ("LENGTH", "x"), "c": ("DIMENSIONLESS", "x")}, "LENGTH")
_probe("B13K-MULDIV", "OUT = a * b / c", {"a": ("AREA", "x"), "b": ("LENGTH", "x"), "c": ("LENGTH", "x")}, "AREA")
_probe("B13K-POW", "OUT = a ** 2 + sqrt(b)", {"a": ("LENGTH", "x"), "b": ("AREA", "x")}, "AREA")
_probe("B13K-MINMAX", "OUT = min(a, b) + max(a, b) + abs(a - b)", {"a": ("LENGTH", "x"), "b": ("LENGTH", "x")}, "LENGTH")
_probe("B13K-DIV", "OUT = a / b", {"a": ("VOLUME", "x"), "b": ("LENGTH", "x")}, "AREA")
_probe("B13K-MUL", "OUT = a * a", {"a": ("LENGTH", "x")}, "AREA")
_probe("B13K-LOG", "OUT = log10(a)", {"a": ("CONCENTRATION", "x")}, "DIMENSIONLESS")
_probe("B13K-MIN3", "OUT = min(a, b, a - b)", {"a": ("LENGTH", "x"), "b": ("LENGTH", "x")}, "LENGTH")


class _Sink:
    """录音 sink（TraceNodeSpec 快照收存）。"""

    def __init__(self) -> None:
        self.nodes: list[Any] = []

    def record(self, node: Any) -> None:
        self.nodes.append(node)


def _bind(**values: float) -> dict[str, numpy.ndarray]:
    return {key: numpy.asarray([value]) for key, value in values.items()}


def test_n1_identity_arithmetic_face() -> None:
    """R1：N=1 批与标量 apply 位级恒等（全算术面探针）。"""
    cases = [
        ("B13K-ADD", {"a": 0.1, "b": 0.2, "c": 0.3}),
        ("B13K-MULDIV", {"a": 3.7, "b": 94.2178, "c": 1.3}),
        ("B13K-POW", {"a": 37.6871, "b": 3550.798}),
        ("B13K-MINMAX", {"a": 3.5, "b": 9.1}),
        ("B13K-DIV", {"a": 3.0, "b": 7.0}),
        ("B13K-MUL", {"a": 94.2178}),
    ]
    for formula_id, bindings in cases:
        scalar = apply(formula_id, dict(bindings), _CTX)
        batch = apply_batch(formula_id, _bind(**bindings), _CTX)
        assert batch.shape == (1,)
        assert float(batch[0]) == scalar  # 位级(== 精确)


def test_batch_log10_rowwise_approx() -> None:
    """R2 补面：log10 批/标量恒等以 approx 锚（非位级——平台注记）。

    numpy log10（SIMD 实现）与 Python math.log10（libm）在 Linux 存在
    末位 ulp 差（CI 34130863494 实证：-0.2491121963984876 vs …764），
    Windows 同源零差——log10 非位保证运算；全语料 log10 零使用（32 包
    manifest grep），批/标量恒等以 1e-15 相对容差锚（CI 失守修锚笔——
    位级电池不含 log10，kernel R5 注记同步）。"""
    count = 64
    arrays = {"a": numpy.linspace(0.5, 4.5, count)}
    batch = apply_batch("B13K-LOG", dict(arrays), _CTX)
    for row in range(count):
        expected = apply("B13K-LOG", {"a": float(arrays["a"][row])}, _CTX)
        assert float(batch[row]) == pytest.approx(expected, rel=1e-15)


@pytest.mark.parametrize(
    "formula_id",
    [
        "B13K-ADD",
        "B13K-MULDIV",
        "B13K-POW",  # **2 快路径+sqrt（walker 幂/开方面——D 二版 G1-02）
        "B13K-MINMAX",  # min/max/abs（最值面）
        "B13K-DIV",
        "B13K-MUL",
        "B13K-MIN3",  # min 三参链接归约（G1-04）
    ],
)
def test_batch_matches_rowwise_scalar(formula_id: str) -> None:
    """R2：N=64 批量与逐行 apply 位级相同（全算术面探针参数化——幂/开方/
    最值/对数位恒等从设计腿离线探针转常驻回归锚）。"""
    count = 64
    pool = {
        "a": numpy.linspace(0.5, 4.5, count),
        "b": numpy.linspace(1.0, 9.0, count),
        "c": numpy.linspace(0.5, 2.0, count),
    }
    arrays = {key: pool[key] for key in by_id(formula_id).symbols}
    batch = apply_batch(formula_id, dict(arrays), _CTX)
    for row in range(count):
        expected = apply(
            formula_id,
            {key: float(arrays[key][row]) for key in arrays},
            _CTX,
        )
        assert float(batch[row]) == expected


def test_domain_rows_nan_mixed_batch() -> None:
    """R3：混合批良行取值/域拒行 NaN——除零(重放异常)与静默溢出(重放
    非有限值)两类定位机制。"""
    zeros = apply_batch(
        "B13K-DIV",
        {"a": numpy.asarray([1.0, 2.0, 3.0]), "b": numpy.asarray([2.0, 0.0, 4.0])},
        _CTX,
    )
    assert float(zeros[0]) == 0.5
    assert numpy.isnan(zeros[1])  # 除零行=NaN(重放 ZeroDivisionError 定位)
    assert float(zeros[2]) == 0.75
    overflows = apply_batch("B13K-MUL", {"a": numpy.asarray([2.0, 1e200, 3.0])}, _CTX)
    assert float(overflows[0]) == 4.0
    assert numpy.isnan(overflows[1])  # 静默溢出行=NaN(重放非有限值定位)
    assert float(overflows[2]) == 9.0


def test_gr37_errstate_and_n1_message_identity() -> None:
    """R4：N=1 域拒消息与标量恒等(同一异常构造点)+N=1 溢出同类。"""
    with pytest.raises(InvalidFormulaError) as batch_exc:
        apply_batch("B13K-DIV", _bind(a=1.0, b=0.0), _CTX)
    with pytest.raises(InvalidFormulaError) as scalar_exc:
        apply("B13K-DIV", {"a": 1.0, "b": 0.0}, _CTX)
    assert str(batch_exc.value) == str(scalar_exc.value)  # R1 锚②域拒判定标准
    assert "float division by zero" in str(scalar_exc.value)
    # N=1 静默溢出(标量乘不抛):「结果非有限」路径——与 apply 面同构造点
    with pytest.raises(InvalidFormulaError, match="求值结果非有限"):
        apply_batch("B13K-MUL", _bind(a=1e200), _CTX)


def test_batch_guard_rejections() -> None:
    """R5：批量绑定校验+迹守卫+共用拒绝面。"""
    with pytest.raises(InvalidFormulaError, match="批量绑定值必须为一维"):
        apply_batch("B13K-ADD", {"a": 1.0, "b": 2.0, "c": 3.0}, _CTX)  # type: ignore[arg-type]
    with pytest.raises(InvalidFormulaError, match="dtype 非数值"):
        apply_batch(
            "B13K-ADD",
            {"a": numpy.asarray([True]), "b": numpy.asarray([1.0]), "c": numpy.asarray([1.0])},
            _CTX,
        )
    with pytest.raises(InvalidFormulaError, match="非空一维"):
        apply_batch(
            "B13K-ADD",
            {"a": numpy.asarray([[1.0]]), "b": numpy.asarray([1.0]), "c": numpy.asarray([1.0])},
            _CTX,
        )
    with pytest.raises(InvalidFormulaError, match="非空一维"):
        apply_batch(
            "B13K-ADD",
            {"a": numpy.asarray([]), "b": numpy.asarray([1.0]), "c": numpy.asarray([1.0])},
            _CTX,
        )
    with pytest.raises(InvalidFormulaError, match="含非有限值"):
        apply_batch(
            "B13K-ADD",
            {"a": numpy.asarray([float("inf")]), "b": numpy.asarray([1.0]), "c": numpy.asarray([1.0])},
            _CTX,
        )
    with pytest.raises(InvalidFormulaError, match="批量长度不一致"):
        apply_batch(
            "B13K-ADD",
            {"a": numpy.asarray([1.0, 2.0]), "b": numpy.asarray([1.0]), "c": numpy.asarray([1.0])},
            _CTX,
        )
    with pytest.raises(InvalidFormulaError, match="禁携迹收集器"):
        apply_batch(
            "B13K-ADD",
            {"a": numpy.asarray([1.0, 2.0]), "b": numpy.asarray([1.0, 2.0]), "c": numpy.asarray([1.0, 2.0])},
            _CTX,
            sink=_Sink(),
        )
    with pytest.raises(InvalidFormulaError, match="未登记公式"):
        apply_batch("B13K-NONE", {"a": numpy.asarray([1.0])}, _CTX)
    with pytest.raises(InvalidFormulaError, match="键集不一致"):
        apply_batch("B13K-ADD", {"a": numpy.asarray([1.0]), "b": numpy.asarray([1.0])}, _CTX)


def test_n1_sink_records_trace_node() -> None:
    """R1 追点：N=1 批携 sink 记一条 TraceNodeSpec（标量形态绑定）。"""
    sink = _Sink()
    apply_batch("B13K-ADD", _bind(a=0.1, b=0.2, c=0.3), _CTX, sink=sink)
    assert len(sink.nodes) == 1
    node = sink.nodes[0]
    assert isinstance(node, TraceNodeSpec)
    assert node.formula_id == "B13K-ADD"
    assert node.unit_id == _CTX[0]
    assert node.condition_key == _CTX[1]
    assert node.bindings == {"a": 0.1, "b": 0.2, "c": 0.3}


def test_kernel_zero_dim_broadcast_defensive() -> None:
    """R6：裸常量右式 0 维广播（白盒合成树——登记期防线后不可达，语料外
    防御面）。"""
    tree = ast.Expression(body=ast.Constant(value=60.0))
    outcome = kernel_evaluate_batch(
        tree, {"a": numpy.asarray([1.0, 2.0])}
    )
    assert outcome.values.tolist() == [60.0, 60.0]
    assert outcome.issues == (None, None)


def test_kernel_unreachable_node_defensive() -> None:
    """R6：算术子集外节点=KernelUnsupportedError（白盒合成树——登记期
    防线后运行时不可达，防御性拒绝）。"""
    tree = ast.Expression(body=ast.Compare(
        left=ast.Name(id="a", ctx=ast.Load()),
        ops=[ast.Lt()],
        comparators=[ast.Name(id="b", ctx=ast.Load())],
    ))
    with pytest.raises(KernelUnsupportedError, match="越子集"):
        kernel_evaluate_batch(tree, {"a": numpy.asarray([1.0]), "b": numpy.asarray([2.0])})
