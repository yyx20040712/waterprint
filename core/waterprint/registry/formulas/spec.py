"""公式规格件：FormulaSpec 声明面+表达式 DSL 解析（b2-s2 拆自 formulas.py）。

输入:  单元包 manifest 构造 FormulaSpec 的字段值（symbols/output_dim
       构造收 DimKey | str，__post_init__ 归一）
输出:  InvalidFormulaError（登记/求值统一拒绝载体）、FormulaSpec
       （不可变五字段）、_split_expression/_parse_rhs（D7①②解析器）、
       _normalize_dim（D6 归一——store 件复用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（拆自 formulas.py 规格头——完整原文见 git 历史；T4 冻结）：
#   FormulaSpec 五字段：formula_id（全库唯一，R5）/expression（"OUT =
#   RHS" 或裸 "RHS"）/symbols Mapping[符号→(DimKey, 中文含义)]（构造
#   收 (DimKey | str, str) 归一为 (DimKey, str)，__post_init__ 快照
#   MappingProxyType——T3A-01 外部改原容器不泄漏；值先过形态守卫：
#   非二元组拒，消息含 symbol 键+原值 repr，ARCH1 D1d，杜绝 2 字符
#   str 静默解包后消息失真）/output_dim（同款归一，D6）/norm_ref
#   （规范条文号+出处，R2 无条文出处禁止登记）。
#   表达式 DSL（T0.5 冻结；求值内核=contracts/expr.py 受限求值器）：
#   算术子集 Name|Constant|+ - * / **|( )|白名单函数 {min,max,abs,
#   sqrt,log10}；禁比较/布尔/条件（Compare/BoolOp/IfExp 属工况映射
#   DSL，公式侧拒绝——_parse_rhs 收窄）；数值常量允许内联（条文系数，
#   registry=数值真源区，魔法数字门禁放行）。
#   本文件数值字面量仅 _SYMBOL_PAIR_LEN=2（宪法 §3 允许集 {0,1,2,10}）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, final

from waterprint.contracts.expr import ExprSyntaxError, parse_checked
from waterprint.contracts.quantity import DimKey


class InvalidFormulaError(Exception):
    """公式登记/求值非法（登记期静态校验拒绝 + apply 一切拒绝路径）。"""


# symbols 值二元组长度（ARCH1 D1d 形态守卫；Final 常量化解 PLR2004，
# 字面量 2 在宪法 §3 允许集 {0,1,2,10} 内）。
_SYMBOL_PAIR_LEN: Final[int] = 2

# 输出符号文法（D7①）：LHS 剥离 = 后须匹配（不参与 Name 集/量纲校验）。
_OUTPUT_SYMBOL_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _normalize_dim(value: DimKey | str, what: str) -> DimKey:
    """D6 归一：DimKey | str → DimKey（非法字符串拒，消息含原值）。"""
    if isinstance(value, DimKey):
        return value
    if not isinstance(value, str):
        raise InvalidFormulaError(
            f"{what} 必须为 DimKey 或其成员名字符串：得到 {value!r}"
        )
    try:
        return DimKey(value)
    except ValueError as exc:
        members = sorted(member.value for member in DimKey)
        raise InvalidFormulaError(
            f"{what} 非法：{value!r}（合法 {members}）"
        ) from exc


@dataclass(frozen=True)
@final
class FormulaSpec:
    """单条公式声明：ID + 表达式 + 符号量纲表 + 输出量纲 + 条文出处。

    symbols 构造收 Mapping[符号→(DimKey | str, str)]，__post_init__ 归一
    为 (DimKey, str) 并快照 MappingProxyType（外部改原容器不泄漏，
    T3A-01 防线首日到位）；output_dim 同款归一（D6）。
    """

    formula_id: str
    expression: str
    symbols: Mapping[str, tuple[DimKey | str, str]]
    output_dim: DimKey | str
    norm_ref: str

    def __post_init__(self) -> None:
        """symbols/output_dim 归一（D6）+ symbols 值形态守卫（ARCH1 D1d）
        + symbols 只读快照（T3A-01）。"""
        normalized: dict[str, tuple[DimKey, str]] = {}
        for symbol, pair in self.symbols.items():
            if not isinstance(pair, tuple) or len(pair) != _SYMBOL_PAIR_LEN:
                raise InvalidFormulaError(
                    f"symbols[{symbol!r}] 值形态非法：{pair!r}"
                    "（期望 (DimKey|str, str) 二元组——ARCH1 D1d：杜绝 2 字符"
                    " str 静默解包后消息失真）"
                )
            dim, meaning = pair
            normalized[symbol] = (
                _normalize_dim(dim, f"symbols[{symbol!r}].dim"),
                meaning,
            )
        object.__setattr__(self, "symbols", MappingProxyType(normalized))
        object.__setattr__(
            self, "output_dim", _normalize_dim(self.output_dim, "output_dim")
        )


def _split_expression(expression: str) -> tuple[str, str | None]:
    """D7①：拆分 (RHS, 输出符号|None)；恰含一个 = 或裸 RHS，非法即拒。"""
    if not isinstance(expression, str) or not expression:
        raise InvalidFormulaError(
            f"expression 必须为非空字符串：得到 {expression!r}"
        )
    if expression.count("=") > 1:
        raise InvalidFormulaError(
            f"表达式含多个 =：{expression!r}（恰允许一个——输出符号 = 右式）"
        )
    if "=" in expression:
        lhs, rhs = expression.split("=")
        symbol = lhs.strip()
        if not _OUTPUT_SYMBOL_PATTERN.fullmatch(symbol):
            raise InvalidFormulaError(
                f"输出符号非法：{symbol!r}（须匹配 [A-Za-z_][A-Za-z0-9_]*，"
                "不参与 symbols 声明与量纲校验）"
            )
        return rhs.strip(), symbol
    return expression.strip(), None


def _parse_rhs(rhs: str, symbols: Mapping[str, tuple[DimKey, str]]) -> ast.Expression:
    """D7②：RHS 受限解析（ExprSyntaxError 包装）+ 公式语法子集收窄。"""
    try:
        tree = parse_checked(rhs, frozenset(symbols))
    except ExprSyntaxError as exc:
        raise InvalidFormulaError(
            f"表达式右式非受限 DSL：{rhs!r}（{exc}）"
        ) from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare | ast.BoolOp | ast.IfExp):
            raise InvalidFormulaError(
                f"公式语法子集拒绝 {type(node).__name__}：{ast.unparse(node)}"
                "（Compare/BoolOp/IfExp 属工况映射 DSL，公式=纯数值）"
            )
    return tree
