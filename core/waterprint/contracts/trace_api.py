"""计算迹协议：TraceSink 与 TraceNodeSpec（registry 与迹收集器的唯一耦合面）。

输入:  registry/formulas.apply 的公式应用事件（id/单元/工况/实参快照/结果）
输出:  TraceSink 协议（L4 trace/collector.py 实现）；TraceNodeSpec 快照数据类
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T0.5 冻结；正式镜像测试由人类流程补，见简报 T0.5）
#
# 【公开接口】
#   @dataclass(frozen=True) class TraceNodeSpec：
#       formula_id: str                    公式全库唯一 ID（registry/formulas）
#       unit_id: str                       应用发生的单元（内置节点用节点 id）
#       condition_key: str                 所属工况稳定键（contracts/condition）
#       bindings: Mapping[str, float]      求值实参快照（可审计）
#       result: float                      求值输出
#   class TraceSink(Protocol)：
#       def record(self, node: TraceNodeSpec) -> None
#
# 【行为规格】
#   R1 协议是唯一耦合面：registry（L1）与单元层只 import 本文件（L0），
#      永不 import L4 trace/collector.py——依赖只许向下（AGENTS.md §1）；
#      本文件消除 unit_api 规格头原先指向 L4 收集器的越层文字暗示。
#   R2 TraceNodeSpec 不可变；bindings 为求值实参快照，序列化规则同
#      result_schema 的 TraceNode（本协议是其生产侧契约）。
#   R3 record 无返回值；实现方保证确定性与零遗漏（同输入同序收集，
#      支撑可复算三元组与 §16 A1"注册表与实现漂移"审计防线）。
#   R4 实现归属：L4 trace/collector.py 的收集器实现本协议，经
#      UnitContext.trace 携带进单元；formulas.apply 以 sink 形参接收
#      （缺省 None = 本次求值不落迹，如批量枚举热路径）。
#
# 【禁止】本文件不得定义收集器实现/IO/聚合逻辑（协议即全部职责）；
#   不得 import 内部其他模块（L0 零内部依赖，仅标准库）。
#
# 【测试要求】协议结构契约（字段存在/不可变/record 签名）；收集行为由
#   trace/collector 镜像测试覆盖（收集顺序、快照完整性、确定性）。
#
# 【参照】简报 T0.5 决策 4；重写计划 §16 A1；contracts/unit_api.py trace 字段
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TraceNodeSpec:
    """单次公式应用的完整快照（计算迹最小溯源单元）。"""

    formula_id: str
    unit_id: str
    condition_key: str
    bindings: Mapping[str, float]
    result: float


class TraceSink(Protocol):
    """计算迹收集协议：registry 求值正门的唯一观测出口。"""

    def record(self, node: TraceNodeSpec) -> None: ...
