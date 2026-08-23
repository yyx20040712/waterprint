"""进程池工作函数入口：序列化边界 + core 调用 + 进度上报（零业务逻辑）。

输入:  TaskRequest payload（JSON 可序列化）+ 取消令牌 + 进度队列
输出:  任务结果（JSON 可序列化）+ 进度消息序列
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/jobs/test_worker.py）
#
# 【公开接口】
#   run_task(payload: Mapping, cancel_token, progress_queue) -> Mapping
#       进程池 submit 的顶层函数（pickle 边界上的唯一函数面）
#
# 【行为规格】
#   R1 序列化边界（§18 IPC 行）：payload/结果只含经校验的基本类型
#      （字符串/数值/列表/映射）——外部输入先过 schema 再进 IPC，
#      永不 pickle 任意对象图。
#   R2 调用映射：kind → app L4 入口（calc→run_full_calc、enumerate→
#      run_enumeration、export_batch→export_artifact；SENS-B 2026-08-23
#      UF-33——一律经 waterprint.app 用例面，不直连 L3 子系统）；
#      映射表集中一处，禁止散落 if。
#   R3 进度上报：阶段百分比 + condition_key（逐工况粒度）；
#      大结果写 arrow 文件返回路径句柄（§16 A6），不整包过 pickle；
#      落盘一律临时文件+同分区 rename 原子写（GR-38，SENS-B
#      2026-08-23 UF-38）。
#   R4 取消协作：每阶段/每批迭代检查令牌；置位 → 清理临时产物 →
#      返回 cancelled 状态（不写半途结果）。
#   R5 导入零副作用：本模块 import 不创建池/不连队列（Windows
#      spawn 重复导入安全，AGENTS §1）。
#
# 【测试要求】各 kind 映射、取消清理、大结果走文件、异常序列化
#   （领域异常诊断字段完整）。
#
# 【参照】重写计划 §12.2/§16 A6/§18
# ══════════════════════════════════════════════════════════════════
