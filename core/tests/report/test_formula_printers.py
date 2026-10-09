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


# ══════════════════════════════════════════════════════════════════
# B6 R1 回炉锚定（2026-10-09 拨4）：B1 Mul-Add 括号分组+W-A 原生词表
# +W-E sympify 闭世界——红先实录见 .workflow/b6-20261009/red-run-b6.txt
# 「R1」节。
# ══════════════════════════════════════════════════════════════════


class TestMulAddFactorGrouping:
    """B1（必修）：_print_Mul 对 Add 因子不包括号——乘积域邻接歧义使
    39 式 PDF 静默错值（k2+d1 双席互证）。修复=Add 因子统一括号分组
    （num 乘积路与 den 递归路共享 _print_product）。"""

    def test_typst_mul_add_factor_parenthesized(self) -> None:
        """单元锚定：q·y·(a-b)/5 → 分子 Add 因子括号分组（禁分配陷阱）。"""
        out = TypstMathPrinter().doprint(sympify("q*y*(a-b)/5"))
        assert out == "frac(q y (a - b), 5)"

    def test_typst_negative_mul_add_factor(self) -> None:
        """负号路径：-x(a+b) → 符号提出后 Add 因子整组括号（Rational
        系数×Add 在 sympy 构造期已分配展开——负号+Add 因子组合需符号
        系数承载，此为 _print_Add 负项经 Mul 时的同洞位）。"""
        out = TypstMathPrinter().doprint(sympify("-x*(a+b)"))
        assert out == "- x (a + b)"

    def test_typst_mixed_product_add_factor(self) -> None:
        """符号因子×Rational×Add：c·2(a-b) 规范序（Rational 分配入 Add）。"""
        out = TypstMathPrinter().doprint(sympify("2*(a-b)*c"))
        assert out == "c (2 a - 2 b)"

    def test_typst_ao_f24_registry_anchor(self) -> None:
        """registry 锚定（主控亲证形态）：AO-F24 搅拌功率——Add 因子
        (v_aerobic + v_anoxic) 整组括号（修复前=分子裸并号静默错值）。"""
        assert to_typst_math("AO-F24") == (
            "p_(s t i r) = frac(w_(s t i r   b i o) "
            "(v_(a n a e r o b i c) + v_(a n o x i c)), 1000)"
        )

    def test_typst_affected_formulas_semantic_equivalence(self) -> None:
        """双态语义等价（d1）：受影响 39 式抽样 6 式——Typst 串含与
        LaTeX 结构对应的括号分组（形态正确性断言，非漂移对账）。"""
        expected = {
            # LaTeX: \frac{432 q y \left(bod_{5 in} - bod_{5 out}\right)}{5}
            "AO-F6": "432 q_(a v g   d a i l y) y_(y i e l d) "
            "(b o d 5_(i n) - b o d 5_(o u t))",
            # LaTeX: i_{slope} \left(\frac{D}{2} - r_{1}\right)（隐蔽分配陷阱）
            "CC-F14": "frac(i_(s l o p e) (D - 2 r 1), 2)",
            # LaTeX: \frac{x_{mlss} \left(r_{external} + 1\right)}{r_{external}}
            "EC-F10": "frac(x_(m l s s) (r_(e x t e r n a l) + 1), "
            "r_(e x t e r n a l))",
            # LaTeX: \frac{h n \left(v_1+v_2+v_3+v_4\right)}{h_2}
            "KN-F15": "frac(h_(t o t a l) n w a l l_(c o e f) "
            "(v 1 + v 2 + v 3 + v 4), h 2)",
            # LaTeX: \frac{q \left(ss_{in gm} - ss_{out gm}\right)}{1000}
            "MS-F3": "frac(q_(a v g   d a i l y) "
            "(s s_(i n   g m) - s s_(o u t   g m)), 1000)",
            # LaTeX: \frac{1000 w_{ss}}{\rho_{sludge} \left(1 - p_{sludge}\right)}
            # （分母侧 Mul×Add 因子——den 递归路共享分组；rho=W-A 原生词）
            "KS-F7": "frac(1000 w_(s s), "
            "rho_(s l u d g e) (1 - p_(s l u d g e)))",
        }
        for fid, fragment in expected.items():
            assert fragment in to_typst_math(fid), f"{fid} 缺 Add 因子括号分组"


class TestNativeWordIdentifiers:
    """W-A（应修）：希腊/函数词直出原生标识符——不再字符空格拆分
    （pi→"p i" 三变量积=语义错值；eta/alpha/…/tan/sin 同族）。"""

    def test_typst_pi_native(self) -> None:
        assert TypstMathPrinter().doprint(Symbol("pi")) == "pi"

    def test_typst_greek_compound_base(self) -> None:
        """希腊词基座+普通下标：eta_pump → eta_(p u m p)（η 原生形）。"""
        assert TypstMathPrinter().doprint(Symbol("eta_pump")) == "eta_(p u m p)"

    def test_typst_function_word_base_and_greek_sub(self) -> None:
        """函数词基座+希腊下标：tan_theta → tan_(theta)。"""
        assert TypstMathPrinter().doprint(Symbol("tan_theta")) == "tan_(theta)"

    def test_typst_sub_word_function_tag(self) -> None:
        """下标段函数词：n_log → n_(log)（原生标识符）。"""
        assert TypstMathPrinter().doprint(Symbol("n_log")) == "n_(log)"

    def test_typst_nonvocab_word_unchanged(self) -> None:
        """词表外多词保持字符空格拆分（bod 三变量——既有语义面零动）。"""
        assert TypstMathPrinter().doprint(Symbol("bod")) == "b o d"
        assert TypstMathPrinter().doprint(Symbol("bod5_in")) == "b o d 5_(i n)"

    def test_typst_registry_greek_anchors(self) -> None:
        """registry 实样：451 命中面抽样——原生词直出（LaTeX 侧对照形）。"""
        assert to_typst_math("CC-F3") == "d_(r a w) = 2 sqrt(frac(f_(r e q), pi))"
        assert to_typst_math("NM-F2-Q") == (
            "q_(p a r t) = 0.7853981625 alpha v_(p a r t) d^2"
        )
        assert to_typst_math("KS-F5") == (
            "v_(l i n e) = frac(d_(d i s k) omega pi, 60)"
        )
        assert to_typst_math("XH-F4") == "w_(v s   d e g) = eta_(v s) w_(v s)"


class TestSympifyClosedWorld:
    """W-E（应修）：sympify 闭世界校验——RHS 解析后 free_symbols 与声明
    符号集求差非空=显式 InvalidFormulaError（防命名空间劫持/漏声明静默
    造符——"q+tiny" 的 tiny 拼写漂移即静默自由变量）。"""

    def test_undeclared_rhs_symbol_rejected(self) -> None:
        with pytest.raises(InvalidFormulaError, match="ghost"):
            typst_of_expression("y = q + ghost", {"q": Symbol("q")})

    def test_undeclared_bare_rhs_rejected(self) -> None:
        with pytest.raises(InvalidFormulaError):
            latex_of_expression("q * oops", {"q": Symbol("q")})

    def test_declared_symbols_pass(self) -> None:
        out = typst_of_expression(
            "y = q * r", {"q": Symbol("q"), "r": Symbol("r")}
        )
        assert out == "y = q r"

    def test_lhs_output_symbol_exempt(self) -> None:
        """LHS 输出符号=等式自身声明（DSL 惯例——451 全量 LHS 均不在
        symbols 声明集，闭世界仅施 RHS 侧）。"""
        out = typst_of_expression("y = 2 * q", {"q": Symbol("q")})
        assert out == "y = 2 q"
