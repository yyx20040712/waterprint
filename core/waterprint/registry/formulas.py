"""公式注册表：每条公式挂表达式/条文号/量纲签名，加载时静态校验（溯源基石）。

输入:  各单元/子系统登记的公式规格（FormulaSpec）+ apply 期数值绑定
输出:  查询 API、启动期量纲静态校验结果、apply 唯一求值正门（含迹记录）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T4 实现；镜像测试 tests/registry/test_formulas.py）
#
# 【公开接口】
#   class FormulaSpec(不可变)：
#       formula_id: str          全库唯一（如 "GB50014-6.6.11-AAO-volume"）
#       expression: str          人类可读表达式（符号定义见 symbols）
#       symbols: Mapping[符号→(DimKey 与中文含义)]——D6 同款归一：
#           构造收 (DimKey | str, str)，__post_init__ 归一为
#           (DimKey, str) 并快照为 MappingProxyType（T3A-01 防线首日
#           到位：外部改原容器不泄漏）
#       output_dim: DimKey       输出量纲签名（构造收 DimKey | str，
#           归一为 DimKey，D6）
#       norm_ref: str            规范条文号（GB 50014-2021 §x.x.x 等）+出处
#   class InvalidFormulaError(Exception)
#       登记与求值一切拒绝的统一载体（GR-11 族）
#   register(spec: FormulaSpec) -> None   登记+静态校验（非法=启动失败）
#   by_id(formula_id: str) -> FormulaSpec 未知 id = 领域异常（禁 None）
#   validate_all() -> ValidationReport
#       启动期对全部登记项重跑静态校验①~⑤收集失败、不抛（启动失败
#       判定归装配层 T7）；ValidationReport(frozen)：checked: int、
#       failures: tuple[(formula_id, 消息), ...]
#   apply(formula_id, bindings: Mapping[str→float],
#         ctx: (unit_id, condition_key),
#         sink: TraceSink | None = None) -> float
#       唯一求值正门：内部经 contracts/expr.py eval_checked 求值登记期
#       缓存的解析树（禁止 Python eval/exec/lambda），sink 非 None 时
#       记录一条 TraceNodeSpec 五字段快照（协议见 contracts/trace_api.py；
#       bindings 传副本——trace_api 无快照防线，T3A-01 复发位防线前移；
#       registry 只 import contracts——L1→L0 合法，永不 import L4 收集器）
#
# 【表达式 DSL】（T0.5 冻结；求值内核 = contracts/expr.py 共享受限求值器）
#   语法子集：算术表达式 = Name | Constant | + - * / ** | ( ) |
#      白名单函数 {min, max, abs, sqrt, log10}；不含比较/布尔/条件
#      （公式 = 纯数值；Compare/BoolOp/IfExp 属工况映射 DSL，公式侧拒绝）。
#   symbols：Mapping[符号→(DimKey, 中文含义)]；表达式引用的 Name 集合必须
#      == symbols 键集（多声明/漏声明 = 登记失败）；output_dim 人工声明
#      （不做量纲推导，量纲一致性由测试断言背书——D7 裁决）。
#   数值常量允许内联（如堰流 1.36 系数）：常量是公式自身的条文系数，
#      出处 = FormulaSpec.norm_ref（registry 本就是数值真源区，魔法数字
#      门禁放行）。
#
# 【行为规格】
#   R1 量纲静态校验（§12.1 元数据层）：登记期静态校验（全走
#      InvalidFormulaError，D7①~⑥）：
#      ① 表达式形态 "OUT = RHS" 或裸 "RHS"——恰含一个 =（多于一个拒）；
#         LHS 剥离后须匹配 [A-Za-z_][A-Za-z0-9_]*（输出符号，不参与
#         Name 集/量纲校验）；无 = 则整串为 RHS。
#      ② RHS 经 expr.parse_checked（ExprSyntaxError 以 from exc 包装）；
#         公式语法子集：解析树再拒 Compare/BoolOp/IfExp（工况映射 DSL
#         专属，公式侧禁）。
#      ③ Name 集双向 == symbols 键集（多声明/漏声明均拒）。
#      ④ 恒等式规则：RHS 为裸 Name 时 symbols[名].dim == output_dim
#         必须成立（唯一无推导可判的量纲规则）；多符号 RHS 量纲一致性
#         由未来单元包 golden 断言背书（R4，规格明文）。
#      ⑤ norm_ref 非空 str（R2：无条文出处禁止登记）。
#      ⑥ formula_id 非空且全库唯一（R5；重复登记即拒，禁"已存在静默
#         跳过"——改名 = 破坏可复算，只能新增）。
#   R2 公式语义依据 = 规范条文；旧实现仅作交叉对照，不作依据（§5 迁移原则）。
#   R3 apply 是唯一求值路径：绕过 apply 直接抄公式代码 = 评审拒绝
#      （否则计算迹断链，§16 A1"注册表与实现漂移"防线）。
#   R4 实现与注册表一致性由测试背书：每条公式至少一个 golden 数值断言
#      + trace 中 formula_id 与实参值域校验（A1 缓解措施，落进单元包测试）。
#   R5 formula_id 稳定：进入项目计算迹与审计报告，改名 = 破坏可复算，
#      必须新增不修改。
#   R6 apply 拒绝路径（D8）：未知 id 拒；bindings 键集 == symbols 键集
#      （缺/多键拒，消息含 formula_id+键名）；绑定值非有限拒（GR-02
#      输入即拒）；原生数值异常（除零/溢出/定义域，expr R5）from exc
#      包装上抛；结果非有限拒（GR-02 运算产生转领域异常）。
#
# 【T4 实现注记】（总控简报 D7/D8/D9 裁决，2026-08-24）
#   - 不做 pint 量纲推导（规格明令 output_dim 人工声明；全量纲代数需
#     quantity 暴露 pint 面或扩 API，明确不建）。
#   - 内部登记表：模块级 dict[str, _Entry]（进程内唯一真源），条目持
#     spec+登记期缓存解析树（仅内存，不落盘）。
#   - 零预置公式（D10）：本任务只交付机制；真实公式登记归单元包任务
#     （数值纪律：条文系数须 norms 摘录+手算对照+签字——registry 虽在
#     魔法数字白名单，仍禁编造）。本文件当前零数值字面量。
#
# 【测试要求】登记→查询往返、量纲不匹配拒绝、norm_ref 必填、
#   apply 产生一条完整 TraceNode。
#
# 【参照】重写计划 §3-5/§12.1/§16 A1；简报 T4 D7/D8/D9/D10
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import final

from waterprint.contracts.expr import ExprSyntaxError, eval_checked, parse_checked
from waterprint.contracts.quantity import DimKey
from waterprint.contracts.trace_api import TraceNodeSpec, TraceSink


class InvalidFormulaError(Exception):
    """公式登记/求值非法（登记期静态校验拒绝 + apply 一切拒绝路径）。"""


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
        """symbols/output_dim 归一（D6）+ symbols 只读快照（T3A-01）。"""
        normalized: dict[str, tuple[DimKey, str]] = {}
        for symbol, pair in self.symbols.items():
            dim, meaning = pair
            normalized[symbol] = (
                _normalize_dim(dim, f"symbols[{symbol!r}].dim"),
                meaning,
            )
        object.__setattr__(self, "symbols", MappingProxyType(normalized))
        object.__setattr__(
            self, "output_dim", _normalize_dim(self.output_dim, "output_dim")
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
    names = frozenset(
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    )
    declared = frozenset(symbols)
    if names != declared:
        raise InvalidFormulaError(
            f"公式 {spec.formula_id!r} 表达式 Name 集与 symbols 键集不一致："
            f"表达式引用 {sorted(names)}，声明 {sorted(declared)}"
            "（多声明/漏声明均拒——双向==）"
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


def apply(
    formula_id: str,
    bindings: Mapping[str, float],
    ctx: tuple[str, str],
    sink: TraceSink | None = None,
) -> float:
    """唯一求值正门（R3/R6）：静态绑定校验 → 缓存树求值 → 有限性 → 落迹。"""
    entry = _REGISTRY.get(formula_id)
    if entry is None:
        raise InvalidFormulaError(
            f"未登记公式：{formula_id!r}（apply 只消费 register 登记项）"
        )
    expected = frozenset(entry.spec.symbols)
    given = frozenset(bindings)
    if given != expected:
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 求值绑定键集与 symbols 键集不一致："
            f"缺 {sorted(expected - given)}，多 {sorted(given - expected)}"
            f"（应恰为 {sorted(expected)}）"
        )
    values: dict[str, float] = {}
    for symbol, value in bindings.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidFormulaError(
                f"公式 {formula_id!r} 符号 {symbol!r} 的绑定值必须为数值："
                f"得到 {value!r}"
            )
        if not isfinite(value):
            raise InvalidFormulaError(
                f"公式 {formula_id!r} 符号 {symbol!r} 的绑定值非有限："
                f"{value!r}（GR-02 输入即拒）"
            )
        values[symbol] = float(value)
    try:
        outcome = eval_checked(entry.tree, values)
    except (ArithmeticError, ValueError) as exc:
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 求值数值域错误（除零/溢出/定义域，"
            f"expr R5 原生异常包装）：{exc}"
        ) from exc
    if isinstance(outcome, bool) or not isinstance(outcome, int | float):
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 求值结果非数值：{outcome!r}"
            "（公式=纯数值；布尔面属工况映射 DSL）"
        )
    result = float(outcome)
    if not isfinite(result):
        raise InvalidFormulaError(
            f"公式 {formula_id!r} 求值结果非有限：{result!r}"
            "（GR-02 运算产生即转领域异常）"
        )
    if sink is not None:
        sink.record(
            TraceNodeSpec(
                formula_id=formula_id,
                unit_id=ctx[0],
                condition_key=ctx[1],
                bindings=dict(bindings),
                result=result,
            )
        )
    return result
