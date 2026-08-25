"""布尔约束过滤（含 UI 覆盖）：可行方案子集与逐约束通过矩阵。

输入:  枚举 DataFrame + 约束集（constraint_kb 迁移 51 条 + UI 临时覆盖）
输出:  可行子集 + 每行×每约束的通过矩阵（供 diagnose）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_constraints.py）
#
# 【公开接口】
#   class Constraint(不可变)：key、表达式 DSL（受限比较式：
#      field_id 与常数的 </<=/>/>=/∈ 关系 + AND 组合）、
#      source（constraint_kb 键或 "ui:临时覆盖"）、severity
#      （contracts.Severity，默认 ERROR=硬性过滤）
#   apply_constraints(df, constraints) -> FilterResult
#   class FilterResult(不可变)：feasible（可行子集位置索引）、
#       pass_matrix（DataFrame 布尔矩阵，行=方案 列=约束）
#   class InvalidConstraintError(Exception)：DSL 非法（未知字段/
#       非法算符/非法常数/空表达式）——GR-11 族，本文件定义
#
# 【行为规格】
#   R1 约束是数据：知识库 51 条（旧 constraint_hints 迁移）+ UI 覆盖，
#      表达式走受限 DSL（白名单字段 ID 与运算符），禁止任意 Python
#      lambda 注入（安全与可序列化）。
#   R2 pass_matrix 必须完整产出（哪怕全 False）——diagnose 的输入，
#      禁止只返回可行集丢弃失败信息（否则无解诊断不可能）。
#   R3 UI 覆盖不落盘为代码：临时覆盖只在会话内（design 态可保存勾选，
#      表达式本体永远来自知识库数据）。
#   R4 约束求值向量化（numpy 布尔运算），万级行 <1s（§18.1 预算内）。
#
# 【DSL 口径】子句 = field_id OP 常数，OP ∈ {<, <=, >, >=, ∈}；组合 =
#   子句 " and " 连接（AND 语义）；∈ 右侧为方括号数档列表
#   [v1, v2, ...]。常数来自 Constraint 数据（R1），代码零数值注入；
#   常数原子有限性守卫（1e999→inf 拒，M-3 R1 轮补——grid._number
#   同口径）。pass_matrix 列名 = 约束表达式串（锁定测试口径——列名即
#   约束的可读展开，diagnose 侧调用方按表达式串对账约束键）。
#   severity 本批为元数据面（全级别一律硬过滤参与 feasible）——WARN
#   软语义归 constraint_kb 数据批/server 批定义（M-4 R1 注记）。
#
# 【测试要求】布尔矩阵正确性（含全 False 用例）、UI 覆盖生效与还原、
#   非法表达式（未知字段/运算符）拒绝、迁移知识库样例条目可用。
#
# 【参照】重写计划 §5/§12.4；数据包 data/constraint_kb/README.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from ast import literal_eval
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.unit_api import Severity

_AND_SPLIT: re.Pattern[str] = re.compile(r"\s+and\s+")
_CLAUSE: re.Pattern[str] = re.compile(
    r"^(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<op><=|>=|<|>|∈)\s*(?P<value>.+)$"
)
_NUMBER: re.Pattern[str] = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_LIST: re.Pattern[str] = re.compile(r"^\[(?P<items>.+)\]$")


class InvalidConstraintError(Exception):
    """约束 DSL 非法（未知字段/非法算符/非法常数/空表达式）——GR-11 族。"""


@dataclass(frozen=True)
@final
class Constraint:
    """单条布尔约束（不可变）：键 + 受限 DSL 表达式 + 出处 + 级别。"""

    key: str
    expression: str
    source: str
    severity: Severity = Severity.ERROR

    def __post_init__(self) -> None:
        """key/expression/source 非空 str 守卫（R1 数据面准入）。"""
        for name in ("key", "expression", "source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise InvalidConstraintError(
                    f"Constraint.{name} 必须为非空字符串：得到 {value!r}"
                )


def _atom(text: str, where: str) -> float:
    """单数值原子守卫（DSL 右值最小单元；有限性同 grid._number 口径）。"""
    stripped = text.strip()
    if not _NUMBER.match(stripped):
        raise InvalidConstraintError(
            f"{where} 须为数值：得到 {stripped!r}（R1 受限 DSL）"
        )
    number = float(stripped)
    if not isfinite(number):  # M-3（R1 轮修）："1e999"→inf 恒真/恒假约束禁入
        raise InvalidConstraintError(
            f"{where} 非有限：{stripped!r} → {number!r}（GR-02 输入即拒）"
        )
    return number


def _constant(text: str, where: str) -> float | tuple[float, ...]:
    """DSL 右值归一：数值或方括号数档列表（常数来自数据，代码零注入）。"""
    stripped = text.strip()
    listed = _LIST.match(stripped)
    if listed is None:
        return _atom(stripped, where)
    try:
        parsed = literal_eval(stripped)
    except (ValueError, SyntaxError) as exc:
        raise InvalidConstraintError(
            f"{where} 的档位列表非法：{stripped!r}（{exc}）"
        ) from exc
    if not isinstance(parsed, tuple | list) or not parsed:
        raise InvalidConstraintError(
            f"{where} 的档位列表须非空：{stripped!r}（GR-14 空集显式语义）"
        )
    return tuple(
        _atom(str(item), f"{where} 档位[{position}]")
        for position, item in enumerate(parsed)
    )


def _clauses(expression: str) -> tuple[tuple[str, str, float | tuple[float, ...]], ...]:
    """表达式 → 子句树（field, op, 常数）元组；语法/算符非法即拒。"""
    parts = [part for part in _AND_SPLIT.split(expression.strip()) if part]
    if not parts:
        raise InvalidConstraintError(f"约束表达式为空或仅含 and：{expression!r}")
    parsed: list[tuple[str, str, float | tuple[float, ...]]] = []
    for clause in parts:
        match = _CLAUSE.match(clause.strip())
        if match is None:
            raise InvalidConstraintError(
                f"约束子句语法非法：{clause!r}（形如 field_id (</<=/>/>=/∈) 常数，"
                "子句间以 and 组合——R1 受限 DSL）"
            )
        parsed.append(
            (
                match.group("field"),
                match.group("op"),
                _constant(match.group("value"), f"子句 {clause!r}"),
            )
        )
    return tuple(parsed)


def _evaluate(
    df: pandas.DataFrame, clauses: tuple[tuple[str, str, float | tuple[float, ...]], ...]
) -> pandas.Series:
    """numpy 布尔运算求值（R4 向量化）：未知字段即拒（消息含合法列）。"""
    columns = tuple(df.columns)
    combined: pandas.Series | None = None
    for field_id, op, constant in clauses:
        if field_id not in df.columns:
            raise InvalidConstraintError(
                f"约束引用未知字段 {field_id!r}（合法列 {list(columns)}——"
                "R1 DSL 白名单：字段须为枚举结果列/注册字段 ID）"
            )
        series = df[field_id]
        if op == "<":
            mask = series < constant
        elif op == "<=":
            mask = series <= constant
        elif op == ">":
            mask = series > constant
        elif op == ">=":
            mask = series >= constant
        else:
            mask = series.isin(constant)
        combined = mask if combined is None else combined & mask
    assert combined is not None  # 子句非空已在 _clauses 守卫
    return combined


@dataclass(frozen=True)
@final
class FilterResult:
    """过滤产出（不可变）：可行子集位置索引 + 行×约束布尔通过矩阵。"""

    feasible: tuple[int, ...]
    pass_matrix: pandas.DataFrame


def apply_constraints(
    df: pandas.DataFrame, constraints: Sequence[Constraint]
) -> FilterResult:
    """过滤正门：逐约束向量化求值（列名=表达式串）→ 可行索引 + 完整矩阵。

    约束空集合法=全可行（本批约束由调用方传入；constraint_kb 51 条
    迁移 0.0.0→1.0.0 不属本批——独立数据批挂账）。
    """
    columns: dict[str, pandas.Series] = {}
    for constraint in constraints:
        columns[constraint.expression] = _evaluate(df, _clauses(constraint.expression))
    matrix = pandas.DataFrame(columns, index=df.index)
    if constraints:
        feasible = tuple(
            int(index) for index in matrix.all(axis=1).to_numpy().nonzero()[0]
        )
    else:
        feasible = tuple(range(len(df)))  # 空约束集=全可行（GR-14 显式语义）
    return FilterResult(feasible=feasible, pass_matrix=matrix)
