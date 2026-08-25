"""无可行解最小冲突集诊断：失败模式定位 + 调参建议（不是只会说"无解"）。

输入:  constraints.apply_constraints 的 pass_matrix（全 False 场景）
输出:  诊断报告（最小冲突约束集 + 各约束失败计数 + 放宽建议）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_diagnose.py）
#
# 【公开接口】
#   diagnose_infeasibility(pass_matrix, constraints, grid=None)
#       -> DiagnosisReport（grid=枚举网格，建议幅度统计源——当前无
#       网格数据时 magnitude=None 不编造，R2 来源③挂账）
#   class DiagnosisReport(不可变)：
#       minimal_conflicts: tuple[frozenset[str], ...]   最小冲突集（去重）
#       fail_counts: Mapping[约束键→失败行数]
#       suggestions: tuple[Suggestion, ...]    工业级调节建议（§4）
#   class Suggestion(可序列化，dataclass 原生字段）：param_key（调哪个
#       参数）/ direction（方向）/ magnitude（建议幅度，None=无据不编造）/
#       basis（依据：constraint_kb 键或条文）/ affected_conflicts
#       （预期化解哪个冲突约束集）/ expected_effect（一句话影响预判）
#   class InvalidDiagnosisError(Exception)：无 pass_matrix/空矩阵——
#       GR-11 族，本文件定义
#
# 【行为规格】
#   R1 最小冲突集：在"逐约束去除后是否存在全通过行"意义上求最小集
#      （贪心/精确均可，但结果确定性：同输入同报告——进 UI 与日志）。
#      【实现口径】= 失败超图（每行的失败约束集为超边）的极小横截集：
#      每"有失败行的方案"都失败于集中至少一员 ⟺ 该约束集联合不可
#      满足；极小性=去掉任一员即出现全通过行（含全部通过行的可行态
#      下冲突集为空）。已全通过的行不构成超边（可行行在场=系统可行，
#      冲突面只覆盖受约束行）。
#   R2 诊断可解释：每条建议必须引用它依据的冲突约束与失败计数，
#      禁止"建议放宽所有约束"式无用输出。建议来源三条按优先级
#      （business-logic.md §4）：①constraint_kb 规则（约束自带
#      "失败时建议"，带出处）；②枚举统计（可行域边缘分布→方向幅度
#      ——需 grid，挂账）；③专家经验表（coefficients，归数据批）。
#   R3 无 pass_matrix（调用前置条件违反）→ 领域异常；空网格同抛。
#   R4 输出可序列化（UI 渲染 + 持久化诊断面板记录，§19.3 反馈三通道）。
#   R5 本模块只"建议"不"改值"：建议应用 = 上层（services/calculation）
#      执行的显式 design 变更（新 content_hash + 旧结果标 stale），
#      禁止诊断引擎静默改参数。
#
# 【测试要求】构造两约束冲突 → 冲突集恰为该两条、失败计数正确、
#   建议引用依据、确定性（乱序约束同报告）。
#
# 【参照】重写计划 §6.1 测试金字塔/§12.4
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

_DIRECTION: dict[str, str] = {
    "<": "上调该上限档或放宽约束",
    "<=": "上调该上限档或放宽约束",
    ">": "下调该下限档或放宽约束",
    ">=": "下调该下限档或放宽约束",
    "∈": "增补相邻档位或放宽档域",
}
_CLAUSE: re.Pattern[str] = re.compile(
    r"^\s*(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<op><=|>=|<|>|∈)"
)


class InvalidDiagnosisError(Exception):
    """诊断输入非法（无 pass_matrix/空矩阵）——GR-11 族。"""


@dataclass(frozen=True)
@final
class Suggestion:
    """单条调节建议（可序列化）：参数指向 + 方向 + 幅度 + 依据 + 预判。"""

    param_key: str
    direction: str
    magnitude: float | None
    basis: str
    affected_conflicts: tuple[str, ...]
    expected_effect: str


@dataclass(frozen=True)
@final
class DiagnosisReport:
    """诊断报告（不可变）：最小冲突集 + 失败计数 + 建议（R1/R2）。"""

    minimal_conflicts: tuple[frozenset[str], ...]
    fail_counts: Mapping[str, int]
    suggestions: tuple[Suggestion, ...]


def _failure_edges(matrix: pandas.DataFrame) -> list[frozenset[str]]:
    """失败超边集：每行失败约束集（非空、去重、剔除非极小边）。"""
    edges = {
        frozenset(column for column in matrix.columns if not bool(row[column]))
        for _, row in matrix.iterrows()
    }
    edges.discard(frozenset())
    return sorted(
        (edge for edge in edges if not any(other < edge for other in edges)),
        key=sorted,
    )


def _transversals(
    edges: Sequence[frozenset[str]], candidate: frozenset[str]
) -> set[frozenset[str]]:
    """极小横截集递归求值（R1：贪心生长候选集，命中全部边为叶）。"""
    uncovered = [edge for edge in edges if not candidate & edge]
    if not uncovered:
        return {candidate}
    found: set[frozenset[str]] = set()
    for element in sorted(uncovered[0]):
        found |= _transversals(edges, candidate | {element})
    return {item for item in found if not any(other < item for other in found)}


def _basis_of(entry: object, key: str) -> str:
    """约束出处提取（Constraint 对象或 Mapping 声明面）。"""
    source = getattr(entry, "source", None)
    if source is None and isinstance(entry, Mapping):
        source = entry.get("source")
    return str(source) if source else f"constraint:{key}"


def _param_direction(entry: object, key: str) -> tuple[str, str]:
    """从表达式取参数指向与方向（无表达式面时以约束键指代，方向=复核）。"""
    expression = getattr(entry, "expression", None)
    if expression is None and isinstance(entry, Mapping):
        expression = entry.get("expression")
    if not isinstance(expression, str):
        return key, "复核该约束可行域边界（无表达式面，方向未定——R2 拒空话）"
    match = _CLAUSE.match(expression)
    if match is None:
        return key, "复核该约束表达式（DSL 子句不可解析）"
    return match.group("field"), _DIRECTION.get(match.group("op"), "复核约束方向")


def _suggestions(
    conflicts: tuple[frozenset[str], ...],
    fail_counts: Mapping[str, int],
    constraints: Mapping[str, object],
) -> tuple[Suggestion, ...]:
    """R2 建议生成：逐冲突集逐约束，必引冲突键与失败计数。"""
    made: list[Suggestion] = []
    for conflict in conflicts:
        for key in sorted(conflict):
            param_key, direction = _param_direction(constraints.get(key, key), key)
            made.append(
                Suggestion(
                    param_key=param_key,
                    direction=direction,
                    magnitude=None,  # 幅度来源②（枚举统计）需 grid——挂账，不编造
                    basis=_basis_of(constraints.get(key, key), key),
                    affected_conflicts=tuple(sorted(conflict)),
                    expected_effect=(
                        f"放宽 {key} 预期化解冲突集 {sorted(conflict)}"
                        f"（该约束失败 {fail_counts[key]} 行——矩阵列求和口径）"
                    ),
                )
            )
    return tuple(made)


def diagnose_infeasibility(
    pass_matrix: pandas.DataFrame | None,
    constraints: Mapping[str, object],
    grid: object = None,
) -> DiagnosisReport:
    """诊断正门：失败超图 → 极小横截集（R1）+ 失败计数 + 有据建议（R2/R5）。

    grid 为枚举网格占位（建议幅度统计源，R2 来源②——当前无网格数据
    时 magnitude=None；R5 只建议不改值）。
    """
    del grid  # 占位透传（R2 来源②挂账；幅面统计随服务层接入落地）
    if pass_matrix is None:
        raise InvalidDiagnosisError(
            "无 pass_matrix（调用前置条件违反——diagnose 消费 constraints."
            "apply_constraints 的产出，R3）"
        )
    if pass_matrix.empty:
        raise InvalidDiagnosisError(
            "pass_matrix 为空（空网格/零约束矩阵=无诊断面，GR-14 显式拒绝）"
        )
    fail_counts: dict[str, int] = {
        str(column): int((~pass_matrix[column]).sum())
        for column in pass_matrix.columns
    }
    edges = _failure_edges(pass_matrix)
    if not edges:
        return DiagnosisReport((), MappingProxyType(fail_counts), ())  # 存在可行行
    raw = _transversals(edges, frozenset())
    conflicts = tuple(sorted(raw, key=lambda item: (len(item), sorted(item))))
    return DiagnosisReport(
        minimal_conflicts=conflicts,
        fail_counts=MappingProxyType(fail_counts),
        suggestions=_suggestions(conflicts, fail_counts, constraints),
    )
