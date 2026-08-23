"""单元计算协议：UnitContext → UnitResult（图执行器与工艺单元之间的唯一耦合面）。

输入:  上游端口量快照（水/泥）、参数（规范单位裸值）、工况、假设注入、迹收集器
输出:  UnitResult（输出端口量 + 维度字段数组 + 警告 + 已用公式清单）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 冻结；镜像测试 tests/contracts/test_unit_api.py）
#
# 【公开接口】
#   class Severity(StrEnum)：ERROR / WARN / INFO（字面量冻结，D3）
#   class Warning(不可变)：单条工业级提示——business-logic §8"来源+调节
#       方向+影响面"三必带逐条落字段：
#       severity: Severity             级别（error=计算失败/诊断面板，
#                                    warn=越出建议带未违强条，
#                                    info=假设生效提示/裕度充裕）
#       source: str                   来源（条文号或知识库键，必带——
#                                    禁止无出处的裸警告文本）
#       message: str                  人类可读消息（进迹冻结，GR-09 精神）
#       param_key: str | None = None  调节方向指向（参数键）
#       condition_key: str | None = None   影响面：所属工况键
#       affected_unit_ids: tuple[str, ...] = ()  影响面：下游单元
#   class UnitContext(不可变)：
#       unit_id: str
#       inflows:  Mapping[PortRef → WaterFlow | SludgeFlow]   上游快照
#       inqualities: Mapping[PortRef → WaterQuality]
#       params:   Mapping[str → float]    规范单位裸值（manifest 校验过）
#       condition: OperatingCondition    当前工况（ADR-007）
#       assumptions: Mapping[str → float]  假设键→注入值视图（D1）
#       trace: TraceSink 协议引用        记录公式应用（contracts/trace_api.py）
#   class UnitResult(不可变)：
#       outflows: Mapping[PortRef → WaterFlow | SludgeFlow]
#       outqualities: Mapping[PortRef → WaterQuality]
#       dims:      Any    结构化数组（字段、单位、值——dtype 由 dimensions
#                        注册表定义；类型注记 Any，T4 dtype 冻结后只增收紧）
#       warnings:  tuple[Warning, ...]
#       formula_ids: tuple[str, ...]     本次执行实际应用的公式 ID（可审计）
#   class Unit(Protocol)：结构协议（执行器与具体单元解耦的装配边界）
#       manifest: UnitManifest
#       def compute(self, ctx: UnitContext) -> UnitResult: ...
#
# 【行为规格】
#   R1 compute 是纯函数：同 ctx 必同 UnitResult（可复算基石，§3 保证 6）；
#      禁止读写全局状态、禁止随机数、禁止时钟访问。
#   R2 协议即装配边界：graph/executor.py 只 import 本协议，永不 import 具体单元
#      （import-linter "装配点唯一"契约强制）。
#   R3 向量化唯一实现：compute 的数值路径必须是向量化实现，标量 = N=1 特例
#      （§3 保证 1；禁止双轨——单元测试断言标量与 N=1 数组结果一致）。
#   R4 中文名只存在于 i18n 显示层：dims 按字段 ID 取数（§3 保证 4）。
#   R5 工况影响只经 ctx.condition + manifest 声明式映射进入参数，compute 内
#      禁止工况 if 分支（ADR-007，评审拒绝项）。
#
# 【T3 冻结注记】（总控简报 D1/D3 裁决，2026-08-23）
#   - D1：assumptions 类型裁定 Mapping[str, float]（假设键→注入值视图）——
#     registry 的 AssumptionSet 实现 __getitem__ 即结构满足；假设元数据
#     （出处/调节影响）的消费走 registry 层（建议引擎），不经本面（L0 零依赖）。
#   - D3（UF-17 冻结）：Severity/Warning 定义于本文件；result_schema 的
#     UnitResultSnapshot 直接复用 Warning（同层 import 合法）。
#     param_key/condition_key 可 None（error 级失败可无调节指向）——"必带"
#     指结构字段必带（§8 三必带逐条落字段），非值恒非空。
#   - UnitContext/UnitResult 的 Mapping 字段构造时快照为只读
#     （MappingProxyType，quality.py 同款防线）；tuple 字段归一为 tuple。
#     构造即快照——先复制后代理：外部改原容器不泄漏进对象（T3A-01）。
#   - UnitManifest 类型面经 TYPE_CHECKING 注解引用（运行时零耦合；
#     Protocol 属性注解在 future-annotations 下不求值，T3④ 落地接线）。
#   - 数值纪律：本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】协议结构契约（字段存在/不可变）、N=1 特例断言模板、
#   纯函数断言模板（供 32 个单元包镜像套用）。
#
# 【参照】重写计划 §3/§13.1/§14.1；business-logic §8；简报 T3 D1/D3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, final

from waterprint.contracts.condition import OperatingCondition
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import WaterQuality
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.trace_api import TraceSink

if TYPE_CHECKING:
    from waterprint.contracts.manifest import UnitManifest

_Flows = Mapping[PortRef, WaterFlow | SludgeFlow]
_Qualities = Mapping[PortRef, WaterQuality]


class Severity(StrEnum):
    """警告级别（business-logic §8 分级表，D3 字面量冻结）。"""

    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass(frozen=True)
@final
class Warning:
    """单条工业级提示：来源 + 调节方向 + 影响面三必带（UF-17 冻结结构）。"""

    severity: Severity
    source: str
    message: str
    param_key: str | None = None
    condition_key: str | None = None
    affected_unit_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
@final
class UnitContext:
    """单元计算入参快照（不可变）：上游量 + 参数 + 工况 + 假设视图 + 迹收集器。"""

    unit_id: str
    inflows: _Flows
    inqualities: _Qualities
    params: Mapping[str, float]
    condition: OperatingCondition
    assumptions: Mapping[str, float]
    trace: TraceSink

    def __post_init__(self) -> None:
        """Mapping 字段只读快照冻结（quality.py 同款防线）。"""
        object.__setattr__(self, "inflows", MappingProxyType(dict(self.inflows)))
        object.__setattr__(
            self, "inqualities", MappingProxyType(dict(self.inqualities))
        )
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))
        object.__setattr__(
            self, "assumptions", MappingProxyType(dict(self.assumptions))
        )


@dataclass(frozen=True)
@final
class UnitResult:
    """单元计算产出（不可变）：输出端口量 + 维度字段 + 警告 + 公式审计通道。"""

    outflows: _Flows
    outqualities: _Qualities
    dims: Any
    warnings: tuple[Warning, ...]
    formula_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Mapping 只读快照冻结 + tuple 归一（与 UnitContext 同款防线，T3A-01）。

        dims 不动：类型 Any（T4 dtype 冻结后只增收紧）；构造即快照——
        外部 dict/list 传入后即与本对象解绑，后续外部修改不泄漏。
        """
        object.__setattr__(self, "outflows", MappingProxyType(dict(self.outflows)))
        object.__setattr__(
            self, "outqualities", MappingProxyType(dict(self.outqualities))
        )
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "formula_ids", tuple(self.formula_ids))


class Unit(Protocol):
    """工艺单元结构协议：装配边界（执行器据此与具体单元解耦，R2）。"""

    manifest: UnitManifest

    def compute(self, ctx: UnitContext) -> UnitResult: ...
