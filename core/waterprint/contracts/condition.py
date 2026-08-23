"""工况契约：flow_case 全局档 × pool 逐单元检修敏感性（ADR-007 冻结语义）。

输入:  工况轴取值（用户勾选的受检单元集合）
输出:  OperatingCondition / ConditionSet / condition_key（稳定可序列化）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 冻结；镜像测试 tests/contracts/test_condition.py）
#
# 【公开接口】
#   class FlowCase(Enum)：DESIGN（最高日最高时）/ AVG（平均时）
#       值 = "design"/"avg"（condition_key 基线两档字面量，GR-20 冻结）
#   class OperatingCondition(不可变)：
#       flow_case: FlowCase
#       offline_unit: str | None = None    非空 = "该单元 n-1 池、其余全池"
#                                          敏感性校核（缺省 None = 基线工况）
#   class ConditionSet(不可变)：
#       baseline: tuple[OperatingCondition, ...]        # 恒为 design/avg 两档
#       sensitivity: tuple[OperatingCondition, ...]     # 每个受检单元一条
#       def iter_all(self) -> Iterator[OperatingCondition]   # baseline 后
#           sensitivity（受检单元列表序）
#       @classmethod
#       def key(condition: OperatingCondition) -> str   # 稳定键（序列化/索引）
#   build_condition_set(checked_units: Sequence[str]) -> ConditionSet
#       位置参数唯一正门
#
# 【行为规格】
#   R1 运行次数 = 2 + k（k=受检单元数），线性；禁止 2^n 全组合——
#      build_condition_set 输出条数断言进测试（ADR-007，§16 A3 曾有两版
#      矛盾表述，本文件是冻结后的唯一语义源）。sensitivity 条目统一
#      flow_case=design：检修敏感性 = 最不利检修组合（该单元 n-1 池、
#      其余单元全池，叠加最高日最高时流量），不构造 avg 档检修工况。
#   R2 condition_key 确定性：同工况同键；用于结果索引、缓存键、SSE 通道、
#      日志字段（§15 工程细节 2）。键格式样例（稳定拼接规则）：
#      基线两档 = `design` / `avg`；敏感性 = `design_offline_<unit_id>`
#      （如 `design_offline_aao`，unit_id 即单元注册 id，禁止含空格/斜杠）。
#   R3 工况对参数的影响只经 manifest 工况映射（见 manifest.py R1c），
#      本契约只描述"跑哪些工况"，不描述"参数怎么变"。
#   R4 远期扩展轴（季节水温等）：只增 FlowCase 枚举值或新轴字段 + manifest
#      映射，不改引擎（开放封闭，§14.1）。
#   R5 汇流加权随工况：design 工况用 q_design、avg 用 q_avg_daily——
#      语义归属 propagate.py，本契约提供 flow_case 判别手段。
#   R6 受检单元 id 格式校验（本文件执行面）：非 ASCII 字母数字下划线 /
#      空串 / 重复 → InvalidUnitConfig（GR-26，消息含 unit_id 原值）。
#
# 【T3 冻结注记】（总控简报 D4 裁决，2026-08-23）
#   - 原 R6"资格校验（受检单元须 manifest 声明检修降级）"的执行点是
#     装配层（app/executor，T7 落地）——build_condition_set 签名（测试
#     锁定）无 manifest 通道，规格原文自相矛盾；本文件只做格式校验
#     （GR-26），资格校验移交 T7 装配层执行。
#   - key 为类方法（@classmethod）——锁定测试以 type(cs).key(c) 形态
#     调用；offline 键前缀固定 design_offline_（敏感性统一 design 档
#     与键字面量族绑定，GR-20 冻结：design/avg/design_offline_<unit_id>）。
#   - 数值纪律：本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】2+k 条数断言、key 确定性与唯一性、offline 语义字段、
#   空受检集合 = 仅基线两档、sensitivity 全为 design 档、
#   非法 unit_id 入参抛 InvalidUnitConfig、key 样例
#   （design/avg/design_offline_<unit_id>）逐字对照。
#
# 【参照】重写计划 §14.1/§16 A3；ADR-007；简报 T3 D4 预裁决
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import final

from waterprint.contracts.manifest import InvalidUnitConfig

# GR-26：标识符仅 ASCII 字母/数字/下划线且非空（condition_key 拼接依赖）。
_UNIT_ID_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z0-9_]+\Z")


class FlowCase(Enum):
    """全局流量档：design（最高日最高时）/ avg（平均时）——ADR-007 冻结轴。"""

    DESIGN = "design"
    AVG = "avg"


@dataclass(frozen=True)
@final
class OperatingCondition:
    """单条运行工况：流量档 × 可选检修单元（n-1 池敏感性，R1）。"""

    flow_case: FlowCase
    offline_unit: str | None = None


@dataclass(frozen=True)
@final
class ConditionSet:
    """一次全厂计算的工况集合：基线两档 + 逐受检单元敏感性（2+k 线性）。"""

    baseline: tuple[OperatingCondition, ...]
    sensitivity: tuple[OperatingCondition, ...]

    def iter_all(self) -> Iterator[OperatingCondition]:
        """全量工况迭代：baseline 后 sensitivity（受检单元列表序，确定性）。"""
        return iter(self.baseline + self.sensitivity)

    @classmethod
    def key(cls, condition: OperatingCondition) -> str:
        """工况稳定键：design / avg / design_offline_<unit_id>（GR-20 冻结）。"""
        if condition.offline_unit is None:
            return condition.flow_case.value
        return f"design_offline_{condition.offline_unit}"


def _require_unit_id(unit_id: str, seen: set[str]) -> None:
    """受检单元 id 守卫：GR-26 字符集 + 非重复（消息含原值，GR-09）。"""
    if not isinstance(unit_id, str) or not _UNIT_ID_PATTERN.fullmatch(unit_id):
        raise InvalidUnitConfig(
            f"受检单元 id 非法：{unit_id!r}（GR-26：仅 ASCII 字母数字下划线"
            "且非空串——condition_key 拼接依赖）"
        )
    if unit_id in seen:
        raise InvalidUnitConfig(
            f"受检单元重复：{unit_id!r}（每单元恰一条敏感性工况，R1 的 2+k 语义）"
        )


def build_condition_set(checked_units: Sequence[str]) -> ConditionSet:
    """工况集合唯一正门（位置参数）：基线 design/avg 两档 + 每受检单元一条
    design 档检修敏感性（R1：2+k 线性，禁止 2^n 全组合）。"""
    seen: set[str] = set()
    for unit_id in checked_units:
        _require_unit_id(unit_id, seen)
        seen.add(unit_id)
    baseline = (
        OperatingCondition(flow_case=FlowCase.DESIGN),
        OperatingCondition(flow_case=FlowCase.AVG),
    )
    sensitivity = tuple(
        OperatingCondition(flow_case=FlowCase.DESIGN, offline_unit=unit_id)
        for unit_id in checked_units
    )
    return ConditionSet(baseline=baseline, sensitivity=sensitivity)
