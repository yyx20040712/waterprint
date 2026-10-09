"""公式双打印机测试（LaTeX/Typst math——B6 计算说明批 TDD 先红）。

面一：registry 全量对账——451 条公式双打印机零失败+逐公式快照 golden
（__snapshots__/formula_printers.{latex,typst}.txt——漂移即红；重录=
tools/report_golden.py --write 同批再生成）。基数与快照对账经子进程隔离
（_REGISTRY 进程内全局单例——tests/registry 等上游套件登记的临时公式
会污染计数，全量套件序下 451→464 实录；子进程=干净装载面，test_lock
子进程先例同款）。面二：四项生产化锚定（负项连接/Float 最短往返/
Min-Max 显式分派/log 基序）。面三：错误面——未知 formula_id 显式
InvalidFormulaError（禁吞错空串）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from sympy import Max, Min, Symbol, log, sympify

from waterprint.registry import InvalidFormulaError
from waterprint.report.formula_printers import (
    LatexPrinter,
    TypstMathPrinter,
    latex_of_expression,
    to_latex,
    to_typst_math,
    typst_of_expression,
)
from waterprint.units_lib import discover_units

# registry 全量基数（units_lib 四线 manifest+elevation.losses+network.manning
# 装载面——451 条，B6 前置#2 实测口径；业务线扩充时同步）
_EXPECTED_FORMULAS = 451

_SNAP_DIR = Path(__file__).resolve().parent / "__snapshots__"
_LATEX_SNAP = _SNAP_DIR / "formula_printers.latex.txt"
_TYPST_SNAP = _SNAP_DIR / "formula_printers.typst.txt"

# 子进程装载面脚本（干净 registry——stdout 出 JSON：count/latex/typst）
_SNAPSHOT_WORKER = """
import io, json, sys
from contextlib import redirect_stdout
with redirect_stdout(io.StringIO()):
    from waterprint.units_lib import discover_units
    discover_units()
    import waterprint.elevation.losses
    import waterprint.network.manning
from waterprint.registry.formulas.store import _REGISTRY
from waterprint.report.formula_printers import (
    latex_of_expression,
    typst_of_expression,
)
rows_latex, rows_typst = [], []
for fid in sorted(_REGISTRY):
    spec = _REGISTRY[fid].spec
    rows_latex.append(f"{fid}\\t{latex_of_expression(spec.expression, spec.symbols)}")
    rows_typst.append(f"{fid}\\t{typst_of_expression(spec.expression, spec.symbols)}")
print(json.dumps({
    "count": len(_REGISTRY),
    "latex": "\\n".join(rows_latex) + "\\n",
    "typst": "\\n".join(rows_typst) + "\\n",
}, ensure_ascii=False))
"""


@pytest.fixture(scope="module")
def clean_registry_outputs() -> dict[str, object]:
    """子进程干净装载面产物（count+双态全文——模块级共享单跑）。"""
    result = subprocess.run(
        [sys.executable, "-c", _SNAPSHOT_WORKER],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def _all_formula_ids() -> list[str]:
    """装载面全量 formula_id（discover_units+elevation+network——原 #2 同径）。"""
    import waterprint.elevation.losses
    import waterprint.network.manning
    from waterprint.registry.formulas.store import _REGISTRY

    discover_units()
    return sorted(_REGISTRY)


class TestFullCoverage:
    """registry 全量对账：双打印机零失败+基数钳制（子进程隔离面）。"""

    def test_registry_loads_expected_count(
        self, clean_registry_outputs: dict[str, object]
    ) -> None:
        assert clean_registry_outputs["count"] == _EXPECTED_FORMULAS

    def test_all_formulas_print_both_ways(self) -> None:
        ids = _all_formula_ids()
        failures = []
        for fid in ids:
            try:
                tex = to_latex(fid)
                typ = to_typst_math(fid)
            except (
                InvalidFormulaError,
                ValueError,
                TypeError,
                ArithmeticError,
            ) as exc:
                failures.append(f"{fid}: {type(exc).__name__}: {exc}")
                continue
            if not tex or not typ:
                failures.append(f"{fid}: 空输出（禁吞错产空串）")
        assert not failures, "\n".join(failures[:10])

    def test_latex_snapshot_golden(
        self, clean_registry_outputs: dict[str, object]
    ) -> None:
        assert (
            _LATEX_SNAP.read_text(encoding="utf-8")
            == clean_registry_outputs["latex"]
        )

    def test_typst_snapshot_golden(
        self, clean_registry_outputs: dict[str, object]
    ) -> None:
        assert (
            _TYPST_SNAP.read_text(encoding="utf-8")
            == clean_registry_outputs["typst"]
        )


