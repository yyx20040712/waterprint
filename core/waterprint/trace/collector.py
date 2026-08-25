"""计算迹收集：公式应用记录的采集与组织（全程可审计的数据半）。

输入:  registry.formulas.apply 的每次调用事件（TraceNodeSpec——经
       UnitContext.trace / env.trace_sink 注入本收集器）
输出:  TraceTree（tuple[TraceNode, ...] 平铺、按到达序——序列化确定性）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1b 实现，简报 D1 裁决 2026-08-25；镜像测试 tests/trace/
#   test_collector.py）
#
# 【公开接口】
#   class InvalidTraceError(Exception)（GR-11 族新类，本文件定义）
#   TraceTree = tuple[TraceNode, ...]（UF-43③ 形态裁决：平铺+到达序；
#       树形聚合归渲染层 calcbook/audit 自行分组）
#   class TraceCollector（实现 contracts.trace_api.TraceSink 协议）：
#       record(node: TraceNodeSpec) -> None   单对象参数（T0.5 协议，
#           规格头旧 6 散参文已刷新——UF-43②闭合）
#       tree() -> TraceTree                    不可变快照（到达序）
#       collect(execution) -> TraceTree        执行期聚合正门
#   collect(execution: Callable[[], Any]) -> TraceTree（模块级正门）
#
# 【行为规格】
#   R1 采集零遗漏：每条公式应用的输入快照/输出/单元/工况全部入迹；
#       TraceNodeSpec(5 字段)→TraceNode(6 字段) 就地转换，norm_ref 经
#       registry 只读查询面 norm_ref_of(formula_id) 反查（UF-43①闭合；
#       trace→registry 边在图谱 §1 在案）；未知 formula_id =
#       InvalidTraceError（消息含 formula_id，GR-09）。
#   R2 记录顺序确定性：按到达序平铺累积（同执行同迹序——双跑同序列化
#       字节的组成部分）；tree() 返回 tuple 快照（不可变）。
#   R3 采集不改变语义：采集失败 = 执行失败（宁可失败不可无迹成功，
#       审计完整性优先）——collect 正门异常照抛不吞。
#   R4 内存治理（万级枚举采样）归 assumptions 配置批（M1/M3），
#       全流程计算全量入迹（本文件 v1 全量）。
#
# 【collect 正门口径】execution 为零参闭包（内部以 TraceCollector 为
#   trace_sink 完成执行并**返回该 collector**）；异常照抛（R3 不吞——
#   部分迹自然保留在 collector 供审计），正常返回 collector.tree()；
#   闭包返回非 TraceCollector = InvalidTraceError（采集链断链即失败）。
#   （R1-c 二审 M-1 清理：原 try/finally:pass 死构造已删，零行为变化。）
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】节点数 == apply 数（零遗漏）、双采迹序列化字节同、
#   norm_ref 反查非空、未知 formula_id 拒。
#
# 【参照】重写计划 §3-5/§3-6；简报 M1b D1；contracts/trace_api.py
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from typing import final

from waterprint.contracts.result_schema import TraceNode
from waterprint.contracts.trace_api import TraceNodeSpec
from waterprint.registry import formulas

__all__ = ["InvalidTraceError", "TraceCollector", "TraceTree", "collect"]

type TraceTree = tuple[TraceNode, ...]


class InvalidTraceError(Exception):
    """计算迹非法（未知公式反查失败/采集链断链）——GR-11 族（M1b D1）。"""


@final
class TraceCollector:
    """计算迹收集器：TraceSink 协议实现（到达序平铺累积，R1/R2）。"""

    def __init__(self) -> None:
        self._nodes: list[TraceNode] = []

    def record(self, node: TraceNodeSpec) -> None:
        """单条公式应用入迹：Spec→Node 就地转换（norm_ref 反查，UF-43①）。"""
        try:
            norm_ref = formulas.norm_ref_of(node.formula_id)
        except formulas.InvalidFormulaError as exc:
            raise InvalidTraceError(
                f"计算迹含未知公式：{node.formula_id!r}（单元 {node.unit_id!r}、"
                f"工况 {node.condition_key!r}——norm_ref 反查失败，采集失败="
                "执行失败，R3）"
            ) from exc
        self._nodes.append(
            TraceNode(
                formula_id=node.formula_id,
                inputs=dict(node.bindings),
                output=node.result,
                norm_ref=norm_ref,
                unit_id=node.unit_id,
                condition_key=node.condition_key,
            )
        )

    def tree(self) -> TraceTree:
        """迹快照（不可变 tuple，到达序=R2 确定性）。"""
        return tuple(self._nodes)

    def collect(self, execution: Callable[[], object]) -> TraceTree:
        """执行期聚合正门（实例形态）：以 self 为 sink 的零参闭包包裹执行。"""
        execution()  # 异常照抛（R3 不吞）；部分迹已留存 self 供审计
        return self.tree()


def collect(execution: Callable[[], object]) -> TraceTree:
    """执行期聚合正门（模块级）：execution 返回其内部使用的 collector。

    R3 不吞异常：execution 抛出的异常原样上抛；部分迹自然保留在
    collector 供审计（宁可失败不可无迹成功）。
    """
    outcome = execution()
    if not isinstance(outcome, TraceCollector):
        raise InvalidTraceError(
            "collect 正门要求执行闭包返回其内部使用的 TraceCollector"
            "（采集链断链即失败——R3 宁可失败不可无迹成功）"
        )
    return outcome.tree()
