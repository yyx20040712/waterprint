"""公式双打印机：registry 表达式 → LaTeX／Typst math 双态字符串。

路径:   waterprint/report/formula_printers.py
职责:   FormulaSpec.expression（"OUT = RHS" 或裸 RHS——Python 算术子集+
        五白名单函数）经 sympify 转表达式树后双态打印：LatexPrinter 供
        web KaTeX 与说明书数学块／溯源附录；TypstMathPrinter 供 PDF 路
        （引擎中立：公式源=sympy 树单源，换引擎=换渲染器不动树）。
        生产化 DoD 四项（原型已知瑕疵）：①Add 负项并号连接（a - b 形）
        ②Float 最短往返表示（str(Float) 尾噪防治）③Min/Max 显式
        _print_Max/_print_Min（MinMaxBase 的 MRO 不含 Function——
        _print_Function 兜底不可达，删显式分派即锚定测试红）④log(x,10)
        基序（Typst log(值, 基) 形序）。
输入:   registry by_id 取 FormulaSpec（formula_id 正门）；或表达式级
        直给（expression+symbols——附录装配单查省一次 by_id）。
输出:   to_latex(formula_id)／to_typst_math(formula_id) 入口串；
        LatexPrinter／TypstMathPrinter 打印机类（doprint）；
        latex_of_expression／typst_of_expression 表达式级入口。
        451 全量快照重录在 tools/report_golden.py --write（本件零
        units_lib/elevation/network import——report 节点边域纪律）。
禁区:   禁吞错产空串——未知 formula_id=InvalidFormulaError 直抛（by_id
        面沿承）；表达式不可 sympify=解析异常族包装 InvalidFormulaError。
        禁改输入 spec（registry 只读消费）。
参照:   .workflow/b6-20261009/formula-latex-coverage.md 与两原型脚本
        （451/451 LaTeX+Typst 全量零错实证——sympy 1.14.0）。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import sympy  # type: ignore[import-untyped]  # sympy 无 py.typed（pandas 先例同款记档）
from sympy import (
    Abs,
    Eq,
    Max,
    Min,
    Symbol,
    log,
    sympify,
)
from sympy.core.sympify import (  # type: ignore[import-untyped]  # 同上
    SympifyError,
)
from sympy.printing.latex import (  # type: ignore[import-untyped]  # 同上
    LatexPrinter as _SympyLatexPrinter,
)
from sympy.printing.printer import (  # type: ignore[import-untyped]  # 同上
    Printer,
)

from waterprint.registry import InvalidFormulaError, by_id

__all__ = [
    "FUNC_MAP",
    "LatexPrinter",
    "TypstMathPrinter",
    "latex_of_expression",
    "to_latex",
    "to_typst_math",
    "typst_of_expression",
]

# 白名单函数映射（registry DSL 五函数——sympify locals 注入；log10 保
# 两参形态不塌缩为对数商：log(x, 10, evaluate=False)）
# 幂底包裹阈值（字符数超此值即加括号防邻接歧义——原型 451 条编译实证口径；
# Final 常量化解 PLR2004，值 2 在宪法 §3 允许集 {0,1,2,10} 内——spec.py 先例）
_POW_BASE_WRAP_ABOVE: Final[int] = 2

# 原生词表（W-A——B6 R1 回炉 2026-10-09）：Typst math 原生标识符=希腊
# 字母全族+函数词（451 全量扫描命中面：pi 31 处/eta 14/rho 6/sin 6/
# alpha 10/max 5/min 5/tan 3/xi 3/zeta 3/beta 4/theta 2/lambda 2/
# mu 1/omega 1/delta 1/log 1——cos 零命中入表为对称面）。词表内整词
# 直出（不再字符空格拆分——"pi"拆作"p i"=三变量积语义错值）；词表外
# 多词保持既有字符空格拆分（bod→"b o d"——KaTeX 渲染形同构面零动）。
# 注记申报：LaTeX 侧 sympy 自动 \mathcal 吞名（h_lo→h_{\mathcal{lo}}
# 二字母下标族）=接受现状（LaTeX 快照零动锚定；Typst 侧无对应脚本字
# 形，h_(l o) 普通斜体形与 LaTeX \mathcal 呈排版面分歧——数学语义同
# 竖线/字形族恒等，双席审报备口径）。
_NATIVE_WORDS: Final[frozenset[str]] = frozenset({
    # 希腊字母（Typst math 原生符号——与 sympy LaTeX \alpha 族同构）
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
    "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi",
    "rho", "sigma", "tau", "phi", "chi", "psi", "omega",
    # 函数词（Typst math 原生函数名——正体呈现，与 LaTeX \tan 族对应）
    "sin", "cos", "tan", "log", "min", "max",
})

FUNC_MAP: dict[str, Any] = {
    "min": Min,
    "max": Max,
    "abs": Abs,
    "sqrt": sympy.sqrt,
    "log10": lambda x: log(x, 10, evaluate=False),
}


def _split(expression: str) -> tuple[str | None, str]:
    """拆分 (输出符号|None, RHS)——registry 保证恰一个 = 或裸 RHS。"""
    if "=" in expression:
        lhs, rhs = (part.strip() for part in expression.split("=", 1))
        return lhs, rhs
    return None, expression.strip()


def _sympify_side(text: str, symbols: Mapping[str, Any]) -> sympy.Expr:
    """单侧文本 → sympy 表达式（locals=函数映射∪显式符号表）。

    解析异常族（SympifyError/TypeError/SyntaxError）包装 InvalidFormulaError
    （领域异常——禁让底层解析错裸穿服务面）。
    """
    locals_map: dict[str, Any] = dict(FUNC_MAP)
    locals_map.update({name: Symbol(name) for name in symbols})
    try:
        expr = sympify(text, locals=locals_map)
    except (SympifyError, TypeError, SyntaxError) as exc:
        raise InvalidFormulaError(
            f"公式表达式不可转换为 sympy 树：{text!r}"
            f"（{type(exc).__name__}: {exc}）"
        ) from exc
    if not isinstance(expr, sympy.Expr):
        raise InvalidFormulaError(
            f"公式表达式非 sympy 表达式节点：{text!r} → {type(expr).__name__}"
        )
    return expr


def _assert_closed_world(
    expr: sympy.Expr, symbols: Mapping[str, Any], text: str
) -> None:
    """闭世界校验（W-E）：解析后自由符号 ⊆ 声明符号集。

    sympify 对未知裸名自动造 Symbol（命名空间劫持面）——声明集外符号
    非空=显式 InvalidFormulaError（防漏声明静默自由变量：RHS 拼写漂移
    即「ghost」形）。施加面=RHS 侧（LHS 输出符号=等式自身声明，DSL
    惯例 451 全量 LHS 均不在 symbols 声明集——闭世界仅施输入面）。
    """
    undeclared = {s.name for s in expr.free_symbols} - set(symbols)
    if undeclared:
        raise InvalidFormulaError(
            f"公式表达式含未声明符号 {sorted(undeclared)}"
            f"（闭世界——自由符号必须 ⊆ 声明符号集，防命名空间静默造符）："
            f"{text!r}"
        )


def _float_shortest(value: sympy.Float) -> str:
    """Float 最短往返表示（DoD②——str(Float) 产 247.104000000000 尾噪，
    repr(float(...)) 取最短双精度往返串）。"""
    return repr(float(value))


class LatexPrinter(_SympyLatexPrinter):  # type: ignore[misc]  # sympy 无 stubs 基类面
    """LaTeX 打印机（KaTeX 消费面——sympy LatexPrinter 派生）。

    覆盖点：_print_Float 最短往返（防尾噪）+指数形态组版；_print_log
    两参基序（sympy latex 对 log(x, 10) 只印值丢基——补 \\log_{10} 形）。
    """

    def _print_Float(self, expr: sympy.Float) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        text = _float_shortest(expr)
        if "e" in text:
            mantissa, _, exponent = text.partition("e")
            return f"{mantissa} \\cdot 10^{{{exponent}}}"
        return text

    def _print_log(self, expr: sympy.Expr) -> str:
        args = expr.args
        if len(args) > 1:  # log10 载体：log(值, 基) → \log_{基}
            arg, base = args
            return rf"\log_{{{self._print(base)}}}{{\left({self._print(arg)}\right)}}"
        return str(super()._print_log(expr))


class TypstMathPrinter(Printer):  # type: ignore[misc]  # sympy 无 stubs 基类面
    """Typst math 打印机（PDF 路消费面——受限子集专用）。

    多词符号=字符空格分隔（Typst 语义与 LaTeX 相反：连续字母=单标识符，
    空格=独立斜体变量——空格分隔后与 KaTeX 渲染形同构）；Min/Max 显式
    分派（DoD③——MRO 不含 Function）；Add 负项并号（DoD①）。
    """

    def _spaced(self, text: str) -> str:
        """多词段字符空格分隔（"bod"→"b o d"；下划线段同律）。

        W-A：下划线分段后词表内整词直出原生标识符（"sin_alpha"→
        "sin   alpha"/"pi"→"pi"——与 sympy LaTeX \\alpha 族翻译层同构），
        词表外段保持字符拆分；段间三空格=既有字符流形态（Typst 数学
        域空白不敏感——呈现零变）。
        """
        mapped = [
            part if part in _NATIVE_WORDS else " ".join(part)
            for part in text.split("_")
        ]
        return "   ".join(mapped)

    def _print_str(self, s: str) -> str:
        base, *subs = str(s).split("_", 1)
        out = self._spaced(base)
        if subs:
            out += f"_({self._spaced(subs[0])})"
        return out

    def _print_Symbol(self, expr: sympy.Symbol) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        return self._print_str(expr.name)

    def _print_Rational(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        if expr.q == 1:
            return str(self._print(expr.p))
        return f"frac({self._print(expr.p)}, {self._print(expr.q)})"

    def _print_Integer(self, expr: sympy.Integer) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        return str(expr.p)

    def _print_Float(self, expr: sympy.Float) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        text = _float_shortest(expr)
        if "e" in text:
            mantissa, _, exponent = text.partition("e")
            return f"{mantissa} times 10^({exponent})"
        return text

    def _print_Add(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        chunks: list[str] = []
        for index, term in enumerate(expr.as_ordered_terms()):
            negative = term.could_extract_minus_sign()
            body = self._print(-term) if negative else self._print(term)
            if index == 0:
                chunks.append(f"- {body}" if negative else body)
            else:
                chunks.append(f"- {body}" if negative else f"+ {body}")
        return " ".join(chunks)

    def _print_product(self, factors: tuple[sympy.Expr, ...]) -> str:
        """乘积因子串接（B1——B6 R1 回炉）：Add 因子统一括号分组。

        Typst 乘积域=邻接即乘，Add 因子不分组即「w v_a + v_n」形——
        分配陷阱使 39 式 PDF 静默错值（k2+d1 双席互证）；num 乘积路与
        den 递归路（_print(den)→_print_Mul）共享本件。
        """
        parts: list[str] = []
        for factor in factors:
            text = self._print(factor)
            if isinstance(factor, sympy.Add):
                text = f"({text})"
            parts.append(text)
        return " ".join(parts) if len(parts) > 1 else (parts[0] if parts else "")

    def _print_Mul(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        num, den = expr.as_numer_denom()
        negative = num.could_extract_minus_sign()
        factors = sympy.Mul.make_args(-num if negative else num)
        out = self._print_product(factors)
        if negative:
            out = f"- {out}"
        if den != 1:
            out = f"frac({out or '1'}, {self._print(den)})"
        return out

    def _print_Pow(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        base, exp = expr.args
        if exp == sympy.Rational(1, 2):  # 平方根判定（1/2 幂）
            return f"sqrt({self._print(base)})"  # 平方根显式 sqrt 形
        b = self._print(base)
        if len(b) > _POW_BASE_WRAP_ABOVE and not b.startswith("("):
            b = f"({b})"
        e = self._print(exp)
        if len(e) > 1 and not e[0].isdigit():
            e = f"({e})"
        return f"{b}^{e}"

    def _print_Equality(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        return f"{self._print(expr.lhs)} = {self._print(expr.rhs)}"

    def _print_Max(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        return f"max({', '.join(self._print(a) for a in expr.args)})"

    def _print_Min(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        return f"min({', '.join(self._print(a) for a in expr.args)})"

    def _print_Function(self, expr: sympy.Expr) -> str:  # noqa: N802  # sympy 打印机协议方法名（_print_<Type>）
        name = type(expr).__name__
        if name == "Abs":
            return f"abs({self._print(expr.args[0])})"
        return f"{name}({', '.join(self._print(a) for a in expr.args)})"

    def _print_log(self, expr: sympy.Expr) -> str:
        args = expr.args
        if len(args) == 1:
            return f"ln({self._print(args[0])})"
        return f"log({self._print(args[0])}, {self._print(args[1])})"  # log(值, 基)


def _eq_of(expression: str, symbols: Mapping[str, Any]) -> sympy.Expr:
    """表达式 → Eq（含输出符号）或裸 RHS（RHS 侧闭世界校验——W-E）。"""
    lhs, rhs = _split(expression)
    rhs_expr = _sympify_side(rhs, symbols)
    _assert_closed_world(rhs_expr, symbols, rhs)
    if lhs is None:
        return rhs_expr
    return Eq(_sympify_side(lhs, symbols), rhs_expr)


def latex_of_expression(
    expression: str, symbols: Mapping[str, Any]
) -> str:
    """表达式级 LaTeX 入口（附录装配消费——spec 已在手省一次 by_id）。"""
    return str(LatexPrinter().doprint(_eq_of(expression, symbols)))


def typst_of_expression(
    expression: str, symbols: Mapping[str, Any]
) -> str:
    """表达式级 Typst math 入口（PDF 渲染路消费——B6 段 4 接线）。"""
    return str(TypstMathPrinter().doprint(_eq_of(expression, symbols)))


def to_latex(formula_id: str) -> str:
    """公式 ID → LaTeX（registry by_id 正门——未知 id 显式 InvalidFormulaError）。"""
    spec = by_id(formula_id)
    return latex_of_expression(spec.expression, spec.symbols)


def to_typst_math(formula_id: str) -> str:
    """公式 ID → Typst math（同 to_latex——错误面同律禁吞错）。"""
    spec = by_id(formula_id)
    return typst_of_expression(spec.expression, spec.symbols)
