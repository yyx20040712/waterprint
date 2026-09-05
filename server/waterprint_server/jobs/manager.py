"""计算任务注册表与进程池调度：queued/running/done/cancelled 状态机 + 优先级队列。

输入:  任务提交（kind + payload + 优先级）
输出:  任务状态查询 / 进度事件流 / 取消令牌
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/jobs/test_manager.py）
#
# 【公开接口】
#   class Manager：
#       submit(task: TaskRequest) -> TaskHandle
#       status(task_id) -> TaskStatus（含 progress、stale、error 诊断）
#       cancel(task_id) -> bool（协作令牌置位）
#       events(task_id) -> AsyncIterator[Event]   SSE 数据源
#       shutdown(timeout)                         优雅停机
#   class TaskRequest：kind（calc/enumerate/export_batch）、
#       payload（JSON 可序列化——IPC 边界约束 §18）、priority
#
# 【行为规格】
#   R1 状态机：queued→running→(done|cancelled|failed) 单向；
#      done 附结果句柄（分页/文件路径），failed 附 core 领域异常
#      序列化诊断（不吞栈）。
#   R2 优先级队列（§17.1）：交互计算 > 枚举 > 批量导出；
#      同级 FIFO；取消的 queued 任务直接 cancelled。
#   R3 进度通路：worker → multiprocessing.Queue → asyncio 桥接
#      （run_coroutine_threadsafe）→ events()；事件含
#      {percent, stage, condition_key}。
#   R4 单进程假设（§16 A5）：注册表在内存，api replicas=1 部署契约；
#      多副本 = 未来 Redis 化（ADR 不做）。S2：终态记录落 registry_dir
#      供重启恢复读面（见注记），调度面仍内存单进程。
#   R5 取消语义：令牌经共享值传递，worker 每批迭代检查（§12.2）；
#      取消后已产清单随 result 可查（SVRB §2.3 收口——产物文件已落盘
#      不可撤，清单丢弃=半途产物不可查；新任务不再启动）。
#
# 【实现注记（SERVER 2026-08-26，Windows spawn 实测）】
#   - mp.Queue/Event 不能经 ProcessPoolExecutor.submit 参数传递（标准
#     pickle 拒绝——实测复现）；进度队列经池 initializer/initargs 注入
#     worker 模块全局（ForkingPickler 正门，实测通过），见 worker.py。
#   - 取消令牌=取消标记文件（cancel_dir/<task_id>.cancel，跨进程共享
#     值的文件形态）；worker 在阶段边界轮询（run 内长计算无中断点，
#     core 无协作取消钩子——UF 记档）。
#   - 完成回调经 loop.run_in_executor 的 asyncio 包装（executor→loop
#     桥内建于 asyncio）；进度桥显式用 run_coroutine_threadsafe（R3）。
#   - S2 落盘化（2026-08-30，D1~D5）+ENG5 重启语义增强（2026-08-31，
#     裁决②）：四时机原子写 registry_dir/<task_id>.json——submit 初档
#     queued/_pump running 迁移/_finish 终态/cancel·shutdown 的 queued
#     终态；start() 恢复记录供读（非终态经 registry.iter_restorable 变换
#     标 failed[InterruptedByRestart]——运行态任务重启后可查；损坏/缺键
#     跳过+warning）；幂等表不恢复（D5）；registry_dir 默认 None=不落盘
#     （既有测试零破坏）。公开数据类迁 jobs/records.py（ENG5 D4——500
#     行预算拆分，from-import 再导出面稳定）。
#   - WP4 TTL 淘汰（2026-09-02 修1+R-1 G1-01）：终态记 finished_at；
#     sweep_expired=registry.sweep_plan+unlink_task_face 薄壳——文件面
#     全清才删条目（失败保留重试防孤儿）+_idem 差量删（A-02）；恢复=新租约。
#   - B3 R4（2026-09-05 结构减压批）：_TaskRecord 注册表条目迁 jobs/
#     records.py（TaskRequest/TaskStatus/Event 同籍天然归宿；纯数据类零
#     manager 状态依赖——桥三方法持 5+ manager 状态故留守），本模块顶部
#     import 再导出（包内 _ 前缀合法；manager._TaskRecord 模块属性访问
#     零波移）。
#
# 【测试要求】状态机全路径、优先级次序、取消（queued/running 两态）、
#   进度事件顺序、shutdown 无泄漏。
#
# 【参照】重写计划 §12.2/§17.1/§16 A5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import heapq
import multiprocessing as mp
import threading
import time
import uuid
from collections.abc import AsyncIterator, Mapping
from concurrent.futures import Executor
from contextlib import suppress
from pathlib import Path
from queue import Empty
from typing import Any, Final

import structlog

from waterprint_server.jobs import registry, worker
from waterprint_server.jobs.records import (  # ENG5 D4 再导出（导出面=__all__，下文）
    Event,
    TaskHandle,
    TaskRequest,
    TaskStatus,
    UnknownTaskError,
    _TaskRecord,  # B3 R4：注册表条目自 records 迁入再导入（包内私有面，下文消费）
)
from waterprint_server.jobs.worker import run_task

_LOGGER = structlog.get_logger(__name__)

# SSE 订阅者事件缓冲上限（背压 R4：满则丢最旧进度事件，状态事件不丢）。
_EVENT_BUFFER: Final[int] = 10**2
_POLL_SECONDS: Final[float] = 1 / 2  # 轮询间隔秒；幂商式保白名单 {0,1,2,10}（ADR-009）
_TERMINAL: Final[tuple[str, ...]] = registry.TERMINAL_STATES  # 终态面单定义（S2 R1 同源）

# 显式再导出面（ENG5 D4——mypy no-implicit-reexport；任务域数据类自 records 迁移）。
__all__ = [
    "Event",
    "Manager",
    "TaskHandle",
    "TaskRequest",
    "TaskStatus",
    "UnknownTaskError",
]


class Manager:
    """任务注册表与调度（单事件循环契约；executor 由应用生命周期注入）。"""

    def __init__(  # noqa: PLR0913  # 装配束冻结签名（registry_dir 可选默认 None=不落盘，S2 D3；WP4 三旋钮同款 None=不启用）
        self,
        executor: Executor,
        *,
        cancel_dir: Path,
        loop: asyncio.AbstractEventLoop,
        progress_queue: mp.Queue[Mapping[str, Any]] | None = None,
        max_concurrent: int = 1,
        registry_dir: Path | None = None,
        artifacts_dir: Path | None = None,
        task_retention_s: int | None = None,
        task_registry_cap: int | None = None,
    ) -> None:
        self._executor = executor
        self._cancel_dir = cancel_dir
        self._registry_dir = registry_dir
        self._artifacts_dir = artifacts_dir
        self._task_retention_s = task_retention_s
        self._task_registry_cap = task_registry_cap
        self._loop = loop
        self._progress_queue = progress_queue if progress_queue is not None else mp.Queue()
        self._max_concurrent = max(1, max_concurrent)
        self._tasks: dict[str, _TaskRecord] = {}
        self._idem: dict[str, str] = {}
        self._pending: list[tuple[int, int, str]] = []  # (-priority, seq, id)：同级 FIFO
        self._seq = 0
        self._running: dict[str, asyncio.Future[Mapping[str, Any]]] = {}
        self._project_subscribers: dict[str, set[asyncio.Queue[Event]]] = {}
        self._stopped = threading.Event()
        self._listener = threading.Thread(
            target=self._listen_progress, name="wp-progress-bridge", daemon=True
        )

    def start(self) -> None:
        """启动进度桥线程（应用 startup 调；重复启动幂等）。"""
        self._cancel_dir.mkdir(parents=True, exist_ok=True)
        self._restore_registry()  # S2 D2：终态记录恢复供读（损坏跳过不炸启动）
        # 进程内执行器（ThreadPool 注入口/测试面）：worker 模块全局直挂本队列；
        # 进程池（spawn）路径由池 initializer 注入子进程——两条通路同一队列。
        worker._PROGRESS_QUEUE = self._progress_queue  # noqa: SLF001  # R3 进度通路注入口
        if not self._listener.is_alive():
            self._listener.start()

    # ── 提交与幂等（§15 工程细节 3：同一事件循环临界区内查重+标记）──

    async def submit(
        self, request: TaskRequest, *, idempotency_key: str | None = None
    ) -> TaskHandle:
        """提交任务；同 idempotency_key 且未终态=返回既有句柄（不重复占池）。"""
        if idempotency_key is not None:
            existing = self._tasks.get(self._idem.get(idempotency_key, ""))
            if existing is not None and not existing.terminal:
                return TaskHandle(existing.task_id)
        task_id = uuid.uuid4().hex
        effective = dict(request.payload)
        effective["task_id"] = task_id  # worker 侧产物命名/进度回址（§18 IPC 面）
        self._tasks[task_id] = _TaskRecord(
            task_id=task_id,
            request=TaskRequest(kind=request.kind, payload=effective, priority=request.priority),
        )
        if idempotency_key is not None:
            self._idem[idempotency_key] = task_id
        heapq.heappush(self._pending, (-request.priority, self._seq, task_id))
        self._seq += 1
        self._persist(self._tasks[task_id])  # ENG5 D1：submit 初档 queued（运行态有痕前提）
        await self._emit(
            self._tasks[task_id], Event("state", task_id, 0.0, "queued", None)
        )
        self._pump()
        return TaskHandle(task_id)

    def bind_snapshot(self, task_id: str, design_digest: str) -> None:
        """快照绑定（R2 calc 规格：任务启动即绑定输入 design 哈希）。"""
        self._record(task_id).snapshot_hash = design_digest

    def snapshot(self, task_id: str) -> str | None:
        """已绑定快照读取（stale 判定面）。"""
        return self._record(task_id).snapshot_hash

    def mark_stale(self, task_id: str) -> None:
        """编辑后标 stale（UI 提示性标记，UF-37——守门在消费侧实时比对）。"""
        record = self._record(task_id)
        record.stale = True
        self._loop.create_task(
            self._emit(record, Event("stale", task_id, record.progress, "stale", None)))

    # ── 查询与取消 ──────────────────────────────────────────────

    def status(self, task_id: str) -> TaskStatus:
        """状态快照（含 failed 的领域异常序列化诊断，R1）。"""
        return self._record(task_id).status()

    def task_ids_for_project(self, project_id: str) -> tuple[str, ...]:
        """项目的全部任务 id（注册序——stale 标记与最近结果集消费面）。"""
        return tuple(
            task_id
            for task_id, record in self._tasks.items()
            if record.request.payload.get("project_id") == project_id
        )

    def cancel(self, task_id: str) -> bool:
        """协作取消（R5）：queued 直接 cancelled；running 置标记文件。

        已终态任务不受取消影响（返回 False——"已完成结果不受取消影响"）。
        """
        record = self._tasks.get(task_id)
        if record is None:
            raise UnknownTaskError(task_id)
        if record.terminal:
            return False
        record.cancel_requested = True
        if record.state == "queued":
            record.state = "cancelled"
            record.finished_at = time.time()  # WP4：终态时间戳（TTL 判定面）
            self._loop.create_task(
                self._emit(record, Event("state", task_id, record.progress, "cancelled", None)))
            self._persist(record)  # ENG5 D1：queued 取消=终态迁移同落盘
            return True
        self._cancel_dir.joinpath(f"{task_id}.cancel").write_text(
            "cancelled", encoding="utf-8"
        )
        return True

    async def events(self, task_id: str) -> AsyncIterator[Event]:
        """单任务事件流（每连接独立，R3；断线清理见 finally，背压见 _emit）。"""
        record = self._record(task_id)
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=_EVENT_BUFFER)
        record.subscribers.add(queue)
        try:
            if record.terminal:  # 事件不重放历史（R3）：连接即当前，终态发快照即收
                yield Event("state", task_id, record.progress, record.state, None)
                return
            while True:
                event = await queue.get()
                yield event
                if event.type == "state" and event.message in _TERMINAL:
                    return
        finally:
            record.subscribers.discard(queue)  # 断线清理：订阅释放无泄漏（R2 events）

    async def project_events(self, project_id: str) -> AsyncIterator[Event]:
        """项目通道流（stale 通知/任务完成——断线即清理）。"""
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=_EVENT_BUFFER)
        self._project_subscribers.setdefault(project_id, set()).add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._project_subscribers[project_id].discard(queue)

    async def shutdown(self, timeout: float) -> Mapping[str, str]:
        """优雅停机：停进度桥→queued 置 cancelled→等 running（超时报告）。"""
        self._stopped.set()
        if self._listener.is_alive():
            self._listener.join(timeout=timeout)
        for _, _, task_id in list(self._pending):
            record = self._tasks.get(task_id)
            if record is not None and record.state == "queued":
                record.state = "cancelled"
                record.finished_at = time.time()  # WP4：终态时间戳（TTL 判定面）
                self._persist(record)  # ENG5 D1：优雅停机终态落盘（重启后保持 cancelled）
        report: dict[str, str] = {}
        if self._running:
            _done, _pending = await asyncio.wait(
                list(self._running.values()), timeout=timeout
            )
            unfinished = sorted(
                task_id
                for task_id, fut in self._running.items()
                if not fut.done()  # 超时未收口：报告待强杀清单（强杀归 executor.shutdown）
            )
            if unfinished:
                report = {"timeout_pending": ",".join(unfinished)}
        self._progress_queue.close()
        return report

    def sweep_expired(self) -> int:
        """WP4 TTL 清扫（修1）：超保留窗/超 cap 终态淘汰——文件面先行（R-1 G1-01）。"""
        victims = registry.sweep_plan(
            ((tid, rec.terminal, rec.finished_at) for tid, rec in self._tasks.items()),
            retention_s=self._task_retention_s, cap=self._task_registry_cap,
            total=len(self._tasks), now=time.time(),
        )
        evicted: set[str] = set()  # 文件面全清者——失败条目保留（终态+超龄下轮复选）
        for task_id in victims:
            if registry.unlink_task_face(self._cancel_dir, self._registry_dir,
                                         self._artifacts_dir, task_id):
                self._tasks.pop(task_id, None)
                evicted.add(task_id)
        self._idem = {k: v for k, v in self._idem.items() if v not in evicted}
        return len(evicted)

    # ── 内部：调度与桥接 ────────────────────────────────────────

    def _persist(self, record: _TaskRecord) -> None:
        """S2 D1/D4+ENG5 D1 薄壳：投影平字段→registry 落盘（序列化面归 jobs/registry.py）。"""
        if self._registry_dir is None:
            return
        try:
            registry.write_record(
                self._registry_dir, record.task_id, registry.task_document(
                    task_id=record.task_id, kind=record.request.kind,
                    payload=record.request.payload, state=record.state,
                    progress=record.progress, stage=record.stage,
                    condition_key=record.condition_key, stale=record.stale,
                    error=record.error, error_type=record.error_type,
                    result=record.result, snapshot_hash=record.snapshot_hash,
                    project_id=record.status().project_id,
                ),
            )
        except OSError as exc:  # R2 R1（DS-03）：落盘失败禁阻断 _pump（调度停摆防线）
            _LOGGER.error("任务注册表落盘失败（调度继续；重启后该任务无档可恢复）",
                          task_id=record.task_id, registry_dir=str(self._registry_dir),
                          reason=f"{type(exc).__name__}: {exc}")

    def _restore_registry(self) -> None:
        """S2 D2 薄壳：iter_restorable 流→_TaskRecord 入册（异常同款跳过；幂等表不恢复）。"""
        if self._registry_dir is None:
            return
        for task_id, document in registry.iter_restorable(self._registry_dir):
            try:
                record = _TaskRecord(
                    task_id=task_id,
                    request=TaskRequest(
                        kind=str(document["kind"]), payload=dict(document["payload"])
                    ),
                    state=str(document["state"]), progress=float(document["progress"]),
                    stage=str(document["stage"]), condition_key=document["condition_key"],
                    stale=bool(document["stale"]), error=document["error"],
                    error_type=document["error_type"], result=document["result"],
                    snapshot_hash=document["snapshot_hash"],
                    finished_at=time.time(),  # WP4：恢复=新租约（读面消费窗完整，见注记）
                )
            except (ValueError, KeyError, TypeError) as exc:
                _LOGGER.warning("任务注册表记录跳过（恢复面 fail-visible 不阻断启动）",
                                task_id=task_id, path=str(self._registry_dir / f"{task_id}.json"),
                                reason=f"{type(exc).__name__}: {exc}")
                continue
            self._tasks[task_id] = record

    def _record(self, task_id: str) -> _TaskRecord:
        record = self._tasks.get(task_id)
        if record is None:
            raise UnknownTaskError(f"任务 {task_id!r} 不在注册表（replicas=1 内存契约）")
        return record

    def _pump(self) -> None:
        """按优先级出队（同级 FIFO，R2）到并发上限。"""
        while len(self._running) < self._max_concurrent and self._pending:
            _, _, task_id = heapq.heappop(self._pending)
            record = self._tasks.get(task_id)
            if record is None or record.state != "queued":
                continue  # 已取消的 queued 任务（cancel 已直接置 cancelled）
            record.state = "running"
            self._persist(record)  # ENG5 D1：running 迁移更新档（崩溃残留可辨原状态）
            cancel_path = self._cancel_dir / f"{task_id}.cancel"
            future = self._loop.run_in_executor(
                self._executor, run_task, dict(record.request.payload), cancel_path
            )
            self._running[task_id] = future

            def _on_done(done: asyncio.Future[Mapping[str, Any]], tid: str = task_id) -> None:
                self._loop.create_task(self._finish(tid, done))

            future.add_done_callback(_on_done)

    async def _finish(self, task_id: str, future: asyncio.Future[Mapping[str, Any]]) -> None:
        """终态迁移（R1 单向；cancelled=已产清单随 result 保留——SVRB §2.3）。"""
        self._running.pop(task_id, None)
        record = self._tasks.get(task_id)
        if record is None:
            return
        failure = future.exception()  # 不经 raise 面：failed 诊断不吞栈（R1）
        outcome: Mapping[str, Any] | None = None
        if failure is None:
            outcome = future.result()
        if record.cancel_requested:
            record.state = "cancelled"
        elif failure is not None:
            record.state = "failed"
            record.error = f"{type(failure).__name__}: {failure}"
            record.error_type = type(failure).__name__
        elif outcome is not None and outcome.get("state") == "cancelled":
            record.state = "cancelled"
        else:
            record.state = "done"
        if outcome is not None:  # SVRB：已产 files/failures 灌入（done/cancelled
            record.result = dict(outcome)  # 两态不丢弃——§2.3 缺陷收口）
        record.finished_at = time.time()  # WP4：终态时间戳（TTL 判定面——三终态同点置位）
        await self._emit(
            record, Event("state", task_id, record.progress, record.state, None)
        )
        self._persist(record)  # S2 D1：终态迁移原子落盘（registry_dir=None=跳过）
        self._pump()

    def _listen_progress(self) -> None:
        """进度桥线程（R3）：mp.Queue 阻塞读 → run_coroutine_threadsafe 入环。"""
        while not self._stopped.is_set():
            try:
                message = self._progress_queue.get(timeout=_POLL_SECONDS)
            except (Empty, EOFError, OSError, ValueError):  # 关闭/超时窗口→轮询至停机
                continue
            if message is None:
                continue
            coroutine = self._route_progress(message)
            try:
                asyncio.run_coroutine_threadsafe(coroutine, self._loop)
            except RuntimeError:
                coroutine.close()  # 环已闭：显式关闭未 await 协程（防悬挂告警）
                break  # teardown 竞态窗口：静默收桥，无消息可再路由

    async def _route_progress(self, message: Mapping[str, Any]) -> None:
        """进度消息路由：更新注册表 + 广播（percent/stage/condition_key）。"""
        record = self._tasks.get(str(message.get("task_id", "")))
        if record is None or record.terminal:
            return
        record.progress = float(message.get("percent", record.progress))
        record.stage = str(message.get("stage", record.stage))
        record.condition_key = message.get("condition_key")
        await self._emit(
            record,
            Event(
                "progress",
                record.task_id,
                record.progress,
                record.stage,
                record.condition_key,
            ),
        )

    async def _emit(self, record: _TaskRecord, event: Event) -> None:
        """广播（R4 背压：满丢最旧进度；state/stale 事件不丢）。"""
        targets: list[asyncio.Queue[Event]] = [*record.subscribers]
        project_id = record.request.payload.get("project_id")
        if project_id is not None:
            targets += [*self._project_subscribers.get(str(project_id), set())]
        for queue in targets:  # 本函数内无 await：检查-让位-入队是单环临界区
            if event.type == "progress":
                if queue.full():
                    with suppress(asyncio.QueueEmpty):
                        queue.get_nowait()  # 丢最旧进度事件（保序最新状态）
            else:
                while queue.full():
                    try:
                        queue.get_nowait()  # 状态事件不丢：让位最旧项
                    except asyncio.QueueEmpty:
                        break
            queue.put_nowait(event)
