"""枚举服务用例：单单元枚举任务的编排与结果分页（ADR-005 语义守护）。

输入:  项目 id + unit_id + 网格/约束覆盖 + 排序分页参数
输出:  任务句柄 / 分页方案集 / 诊断报告
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_enumeration.py）
#
# 【公开接口】
#   submit_enumeration(project_id, unit_id, options) -> TaskHandle
#   fetch_solutions(task_id, page, size, sort) -> SolutionPage
#   fetch_diagnosis(task_id) -> DiagnosisReport（无解时）
#
# 【行为规格】
#   R1 语义守护：枚举对象永远是单单元（ADR-005）——请求携带多个
#      unit_id = 422 拒绝（服务层显式拒绝，防语义滑坡成全厂枚举）。
#   R2 分页默认 200/页（§12.2）；排序参数白名单（字段 ID 或
#      margin_min/cost），tie_break 固定（solution.ranking R1）。
#   R3 结果存储：万级行落 arrow 文件（任务产物目录，按 task_id +
#      三元组命名）；页请求按需重载（§16 A6——不整包回传）。
#   R4 无解交付：pass_matrix 全 False → diagnosis 端点可用
#      （最小冲突集 + 建议）；任务状态 done + feasible_count=0
#      是合法终态（不是 failed）。
#
# 【测试要求】多单元拒绝、分页/排序白名单、arrow 重载、
#   无解合法终态。
#
# 【参照】重写计划 §12.2/§12.4/§16 A6；ADR-005
# ══════════════════════════════════════════════════════════════════
