"""任务域公开数据类：请求/句柄/状态快照/SSE 事件 + 注册表条目（纯数据）。

输入:  无（数据类定义面）
输出:  TaskRequest/TaskHandle/TaskStatus/Event/UnknownTaskError/_KINDS/
       _TaskRecord（manager 顶部 import 再导出——模块属性面零波移）
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
#   B3 R4（2026-09-05）自 manager 迁入本文件（manager 500 行预算减压；
#   纯数据类零 manager 状态依赖——终态面 _TERMINAL 经 registry.
#   TERMINAL_STATES 同源单定义，registry 不反向 import records 无环）；
#   manager 顶部 import 再导出（包内 _ 前缀合法——test_server_maintenance
#   的 manager._TaskRecord 模块属性访问零波移）。
#
# 【测试要求】经 manager 再导出面由既有镜像测试覆盖（test_manager/
#   test_calculation/test_events 等 getattr(_mod,...) 零漂移）。
#
# 【参照】ENG5 简报 D4；S2 R1 先例；B3 简报 R4；重写计划 §12.2/§17.1/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final

from waterprint_server.jobs.registry import TERMINAL_STATES

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


# 终态面（B3 R4 随 _TaskRecord 迁入——与 manager._TERMINAL 同源 registry
# 单定义；搬运体 terminal 属性逐字保序引用本名）。
_TERMINAL: Final[tuple[str, ...]] = TERMINAL_STATES


@dataclass
class _TaskRecord:
    """注册表条目（内存，replicas=1 契约 R4）。"""

    task_id: str
    request: TaskRequest
    state: str = "queued"
    progress: float = 0.0
    stage: str = "queued"
    condition_key: str | None = None
    stale: bool = False
    error: str | None = None
    error_type: str | None = None
    result: Mapping[str, Any] | None = None
    snapshot_hash: str | None = None
    cancel_requested: bool = False
    finished_at: float | None = None  # WP4：完成时间戳（终态必置——TTL 判定面）
    subscribers: set[asyncio.Queue[Event]] = field(default_factory=set)

    @property
    def terminal(self) -> bool:
        """终态判定（状态机单向 R1）。"""
        return self.state in _TERMINAL

    def status(self) -> TaskStatus:
        """只读快照（对外不含内部字段）。"""
        return TaskStatus(
            task_id=self.task_id,
            kind=self.request.kind,
            state=self.state,
            progress=self.progress,
            stage=self.stage,
            condition_key=self.condition_key,
            stale=self.stale,
            error=self.error,
            error_type=self.error_type,
            result=self.result,
            project_id=str(self.request.payload.get("project_id", "")),
        )
