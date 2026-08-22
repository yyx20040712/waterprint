"""导出端点：计算书/图纸/概算/审计报告的文件流输出。

输入:  导出选项（kind + condition_key + 单元选择）
输出:  文件流（Content-Disposition 附带安全文件名）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_exports.py）
#
# 【端点集（v1 冻结）】
#   POST /api/exports/calcbook          Excel 计算书（trace.calcbook）
#   POST /api/exports/audit             HTML 审计报告（trace.audit）
#   POST /api/exports/dxf               图纸包（单单元/全厂；M2 起）
#   POST /api/exports/estimate          概算表（M3 起）
#   GET  /api/exports                   已生成产物列表（含三元组摘要）
#
# 【行为规格】
#   R1 消费最近完成结果集（绑定三元组）；若 stale，响应 409 附
#      "输入版本"信息，用户显式选择"导出旧结果"（?force=1）或先重算
#      （§17.1 导出行——禁止静默导出旧结果冒充新结果）。
#   R2 导出走任务队列（批量出图 30 张类请求，优先级低于交互计算
#      §17.1 优先级：交互计算 > 枚举 > 批量导出）。
#   R3 输出路径：Settings.exports_dir 内命名（项目 id + kind +
#      condition + 时间基三元组摘要——确定性命名，禁当前时钟进文件名）；
#      文件名白名单字符集（Content-Disposition 转义）。
#   R4 大文件流式响应（StreamingResponse）；DXF/Excel 均为产物文件
#      读取流，不在内存拼装超大包。
#
# 【测试要求】stale 409 与 force 语义、文件名安全、流式完整性、
#   队列优先级。
#
# 【参照】重写计划 §17.1/§18 路径安全
# ══════════════════════════════════════════════════════════════════
