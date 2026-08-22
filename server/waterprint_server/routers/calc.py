"""计算/枚举任务端点：触发、状态、结果分页、方案应用。

输入:  任务请求（项目 id + 工况选择 / 枚举请求：unit_id + 网格 + 约束覆盖）
输出:  任务句柄（task_id）/ 状态 / 分页结果
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_calc.py）
#
# 【端点集（v1 冻结）】
#   POST /api/calc/run                 全流程计算（异步任务，返 task_id）
#   POST /api/calc/enumerate           单单元枚举任务（ADR-005 语义）
#   GET  /api/calc/tasks/{task_id}     状态（queued/running/done/
#                                      cancelled/failed + stale 标志）
#   POST /api/calc/tasks/{task_id}/cancel   取消（协作令牌）
#   GET  /api/calc/tasks/{task_id}/solutions?page=&size=   分页结果
#                                      （默认 200/页 §12.2）
#   POST /api/calc/solutions/apply     方案应用（原子写 design + 新 hash
#                                      + 触发重算 §17.1）
#
# 【行为规格】
#   R1 幂等（§15 工程细节 3）：提交键 = (design_hash, condition/
#      enumerate 语义)——重复提交返回既有 task_id（不重复占进程池）。
#   R2 任务快照绑定：任务启动即绑定 design_hash；运行期间编辑 →
#      任务完成后结果标 stale=true（响应显式字段，禁止静默覆盖 §17.1）。
#   R3 取消协作语义：取消请求 → 令牌置位 → worker 每批迭代检查；
#      已完成结果不受取消影响。
#   R4 结果分页与排序参数透传 solution.ranking；万级枚举结果不整包
#      返回（分页 + 按 arrow 文件按需重载 §16 A6）。
#   R5 方案应用原子性：design 写入 + hash 更新 + 缓存失效 + 触发重算
#      为一个事务性服务调用（services/calculation.py）；失败回滚。
#
# 【测试要求】幂等提交、stale 标志、取消流、分页边界、
#   方案应用原子性（失败不半写）。
#
# 【参照】重写计划 §12.2/§17.1/§16 A6；ADR-005
# ══════════════════════════════════════════════════════════════════
