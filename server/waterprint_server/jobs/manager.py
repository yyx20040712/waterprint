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
#   R3 进度通路：worker → multiprocessing.Queue → asyncio 桥
#      （run_coroutine_threadsafe）→ events()；事件含
#      {percent, stage, condition_key}。
#   R4 单进程假设（§16 A5）：注册表在内存，api replicas=1 部署契约；
#      多副本 = 未来 Redis 化（ADR 记录，不做）。
#   R5 取消语义：令牌经共享值传递，worker 每批迭代检查（§12.2）；
#      取消后结果不落地（半途结果丢弃）。
#
# 【测试要求】状态机全路径、优先级次序、取消（queued/running 两态）、
#   进度事件顺序、shutdown 无泄漏。
#
# 【参照】重写计划 §12.2/§17.1/§16 A5
# ══════════════════════════════════════════════════════════════════
