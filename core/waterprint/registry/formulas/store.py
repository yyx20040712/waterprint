"""公式登记件：注册表真源+登记期静态校验+查询面（b2-s2 拆自 formulas.py；
原规格头=formulas.py 删除笔+定案 §4.6 锚号体系）。

输入:  各单元/子系统经 register 登记的 FormulaSpec（条目留 manifest 原位）
输出:  _REGISTRY（进程内唯一真源）、register/by_id/norm_ref_of/
       validate_all、ValidationReport
"""

# ══════════════════════════════════════════════════════════════════
# 规格（R1 静态校验①~⑥，全走 InvalidFormulaError；D7 裁决）：
#   ① 表达式恰含一个 =（LHS 须匹配 [A-Za-z_][A-Za-z0-9_]*）或裸 RHS
#   ② RHS 受限解析+拒 Compare/BoolOp/IfExp（解析器=spec 件）
#   ③ Name 集双向 == symbols 键集（ALLOWED_FUNCS 白名单函数名豁免
#      不计入——M1b D4：调用位函数由求值器白名单实现）
#   ④ 裸 Name 右式恒等式：symbols[名].dim == output_dim（唯一无推导
#      可判的量纲规则；多符号 RHS 量纲一致性由单元包 golden 断言背书）
#   ⑤ norm_ref 非空 str（R2：无条文出处禁止登记）
#   ⑥ formula_id 非空且全库唯一（R5；重复登记即拒，禁"已存在静默
#      跳过"——改名=破坏可复算，只能新增）
#   validate_all：启动期对全部登记项重跑①~⑤收集失败、不抛（启动
#   失败判定归装配层 T7）。零预置公式（D10）：本件只交付机制。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import final

from waterprint.contracts.expr import ALLOWED_FUNCS
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas.spec import (
    FormulaSpec,
    InvalidFormulaError,
    _normalize_dim,
    _parse_rhs,
    _split_expression,
)


@dataclass(frozen=True)
@final
class ValidationReport:
    """启动期静态校验汇总（D9）：checked 登记项数 + 逐项失败（id, 消息）。"""

    checked: int
    failures: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
@final
class _Entry:
    """登记项内部形态：spec + 登记期缓存的解析树（仅内存，不落盘）。"""

    spec: FormulaSpec
    tree: ast.Expression


# 进程内唯一真源：formula_id → _Entry（R5：只能新增不能改名）。
_REGISTRY: dict[str, _Entry] = {}


def _validate(spec: FormulaSpec) -> ast.Expression:
    """D7①~⑤ 静态校验（⑥唯一性在 register 内查表）；返回解析树。

    symbols/output_dim 局部幂等再归一（运行时 __post_init__ 已归一，
    此处窄化供类型面——与 dimensions.register_dimension 同款处理）。
    """
    rhs, _symbol = _split_expression(spec.expression)
    symbols: dict[str, tuple[DimKey, str]] = {
        symbol: (_normalize_dim(pair[0], f"symbols[{symbol!r}].dim"), pair[1])
        for symbol, pair in spec.symbols.items()
    }
    output_dim = _normalize_dim(spec.output_dim, "output_dim")
    tree = _parse_rhs(rhs, symbols)
    # M1b D4 豁免：白名单函数名（调用位）不计入符号声明双向==——函数由
    # expr 求值器白名单实现，非符号绑定（单元包占位符号+float(0) 绑定废止）。
    names = frozenset(
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    ) - ALLOWED_FUNCS
    declared = frozenset(symbols)
    if names != declared:
        raise InvalidFormulaError(
            f"公式 {spec.formula_id!r} 表达式 Name 集与 symbols 键集不一致："
            f"表达式引用 {sorted(names)}，声明 {sorted(declared)}"
            "（多声明/漏声明均拒——双向==；白名单函数名豁免不计入，M1b D4）"
        )
    if isinstance(tree.body, ast.Name):
        name = tree.body.id
        dim = symbols[name][0]
        if dim != output_dim:
            raise InvalidFormulaError(
                f"公式 {spec.formula_id!r} 恒等式量纲不符：{name} 声明 "
                f"{dim.value}，output_dim={output_dim.value}"
                "（裸 Name 右式唯一可判规则，D7④）"
            )
    if not isinstance(spec.norm_ref, str) or not spec.norm_ref:
        raise InvalidFormulaError(
            f"公式 {spec.formula_id!r} 的 norm_ref 必须为非空字符串："
            f"得到 {spec.norm_ref!r}（R2——无条文出处禁止登记）"
        )
    if not isinstance(spec.formula_id, str) or not spec.formula_id:
        raise InvalidFormulaError(
            f"formula_id 必须为非空字符串：得到 {spec.formula_id!r}（R5）"
        )
    return tree


def register(spec: FormulaSpec) -> None:
    """登记正门：D7①~⑥ 全量静态校验，非法 = 启动失败（非运行时警告）。"""
    tree = _validate(spec)
    if spec.formula_id in _REGISTRY:
        raise InvalidFormulaError(
            f"formula_id 重复登记：{spec.formula_id!r}"
            "（R5 全库唯一，重复绑定即拒——禁'已存在静默跳过'；"
            "改名=破坏可复算，只能新增）"
        )
    _REGISTRY[spec.formula_id] = _Entry(spec=spec, tree=tree)


def by_id(formula_id: str) -> FormulaSpec:
    """查询正门：未知 id = 领域异常（禁止返回 None 假装成功）。"""
    entry = _REGISTRY.get(formula_id)
    if entry is None:
        raise InvalidFormulaError(
            f"未登记公式：{formula_id!r}（合法公式经 register 登记；"
            "formula_id 进入项目计算迹与审计报告，R5）"
        )
    return entry.spec


def validate_all() -> ValidationReport:
    """D9：对全部登记项重跑①~⑤收集失败、不抛（启动失败判定归装配层 T7）。"""
    failures: list[tuple[str, str]] = []
    for formula_id, entry in sorted(_REGISTRY.items()):
        try:
            _validate(entry.spec)
        except InvalidFormulaError as exc:
            failures.append((formula_id, str(exc)))
    return ValidationReport(checked=len(_REGISTRY), failures=tuple(failures))


def norm_ref_of(formula_id: str) -> str:
    """只读查询面：formula_id → norm_ref 条文号（UF-43① collector 反查口）。"""
    return by_id(formula_id).norm_ref
