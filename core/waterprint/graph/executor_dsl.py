"""执行器 DSL 域件：工况映射求值（受限表达式白名单收集+求值内核消费）。

输入:  rule 串（ConditionMapping.rule）+ params 全量 + OperatingCondition
输出:  _apply_mappings 求值后 params（bool→float 归一）+InvalidExecution
       Error 定义面+_POOL_KEY/_dotted/_rule_names（executor.py 同名再导出
       ——消费面 from waterprint.graph.executor import 零改动）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3 R2 修正① 2026-09-05：DSL 域自 executor.py 拆出——
#   InvalidExecutionError 类定义随域迁入本文件（根除 dsl→executor
#   反向环——direct-first-import 安全），executor.py 同名再导出；
#   搬运零行为变化（签名/语义/报文零变，docstring 随迁）
#
# 【迁移面】InvalidExecutionError（GR-11 族定义面）+_POOL_KEY
#   （"pool.all_pools" 绑定键常量）+_dotted/_rule_names（B4 双胞胎
#   名字收集）+_apply_mappings（DSL 求值正门——bindings=params 全量
#   ∪ pool.all_pools，白名单=rule 引用名∪params∪_POOL_KEY）
#
# 【行为规格】与 executor.py 原文逐字同构（ADR-007 工况映射口径
#   ——见 executor.py 规格说明【工况映射 DSL】节）；测试经 executor
#   再导出面由 test_executor 覆盖，B3-R11 增 test_executor_dsl 恒等钉面。
#
# 【参照】B3 简报 R2；重写计划 §14.1；ADR-003/ADR-007；简报 T7b D3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
from typing import Final

from waterprint.contracts.condition import OperatingCondition
from waterprint.contracts.expr import ExprSyntaxError, eval_checked, parse_checked
from waterprint.contracts.manifest import ConditionMapping

_POOL_KEY: Final[str] = "pool.all_pools"


class InvalidExecutionError(Exception):
    """图执行非法（边形态/注册表缺项/DSL 求值/单元计算失败/回路发散）——GR-11 族。"""


def _dotted(node: ast.AST) -> str | None:
    """Name/Attribute 链 → 点式扁平名（B4 双胞胎：与 manifest_validation 同款）。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        if base is not None:
            return f"{base}.{node.attr}"
    return None


def _rule_names(rule: str) -> frozenset[str]:
    """rule 引用名收集（裸名+点式链）——manifest_validation._referenced_names
    的 B4 双胞胎（禁私有 import，同源同步义务）。"""
    try:
        tree = ast.parse(rule, mode="eval")
    except SyntaxError as exc:
        raise ExprSyntaxError(f"工况映射 rule 语法非法：{rule!r}（{exc.msg}）") from exc
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            path = _dotted(node)
            if path is not None:
                names.add(path)
    return frozenset(names)


def _apply_mappings(
    unit_id: str,
    params: dict[str, float],
    mappings: tuple[ConditionMapping, ...],
    condition: OperatingCondition,
) -> dict[str, float]:
    """DSL 工况映射求值（bindings=params 全量 ∪ pool.all_pools；bool→float 归一）。"""
    result = dict(params)
    bindings: dict[str, float | bool] = dict(result)
    bindings[_POOL_KEY] = condition.offline_unit != unit_id
    for mapping in mappings:
        allowed = _rule_names(mapping.rule) | frozenset(result) | {_POOL_KEY}
        try:
            parsed = parse_checked(mapping.rule, allowed)
            value = eval_checked(parsed, bindings)
        except ExprSyntaxError as exc:
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 工况映射 rule 求值失败"
                f"（target={mapping.target!r}）：{exc}") from exc
        result[mapping.target] = float(value) if isinstance(value, bool) else value
    return result