class TestNegativeTermJoin:
    """生产化锚定①：Add 负项连接——a - b 形（禁「a + -b」形）。"""

    def test_typst_negative_term_joined_with_minus(self) -> None:
        a, b = Symbol("a"), Symbol("b")
        assert TypstMathPrinter().doprint(a - b) == "a - b"

    def test_typst_positive_then_negative(self) -> None:
        a, b, c = Symbol("a"), Symbol("b"), Symbol("c")
        assert TypstMathPrinter().doprint(a + b - c) == "a + b - c"

    def test_latex_negative_term_form(self) -> None:
        a, b = Symbol("a"), Symbol("b")
        out = LatexPrinter().doprint(a - b)
        assert "+ -" not in out and "a - b" in out


class TestFloatShortestRoundtrip:
    """生产化锚定②：Float 最短往返表示（str(Float) 尾噪防治）。"""

    def test_typst_float_no_trailing_noise(self) -> None:
        value = sympify("86400 * 0.00286")  # 求值折算产 15 位精度 Float
        assert TypstMathPrinter().doprint(value) == "247.104"

    def test_typst_float_repr_contract(self) -> None:
        """打印机 Float 面=repr(float) 契约（最短往返——17 位形态为该
        双精度值的诚实表示，非尾噪；str(Float) 15 位补零形态禁现）。"""
        for text in ("0.1 + 0.2", "0.48 + 0.3", "2.86 * 0.33333333"):
            value = sympify(text)
            out = TypstMathPrinter().doprint(value)
            assert out == repr(float(value))
            assert not out.endswith("000000000")  # str(Float) 尾噪形态禁现

    def test_expression_level_typst_float(self) -> None:
        out = typst_of_expression("x = 86400 * 0.00286", {})
        assert "247.104000000000" not in out
        assert "247.104" in out

    def test_latex_float_clean(self) -> None:
        out = latex_of_expression("x = 0.48 + 0.3", {})
        assert "0.780000000000000" not in out
        assert "0.78" in out


class TestMinMaxExplicitDispatch:
    """生产化锚定③：Min/Max 显式 _print_Max/_print_Min——sympy 的
    MinMaxBase MRO 不含 Function（MinMaxBase→AssocOp→Application 直跳），
    _print_Function 兜底不可达；删除显式分派即本锚红。"""

    def test_typst_max(self) -> None:
        a, b = Symbol("a"), Symbol("b")
        assert TypstMathPrinter().doprint(Max(a, b)) == "max(a, b)"

    def test_typst_min(self) -> None:
        a, b = Symbol("a"), Symbol("b")
        assert TypstMathPrinter().doprint(Min(a, b)) == "min(a, b)"

    def test_typst_max_with_numeric_arg(self) -> None:
        a = Symbol("a")
        # sympy 规范序：数值参数居前（确定性）
        assert TypstMathPrinter().doprint(Max(a, sympify("2.5"))) == "max(2.5, a)"


class TestLogBaseOrder:
    """生产化锚定④：log(x,10) 基序——Typst 形=log(值, 基)。"""

    def test_typst_log_base_ten(self) -> None:
        x = Symbol("x")
        carrier = log(x, 10, evaluate=False)  # FUNC_MAP 载体形态（保两参不塌缩）
        assert TypstMathPrinter().doprint(carrier) == "log(x, 10)"

    def test_log10_dsl_end_to_end_order(self) -> None:
        """registry DSL log10 → Typst log(值, 基) 形序（端到端——locals 映射）。"""
        out = typst_of_expression("y = log10(x)", {"x": Symbol("x")})
        assert out == "y = log(x, 10)"

    def test_log10_dsl_latex_base_subscript(self) -> None:
        out = latex_of_expression("y = log10(x)", {"x": Symbol("x")})
        expected = "y = " + "\\log_{10}" + "{\\left(x" + "\\right)}"
        assert out == expected

    def test_registry_sqrt_formula_sample(self) -> None:
        """registry 实样：根式/幂在双打印机面成形（快照 golden 外的行为锚）。"""
        ids = _all_formula_ids()
        assert ids, "registry 装载面非空"
        tex = to_latex(ids[0])
        assert "$" not in tex and tex.strip()


class TestErrorFace:
    """错误面：未知 formula_id 显式 InvalidFormulaError（禁吞错空串）。"""

    def test_to_latex_unknown_formula_raises(self) -> None:
        with pytest.raises(InvalidFormulaError):
            to_latex("GHOST-F9")

    def test_to_typst_unknown_formula_raises(self) -> None:
        with pytest.raises(InvalidFormulaError):
            to_typst_math("GHOST-F9")

    def test_bad_expression_wrapped_as_invalid_formula(self) -> None:
        with pytest.raises(InvalidFormulaError):
            latex_of_expression("x = = 1", {})
