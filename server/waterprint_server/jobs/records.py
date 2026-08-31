"""任务域公开数据类：请求/句柄/状态快照/SSE 事件（纯数据零逻辑）。

输入:  无（数据类定义面）
输出:  TaskRequest/TaskHandle/TaskStatus/Event/UnknownTaskError/_KINDS
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（ENG5 D4 拆分——manager.py 恰 500 行预算，S2 R1「无豁免→
# 拆文件」先例照办：公开数据类自 manager 迁移零行为变化；manager 经
# from-import 再导出=模块属性面稳定，既有 from jobs.manager import
# 十处零破坏）
#
# 【公开接口】（与 manager 既有签名逐字同构——docstring 随迁）
#   UnknownTaskError: 任务 id 不在注册表——领域异常（404 面）
#   TaskRequest: 任务提交束（kind 白名单 _KINDS+payload 快照守卫）
#   TaskHandle: 任务句柄（幂等提交的相等性载体）
#   TaskStatus: 状态查询快照（progress/stage/error 诊断/结果句柄）
#   Event: SSE 事件（{type, task_id, percent, message, condition_key}）
#
# 【行为规格】数据类不变量归各类 docstring；_TaskRecord（注册表条目）
#   留守 manager（进程内私有面——subscribers asyncio 队列绑定调度器）。
#
# 【测试要求】经 manager 再导出面由既有镜像测试覆盖（test_manager/
#   test_calculation/test_events 等 getattr(_mod,...) 零漂移）。
#
# 【参照】ENG5 简报 D4；S2 R1 先例；重写计划 §12.2/§17.1/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final

_KINDS: Final[tuple[str, ...]] = ("calc", "enumerate", "export_batch")


class UnknownTaskError(KeyError):
    """任务 id 不在注册表——领域异常（404 面）。"""


@dataclass(frozen=True)
class TaskRequest:
    """任务提交束：kind + JSON 可序列化 payload + 优先级（§17.1 值域）。"""

    kind: str
    payload: Mapping[str, Any]
    priority: int = 1

    def __post_init__(self) -> None:
        """kind 白名单 + payload 快照守卫（§18 IPC 边界）。"""
        if self.kind not in _KINDS:
            raise ValueError(f"未知任务 kind：{self.kind!r}（合法面 {_KINDS}）")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class TaskHandle:
    """任务句柄（幂等提交的相等性载体）。"""

    task_id: str


@dataclass(frozen=True)
class TaskStatus:
    """状态查询快照：progress/stage/condition_key/stale/error 诊断/结果句柄。"""

    task_id: str
    kind: str
    state: str
    progress: float
    stage: str
    condition_key: str | None
    stale: bool
    error: str | None
    error_type: str | None
    result: Mapping[str, Any] | None
    project_id: str = ""
    error_code: int | None = None  # R1-2：诊断名→HTTP 码（消费面回填，AU-2）


@dataclass(frozen=True)
class Event:
    """SSE 事件（R1：JSON 化 {type, task_id, percent, message, condition_key}）。"""

    type: str
    task_id: str
    percent: float
    message: str
    condition_key: str | None
